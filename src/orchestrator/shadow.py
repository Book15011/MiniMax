"""Shadow mode (Phase C) for book_orch: the team's paper bot, with book_orch's per-coin decision log.

    python -m src.orchestrator.shadow seed   --state-dir results/book/shadow/a          once, as `src.live.runner seed`
    python -m src.orchestrator.shadow run    --bot a  --state-dir results/book/shadow/a  every layer off (= vt_mom)
    python -m src.orchestrator.shadow run    --bot e5 --state-dir results/book/shadow/e5 E (staged entries) at band 0.05
    python -m src.orchestrator.shadow export --root results/book/shadow --out reports/shadow [--date D] [--loop]
    python -m src.orchestrator.shadow parity --bot a --state-dir results/book/shadow/a

- run: builds the paper runner exactly as `python -m src.live.runner run --mode paper --model book_orch
  --state-dir <dir>` does: src.live.runner.build, unchanged. That means public prices, no keys and no orders; the
  state, the price store and the runner's own JSONL logs stay in the state directory. The bot's layer switches are
  set in memory (config.yaml is not changed).
- Only the model object is wrapped. Its targets() returns explain()'s targets, which are the same (tested), and keeps
  the records. After each hour the runner processes, <state-dir>/shadow/<YYYYMMDD>.jsonl gets:
  - one line per coin: coin_log's signals, decision, reason and target, plus the hour's would-be (paper) orders and
    fills, the coin's close and its weight after the hour;
  - one line for the hour: paper equity, gross, universe.
  A failure in this logging is logged and never stops the bot.
- export: with --loop it runs every day at 00:30 UTC. It writes one markdown summary of the previous UTC day per bot,
  reports/shadow/<YYYYMMDD>-<bot>.md: per coin, its decisions, reasons, would-be orders and paper P&L, plus the day's
  totals. It contains paper (simulated) amounts only: no keys and no account data.
- parity: replays the logged hours in the backtest's view (the research panel through backtest.data and
  engine.view_frames, with the point-in-time universe), once the panel covers them. It compares targets, decisions
  and reasons with the logs and writes <state-dir>/shadow/parity.json.

Shadow P&L is never used to decide anything.
"""
from __future__ import annotations

import argparse
import collections
import copy
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import binance_symbol, load_config, resolve

MODEL_NAME = "book_orch"
BOTS = {"a": {}, "e5": {"stage": {"enabled": True}}}         # layer switches on top of config.yaml's book_orch block
TRADE_STEPS = ("rebalance", "guard", "keep_alive", "endgame")
HOUR = pd.Timedelta(hours=1)


def bot_params(cfg: dict, bot: str) -> dict:
    p = copy.deepcopy(cfg["models"][MODEL_NAME])
    for k, v in BOTS[bot].items():
        p[k] = {**p[k], **v}
    return p


class ExplainProxy:
    """book_orch with targets() routed through explain(): the same targets, and the records kept for the log."""

    def __init__(self, model):
        self.inner, self.spec, self.last = model, model.spec, None

    def targets(self, view):
        w, rec = self.inner.explain(view)
        self.last = (view, w, rec)
        return w


def _num(x) -> float | None:
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return x if np.isfinite(x) else None


def hour_records(bot: str, H: pd.Timestamp, last, events: list[tuple[str, dict]], commit: str) -> list[dict]:
    """The shadow lines of one processed hour (pure): one per coin of book_orch's coin_log, then one for the hour."""
    snap = next((d for e, d in reversed(events) if e == "snapshot"), {})
    dec = next((d for e, d in events if e == "decision"), {})
    orders: dict[str, list] = collections.defaultdict(list)
    fills: dict[str, list] = collections.defaultdict(list)
    for e, d in events:
        if e not in TRADE_STEPS:
            continue
        for o in d.get("orders") or []:
            orders[binance_symbol(o["pair"])].append({"step": e, "kind": o["kind"], "usd": _num(o.get("est_value")),
                                                      "reason": o.get("reason")})
        for f in d.get("fills") or []:
            o = f.get("order") or {}
            if o.get("pair"):
                fills[binance_symbol(o["pair"])].append({"step": e, "kind": o.get("kind"), "status": f.get("status"),
                                                         "price": _num(f.get("price")), "qty": _num(f.get("qty")),
                                                         "fee": _num(f.get("fee"))})
    weights = {binance_symbol(p): float(x) for p, x in (snap.get("weights") or {}).items()}
    lines = []
    w = pd.Series(dtype=float)
    if last is not None:
        from src.models.book.book_orch import coin_log
        view, w, rec = last
        recs = coin_log(view, w, rec, None, view.params)
        seen = {r["coin"] for r in recs}
        for c in sorted((set(orders) | set(fills) | {k for k, x in weights.items() if x}) - seen):
            recs.append({"coin": c, "hour": view.t.isoformat(), "signals": None, "probabilities": None,
                         "decision": "none", "reason": "not in the model's records (guard or keep-alive)", "size": 0.0})
        for r in recs:
            c = r["coin"]
            close = view.close[c].iloc[-1] if c in view.close.columns else np.nan
            lines.append({"type": "coin", "bot": bot, "bar": str(H), **r, "close": _num(close),
                          "weight_after": weights.get(c, 0.0), "orders": orders.get(c, []), "fills": fills.get(c, [])})
    lines.append({"type": "hour", "bot": bot, "bar": str(H), "commit": commit, "decided": last is not None,
                  "equity": _num(snap.get("equity")), "gross": _num(snap.get("gross")),
                  "usd_free": _num(snap.get("usd_free")), "universe": list(dec.get("universe") or []),
                  "targets": {k: float(x) for k, x in w.items()}, "weights": weights,
                  "n_orders": sum(len(v) for v in orders.values()),
                  "fees": float(sum(f["fee"] or 0.0 for v in fills.values() for f in v if f["status"] == "FILLED")),
                  "steps": [e for e, _ in events]})
    return lines


