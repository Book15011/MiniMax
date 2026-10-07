"""Tick-scalping sleeve beside the hourly model, on the same Roostoo account (EXPERIMENTAL, off by default).

NOT DEPLOYABLE until AGENTS.md section 2.6 ("directional strategies only: no market-making") is amended through a
reviewed merge (branch feature/agents-tick-scalp). The organisers' public statement (2026-10-05) says tick scalping is
not prohibited and won't be disqualified, and that judges won't value it. 

It runs INSIDE the hourly bot's process (one instance, one process, one API ceiling): src.live.runner starts it as a
thread when `live.sleeve.enabled` (build_in_process). `live.sleeve.mode: paper` trades nothing (fills simulated on the
live quotes with Roostoo's measured rule); `live` trades the account. Every change (paper -> live, capital, lots) is a
committed config change and the usual update (pull, restart); the sleeve picks it up from the config at start.

    python -m src.live.sleeve run --mode paper [--quotes recorder|ticker]       research-server paper run
    python -m src.live.sleeve replay --start ... --end ...                      the live code on recorded quotes
    python -m src.live.sleeve status [--mode paper|live]

The loop, per coin (one lot at a time, fixed USD lot):
  BUYING  a resting limit buy: at the bid at the start and after a pause; one step below the sell after a win; one
          step below the bid after a stop. It trails to bid - 1 step once the bid is `trail_steps` above it.
  HOLDING a resting limit sell at entry + 1 step (at once at the bid, as a taker, if the bid is already there).
          Stop: when the bid is `stop_steps` below entry, cancel the sell and sell at market.
  PAUSED  after `pause_after_stops` stops within `pause_s`, nothing for `pause_s`.
Roostoo's matching (measured on 65 real orders, 2026-10-06/07): a resting buy at P fills once Roostoo's bid <= P; a
resting sell at S once its mid (bid with a one-step spread) >= S. PaperExchange applies exactly that rule.

Safety and robustness:
- calls go through the bot's limiter; minutes `runner_window` of each hour belong to the hourly model (no new sleeve
  orders, quotes every 30 s, stops still run); order checks at most every `min_check_s` per pair, a sweep every 60 s;
- books come from each fill's quantity, price and commission; partial fills are read after every cancel; the coins
  are reconciled with the wallet every `reconcile_s` (the model never holds the sleeve's pairs, so the wallet's coins
  of those pairs are the sleeve's);
- an order whose outcome is unknown (timeout, 5xx) is reconciled from the exchange (open orders, coins), not fatal;
- API errors back off (30 s doubling to 5 min); only `error_kill_minutes` of continuous failure flattens and stops;
- a refused buy (cash not yet freed by the hourly model, or any other refusal) backs that coin off; before a live buy
  the wallet's free USD is checked (at most once a minute);
- a daily loss limit (HKT day) stops new buys until the next day; a total loss limit flattens and stops; so does a
  KILL file (data/live/sleeve.KILL);
- an edge breaker pauses a coin for `breaker_pause_s` when its last `breaker_trips` trips lost money in total with a
  win rate under `breaker_win` (e.g. if Roostoo changed its matching); no new buys while one price step is under
  `min_step_frac` of the price (the +1-step win must beat the fees);
- nothing trades before `live.start_at`; it flattens and stops `flatten_before_end_s` before `live.end_at`; with
  `respect_lock` it also flattens when the hourly model's end-of-round lock-in fires;
- the state (cash, coins, open orders) is written atomically every loop; the hourly bot reads `cash_free` from it.
"""
from __future__ import annotations

import argparse
import glob as globmod
import json
import logging
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Callable, Protocol

import pandas as pd

from src.api.client import OrderStateUnknown, RoostooClient, RoostooError
from src.api.rules import PairRule, fmt, parse_exchange_info, truncate
from src.config import REPO_ROOT, load_config, resolve

MAKER, TAKER = 0.0005, 0.001
PERMANENT = ("kill", "total_loss", "errors", "round_end", "lock")


# ---------------------------------------------------------------- exchange interface
@dataclass
class Fill:
    status: str                  # FILLED | PENDING | PARTIAL | CANCELED | UNKNOWN
    price: float = 0.0
    qty: float = 0.0             # coins traded
    coin_change: float = 0.0     # coins received (+) or given (-), after any fee in coin
    usd_change: float = 0.0      # USD received (+) or paid (-), after any fee in USD
    order_id: str | None = None
    role: str = ""
    side: str = ""


