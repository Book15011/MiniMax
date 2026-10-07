"""Tick-scalping sleeve beside the hourly model, on the same Roostoo account (EXPERIMENTAL, off by default).

NOT DEPLOYABLE until AGENTS.md section 2.6 ("directional strategies only: no market-making") is amended through a
reviewed merge. The organisers' public statement (2026-10-05) says tick scalping is not prohibited and won't be
disqualified; the team rule is stricter until changed. 

Runs INSIDE the hourly bot's process (one instance, one process, one API ceiling): src.live.runner starts it as a
thread when `live.sleeve.enabled` (build_in_process). `live.sleeve.mode: paper` trades nothing (fills simulated on
the live quotes); `live` trades the account. Going from paper to live, or changing its capital, is a committed config
change: the usual update (pull, restart).

    python -m src.live.sleeve run --mode paper [--quotes recorder|ticker] [--once]    research server paper runs
    python -m src.live.sleeve status [--mode paper|live]

The loop, per coin (one lot at a time, fixed USD lot):
  BUYING  a resting limit buy. At the start and after a pause it sits at the bid; after a win one step below the
          sell; after a stop one step below the bid. It trails to bid - 1 step once the bid is `trail_steps` above it.
  HOLDING a resting limit sell at entry + 1 step (or at once at the bid, as a taker, if the bid is already there).
          Stop: when the bid is `stop_steps` below entry, cancel the sell and sell at market.
  PAUSED  after `pause_after_stops` stops within `pause_s`, nothing for `pause_s`.
Roostoo's matching (measured on 65 real orders, 2026-10-06/07): a resting buy at P fills once Roostoo's bid <= P;
a resting sell at S once its bid (or mid) >= S. PaperExchange applies exactly that rule to the quotes it sees.

Safety:
- every call goes through the client's limiter (`calls_per_minute`, below the hourly bot's share);
- minutes `runner_window` of every hour belong to the hourly bot: no new orders, quotes every 30 s, stops still run;
- a daily loss limit (from the HKT day's start) stops new buys until the next day; a total loss limit flattens and
  stops the sleeve; so does a KILL file next to the state, or `kill_after_errors` API errors in a row;
- before `live.start_at` nothing trades; from `live.end_at - flatten_before_end_s` the sleeve flattens and stops;
- if the hourly bot's end-of-round lock-in has fired (its state's locked_at) and `respect_lock`, it flattens and stops;
- the state file (cash, coins, open orders) is written atomically every loop; the hourly bot reads `cash_free` from it
  so the model never spends the sleeve's cash or trades its coins (runner: live.sleeve).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Callable, Protocol

import pandas as pd

from src.api.client import OrderStateUnknown, RoostooClient, RoostooError, load_credentials
from src.api.rules import PairRule, fmt, parse_exchange_info, truncate
from src.config import REPO_ROOT, load_config, resolve

MAKER, TAKER = 0.0005, 0.001


# ---------------------------------------------------------------- exchange interface
@dataclass
class Fill:
    status: str                  # FILLED | PENDING | CANCELED | UNKNOWN
    price: float = 0.0
    qty: float = 0.0             # coins traded (before any fee in coin)
    coin_change: float = 0.0     # coins received (+) or given (-) after fees
    usd_change: float = 0.0      # USD received (+) or paid (-) after fees
    order_id: str | None = None
    role: str = ""


class Exchange(Protocol):
    def quotes(self, pairs: list[str]) -> dict[str, tuple[float, float, float]]: ...
    def place_limit(self, pair: str, side: str, qty: Decimal, price: Decimal) -> Fill: ...
    def market_sell(self, pair: str, qty: Decimal) -> Fill: ...
    def cancel(self, pair: str, order_id: str) -> bool: ...
    def order(self, pair: str, order_id: str) -> Fill: ...
    def pending_pairs(self) -> dict[str, int]: ...
    def coins(self, coin: str) -> float: ...


def fill_from_detail(d: dict, side: str) -> Fill:
    """An OrderDetail / OrderMatched row -> Fill. Field names as the API docs give them; CoinChange and UnitChange
    are taken as the account's net changes after fees (UNVERIFIED sign convention: absolute values are used and the
    side sets the sign)."""
    st = str(d.get("Status") or "").upper()
    st = "CANCELED" if st == "CANCELLED" else (st or "UNKNOWN")
    qty = float(d.get("FilledQuantity") or 0.0)
    px = float(d.get("FilledAverPrice") or d.get("Price") or 0.0)
    fee = float(d.get("CommissionChargeValue") or 0.0)
    fee_coin = str(d.get("CommissionCoin") or "")
    cc = d.get("CoinChange")
    uc = d.get("UnitChange")
    if side == "BUY":
        coin = abs(float(cc)) if cc is not None else qty - (fee if fee_coin and fee_coin != "USD" else 0.0)
        usd = -abs(float(uc)) if uc is not None else -(qty * px + (fee if fee_coin == "USD" else 0.0))
    else:
        coin = -abs(float(cc)) if cc is not None else -qty
        usd = abs(float(uc)) if uc is not None else qty * px - (fee if fee_coin in ("USD", "") else 0.0)
    return Fill(st, px, qty, coin, usd, str(d.get("OrderID") or ""), str(d.get("Role") or ""))


class RoostooExchange:
    """The real account. Order calls are never retried (the client raises OrderStateUnknown instead)."""

    def __init__(self, client: RoostooClient):
        self.c = client

    def quotes(self, pairs):
        t = self.c.ticker()
        out = {}
        for p in pairs:
            q = t.get(p) or {}
            b, a, l = float(q.get("MaxBid") or 0), float(q.get("MinAsk") or 0), float(q.get("LastPrice") or 0)
            if b > 0 and a >= b:
                out[p] = (b, a, l)
        return out

    def place_limit(self, pair, side, qty, price):
        return fill_from_detail(self.c.place_order(pair, side, fmt(qty), "LIMIT", fmt(price)), side)

    def market_sell(self, pair, qty):
        return fill_from_detail(self.c.place_order(pair, "SELL", fmt(qty), "MARKET"), "SELL")

    def cancel(self, pair, order_id):
        return bool(self.c.cancel_order(order_id=order_id))

    def order(self, pair, order_id):
        rows = self.c.query_order(order_id=order_id)
        if not rows:
            return Fill("UNKNOWN", order_id=order_id)
        return fill_from_detail(rows[0], str(rows[0].get("Side") or "").upper())

    def pending_pairs(self):
        return {k: int(v) for k, v in (self.c.pending_count().get("OrderPairs") or {}).items()}

    def coins(self, coin):
        b = self.c.balance().get(coin) or {}
        return float(b.get("Free") or 0.0) + float(b.get("Lock") or 0.0)


class PaperExchange:
    """No orders: resting orders fill by Roostoo's measured rule on the quotes this object is shown (buy: bid <= P;
    sell: mid >= S, or bid >= S with sell_rule="bid"). Market sells fill at the bid. Fees as Roostoo charges them."""

    def __init__(self, quote_fn: Callable[[list[str]], dict], sell_rule: str = "mid", usd: float = 0.0):
        self.quote_fn, self.sell_rule = quote_fn, sell_rule
        self.open: dict[str, dict] = {}
        self.done: dict[str, Fill] = {}
        self.held: dict[str, float] = {}
        self.usd = usd
        self.n = 0
        self.last: dict[str, tuple[float, float, float]] = {}

    def _match(self):
        for oid, o in list(self.open.items()):
            q = self.last.get(o["pair"])
            if not q:
                continue
            b, a, _ = q
            ref_s = (a + b) / 2 if self.sell_rule == "mid" else b
            if (o["side"] == "BUY" and b <= o["price"] + 1e-15) or (o["side"] == "SELL" and ref_s >= o["price"] - 1e-15):
                coin = o["pair"].split("/")[0]
                if o["side"] == "BUY":
                    got = o["qty"] * (1 - MAKER)
                    self.held[coin] = self.held.get(coin, 0.0) + got
                    f = Fill("FILLED", o["price"], o["qty"], got, -o["qty"] * o["price"], oid, "MAKER")
                else:
                    usd = o["qty"] * o["price"] * (1 - MAKER)
                    self.held[coin] = self.held.get(coin, 0.0) - o["qty"]
                    self.usd += usd
                    f = Fill("FILLED", o["price"], o["qty"], -o["qty"], usd, oid, "MAKER")
                self.done[oid] = f
                del self.open[oid]

    def quotes(self, pairs):
        self.last.update(self.quote_fn(pairs))
        self._match()
        return {p: self.last[p] for p in pairs if p in self.last}

    def place_limit(self, pair, side, qty, price):
        self.n += 1
        oid = f"paper-{self.n}"
        b, a, _ = self.last[pair]
        qty, price = float(qty), float(price)
        coin = pair.split("/")[0]
        if side == "SELL" and b >= price:                       # marketable: a taker fill at the bid
            usd = qty * b * (1 - TAKER)
            self.held[coin] = self.held.get(coin, 0.0) - qty
            self.usd += usd
            f = Fill("FILLED", b, qty, -qty, usd, oid, "TAKER")
            self.done[oid] = f
            return f
        if side == "BUY":
            self.usd -= qty * price
        self.open[oid] = {"pair": pair, "side": side, "qty": qty, "price": price}
        return Fill("PENDING", price, 0.0, 0.0, 0.0, oid)

    def market_sell(self, pair, qty):
        self.n += 1
        b = self.last[pair][0]
        coin = pair.split("/")[0]
        qty = float(qty)
        usd = qty * b * (1 - TAKER)
        self.held[coin] = self.held.get(coin, 0.0) - qty
        self.usd += usd
        return Fill("FILLED", b, qty, -qty, usd, f"paper-{self.n}", "TAKER")

    def cancel(self, pair, order_id):
        o = self.open.pop(order_id, None)
        if o is None:
            return False
        if o["side"] == "BUY":
            self.usd += o["qty"] * o["price"]
        self.done[order_id] = Fill("CANCELED", o["price"], 0.0, 0.0, 0.0, order_id)
        return True

    def order(self, pair, order_id):
        if order_id in self.open:
            return Fill("PENDING", self.open[order_id]["price"], 0.0, 0.0, 0.0, order_id)
        return self.done.get(order_id, Fill("UNKNOWN", order_id=order_id))

    def pending_pairs(self):
        out: dict[str, int] = {}
        for o in self.open.values():
            out[o["pair"]] = out.get(o["pair"], 0) + 1
        return out

    def coins(self, coin):
        return max(self.held.get(coin, 0.0), 0.0)


def recorder_quotes(path_glob: str, offset_s: float = 0.0) -> Callable[[list[str]], dict]:
    """Quotes from the research server's recorder files (one row per pair every 6 s): the newest row per pair.
    Paper mode on the research server uses this so it adds no calls to Roostoo."""
    import glob

    def fn(pairs):
        files = sorted(glob.glob(path_glob))
        if not files:
            return {}
        with open(files[-1], "rb") as fh:
            fh.seek(0, 2)
            fh.seek(max(0, fh.tell() - 40_000))
            lines = fh.read().decode(errors="ignore").splitlines()[1:]
        out = {}
        for ln in reversed(lines):
            parts = ln.split(",")
            if len(parts) < 5 or parts[1] not in pairs or parts[1] in out:
                continue
            try:
                out[parts[1]] = (float(parts[2]), float(parts[3]), float(parts[4]))
            except ValueError:
                continue
        return out
    return fn


# ---------------------------------------------------------------- the strategy core (no I/O)
@dataclass
class Coin:
    pair: str
    lot_usd: float
    phase: str = "BUYING"                # BUYING | HOLDING | PAUSED
    order_id: str | None = None          # the resting order (a buy in BUYING, the target sell in HOLDING)
    order_px: float | None = None
    order_qty: float = 0.0
    next_px: float | None = None         # where the next buy goes (None = at the bid)
    entry: float | None = None
    qty: float = 0.0                     # coins held by the sleeve in this pair
    cost: float = 0.0                    # USD paid for them
    paused_until: float = 0.0
    stop_times: list = field(default_factory=list)
    trips: int = 0
    wins: int = 0
    stops: int = 0
    pnl: float = 0.0


@dataclass
class Params:
    stop_steps: int = 2
    trail_steps: int = 2
    pause_after_stops: int = 3
    pause_s: float = 3600.0


def buy_price(c: Coin, bid: float, ask: float, step: float) -> float:
    px = c.next_px if c.next_px is not None else bid
    return min(px, ask - step)                               # never marketable


def should_trail(c: Coin, bid: float, step: float, p: Params) -> bool:
    return c.phase == "BUYING" and c.order_id is not None and c.order_px is not None and \
        bid >= c.order_px + p.trail_steps * step - step * 1e-6


def should_stop(c: Coin, bid: float, step: float, p: Params) -> bool:
    return c.phase == "HOLDING" and c.entry is not None and bid <= c.entry - p.stop_steps * step + step * 1e-6


def after_win(c: Coin, sell_px: float, step: float) -> None:
    c.phase, c.next_px, c.entry, c.order_id, c.order_px = "BUYING", sell_px - step, None, None, None


def after_stop(c: Coin, bid: float, step: float, t: float, p: Params) -> None:
    c.stop_times = [x for x in c.stop_times if x > t - p.pause_s] + [t]
    c.entry, c.order_id, c.order_px = None, None, None
    if len(c.stop_times) >= p.pause_after_stops:
        c.phase, c.paused_until, c.stop_times, c.next_px = "PAUSED", t + p.pause_s, [], None
    else:
        c.phase, c.next_px = "BUYING", bid - step


# ---------------------------------------------------------------- the driver
def state_path(cfg: dict, state_dir: Path, mode: str) -> Path:
    """The live sleeve's state is `state_file` (the hourly bot reads its cash from it); a paper sleeve keeps its own."""
    name = cfg["live"]["sleeve"].get("state_file") or "sleeve.json"
    return state_dir / (name if mode == "live" else name.replace(".json", "-paper.json"))