def append_lines(d: Path, H: pd.Timestamp, lines: list[dict]) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{H:%Y%m%d}.jsonl"
    with open(p, "a") as fh:
        for x in lines:
            fh.write(json.dumps(x, default=str) + "\n")
    return p


def run(bot: str, state_dir: str, once: bool, log: logging.Logger) -> None:
    from src.live import runner as R
    from src.live.broker import PaperAccount
    cfg = load_config()
    cfg["live"]["state_dir"] = state_dir
    cfg["models"][MODEL_NAME] = bot_params(cfg, bot)
    rn = R.build(cfg, argparse.Namespace(mode="paper", model=MODEL_NAME, long_only=False, once=once), log)
    assert rn.mode == "paper" and rn.client.creds is None and isinstance(rn.broker, PaperAccount), "paper only, no keys"
    proxy = ExplainProxy(rn.model)
    rn.model = proxy
    events: list[tuple[str, dict]] = []
    emit0, process0 = rn.emit, rn.process
    out = resolve(state_dir) / "shadow"

    def emit(event: str, **data) -> None:
        events.append((event, data))
        emit0(event, **data)

    def process(H: pd.Timestamp) -> None:
        events.clear()
        proxy.last = None
        process0(H)
        try:
            append_lines(out, H, hour_records(bot, H, proxy.last, events, rn.commit))
        except Exception:                                  # noqa: BLE001 - the log must never stop the bot
            log.exception("shadow log failed for %s", H)

    rn.emit, rn.process = emit, process
    rn.run(once=once)


# ---------------------------------------------------------------- daily summary ---------------------------------------