def fill_from_detail(d: dict, side: str | None = None) -> Fill:
    """An OrderDetail / OrderMatched row -> Fill, from the filled quantity, the average price and the commission
    (CommissionCoin says which side paid it). CoinChange / UnitChange are not used: their sign and fee convention are
    UNVERIFIED. Without a commission field the fee is assumed: maker 0.05% for a limit fill, taker 0.1% otherwise."""
    side = (side or str(d.get("Side") or "")).upper()
    st = str(d.get("Status") or "").upper()
    st = {"CANCELLED": "CANCELED", "PARTIALLY_FILLED": "PARTIAL", "PARTIAL_FILLED": "PARTIAL"}.get(st, st or "UNKNOWN")
    qty = float(d.get("FilledQuantity") or 0.0)
    px = float(d.get("FilledAverPrice") or 0.0) or float(d.get("Price") or 0.0)
    if st == "FILLED" and qty == 0.0:
        qty = float(d.get("Quantity") or 0.0)
    base = str(d.get("Pair") or "").split("/")[0]
    fee_ccy = str(d.get("CommissionCoin") or "")
    fee = float(d.get("CommissionChargeValue") or 0.0)
    role = str(d.get("Role") or "").upper()
    if not fee_ccy:
        rate = TAKER if (role == "TAKER" or str(d.get("Type") or "").upper() == "MARKET") else MAKER
        fee_ccy, fee = ((base, qty * rate) if side == "BUY" else ("USD", qty * px * rate))
    fee_coin = fee if fee_ccy == base else 0.0
    fee_usd = fee if fee_ccy == "USD" else 0.0
    if side == "BUY":
        coin, usd = qty - fee_coin, -(qty * px) - fee_usd
    else:
        coin, usd = -qty - fee_coin, qty * px - fee_usd
    return Fill(st, px, qty, coin, usd, str(d.get("OrderID") or "") or None, role, side)


class Exchange(Protocol):
    def quotes(self, pairs: list[str]) -> dict[str, tuple[float, float, float]]: ...
    def place_limit(self, pair: str, side: str, qty: Decimal, price: Decimal) -> Fill: ...
    def market_sell(self, pair: str, qty: Decimal) -> Fill: ...
    def cancel(self, pair: str, order_id: str) -> bool: ...
    def order(self, pair: str, order_id: str) -> Fill: ...
    def open_orders(self, pair: str) -> list[Fill]: ...
    def pending_pairs(self) -> dict[str, int]: ...
    def balances(self) -> dict[str, float]: ...


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
        return fill_from_detail({"Pair": pair, **self.c.place_order(pair, side, fmt(qty), "LIMIT", fmt(price))}, side)

    def market_sell(self, pair, qty):
        return fill_from_detail({"Pair": pair, "Type": "MARKET", **self.c.place_order(pair, "SELL", fmt(qty), "MARKET")},
                                "SELL")

    def cancel(self, pair, order_id):
        return bool(self.c.cancel_order(order_id=order_id))

    def order(self, pair, order_id):
        rows = self.c.query_order(order_id=order_id)
        return fill_from_detail({"Pair": pair, **rows[0]}) if rows else Fill("UNKNOWN", order_id=order_id)

    def open_orders(self, pair):
        return [fill_from_detail({"Pair": pair, **r}) for r in self.c.query_order(pair=pair, pending_only=True)]

    def pending_pairs(self):
        return {k: int(v) for k, v in (self.c.pending_count().get("OrderPairs") or {}).items()}

    def balances(self):
        return {k: float(v.get("Free") or 0.0) + (float(v.get("Lock") or 0.0) if k != "USD" else 0.0)
                for k, v in self.c.balance().items()}               # USD: free only (what a new buy can use)


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

    def restore(self, coins: dict) -> None:
        """A restarted paper sleeve carries on from its state: its resting orders and coins come back."""
        for c in coins.values():
            self.held[c.pair.split("/")[0]] = c.qty
            if c.order_id:
                self.open[c.order_id] = {"pair": c.pair, "side": "BUY" if c.phase == "BUYING" else "SELL",
                                         "qty": c.order_qty, "price": c.order_px}
                tail = str(c.order_id).split("-")[-1]
                self.n = max(self.n, int(tail) if tail.isdigit() else 0)

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
                    f = Fill("FILLED", o["price"], o["qty"], got, -o["qty"] * o["price"], oid, "MAKER", "BUY")
                else:
                    usd = o["qty"] * o["price"] * (1 - MAKER)
                    self.held[coin] = self.held.get(coin, 0.0) - o["qty"]
                    self.usd += usd
                    f = Fill("FILLED", o["price"], o["qty"], -o["qty"], usd, oid, "MAKER", "SELL")
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
            f = Fill("FILLED", b, qty, -qty, usd, oid, "TAKER", "SELL")
            self.done[oid] = f
            return f
        if side == "BUY":
            self.usd -= qty * price
        self.open[oid] = {"pair": pair, "side": side, "qty": qty, "price": price}
        return Fill("PENDING", price, 0.0, 0.0, 0.0, oid, "", side)

    def market_sell(self, pair, qty):
        self.n += 1
        b = self.last[pair][0]
        coin = pair.split("/")[0]
        qty = float(qty)
        usd = qty * b * (1 - TAKER)
        self.held[coin] = self.held.get(coin, 0.0) - qty
        self.usd += usd
        return Fill("FILLED", b, qty, -qty, usd, f"paper-{self.n}", "TAKER", "SELL")

    def cancel(self, pair, order_id):
        o = self.open.pop(order_id, None)
        if o is None:
            return False
        if o["side"] == "BUY":
            self.usd += o["qty"] * o["price"]
        self.done[order_id] = Fill("CANCELED", o["price"], 0.0, 0.0, 0.0, order_id, "", o["side"])
        return True

    def order(self, pair, order_id):
        if order_id in self.open:
            o = self.open[order_id]
            return Fill("PENDING", o["price"], 0.0, 0.0, 0.0, order_id, "", o["side"])
        return self.done.get(order_id, Fill("UNKNOWN", order_id=order_id))

    def open_orders(self, pair):
        return [Fill("PENDING", o["price"], 0.0, 0.0, 0.0, k, "", o["side"]) for k, o in self.open.items() if o["pair"] == pair]

    def pending_pairs(self):
        out: dict[str, int] = {}
        for o in self.open.values():
            out[o["pair"]] = out.get(o["pair"], 0) + 1
        return out

    def balances(self):
        return {**{k: max(v, 0.0) for k, v in self.held.items()}, "USD": self.usd}