class Sleeve:
    def __init__(self, cfg: dict, ex: Exchange, rules: dict[str, PairRule], state_dir: Path, mode: str,
                 log: logging.Logger, clock: Callable[[], float] = time.time):
        self.cfg, self.ex, self.rules, self.dir, self.mode, self.log, self.clock = cfg, ex, rules, state_dir, mode, log, clock
        self.sc = cfg["live"]["sleeve"]
        self.p = Params(int(self.sc["stop_steps"]), int(self.sc["trail_steps"]), int(self.sc["pause_after_stops"]),
                        float(self.sc["pause_s"]))
        self.state_path = state_path(cfg, state_dir, mode)
        self.kill_path = state_dir / "sleeve.KILL"                # one name in both modes
        self.errors = 0
        self.last_check: dict[str, float] = {}
        self.cash_wait_until = 0.0
        self.commit = subprocess.run(["git", "rev-parse", "--short=12", "HEAD"], cwd=REPO_ROOT, capture_output=True,
                                     text=True).stdout.strip()
        lv = cfg["live"]
        self.start_at = pd.Timestamp(lv["start_at"]).tz_localize("UTC").timestamp() if lv.get("start_at") and mode == "live" else None
        self.end_at = pd.Timestamp(lv["end_at"]).tz_localize("UTC").timestamp() if lv.get("end_at") else None
        st = json.loads(self.state_path.read_text()) if self.state_path.exists() else None
        if st and st.get("mode") != mode:
            raise SystemExit(f"{self.state_path} is for {st.get('mode')} mode; move it away to start {mode} fresh")
        if st:
            self.coins = {k: Coin(**v) for k, v in st["coins"].items()}
            self.cash, self.capital = float(st["cash"]), float(st["capital"])
            self.day, self.day_start_value, self.stopped = st["day"], float(st["day_start_value"]), st.get("stopped")
        else:
            lots = {k: float(v) for k, v in self.sc["lots_usd"].items()}
            self.coins = {p: Coin(p, lot) for p, lot in lots.items()}
            self.capital = self.cash = float(self.sc["capital_usd"])
            self.day, self.day_start_value, self.stopped = None, self.capital, None
        for p in self.coins:
            if p not in rules:
                raise SystemExit(f"{p}: no trading rule from exchangeInfo")

    # ---- helpers
    def step(self, pair: str) -> float:
        return float(Decimal(1).scaleb(-self.rules[pair].price_precision))

    def price(self, pair: str, x: float) -> Decimal:
        return Decimal(str(round(x / self.step(pair)) * self.step(pair))).quantize(Decimal(1).scaleb(-self.rules[pair].price_precision))

    def emit(self, event: str, **data) -> None:
        line = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "event": event, "mode": self.mode,
                "commit": self.commit, **data}
        d = self.dir / "logs"
        d.mkdir(parents=True, exist_ok=True)
        with open(d / f"sleeve-{datetime.now(timezone.utc):%Y%m%d}.jsonl", "a") as fh:
            fh.write(json.dumps(line, default=str) + "\n")

    def value(self, quotes: dict) -> float:
        v = self.cash
        for p, c in self.coins.items():
            if c.phase == "BUYING" and c.order_id is not None:
                v += c.order_qty * (c.order_px or 0.0)            # cash locked in the resting buy
            if c.qty > 0 and p in quotes:
                v += c.qty * quotes[p][0]
        return v

    def cash_free(self) -> float:
        return self.cash

    def save(self, quotes: dict | None = None) -> None:
        st = {"mode": self.mode, "ts": self.clock(), "capital": self.capital, "cash": self.cash, "cash_free": self.cash_free(),
              "value": self.value(quotes or {}), "day": self.day, "day_start_value": self.day_start_value,
              "stopped": self.stopped, "pairs": sorted(self.coins), "coins": {k: asdict(v) for k, v in self.coins.items()}}
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(st, indent=1, default=str))
        tmp.replace(self.state_path)

    # ---- order actions (each updates the sleeve's books from what the exchange answered)
    def _place_buy(self, c: Coin, px: float) -> None:
        rule = self.rules[c.pair]
        lot = min(c.lot_usd, self.cash)
        qty = truncate(Decimal(str(lot)) / Decimal(str(px)), rule.amount_precision)
        if qty <= 0 or float(qty) * px < float(rule.min_order) or float(qty) * px < 10:
            return
        try:
            f = self.ex.place_limit(c.pair, "BUY", qty, self.price(c.pair, px))
        except RoostooError as e:
            if any(w in str(e).lower() for w in ("balance", "insufficient", "not enough")):
                self.cash_wait_until = self.clock() + 60.0          # the hourly bot has not freed the cash yet
                self.emit("waiting_for_cash", pair=c.pair, lot=float(qty) * px, error=str(e)[:200])
                return
            raise
        self.cash -= float(qty) * px
        c.order_id, c.order_px, c.order_qty, c.next_px = f.order_id, float(self.price(c.pair, px)), float(qty), None
        self.emit("order", pair=c.pair, side="BUY", px=c.order_px, qty=float(qty), status=f.status, id=f.order_id)
        if f.status == "FILLED":
            self._bought(c, f)

    def _bought(self, c: Coin, f: Fill) -> None:
        c.qty += f.coin_change if f.coin_change > 0 else f.qty * (1 - MAKER)
        c.cost = c.order_qty * (c.order_px or f.price)
        c.entry, c.phase, c.order_id, c.order_px = c.order_px or f.price, "HOLDING", None, None
        self.emit("fill", pair=c.pair, side="BUY", px=c.entry, qty=c.qty, role=f.role)

    def _place_target(self, c: Coin, bid: float) -> None:
        step = self.step(c.pair)
        s = c.entry + step
        qty = truncate(c.qty, self.rules[c.pair].amount_precision)
        if qty <= 0:
            return
        f = self.ex.place_limit(c.pair, "SELL", qty, self.price(c.pair, max(s, bid)))
        c.order_id, c.order_px, c.order_qty = f.order_id, float(self.price(c.pair, max(s, bid))), float(qty)
        self.emit("order", pair=c.pair, side="SELL", px=c.order_px, qty=float(qty), status=f.status, id=f.order_id)
        if f.status == "FILLED":
            self._sold(c, f, "target")

    def _sold(self, c: Coin, f: Fill, kind: str, t: float | None = None, bid: float | None = None) -> None:
        usd = f.usd_change if f.usd_change > 0 else f.qty * f.price * (1 - (TAKER if kind != "target" else MAKER))
        self.cash += usd
        c.qty = max(0.0, c.qty - f.qty)
        pnl = usd - c.cost
        c.pnl += pnl
        c.trips += 1
        c.wins += pnl > 0
        self.emit("fill", pair=c.pair, side="SELL", kind=kind, px=f.price, qty=f.qty, pnl=round(pnl, 4), role=f.role)
        step = self.step(c.pair)
        sell_px = f.price or (c.order_px or 0.0)
        c.cost = 0.0
        if kind == "stop":
            c.stops += 1
            after_stop(c, bid if bid is not None else sell_px, step, t or self.clock(), self.p)
        elif kind == "flatten":
            c.phase, c.entry, c.order_id, c.order_px, c.next_px = "BUYING", None, None, None, None
        else:
            after_win(c, sell_px, step)

    def _cancel(self, c: Coin) -> Fill | None:
        """Cancel the resting order. If the cancel finds nothing, the order filled: returns that fill."""
        oid = c.order_id
        if oid is None:
            return None
        ok = self.ex.cancel(c.pair, oid)
        if ok:
            if c.phase == "BUYING":
                self.cash += c.order_qty * (c.order_px or 0.0)
            c.order_id, c.order_px = None, None
            self.emit("cancel", pair=c.pair, id=oid)
            return None
        f = self.ex.order(c.pair, oid)
        if f.status == "FILLED":
            return f
        if f.status == "CANCELED":
            if c.phase == "BUYING":
                self.cash += c.order_qty * (c.order_px or 0.0)
            c.order_id, c.order_px = None, None
            return None
        raise RoostooError(f"{c.pair}: cancel of {oid} not confirmed (status {f.status}); reconcile")

    def flatten(self, quotes: dict, why: str) -> None:
        for p, c in self.coins.items():
            f = self._cancel(c)
            if f is not None:                                   # the cancel found it filled
                if c.phase == "BUYING":
                    self._bought(c, f)
                else:
                    self._sold(c, f, "target")
            if c.qty > 0 and p in quotes:
                qty = truncate(c.qty, self.rules[p].amount_precision)
                if qty > 0:
                    self._sold(c, self.ex.market_sell(p, qty), "flatten", bid=quotes[p][0])
        self.emit("flatten", why=why, value=self.value(quotes))

    # ---- one loop
    def tick(self) -> None:
        t = self.clock()
        now = pd.Timestamp(t, unit="s", tz="UTC")
        pairs = sorted(self.coins)
        if self.kill_path.exists() and self.stopped != "kill":
            q = self.ex.quotes(pairs)
            self.flatten(q, "KILL file")
            self.stopped = "kill"
            self.save(q)
            return
        if self.stopped:
            return
        if self.start_at is not None and t < self.start_at:
            return
        q = self.ex.quotes(pairs)
        if not q:
            return
        if self.end_at is not None and t >= self.end_at - float(self.sc["flatten_before_end_s"]):
            self.flatten(q, "round end")
            self.stopped = "round_end"
            self.save(q)
            return
        if self.sc.get("respect_lock") and self._runner_locked():
            self.flatten(q, "hourly bot locked in (endgame)")
            self.stopped = "lock"
            self.save(q)
            return
        # the HKT day (as the hourly bot counts it) and the loss limits
        grid = int(self.cfg["harness"]["grid_hour_utc"])
        day = str((now - pd.Timedelta(hours=grid)).floor("D") + pd.Timedelta(hours=grid))
        v = self.value(q)
        if day != self.day:
            self.day, self.day_start_value = day, v
        if v <= self.capital * (1 - float(self.sc["total_loss_limit"])):
            self.flatten(q, f"total loss limit: value {v:.2f} vs capital {self.capital:.2f}")
            self.stopped = "total_loss"
            self.save(q)
            return
        no_new = v <= self.day_start_value * (1 - float(self.sc["daily_loss_limit"]))
        w0, w1 = self.sc["runner_window"]
        in_window = w0 <= now.minute < w1
        pend = None
        for p in pairs:
            c = self.coins[p]
            if p not in q:
                continue
            b, a, _ = q[p]
            step = self.step(p)
            # learn fills: a resting order whose pair shows no pending order has filled (or was cancelled)
            if c.order_id is not None:
                touch = (c.phase == "BUYING" and b <= (c.order_px or 0) + step * 1e-6) or \
                        (c.phase == "HOLDING" and (a + b) / 2 >= (c.order_px or 1e18) - step * 1e-6)
                if touch or t - self.last_check.get(p, 0.0) >= 60.0:       # a fill between quotes is caught in 60 s
                    self.last_check[p] = t
                    if pend is None:
                        pend = self.ex.pending_pairs()
                    if pend.get(p, 0) == 0:
                        f = self.ex.order(p, c.order_id)
                        if f.status == "FILLED":
                            if c.phase == "BUYING":
                                self._bought(c, f)
                            else:
                                self._sold(c, f, "target")
                        elif f.status == "CANCELED":
                            if c.phase == "BUYING":
                                self.cash += c.order_qty * (c.order_px or 0.0)
                            c.order_id, c.order_px = None, None
            # stops run even inside the hourly bot's window
            if should_stop(c, b, step, self.p):
                f = self._cancel(c)
                if f is not None:
                    self._sold(c, f, "target")
                else:
                    qty = truncate(c.qty, self.rules[p].amount_precision)
                    if qty > 0:
                        self._sold(c, self.ex.market_sell(p, qty), "stop", t, b)
                continue
            if in_window:
                continue
            if c.phase == "PAUSED":
                if t < c.paused_until:
                    continue
                c.phase, c.next_px = "BUYING", None
            if no_new and c.phase == "BUYING" and c.order_id is not None:
                f = self._cancel(c)
                if f is not None:
                    self._bought(c, f)
                continue
            if c.phase == "HOLDING" and c.order_id is None:
                self._place_target(c, b)
            elif c.phase == "BUYING":
                if c.order_id is not None and should_trail(c, b, step, self.p):
                    f = self._cancel(c)
                    if f is not None:
                        self._bought(c, f)
                        continue
                    c.next_px = b - step
                if c.order_id is None and not no_new and t >= self.cash_wait_until:
                    self._place_buy(c, buy_price(c, b, a, step))
        self.save(q)

    def _runner_locked(self) -> bool:
        st = self.dir / "state.json"
        try:
            return bool(json.loads(st.read_text()).get("locked_at"))
        except (OSError, ValueError):
            return False

    def reconcile(self) -> None:
        """Live start: coins of a sleeve pair in the wallet that the state does not show (a lost state file) are
        adopted as a lot bought at the current bid, so the stop and target logic manage them."""
        q = self.ex.quotes(sorted(self.coins))
        for p, c in self.coins.items():
            if c.qty > 0 or c.order_id is not None or p not in q:
                continue
            held = self.ex.coins(p.split("/")[0])
            if held * q[p][0] >= 10:
                c.qty, c.entry, c.cost, c.phase = held, q[p][0], held * q[p][0], "HOLDING"
                self.cash = max(0.0, self.cash - c.cost)
                self.emit("adopt", pair=p, qty=held, at=q[p][0])
        self.save(q)

    def run(self, once: bool = False) -> None:
        if self.mode == "live" and not self.stopped:
            self.reconcile()
        self.emit("start", capital=self.capital, coins={k: v.lot_usd for k, v in self.coins.items()},
                  params=asdict(self.p), stopped=self.stopped)
        while True:
            t0 = self.clock()
            try:
                self.tick()
                self.errors = 0
            except OrderStateUnknown as e:              # an order whose outcome is unknown: stop and reconcile by hand
                self.emit("error", error=f"order state unknown: {e}; sleeve stopped")
                self.stopped = "order_unknown"
                self.save()
                raise
            except Exception as e:                      # noqa: BLE001 - count, back off, maybe kill
                self.errors += 1
                self.log.exception("sleeve tick failed")
                self.emit("error", error=f"{type(e).__name__}: {e}", in_a_row=self.errors)
                if self.errors >= int(self.sc["kill_after_errors"]):
                    try:
                        q = self.ex.quotes(sorted(self.coins))
                        self.flatten(q, f"{self.errors} errors in a row")
                    finally:
                        self.stopped = "errors"
                        self.save()
                    return
                time.sleep(30)
            if once or self.stopped:
                return
            now = pd.Timestamp(self.clock(), unit="s", tz="UTC")
            w0, w1 = self.sc["runner_window"]
            loop = 30.0 if w0 <= now.minute < w1 else float(self.sc["loop_s"])
            time.sleep(max(0.5, loop - (self.clock() - t0)))


