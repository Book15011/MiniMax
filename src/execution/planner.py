"""Order planner: target weights -> the orders that move current holdings there.

Shared by paper trading and the live bot, so both place exactly the same orders.
- Weights are fractions of equity: > 0 long spot, < 0 short (Roostoo 1x short: collateral = notional).
- Longs are valued at the bid, shorts at the ask (what closing them would get).
- At a normal decision a pair trades only if its weight is off target by more than `band`; a full exit
  (target 0) always trades; `exact=True` (activity guard) trades every difference.
- Reductions and exits come first (they free cash); buys and new shorts follow, scaled down together so they
  fit the free USD after fees and a cash buffer. Quantities are truncated to each pair's precision; orders
  below the pair's minimum or `min_trade_usd` are skipped (except closing a whole short).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from src.api.rules import PairRule, meets_minimum, quantity_for, truncate

SELL, SHORT_CLOSE, BUY, SHORT_OPEN = "SELL", "SHORT_CLOSE", "BUY", "SHORT_OPEN"


@dataclass(frozen=True)
class Quote:
    bid: float
    ask: float


@dataclass(frozen=True)
class ShortPos:
    qty: float
    collateral: float
    entry: float


@dataclass
class Holdings:
    usd_free: float
    spot: dict[str, float] = field(default_factory=dict)       # pair -> coins held (Free + Lock)
    shorts: dict[str, ShortPos] = field(default_factory=dict)  # pair -> open short


@dataclass(frozen=True)
class Order:
    kind: str                       # SELL | SHORT_CLOSE | BUY | SHORT_OPEN
    pair: str
    quantity: Decimal | None        # coins; None on SHORT_CLOSE means "close the whole short"
    collateral: Decimal | None      # USD, SHORT_OPEN only
    est_value: float                # USD notional, for logs and cash checks
    reason: str


def short_value(p: ShortPos, ask: float) -> float:
    return p.collateral + p.qty * (p.entry - ask)


def equity(h: Holdings, quotes: dict[str, Quote]) -> float:
    e = h.usd_free
    for pair, qty in h.spot.items():
        if qty and pair in quotes:
            e += qty * quotes[pair].bid
    for pair, p in h.shorts.items():
        if pair in quotes:
            e += short_value(p, quotes[pair].ask)
        else:
            e += p.collateral
    return e


def current_weights(h: Holdings, quotes: dict[str, Quote], eq: float) -> dict[str, float]:
    w: dict[str, float] = {}
    for pair, qty in h.spot.items():
        if qty and pair in quotes:
            w[pair] = w.get(pair, 0.0) + qty * quotes[pair].bid / eq
    for pair, p in h.shorts.items():
        if p.qty and pair in quotes:
            w[pair] = w.get(pair, 0.0) - p.qty * quotes[pair].ask / eq
    return w


def plan_orders(targets: dict[str, float], h: Holdings, quotes: dict[str, Quote], rules: dict[str, PairRule],
                band: float, fee: float = 0.001, cash_buffer: float = 0.01, min_trade_usd: float = 10.0,
                exact: bool = False) -> tuple[list[Order], list[str]]:
    """Returns (orders in execution order, notes about anything skipped)."""
    notes: list[str] = []
    eq = equity(h, quotes)
    if eq <= 0:
        return [], ["equity is not positive; nothing planned"]
    cur = current_weights(h, quotes, eq)
    reduce: list[Order] = []
    adds: list[tuple[str, str, float]] = []       # (kind, pair, usd value)
    proceeds = 0.0
    for pair in sorted(set(targets) | set(cur)):
        tw, cw = float(targets.get(pair, 0.0)), float(cur.get(pair, 0.0))
        rule, q = rules.get(pair), quotes.get(pair)
        if rule is None or q is None or not rule.can_trade:
            if abs(tw - cw) > 1e-12:
                notes.append(f"{pair}: not tradable now (no rule, quote or CanTrade=false); skipped")
            continue
        if not exact and abs(tw - cw) <= band and not (tw == 0.0 and cw != 0.0):
            continue
        cl, cs, tl, ts = max(cw, 0.0), max(-cw, 0.0), max(tw, 0.0), max(-tw, 0.0)
        if tl < cl:                                                   # sell spot
            held = h.spot.get(pair, 0.0)
            qty = truncate(held, rule.amount_precision) if tl == 0.0 else quantity_for((cl - tl) * eq, q.bid, rule)
            if meets_minimum(qty, q.bid, rule, min_trade_usd):
                reduce.append(Order(SELL, pair, qty, None, float(qty) * q.bid, f"weight {cw:+.3f} -> {tw:+.3f}"))
                proceeds += float(qty) * q.bid * (1 - fee)
            else:
                notes.append(f"{pair}: sell of {qty} below the minimum order; left as dust")
        if ts < cs:                                                   # reduce or close the short
            pos = h.shorts[pair]
            if ts == 0.0:
                reduce.append(Order(SHORT_CLOSE, pair, None, None, pos.qty * q.ask, f"close short ({cw:+.3f} -> {tw:+.3f})"))
                proceeds += short_value(pos, q.ask) - pos.qty * q.ask * fee
            else:
                qty = quantity_for((cs - ts) * eq, q.ask, rule)
                if meets_minimum(qty, q.ask, rule, min_trade_usd):
                    frac = min(float(qty) / pos.qty, 1.0)
                    reduce.append(Order(SHORT_CLOSE, pair, qty, None, float(qty) * q.ask, f"reduce short {cw:+.3f} -> {tw:+.3f}"))
                    proceeds += frac * short_value(pos, q.ask) - float(qty) * q.ask * fee
        if tl > cl:
            adds.append((BUY, pair, (tl - cl) * eq))
        if ts > cs:
            adds.append((SHORT_OPEN, pair, (ts - cs) * eq))

    available = h.usd_free + proceeds - cash_buffer * eq
    need = sum(v for _, _, v in adds) * (1 + fee)
    scale = 1.0 if need <= 0 else max(0.0, min(1.0, available / need))
    if scale < 1.0:
        notes.append(f"buys and new shorts scaled to {scale:.1%} to fit free cash")
    grow: list[Order] = []
    for kind, pair, value in adds:
        rule, q = rules[pair], quotes[pair]
        value *= scale
        if kind == BUY:
            qty = quantity_for(value, q.ask, rule)
            if meets_minimum(qty, q.ask, rule, min_trade_usd):
                grow.append(Order(BUY, pair, qty, None, float(qty) * q.ask, "add long"))
            else:
                notes.append(f"{pair}: buy of ${value:.2f} below the minimum order; skipped")
        else:
            coll = truncate(value, 2)
            if coll >= max(Decimal("1"), Decimal(str(min_trade_usd))):
                grow.append(Order(SHORT_OPEN, pair, None, coll, float(coll), "add short"))
            else:
                notes.append(f"{pair}: short of ${value:.2f} below the minimum; skipped")
    order = {SELL: 0, SHORT_CLOSE: 1, BUY: 2, SHORT_OPEN: 3}
    return sorted(reduce, key=lambda o: order[o.kind]) + sorted(grow, key=lambda o: order[o.kind]), notes