def recorder_quotes(path_glob: str, max_age_s: float = 60.0, clock: Callable[[], float] = time.time,
                    offset_s: float = 3.15) -> Callable[[list[str]], dict]:
    """Quotes from the research server's recorder files (every pair every 6 s): the newest row per pair, if it is at
    most max_age_s old (a stopped recorder gives no quotes rather than frozen ones). The recorder's clock is
    offset_s behind true time (measured 2026-10-06). Paper runs on the research server add no Roostoo calls."""
    def fn(pairs):
        files = sorted(globmod.glob(path_glob))
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
                ts = pd.Timestamp(parts[0]).timestamp() + offset_s
                if clock() - ts > max_age_s:
                    continue
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
    blocked_until: float = 0.0           # edge breaker or refused orders: no new buys before this
    rejects: int = 0
    stop_times: list = field(default_factory=list)
    recent: list = field(default_factory=list)   # net return of the last trips (edge breaker)
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
    breaker_trips: int = 20
    breaker_win: float = 0.75
    breaker_pause_s: float = 6 * 3600.0


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


def edge_breaker(c: Coin, ret: float, t: float, p: Params) -> bool:
    """Record a trip; True (and the coin blocked) when the last breaker_trips trips lost money with a low win rate."""
    c.recent = (c.recent + [ret])[-p.breaker_trips:]
    if len(c.recent) >= p.breaker_trips and sum(c.recent) < 0 and \
            sum(1 for x in c.recent if x > 0) / len(c.recent) < p.breaker_win:
        c.blocked_until, c.recent = t + p.breaker_pause_s, []
        return True
    return False


# ---------------------------------------------------------------- the driver
def state_path(cfg: dict, state_dir: Path, mode: str) -> Path:
    """The live sleeve's state is `state_file` (the hourly bot reads its cash from it); a paper sleeve keeps its own."""
    name = cfg["live"]["sleeve"].get("state_file") or "sleeve.json"
    return state_dir / (name if mode == "live" else name.replace(".json", "-paper.json"))


