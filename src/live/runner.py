"""The live bot: one registered model, every hour, on Roostoo (paper or live).

    python -m src.live.runner seed                      once: copy the research panel's last history_days to the store
    python -m src.live.runner run [--once] [--mode paper|live] [--model NAME] [--long-only]

Each completed hour bar H (UTC), about `process_after_s` after the hour:
1. Top up the hourly store (src/live/feed.py); read quotes and holdings.
2. Decision: at the model's decision hours (16:00 UTC + k x rebalance_hours), or when one is overdue, the model
   sees the same MarketView as in the backtest: bars up to H, the universe by Book's rule
   (src.validation.features) on complete data, cut to Roostoo, and its own previous targets. Hours no source
   could fill (the bot was down and Binance's API is unreachable) are carried forward up to `max_fill_hours`,
   as the backtest engine carries prices; without that, a model that needs a full 30 days of bars sees none. The shared planner
   turns targets into orders (the first decision trades every difference, later ones only beyond the band).
3. Activity guard, as backtest/engine.py: from hour `activity_guard_offset_hours` + 1 of the HKT day on (04:00 UTC
   with the proposed 11), if the day has no confirmed trade yet, rebalance exactly to the standing targets; if that
   needs no order, make the keep-alive trade (0.2% of equity more BTC, or that much less of the largest holding).
   A fill counts only when the account's positions moved (an order response alone is not proof), and an
   unconfirmed guard is retried every later hour of the same day. With `harness.guard_utc_day`, the guard also
   fires when the day's only confirmed trades came before 00:00 UTC, so the day counts in UTC and in HKT.
4. Log every step as one JSONL line (git commit stamped, no keys) and save the state atomically.
Live trades about an hour earlier than the backtest assumes (it lags fills by one bar), so the backtest is the
conservative side. Hours, days and the start time run on Roostoo's server clock (machine clock plus the offset
measured every hour); the offset is logged, with a warning above clock_warn_s. Restarts resume from the state file; missed hours are not replayed, an overdue decision or
guard runs at the next hour. In live mode, before `live.start_at` the bot only records bars. A committed change of
`live.model` takes effect at the next hour (the new model decides at once; active days are kept); paper and
live never share a state file. If the exchange refuses a short, the bot trades long-only from then on.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from src.api.client import RoostooClient, load_credentials
from src.api.rules import parse_exchange_info
from src.config import REPO_ROOT, binance_symbol, load_config, resolve, universe
from src.contracts import MarketView, check_targets
from src.execution.planner import Holdings, ShortPos, current_weights, equity, plan_orders
from src.live import feed
from src.live.broker import LiveBroker, PaperAccount, ShortsUnreadable, quotes_from_ticker
from src.models import get
from src.validation.features import daily_bars, is_allowed

HOUR = pd.Timedelta(hours=1)


# ---------------- pure helpers (tested) ----------------

def live_universe(close: pd.DataFrame, qv: pd.DataFrame, t: pd.Timestamp, vcfg: dict, allowed: set[str]) -> tuple:
    """Book's universe rule (StateEngine.universe) at grid time t, then cut to the Roostoo list as
    backtest.data.load_market does: top-N eligible series by trailing quote volume, ties by name."""
    u, hour = vcfg["universe"], vcfg["grid_hour_utc"]
    close_d, qv_d, exists = daily_bars(close.loc[:t], qv.loc[:t], hour)
    if t not in close_d.index:
        return ()
    hist_before = exists.cumsum().shift(1, fill_value=0).loc[t]
    ok = exists.loc[t] & (hist_before >= u["min_history_days"])
    ok &= pd.Series([is_allowed(c, u) for c in close_d.columns], index=close_d.columns)
    q = qv_d.rolling(u["volume_days"], min_periods=1).sum().loc[t][ok]
    ranked = sorted(q.index, key=lambda c: (-q[c], c))[: u["top_n"]]
    return tuple(sorted(c for c in ranked if c in allowed))


def day_start(t: pd.Timestamp, grid_hour: int) -> pd.Timestamp:
    """Start (UTC) of the HKT trading day that contains bar time t."""
    off = pd.Timedelta(hours=grid_hour)
    return (t - off).floor("D") + off


def keep_alive_targets(h: Holdings, quotes: dict, eq: float, ka: float, cap: float, pair: str = "BTC/USD") -> dict:
    """backtest.engine.Simulator._nudge on the account: ka more of `pair`, or ka less of the largest holding."""
    w = current_weights(h, quotes, eq)
    t = dict(w)
    if sum(abs(x) for x in w.values()) + ka <= cap:
        t[pair] = t.get(pair, 0.0) + ka
    elif w:
        k = max(w, key=lambda p: abs(w[p]))
        t[k] = w[k] - np.sign(w[k]) * min(ka, abs(w[k]))
    return t


def positions(h: Holdings) -> dict[str, tuple[float, float]]:
    """Coins held and coins shorted per pair, copied: a fill shows up here whatever the order response said."""
    return {p: (float(h.spot.get(p, 0.0)), float(h.shorts[p].qty) if p in h.shorts else 0.0)
            for p in set(h.spot) | set(h.shorts)}


def confirm_fills(fills: list[dict], before: dict, after: dict) -> list[dict]:
    """A fill reported FILLED (or only SENT) whose pair's position did not move becomes UNCONFIRMED."""
    for f in fills:
        p = f["order"].pair
        if f["status"] == "FILLED" and before.get(p, (0.0, 0.0)) == after.get(p, (0.0, 0.0)):
            f["status"] = "UNCONFIRMED"
    return fills