def read_lines(d: Path, days: list[pd.Timestamp]) -> list[dict]:
    out = []
    for day in days:
        p = d / f"{day:%Y%m%d}.jsonl"
        if p.exists():
            out += [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    return out


def coin_pnl(lines: list[dict], day: pd.Timestamp) -> tuple[dict[str, float], dict[str, float]]:
    """Approximate paper P&L per coin over the UTC day. It sums, over the hours, the previous hour's equity x the
    coin's weight after the previous hour x the coin's return to this hour's close, then subtracts the coin's paper
    fees for the day."""
    hours = {pd.Timestamp(x["bar"]): x for x in lines if x["type"] == "hour"}
    close: dict[str, dict] = collections.defaultdict(dict)
    for x in lines:
        if x["type"] == "coin" and x.get("close") is not None:
            close[x["coin"]][pd.Timestamp(x["bar"])] = x["close"]
    pnl: dict[str, float] = collections.defaultdict(float)
    fees: dict[str, float] = collections.defaultdict(float)
    for H in sorted(t for t in hours if day <= t < day + pd.Timedelta(days=1)):
        prev = hours.get(H - HOUR)
        if prev is not None and prev.get("equity"):
            for c, wt in (prev.get("weights") or {}).items():
                p0, p1 = close[c].get(H - HOUR), close[c].get(H)
                if wt and p0 and p1:
                    pnl[c] += prev["equity"] * wt * (p1 / p0 - 1.0)
    for x in lines:
        if x["type"] == "coin" and day <= pd.Timestamp(x["bar"]) < day + pd.Timedelta(days=1):
            fees[x["coin"]] += sum(f["fee"] or 0.0 for f in x.get("fills") or [] if f.get("status") == "FILLED")
    for c in fees:
        pnl[c] -= fees[c]
    return dict(pnl), dict(fees)


def day_summary(bot: str, day: pd.Timestamp, lines: list[dict]) -> str:
    """Markdown summary of one UTC day of one shadow bot (paper amounts only)."""
    end = day + pd.Timedelta(days=1)
    inday = [x for x in lines if day <= pd.Timestamp(x["bar"]) < end]
    hours = sorted((x for x in inday if x["type"] == "hour"), key=lambda x: x["bar"])
    before = sorted((x for x in lines if x["type"] == "hour" and pd.Timestamp(x["bar"]) < day), key=lambda x: x["bar"])
    e0 = (before[-1] if before else (hours[0] if hours else {})).get("equity")
    e1 = hours[-1]["equity"] if hours else None
    pnl, fees = coin_pnl(lines, day)
    per: dict[str, dict] = collections.defaultdict(lambda: {"hours_held": 0, "decisions": collections.Counter(),
                                                            "reasons": collections.Counter(), "orders": 0,
                                                            "buy_usd": 0.0, "sell_usd": 0.0, "filled": 0})
    for x in inday:
        if x["type"] != "coin":
            continue
        s = per[x["coin"]]
        s["hours_held"] += int((x.get("weight_after") or 0.0) > 0)
        if x.get("decision") not in (None, "none", "hold"):
            s["decisions"][x["decision"]] += 1
            s["reasons"][x.get("reason") or ""] += 1
        for o in x.get("orders") or []:
            s["orders"] += 1
            s["buy_usd" if o["kind"] in ("BUY", "SHORT_CLOSE") else "sell_usd"] += o.get("usd") or 0.0
        s["filled"] += sum(f.get("status") == "FILLED" for f in x.get("fills") or [])
    layers = json.dumps(BOTS[bot]) if BOTS[bot] else "every layer off (= vt_mom)"
    md = [f"# Shadow bot `{bot}`: {day:%Y-%m-%d} (UTC)", "",
          f"book_orch in paper mode (public prices, no orders, no keys). Layers: {layers}.",
          "Shadow P&L is never used to decide anything. Paper amounts only.", "",
          "| Day total | Value |", "|---|---|",
          f"| Hours logged | {len(hours)} of 24 |"]
    if e0 and e1:
        md += [f"| Paper equity, start / end | {e0:,.2f} / {e1:,.2f} |",
               f"| Paper P&L | {e1 - e0:+,.2f} ({(e1 / e0 - 1) * 100:+.3f}%) |"]
    else:
        md += ["| Paper equity | n/a |"]
    md += [f"| Would-be orders / filled on paper | {sum(s['orders'] for s in per.values())} / "
           f"{sum(s['filled'] for s in per.values())} |",
           f"| Paper fees | {sum(fees.values()):,.2f} |",
           f"| Last commit | {hours[-1]['commit'] if hours else 'n/a'} |", "",
           "| Coin | Hours held | Decisions (not hold) | Main reason | Would-be orders | Buy / sell USD | Paper P&L (approx.) |",
           "|---|---|---|---|---|---|---|"]
    for c in sorted(set(per) | set(pnl), key=lambda c: (-abs(pnl.get(c, 0.0)), c)):
        s = per[c]
        dec = ", ".join(f"{k} {n}" for k, n in s["decisions"].most_common()) or "-"
        why = s["reasons"].most_common(1)[0][0] if s["reasons"] else "-"
        md.append(f"| {c} | {s['hours_held']} | {dec} | {why} | {s['orders']} | {s['buy_usd']:,.0f} / "
                  f"{s['sell_usd']:,.0f} | {pnl.get(c, 0.0):+,.2f} |")
    md += ["", "Per-coin P&L is an approximation: over the hours, the previous hour's paper equity x the coin's weight "
               "after it x the coin's return to the next close, minus its paper fees. The day's equity change is exact."]
    return "\n".join(md) + "\n"


def export(root: Path, out: Path, day: pd.Timestamp, log: logging.Logger) -> list[Path]:
    written = []
    for bot in BOTS:
        lines = read_lines(root / bot / "shadow", [day - pd.Timedelta(days=1), day])
        if not any(x["type"] == "hour" and day <= pd.Timestamp(x["bar"]) < day + pd.Timedelta(days=1) for x in lines):
            log.info("export: no %s lines for %s", bot, day.date())
            continue
        out.mkdir(parents=True, exist_ok=True)
        p = out / f"{day:%Y%m%d}-{bot}.md"
        p.write_text(day_summary(bot, day, lines))
        written.append(p)
        log.info("export: wrote %s", p)
    return written


def export_loop(root: Path, out: Path, log: logging.Logger) -> None:
    while True:
        now = pd.Timestamp.now(tz="UTC")
        nxt = now.floor("D") + pd.Timedelta(minutes=30)
        nxt = nxt if nxt > now else nxt + pd.Timedelta(days=1)
        time.sleep(max(1.0, (nxt - pd.Timestamp.now(tz="UTC")).total_seconds()))
        try:
            export(root, out, nxt.floor("D") - pd.Timedelta(days=1), log)
        except Exception:                                  # noqa: BLE001 - keep the loop alive
            log.exception("export failed")


# ---------------------------------------------------------------- parity ----------------------------------------------

def parity(bot: str, state_dir: str, log: logging.Logger) -> dict:
    """Replay the logged hours that the research panel covers, in the backtest's view, and compare with the logs."""
    from backtest.data import load_market, universe_at
    from backtest.engine import view_frames
    from src.contracts import MarketView, check_targets
    from src.models.book.book_orch import MODEL
    cfg = load_config()
    p = bot_params(cfg, bot)
    d = resolve(state_dir) / "shadow"
    lines = [json.loads(x) for f in sorted(d.glob("2*.jsonl")) for x in f.read_text().splitlines() if x.strip()]
    hours = {pd.Timestamp(x["bar"]): x for x in lines if x["type"] == "hour" and x.get("decided")}
    coins: dict[pd.Timestamp, dict] = collections.defaultdict(dict)
    for x in lines:
        if x["type"] == "coin":
            coins[pd.Timestamp(x["bar"])][x["coin"]] = x
    market = load_market(cfg)
    last = market.close.index[-1]
    out = {"bot": bot, "panel_last_bar": str(last), "logged_hours": len(hours), "replayed": 0, "target_mismatch": [],
           "decision_mismatch": [], "universe_mismatch": 0}
    for H in sorted(t for t in hours if t <= last):
        prev = hours.get(H - HOUR, {}).get("targets") or {}
        c, q = view_frames(market.close, market.quote_volume, H)
        v = MarketView(t=H, close=c, quote_volume=q, universe=universe_at(market, H), params=p,
                       prev_targets=pd.Series(prev, dtype=float))
        w, rec = MODEL.explain(v)
        w = check_targets(w, v, MODEL.spec)
        logged = pd.Series(hours[H]["targets"], dtype=float)
        u = w.index.union(logged.index)
        diff = w.reindex(u).fillna(0.0) - logged.reindex(u).fillna(0.0)
        out["replayed"] += 1
        out["universe_mismatch"] += int(set(v.universe) != set(hours[H]["universe"]))
        if len(diff) and float(diff.abs().max()) > 1e-9:
            out["target_mismatch"].append({"bar": str(H), "max_abs_diff": float(diff.abs().max()),
                                           "coins": {k: float(x) for k, x in diff[diff.abs() > 1e-9].items()}})
        for coin, r in rec.items():
            lg = coins[H].get(coin)
            if lg is None or (lg["decision"], lg["reason"]) != (r["decision"], r["reason"]):
                out["decision_mismatch"].append({"bar": str(H), "coin": coin, "replay": [r["decision"], r["reason"]],
                                                 "logged": [lg["decision"], lg["reason"]] if lg else None})
    (d / "parity.json").write_text(json.dumps(out, indent=1))
    log.info("parity %s: %d of %d logged hours covered by the panel (through %s); target mismatches %d, decision "
             "mismatches %d, universe mismatches %d", bot, out["replayed"], len(hours), last, len(out["target_mismatch"]),
             len(out["decision_mismatch"]), out["universe_mismatch"])
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seed")
    s.add_argument("--state-dir", required=True)
    r = sub.add_parser("run")
    r.add_argument("--bot", choices=sorted(BOTS), required=True)
    r.add_argument("--state-dir", required=True)
    r.add_argument("--once", action="store_true")
    e = sub.add_parser("export")
    e.add_argument("--root", default="results/book/shadow")
    e.add_argument("--out", default="reports/shadow")
    e.add_argument("--date", default=None, help="the UTC day to summarize (default: yesterday)")
    e.add_argument("--loop", action="store_true", help="every day at 00:30 UTC, the previous day")
    q = sub.add_parser("parity")
    q.add_argument("--bot", choices=sorted(BOTS), required=True)
    q.add_argument("--state-dir", required=True)
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    log = logging.getLogger("shadow")
    if a.cmd == "seed":
        from src.live import runner as R
        return R.main(["seed", "--state-dir", a.state_dir])
    if a.cmd == "run":
        run(a.bot, a.state_dir, a.once, log)
    elif a.cmd == "export":
        root, out = resolve(a.root), resolve(a.out)
        if a.loop:
            export_loop(root, out, log)
        day = pd.Timestamp(a.date, tz="UTC") if a.date else pd.Timestamp.now(tz="UTC").floor("D") - pd.Timedelta(days=1)
        export(root, out, day, log)
    else:
        parity(a.bot, a.state_dir, log)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