class Sleeve:
    def __init__(self, cfg: dict, ex: Exchange, rules: dict[str, PairRule], state_dir: Path, mode: str,
                 log: logging.Logger, clock: Callable[[], float] = time.time, sleep: Callable[[float], None] = time.sleep):
        self.cfg, self.ex, self.rules, self.dir, self.mode, self.log = cfg, ex, rules, state_dir, mode, log
        self.clock, self.sleep = clock, sleep
        self.sc = sc = cfg["live"]["sleeve"]
        self.p = Params(int(sc["stop_steps"]), int(sc["trail_steps"]), int(sc["pause_after_stops"]), float(sc["pause_s"]),
                        int(sc.get("breaker_trips", 20)), float(sc.get("breaker_win", 0.75)),
                        float(sc.get("breaker_pause_s", 6 * 3600)))
        self.state_path = state_path(cfg, state_dir, mode)
        self.kill_path = state_dir / "sleeve.KILL"                # one name in both modes
        self.log_dir = state_dir / "logs" / "sleeve"              # not logs/: deploy/status.sh reads the bot's logs there
        self.errors, self.error_since = 0, None
        self.last_check: dict[str, float] = {}
        self.last_reconcile = 0.0
        self.usd_checked_at, self.usd_free_seen = -1e18, 0.0
        self.notes_at: dict[str, float] = {}
        self.commit = subprocess.run(["git", "rev-parse", "--short=12", "HEAD"], cwd=REPO_ROOT, capture_output=True,
                                     text=True).stdout.strip()
        lv = cfg["live"]
        self.start_at = pd.Timestamp(lv["start_at"]).tz_localize("UTC").timestamp() if lv.get("start_at") and mode == "live" else None
        self.end_at = pd.Timestamp(lv["end_at"]).tz_localize("UTC").timestamp() if lv.get("end_at") else None
        st = json.loads(self.state_path.read_text()) if self.state_path.exists() else None
        if st and st.get("mode") != mode:
            raise SystemExit(f"{self.state_path} is for {st.get('mode')} mode; move it away to start {mode} fresh")
        lots = {k: float(v) for k, v in sc["lots_usd"].items()}
        cap = float(sc["capital_usd"])
        if st:
            known = set(Coin.__dataclass_fields__)
            self.coins = {k: Coin(**{f: x for f, x in v.items() if f in known}) for k, v in st["coins"].items()}
            self.cash, self.capital = float(st["cash"]), float(st["capital"])
            self.day, self.day_start_value, self.stopped = st["day"], float(st["day_start_value"]), st.get("stopped")
        else:
            self.coins, self.cash = {}, cap
            self.capital, self.day, self.day_start_value, self.stopped = cap, None, cap, None
        # the committed config wins: lots and capital may change with an update (paper -> live, or a new size)
        for p, lot in lots.items():
            if p in self.coins:
                self.coins[p].lot_usd = lot
            else:
                self.coins[p] = Coin(p, lot)
        for p in [p for p in self.coins if p not in lots]:
            self.coins[p].lot_usd = 0.0                         # dropped from the config: no new buys; exits still run
        self._changes = {}
        if st and abs(cap - self.capital) > 1e-6:
            delta = cap - self.capital
            self.cash += delta
            self.capital = cap
            self.day_start_value += delta
            self._changes = {"capital_change": delta}
        for p in self.coins:
            if p not in rules:
                raise SystemExit(f"{p}: no trading rule from exchangeInfo")
        if isinstance(ex, PaperExchange):
            ex.restore(self.coins)

    # ---- helpers
    def step(self, pair: str) -> float:
        return float(Decimal(1).scaleb(-self.rules[pair].price_precision))

    def price(self, pair: str, x: float) -> Decimal:
        return Decimal(str(round(x / self.step(pair)) * self.step(pair))).quantize(Decimal(1).scaleb(-self.rules[pair].price_precision))

    def emit(self, event: str, **data) -> None:
        line = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "t": self.clock(), "event": event,
                "mode": self.mode, "commit": self.commit, **data}
        self.log_dir.mkdir(parents=True, exist_ok=True)
        with open(self.log_dir / f"{datetime.now(timezone.utc):%Y%m%d}.jsonl", "a") as fh:
            fh.write(json.dumps(line, default=str) + "\n")

    def note(self, key: str, every_s: float, event: str, **data) -> None:
        """An event logged at most once per every_s (waiting, step too small, ...)."""
        t = self.clock()
        if t - self.notes_at.get(key, -1e18) >= every_s:
            self.notes_at[key] = t
            self.emit(event, **data)

    def value(self, quotes: dict) -> float:
        v = self.cash
        for p, c in self.coins.items():
            if c.phase == "BUYING" and c.order_id is not None:
                v += c.order_qty * (c.order_px or 0.0)            # cash locked in the resting buy
            if c.qty > 0:
                v += c.qty * (quotes[p][0] if p in quotes else (c.entry or c.order_px or 0.0))
        return v

    def cash_free(self) -> float:
        return max(self.cash, 0.0)

    def flat(self) -> bool:
        return all(c.order_id is None and c.qty * (c.entry or c.order_px or 1.0) < 1.0 for c in self.coins.values())

    def save(self, quotes: dict | None = None) -> None:
        st = {"mode": self.mode, "ts": self.clock(), "capital": self.capital, "cash": self.cash, "cash_free": self.cash_free(),
              "value": self.value(quotes or {}), "day": self.day, "day_start_value": self.day_start_value,
              "stopped": self.stopped, "flat": self.flat(), "pairs": sorted(self.coins),
              "coins": {k: asdict(v) for k, v in self.coins.items()}}
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(st, indent=1, default=str))
        tmp.replace(self.state_path)

    # ---- books
    def _bought(self, c: Coin, f: Fill, t: float) -> None:
        """A buy filled (fully, or partly before a cancel): the coins and their cost join the lot."""
        got = f.coin_change if f.coin_change > 0 else f.qty * (1 - MAKER)
        paid = -f.usd_change if f.usd_change < 0 else f.qty * (f.price or c.order_px or 0.0)
        locked = c.order_qty * (c.order_px or 0.0)
        self.cash += locked - paid                                # the lock comes back; what was paid stays out
        had = c.qty * (c.entry or 0.0) >= 1.0
        c.qty += got
        c.cost += paid
        if not had:
            c.entry = f.price or c.order_px
        c.phase, c.order_id, c.order_px, c.order_qty = "HOLDING", None, None, 0.0
        c.rejects = 0
        self.emit("fill", pair=c.pair, side="BUY", px=c.entry, qty=got, paid=round(paid, 6), role=f.role)

    def _sold(self, c: Coin, f: Fill, kind: str, t: float, bid: float | None = None) -> None:
        got = f.usd_change if f.usd_change > 0 else f.qty * f.price * (1 - (MAKER if kind == "target" else TAKER))
        self.cash += got
        frac = min(1.0, f.qty / c.qty) if c.qty > 0 else 1.0
        cost = c.cost * frac
        c.qty = max(0.0, c.qty - f.qty)
        c.cost -= cost
        pnl = got - cost
        c.pnl += pnl
        c.trips += 1
        c.wins += pnl > 0
        self.emit("fill", pair=c.pair, side="SELL", kind=kind, px=f.price, qty=f.qty, pnl=round(pnl, 6), role=f.role)
        if edge_breaker(c, pnl / cost if cost > 0 else 0.0, t, self.p):
            self.emit("edge_breaker", pair=c.pair, until=c.blocked_until)
        step = self.step(c.pair)
        sell_px = f.price or (c.order_px or 0.0)
        if c.qty * sell_px >= 1.0:                                # a partial exit: the rest stays a lot
            c.order_id, c.order_px, c.order_qty = None, None, 0.0
            return
        c.cost = 0.0
        if kind == "stop":
            c.stops += 1
            after_stop(c, bid if bid is not None else sell_px, step, t, self.p)
        elif kind == "flatten":
            c.phase, c.entry, c.order_id, c.order_px, c.next_px = "BUYING", None, None, None, None
        else:
            after_win(c, sell_px, step)
        c.order_qty = 0.0

    def _apply(self, c: Coin, f: Fill, t: float, bid: float | None = None) -> None:
        """Book a final order state: FILLED or CANCELED (with whatever filled before the cancel)."""
        if f.status not in ("FILLED", "CANCELED"):
            return
        if c.phase == "BUYING":
            if f.qty > 0:
                self._bought(c, f, t)
            else:
                self.cash += c.order_qty * (c.order_px or 0.0)
                c.order_id, c.order_px, c.order_qty = None, None, 0.0
        else:
            if f.qty > 0:
                self._sold(c, f, "target", t, bid)
            else:
                c.order_id, c.order_px, c.order_qty = None, None, 0.0

    def _cancel(self, c: Coin, t: float) -> None:
        """Cancel the resting order and book its final state (a fill, a partial fill, or nothing)."""
        oid = c.order_id
        if oid is None:
            return
        self.ex.cancel(c.pair, oid)
        f = self.ex.order(c.pair, oid)
        if f.status in ("PENDING", "PARTIAL", "UNKNOWN"):
            self._reconcile_pair(c, f"cancel of {oid} left status {f.status}")
            return
        self._apply(c, f, t)
        if f.status == "CANCELED":
            self.emit("cancel", pair=c.pair, id=oid, filled=f.qty)

    def _reconcile_pair(self, c: Coin, why: str) -> None:
        """Rebuild one pair from the exchange: its open orders and the wallet's coins (the sleeve's alone)."""
        opens = self.ex.open_orders(c.pair)
        mine = [o for o in opens if o.order_id == c.order_id]
        for o in opens:
            if o.order_id != c.order_id:
                self.ex.cancel(c.pair, o.order_id)                # an order the books don't know: cancel it
        if not mine and c.order_id is not None:
            f = self.ex.order(c.pair, c.order_id)
            if f.status in ("FILLED", "CANCELED"):
                self._apply(c, f, self.clock())
            else:
                if c.phase == "BUYING":
                    self.cash += c.order_qty * (c.order_px or 0.0)
                c.order_id, c.order_px, c.order_qty = None, None, 0.0
        held = self.ex.balances().get(c.pair.split("/")[0], 0.0)
        ref = c.entry or c.order_px or 0.0
        if not ref:
            q = self.ex.quotes([c.pair]).get(c.pair)
            ref = q[0] if q else 0.0
        if abs(held - c.qty) * ref >= 1.0:
            self.emit("reconcile_coins", pair=c.pair, books=c.qty, wallet=held)
            if held > c.qty and c.phase != "HOLDING":             # coins the books don't know: adopt them at the bid
                c.entry, c.cost = ref, held * ref
                self.cash -= c.cost
                c.phase = "HOLDING"
            c.qty = held
            if c.qty * ref < 1.0 and c.phase == "HOLDING" and c.order_id is None:
                c.phase, c.entry, c.cost = "BUYING", None, 0.0
        self.emit("reconcile", pair=c.pair, why=why, phase=c.phase, qty=c.qty, order=c.order_id)

    # ---- order actions
    def _place_buy(self, c: Coin, px: float, t: float) -> None:
        rule = self.rules[c.pair]
        lot = min(c.lot_usd, self.cash)
        qty = truncate(Decimal(str(lot)) / Decimal(str(px)), rule.amount_precision)
        if qty <= 0 or float(qty) * px < max(float(rule.min_order), 10.0):
            return
        if self.mode == "live":                                   # the wallet must hold the cash (the hourly model
            if t - self.usd_checked_at >= 60.0:                   # frees it at its next hour after a change)
                self.usd_free_seen, self.usd_checked_at = self.ex.balances().get("USD", 0.0), t
            if self.usd_free_seen < float(qty) * px * 1.001:
                self.note("wait-cash", 600, "waiting_for_cash", pair=c.pair, lot=float(qty) * px, usd_free=self.usd_free_seen)
                return
        try:
            f = self.ex.place_limit(c.pair, "BUY", qty, self.price(c.pair, px))
        except OrderStateUnknown as e:
            self._reconcile_pair(c, f"buy outcome unknown: {e}")
            return
        except RoostooError as e:                                 # refused: back this coin off, never fatal
            c.rejects += 1
            c.blocked_until = t + min(60.0 * 2 ** (c.rejects - 1), 1800.0)
            self.emit("rejected", pair=c.pair, side="BUY", error=str(e)[:200], retry_in_s=c.blocked_until - t)
            return
        self.usd_free_seen -= float(qty) * px
        self.cash -= float(qty) * px
        c.order_id, c.order_px, c.order_qty, c.next_px = f.order_id, float(self.price(c.pair, px)), float(qty), None
        self.emit("order", pair=c.pair, side="BUY", px=c.order_px, qty=float(qty), status=f.status, id=f.order_id)
        if f.status == "FILLED":
            self._bought(c, f, t)

    def _place_target(self, c: Coin, bid: float, t: float) -> None:
        s = max(c.entry + self.step(c.pair), bid)
        qty = truncate(c.qty, self.rules[c.pair].amount_precision)
        if qty <= 0 or float(qty) * s < 1.0:
            c.phase, c.entry, c.cost = "BUYING", None, 0.0       # only dust left
            return
        try:
            f = self.ex.place_limit(c.pair, "SELL", qty, self.price(c.pair, s))
        except OrderStateUnknown as e:
            self._reconcile_pair(c, f"sell outcome unknown: {e}")
            return
        except RoostooError as e:
            self.note(f"rej-sell-{c.pair}", 300, "rejected", pair=c.pair, side="SELL", error=str(e)[:200])
            return
        c.order_id, c.order_px, c.order_qty = f.order_id, float(self.price(c.pair, s)), float(qty)
        self.emit("order", pair=c.pair, side="SELL", px=c.order_px, qty=float(qty), status=f.status, id=f.order_id)
        if f.status == "FILLED":
            self._sold(c, f, "target", t)

    def _market_out(self, c: Coin, bid: float, kind: str, t: float) -> None:
        qty = truncate(c.qty, self.rules[c.pair].amount_precision)
        if qty <= 0:
            return
        try:
            f = self.ex.market_sell(c.pair, qty)
        except OrderStateUnknown as e:
            self._reconcile_pair(c, f"market sell outcome unknown: {e}")
            return
        self._sold(c, f, kind, t, bid)

    def flatten(self, quotes: dict, why: str) -> None:
        t = self.clock()
        for p, c in self.coins.items():
            self._cancel(c, t)
            if c.qty > 0 and p in quotes:
                self._market_out(c, quotes[p][0], "flatten", t)
        self.emit("flatten", why=why, value=self.value(quotes))

    def reconcile_all(self) -> None:
        """At start: the exchange's open orders and coins against the books, pair by pair."""
        for c in self.coins.values():
            self._reconcile_pair(c, "start")

    def _runner_locked(self) -> bool:
        try:
            return bool(json.loads((self.dir / "state.json").read_text()).get("locked_at"))
        except (OSError, ValueError):
            return False

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
            self.note("no-quotes", 600, "no_quotes")
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
        if self.mode == "live" and t - self.last_reconcile >= float(self.sc.get("reconcile_s", 300)):
            self.last_reconcile = t                                # the wallet's coins against the books
            bal = self.ex.balances()
            for p, c in self.coins.items():
                if p in q and c.order_id is None and abs(bal.get(p.split("/")[0], 0.0) - c.qty) * q[p][0] >= 1.0:
                    self._reconcile_pair(c, "periodic: wallet and books differ")
        grid = int(self.cfg["harness"]["grid_hour_utc"])          # the HKT day, as the hourly bot counts it
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
        if no_new:
            self.note("daily", 3600, "daily_loss_limit", value=v, day_start=self.day_start_value)
        w0, w1 = self.sc["runner_window"]
        in_window = w0 <= now.minute < w1
        min_check = float(self.sc.get("min_check_s", 12))
        min_step = float(self.sc.get("min_step_frac", 0.0015))
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
                since = t - self.last_check.get(p, -1e18)
                if (touch and since >= min_check) or since >= 60.0:
                    self.last_check[p] = t
                    if pend is None:
                        pend = self.ex.pending_pairs()
                    if pend.get(p, 0) == 0:
                        f = self.ex.order(p, c.order_id)
                        if f.status in ("FILLED", "CANCELED"):
                            self._apply(c, f, t, b)
                        else:
                            self._reconcile_pair(c, f"not pending but status {f.status}")
            if should_stop(c, b, step, self.p):                   # stops run even in the hourly bot's minutes
                self._cancel(c, t)
                if c.phase == "HOLDING" and c.qty > 0:
                    self._market_out(c, b, "stop", t)
                continue
            if in_window:
                continue
            if c.phase == "PAUSED":
                if t < c.paused_until:
                    continue
                c.phase, c.next_px = "BUYING", None
            if c.phase == "HOLDING" and c.order_id is None:
                self._place_target(c, b, t)
                continue
            if c.phase != "BUYING":
                continue
            small = step / b < min_step
            if small:
                self.note(f"step-{p}", 3600, "step_too_small", pair=p, step_frac=step / b)
            stop_buying = no_new or c.lot_usd <= 0 or t < c.blocked_until or small
            if c.order_id is not None and (stop_buying or should_trail(c, b, step, self.p)):
                trail = not stop_buying
                self._cancel(c, t)
                if c.phase == "BUYING" and c.order_id is None and trail:
                    c.next_px = b - step
            if c.phase == "BUYING" and c.order_id is None and not stop_buying:
                self._place_buy(c, buy_price(c, b, a, step), t)
        self.save(q)

    def run(self, once: bool = False) -> None:
        if not self.stopped:
            try:
                self.reconcile_all()
            except Exception as e:                          # noqa: BLE001 - reconcile again at the next error
                self.emit("error", error=f"start reconcile: {type(e).__name__}: {e}")
        self.emit("start", capital=self.capital, coins={k: v.lot_usd for k, v in self.coins.items()},
                  params=asdict(self.p), stopped=self.stopped, **self._changes)
        while True:
            t0 = self.clock()
            try:
                self.tick()
                self.errors, self.error_since = 0, None
            except Exception as e:                          # noqa: BLE001 - back off; only a long outage stops it
                self.errors += 1
                self.error_since = self.error_since or t0
                self.log.exception("sleeve tick failed")
                self.emit("error", error=f"{type(e).__name__}: {e}", in_a_row=self.errors)
                if self.clock() - self.error_since >= 60.0 * float(self.sc.get("error_kill_minutes", 60)):
                    try:
                        self.flatten(self.ex.quotes(sorted(self.coins)), "errors for too long")
                    except Exception as e2:                 # noqa: BLE001
                        self.emit("error", error=f"flatten failed: {type(e2).__name__}: {e2}")
                    self.stopped = "errors"
                    self.save()
                    return
                self.sleep(min(30.0 * 2 ** (self.errors - 1), 300.0))
                try:
                    for c in self.coins.values():           # a failed tick may have left an order half-booked
                        if c.order_id is not None:
                            self._reconcile_pair(c, "after an error")
                except Exception:                           # noqa: BLE001 - the next tick retries
                    pass
                continue
            if once or self.stopped:
                return
            now = pd.Timestamp(self.clock(), unit="s", tz="UTC")
            w0, w1 = self.sc["runner_window"]
            loop = 30.0 if w0 <= now.minute < w1 else float(self.sc["loop_s"])
            self.sleep(max(0.5, loop - (self.clock() - t0)))


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