def holdings_to_json(h: Holdings) -> dict:
    return {"usd_free": h.usd_free, "spot": h.spot, "shorts": {p: asdict(s) for p, s in h.shorts.items()}}


def holdings_from_json(d: dict) -> Holdings:
    return Holdings(float(d["usd_free"]), {k: float(v) for k, v in d["spot"].items()},
                    {p: ShortPos(**s) for p, s in d["shorts"].items()})


# ---------------- the runner ----------------

class Runner:
    def __init__(self, cfg: dict, model_name: str, mode: str, broker, client: RoostooClient, state_dir: Path,
                 log: logging.Logger, long_only: bool = False, rest=None, archive=None):
        self.cfg, self.mode, self.broker, self.client, self.dir, self.log = cfg, mode, broker, client, state_dir, log
        self.lv, self.h, self.ex, self.v = cfg["live"], cfg["harness"], cfg["execution"], cfg["validation"]
        self.model = get(model_name)
        self.params = (cfg.get("models") or {}).get(model_name, {}) or {}
        self.long_only = long_only or not self.model.spec.uses_shorts
        self.pairs = {binance_symbol(p): p for p in universe(cfg)}
        self.rest, self.archive = rest, archive
        self.state_path = state_dir / "state.json"
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {
            "model": model_name, "mode": mode, "last_bar": None, "last_decision": None, "prev_targets": {},
            "standing": {}, "active_days": [], "paper": None}
        if self.state["mode"] != mode:
            raise SystemExit(f"state.json is for {self.state['mode']} mode; move it away to start {mode} fresh")
        self.switched_from = None
        if self.state["model"] != model_name:             # a committed model change (e.g. the team_cash exit)
            self.switched_from = self.state["model"]
            self.state.update(model=model_name, prev_targets={}, standing={}, last_decision=None)
        self.long_only = self.long_only or bool(self.state.get("long_only"))
        self.start_at = (pd.Timestamp(self.lv["start_at"]).tz_localize("UTC")      # live only: paper is a rehearsal
                         if mode == "live" and self.lv.get("start_at") else None)
        self.store = feed.Store.load(state_dir)
        self.rules = parse_exchange_info(client.exchange_info())
        self.commit = subprocess.run(["git", "rev-parse", "--short=12", "HEAD"], cwd=REPO_ROOT, capture_output=True,
                                     text=True).stdout.strip()

    # -- logging and state
    def emit(self, event: str, **data) -> None:
        line = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "event": event, "model": self.model.spec.name,
                "mode": self.mode, "commit": self.commit, **data}
        d = self.dir / "logs"
        d.mkdir(parents=True, exist_ok=True)
        with open(d / f"{datetime.now(timezone.utc):%Y%m%d}.jsonl", "a") as fh:
            fh.write(json.dumps(line, default=str) + "\n")

    def save(self) -> None:
        if self.mode == "paper":
            self.state["paper"] = holdings_to_json(self.broker.h)
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=1, default=str))
        tmp.replace(self.state_path)

    # -- one hour
    def due_decision(self, H: pd.Timestamp) -> bool:
        rb = self.model.spec.rebalance_hours
        last = self.state["last_decision"]
        on_grid = (H.hour - self.h["grid_hour_utc"]) % rb == 0
        return last is None or on_grid or H - pd.Timestamp(last) >= pd.Timedelta(hours=rb)

    def trade(self, kind: str, H: pd.Timestamp, targets: dict, h: Holdings, quotes: dict, band: float,
              exact: bool) -> list[dict]:
        orders, notes = plan_orders(targets, h, quotes, self.rules, band, self.ex["fee"], self.ex["cash_buffer"],
                                    self.ex["min_trade_usd"], exact=exact)
        before = positions(h)
        fills = self.broker.execute(orders, quotes, h) if orders else []
        if fills:                                          # confirm from the account, not from the order response
            confirm_fills(fills, before, positions(self.broker.holdings(with_shorts=not self.long_only)))
        refused = [f for f in fills if f["status"] == "ERROR" and f["order"].kind == "SHORT_OPEN"
                   and "not allow" in str(f.get("error", "")).lower()]
        if refused and not self.long_only:                 # "this competition does not allow short positions"
            self.long_only = self.state["long_only"] = True
            self.emit("error", bar=H, error="shorts refused by the exchange; trading long-only from now on")
        self.emit(kind, bar=H, targets=targets, orders=[asdict(o) for o in orders], notes=notes,
                  fills=[{k: (asdict(v) if k == "order" else v) for k, v in f.items()} for f in fills])
        if any(f["status"] == "FILLED" for f in fills):
            self.state["last_fill"] = str(H)
            day = str(day_start(H, self.h["grid_hour_utc"]))
            if day not in self.state["active_days"]:
                self.state["active_days"].append(day)
        return fills

    def process(self, H: pd.Timestamp) -> None:
        ticker = self.client.ticker()
        quotes = quotes_from_ticker(ticker)
        closes = {binance_symbol(p): float(q.get("LastPrice") or 0.0) for p, q in ticker.items()}
        vols = {binance_symbol(p): float(q.get("UnitTradeValue") or 0.0) for p, q in ticker.items()}   # 24 h quote volume
        added = feed.top_up(self.store, H, self.rest, self.archive, lambda: closes, self.log, lambda: vols)
        self.store.trim(int(self.lv["history_days"]))
        self.store.save(self.dir)
        self.emit("feed", bar=H, added=added, complete_through=self.store.complete_through)
        try:
            h = self.broker.holdings(with_shorts=not self.long_only)
        except ShortsUnreadable as e:
            self.long_only = True
            self.emit("error", bar=H, error=f"{e}; trading long-only from now on (UNVERIFIED short format)")
            h = self.broker.holdings(with_shorts=False)
        eq = equity(h, quotes)
        grid = self.h["grid_hour_utc"]
        decided = False
        if self.start_at is not None and H < self.start_at:  # before the round: record data, never trade
            self.emit("snapshot", bar=H, equity=eq, waiting_until=self.start_at)
            self.state["last_bar"] = str(H)
            self.save()
            return
        if self.due_decision(H):
            g = day_start(min(H, self.store.complete_through), grid)
            uni = live_universe(self.store.close, self.store.qv, g, self.v, set(self.pairs))
            close = self.store.close.loc[:H].ffill(limit=int(self.lv["max_fill_hours"]))   # gaps the sources left
            view = MarketView(t=H, close=close, quote_volume=self.store.qv.loc[:H], universe=uni,
                              params=self.params, prev_targets=pd.Series(self.state["prev_targets"], dtype=float))
            w = check_targets(self.model.targets(view), view, self.model.spec)
            if self.long_only:
                w = w.clip(lower=0.0)
            w = w[w != 0.0]
            first = self.state["last_decision"] is None
            self.state.update(prev_targets={k: float(x) for k, x in w.items()}, last_decision=str(H),
                              standing={self.pairs[s]: float(x) for s, x in w.items() if s in self.pairs})
            self.emit("decision", bar=H, universe=uni, universe_as_of=g, equity=eq, first=first,
                      targets=self.state["standing"])
            self.trade("rebalance", H, self.state["standing"], h, quotes, self.model.spec.band, exact=first)
            decided = True
        start = day_start(H, grid)
        into_day = int((H - start) / HOUR)
        no_trade = str(start) not in self.state["active_days"]                   # none yet in this HKT day
        if self.h.get("guard_utc_day") and H.floor("D") > start:                 # or none since 00:00 UTC
            last = self.state.get("last_fill")
            no_trade = no_trade or last is None or pd.Timestamp(last) < H.floor("D")
        if (not decided and no_trade                                             # every later hour of the day retries
                and into_day >= self.h["activity_guard_offset_hours"] + 1):        # until a fill is confirmed
            h = self.broker.holdings(with_shorts=not self.long_only)
            fills = self.trade("guard", H, self.state["standing"], h, quotes, 0.0, exact=True)
            if not any(f["status"] == "FILLED" for f in fills):
                t = keep_alive_targets(h, quotes, equity(h, quotes), float(self.h["keep_alive_weight"]),
                                       1.0 - float(self.ex["cash_buffer"]))
                self.trade("keep_alive", H, t, h, quotes, 0.0, exact=True)
        h = self.broker.holdings(with_shorts=not self.long_only)
        eq = equity(h, quotes)
        w = current_weights(h, quotes, eq)
        self.emit("snapshot", bar=H, equity=eq, usd_free=h.usd_free, gross=sum(abs(x) for x in w.values()),
                  weights=w, active_days=len(self.state["active_days"]))
        self.state["last_bar"] = str(H)
        self.save()

    def latest_bar(self, now: pd.Timestamp) -> pd.Timestamp:
        return (now - pd.Timedelta(seconds=float(self.lv["process_after_s"]))).floor("h")

    def now(self) -> pd.Timestamp:
        """Roostoo server time: the machine's UTC clock plus the offset measured against /v3/serverTime. Hours, days
        and the start time follow the exchange's clock even if the machine drifts."""
        return pd.Timestamp.now(tz="UTC") + pd.Timedelta(milliseconds=float(self.client.offset_ms))

    def check_clock(self, H: pd.Timestamp | None = None) -> float | None:
        """Re-measure the offset to Roostoo's clock; log it, warn above clock_warn_s, error above clock_error_s."""
        try:
            off = float(self.client.sync_clock())
        except Exception as e:                             # noqa: BLE001 - keep the last offset and say so
            self.emit("clock", bar=H, error=f"server time unavailable ({type(e).__name__}); keeping offset "
                                            f"{self.client.offset_ms:.0f} ms")
            return None
        s = abs(off) / 1000.0
        level = "error" if s > float(self.lv["clock_error_s"]) else "warning" if s > float(self.lv["clock_warn_s"]) else "ok"
        self.emit("clock", bar=H, offset_ms=round(off), level=level)
        if level != "ok":
            self.log.warning("machine clock is %+.1f s off Roostoo's; the bot runs on Roostoo's time (%s)", off / 1000, level)
        return off

    def run(self, once: bool = False) -> None:
        self.emit("start", long_only=self.long_only, state=self.state_path, clock_offset_ms=self.check_clock(),
                  switched_from=self.switched_from, start_at=self.start_at)
        while True:
            H = self.latest_bar(self.now())
            if self.state["last_bar"] is None or H > pd.Timestamp(self.state["last_bar"]):
                try:
                    self.check_clock(H)
                    self.process(H)
                except Exception as e:                     # noqa: BLE001 - log, wait, retry; systemd restarts on crash
                    self.log.exception("hour %s failed", H)
                    self.emit("error", bar=H, error=f"{type(e).__name__}: {e}")
                    if once:
                        raise
                    time.sleep(60)
                    continue
            if once:
                return
            nxt = H + HOUR + pd.Timedelta(seconds=float(self.lv["process_after_s"]))
            time.sleep(max(5.0, min(300.0, (nxt - self.now()).total_seconds())))