def build_in_process(cfg: dict, client: RoostooClient, runner_mode: str, state_dir: Path,
                     log: logging.Logger) -> Sleeve:
    """The sleeve for the hourly bot's process. Its client shares the bot's rate limiter, so the whole process stays
    under `execution.calls_per_minute`. A paper bot never runs a live sleeve."""
    sc = cfg["live"]["sleeve"]
    mode = "live" if (sc.get("mode") == "live" and runner_mode == "live") else "paper"
    c2 = RoostooClient(cfg["exchange"]["base_url"], client.creds, int(cfg["execution"]["calls_per_minute"]),
                       cfg["execution"]["timeout_s"], log=log)
    c2.limiter = client.limiter                          # one ceiling for the process
    c2.offset_ms = client.offset_ms
    rules = parse_exchange_info(c2.exchange_info())
    rx = RoostooExchange(c2)
    ex: Exchange = rx if mode == "live" else PaperExchange(rx.quotes, str(sc.get("paper_sell_rule", "mid")),
                                                           float(sc["capital_usd"]))
    return Sleeve(cfg, ex, rules, state_dir, mode, log)


def status(cfg: dict, mode: str = "live") -> str:
    p = state_path(cfg, resolve(cfg["live"]["state_dir"]), mode)
    if not p.exists():
        return f"no sleeve state at {p}"
    st = json.loads(p.read_text())
    age = time.time() - float(st["ts"])
    lines = [f"sleeve {st['mode']}: value ${st['value']:,.2f} of ${st['capital']:,.2f} ({st['value'] / st['capital'] - 1:+.2%}), "
             f"cash ${st['cash']:,.2f}, state {age:.0f} s old, stopped: {st.get('stopped')}"]
    for k, c in st["coins"].items():
        lines.append(f"  {k:10s} {c['phase']:8s} trips {c['trips']:4d} wins {c['wins']:4d} stops {c['stops']:3d} "
                     f"P&L ${c['pnl']:+,.2f} order {c['order_px']} entry {c['entry']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--mode", choices=("paper", "live"), default="paper")
    r.add_argument("--quotes", choices=("recorder", "ticker"), default="ticker",
                   help="paper only: quotes from the research server's recorder files, or the public ticker")
    r.add_argument("--state-dir", default=None)
    r.add_argument("--once", action="store_true")
    stp = sub.add_parser("status")
    stp.add_argument("--mode", choices=("paper", "live"), default="live")
    a = ap.parse_args(argv)
    cfg = load_config()
    sc = (cfg["live"].get("sleeve") or {})
    if a.cmd == "status":
        print(status(cfg, a.mode))
        return 0
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    log = logging.getLogger("sleeve")
    state_dir = resolve(a.state_dir or cfg["live"]["state_dir"])
    state_dir.mkdir(parents=True, exist_ok=True)
    ex_cfg = cfg["execution"]
    if a.mode == "live":
        raise SystemExit("a live sleeve runs only inside the hourly bot (live.sleeve.mode: live); one process per instance")
    else:
        client = RoostooClient(cfg["exchange"]["base_url"], None, int(sc["calls_per_minute"]), ex_cfg["timeout_s"], log=log)
        if a.quotes == "recorder":
            qf = recorder_quotes(str(resolve(sc["recorder_glob"])))
        else:
            rx = RoostooExchange(client)
            qf = rx.quotes
        ex = PaperExchange(qf, str(sc.get("paper_sell_rule", "mid")), float(sc["capital_usd"]))
    rules = parse_exchange_info(client.exchange_info())
    Sleeve(cfg, ex, rules, state_dir, a.mode, log).run(once=a.once)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