# ---------------------------------------------------------------- replay: the live code on recorded quotes
def replay(cfg: dict, quotes_glob: str, start: str, end: str, rules: dict[str, PairRule], out_dir: Path,
           offset_s: float = 3.15) -> dict:
    """Run this module's Sleeve (paper exchange, Roostoo's measured rule) sample by sample on the recorder's files, with
    a clock that follows the samples: the same code as live, so its result can be checked against the simulator."""
    pairs = sorted(cfg["live"]["sleeve"]["lots_usd"])
    parts = []
    for f in sorted(globmod.glob(quotes_glob)):
        for ch in pd.read_csv(f, chunksize=2_000_000):
            parts.append(ch[ch.pair.isin(pairs)])
    q = pd.concat(parts, ignore_index=True)
    q["t"] = pd.to_datetime(q.ts_utc, utc=True).astype("int64") / 1e9 + offset_s
    t0, t1 = pd.Timestamp(start, tz="UTC").timestamp(), pd.Timestamp(end, tz="UTC").timestamp()
    q = q[(q.t >= t0) & (q.t < t1)].sort_values("t")
    cur: dict[str, tuple] = {}
    clock = {"t": t0}
    ex = PaperExchange(lambda ps: {p: cur[p] for p in ps if p in cur}, str(cfg["live"]["sleeve"].get("paper_sell_rule", "mid")))
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in out_dir.glob("sleeve*"):
        if f.is_file():
            f.unlink()
    c2 = json.loads(json.dumps(cfg, default=str))
    c2["live"]["start_at"] = c2["live"]["end_at"] = None
    sl = Sleeve(c2, ex, rules, out_dir, "paper", logging.getLogger("replay"), clock=lambda: clock["t"], sleep=lambda s: None)
    for t, g in q.groupby("t", sort=True):
        for r in g.itertuples():
            cur[r.pair] = (float(r.max_bid), float(r.min_ask), float(r.last_price))
        clock["t"] = float(t)
        sl.tick()
    last = {p: cur[p] for p in pairs if p in cur}
    v = sl.value(last)
    return {"start": start, "end": end, "capital": sl.capital, "value": v, "return": v / sl.capital - 1,
            "per_coin": {p: {"trips": c.trips, "wins": c.wins, "stops": c.stops, "pnl": c.pnl,
                             "pnl_of_lot": c.pnl / c.lot_usd if c.lot_usd else 0.0} for p, c in sl.coins.items()}}