def clock_report(cfg: dict, samples: int = 3) -> tuple[bool, list[str]]:
    """Machine clock vs Roostoo's, and the operating system's own sync status. For EC2 before going live."""
    import shutil
    c = RoostooClient(cfg["exchange"]["base_url"], None, 10, 10)
    offs = sorted(c.sync_clock() for _ in range(samples))
    off = offs[len(offs) // 2]
    lines = [f"machine UTC   {pd.Timestamp.now(tz='UTC'):%Y-%m-%d %H:%M:%S.%f} UTC",
             f"Roostoo time  {pd.Timestamp.now(tz='UTC') + pd.Timedelta(milliseconds=off):%Y-%m-%d %H:%M:%S.%f} UTC",
             f"offset        {off / 1000:+.3f} s (median of {samples}; Roostoo minus machine)"]
    synced = None
    if shutil.which("timedatectl"):
        r = subprocess.run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"], capture_output=True, text=True)
        synced = r.stdout.strip() == "yes"
        lines.append(f"NTP synced    {r.stdout.strip() or 'unknown'} (timedatectl)")
    if shutil.which("chronyc"):
        r = subprocess.run(["chronyc", "tracking"], capture_output=True, text=True)
        lines += [f"chrony        {ln.strip()}" for ln in r.stdout.splitlines() if ln.startswith(("Reference ID", "System time", "Leap status"))]
    ok = abs(off) / 1000 <= float(cfg["live"]["clock_warn_s"]) and synced is not False
    lines.append("RESULT        " + ("OK" if ok else f"NOT OK: fix the clock before going live (limit {cfg['live']['clock_warn_s']} s, NTP synced)"))
    return ok, lines


def build(cfg: dict, args, log: logging.Logger) -> Runner:
    lv, ex = cfg["live"], cfg["execution"]
    state_dir = resolve(lv["state_dir"])
    if args.mode == "live":
        creds = load_credentials(REPO_ROOT / ex["env_file"])
        if creds.env == "competition" and os.environ.get("MM_HOST") != "ec2":
            raise SystemExit("ROOSTOO_ENV=competition outside EC2: refused (AGENTS.md rule 3)")
    else:
        creds = None
    client = RoostooClient(cfg["exchange"]["base_url"], creds, ex["calls_per_minute"], ex["timeout_s"], log=log)
    if args.mode == "live":
        broker = LiveBroker(client, log, float(lv["order_spacing_s"]))
    else:
        st = state_dir / "state.json"
        paper = json.loads(st.read_text()).get("paper") if st.exists() else None
        h = holdings_from_json(paper) if paper else Holdings(float(lv["paper_equity"]))
        broker = PaperAccount(h, parse_exchange_info(client.exchange_info()), lambda: quotes_from_ticker(client.ticker()),
                              float(ex["fee"]))
    rest = feed.rest_fetcher(lv["binance_rest"]) if lv.get("binance_rest") else None
    archive = feed.archive_fetcher(cfg["data"]["base_url"]) if lv.get("use_archive", True) else None
    return Runner(cfg, args.model or lv["model"], args.mode, broker, client, state_dir, log, args.long_only, rest, archive)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seed", help="copy the research panel's last history_days into the live store")
    s.add_argument("--panel-dir", default=None)
    r = sub.add_parser("run", help="run the bot")
    r.add_argument("--mode", choices=("paper", "live"), default=None)
    r.add_argument("--model", default=None)
    r.add_argument("--once", action="store_true", help="process the latest completed hour, then exit")
    r.add_argument("--long-only", action="store_true", help="force negative targets to 0 (shorts refused)")
    r.add_argument("--state-dir", default=None, help="another state directory (e.g. a second paper bot)")
    s.add_argument("--state-dir", default=None)
    sub.add_parser("clock", help="machine clock vs Roostoo's, and NTP status (run on EC2 before going live)")
    a = ap.parse_args(argv)
    cfg = load_config()
    lv = cfg["live"]
    if a.cmd == "clock":
        ok, lines = clock_report(cfg)
        print("\n".join(lines))
        return 0 if ok else 1
    if a.state_dir:
        lv["state_dir"] = a.state_dir
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    log = logging.getLogger("live")
    if a.cmd == "seed":
        st = feed.seed(resolve(a.panel_dir or cfg["harness"]["panel_dir"]), int(lv["history_days"]))
        st.save(resolve(lv["state_dir"]))
        log.info("seeded %d series x %d hours, complete through %s", st.close.shape[1], len(st.close), st.complete_through)
        return 0
    a.mode = a.mode or lv["mode"]
    build(cfg, a, log).run(once=a.once)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