# ---------------------------------------------------------------- CLI
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
    rp = sub.add_parser("replay")
    rp.add_argument("--start", required=True)
    rp.add_argument("--end", required=True)
    rp.add_argument("--out", default="results/sleeve_replay")
    stp = sub.add_parser("status")
    stp.add_argument("--mode", choices=("paper", "live"), default="live")
    a = ap.parse_args(argv)
    cfg = load_config()
    sc = cfg["live"].get("sleeve") or {}
    if a.cmd == "status":
        print(status(cfg, a.mode))
        return 0
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    log = logging.getLogger("sleeve")
    client = RoostooClient(cfg["exchange"]["base_url"], None, int(sc["calls_per_minute"]), cfg["execution"]["timeout_s"],
                           log=log)
    rules = parse_exchange_info(client.exchange_info())
    if a.cmd == "replay":
        res = replay(cfg, str(resolve(sc["recorder_glob"])), a.start, a.end, rules, resolve(a.out))
        print(json.dumps(res, indent=1, default=float))
        return 0
    if a.mode == "live":
        raise SystemExit("a live sleeve runs only inside the hourly bot (live.sleeve.mode: live); one process per instance")
    state_dir = resolve(a.state_dir or cfg["live"]["state_dir"])
    state_dir.mkdir(parents=True, exist_ok=True)
    qf = recorder_quotes(str(resolve(sc["recorder_glob"]))) if a.quotes == "recorder" else RoostooExchange(client).quotes
    ex = PaperExchange(qf, str(sc.get("paper_sell_rule", "mid")), float(sc["capital_usd"]))
    Sleeve(cfg, ex, rules, state_dir, "paper", log).run(once=a.once)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
