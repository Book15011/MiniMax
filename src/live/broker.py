"""Brokers for the live runner: one interface, two implementations.

- LiveBroker: the Roostoo account. Holdings from /v3/balance and /v6/short_positions, orders through
  src.api.client (never retried). An order whose outcome is unknown (timeout, 5xx) stops the batch: the next
  hour re-reads the holdings and plans again from what actually happened.
- PaperAccount: a simulated account (src.execution.paper.PaperBroker) filled at live Roostoo quotes; its holdings
  persist in the runner's state file. No API key needed.
"""
from __future__ import annotations

import logging
import time
from typing import Callable

from src.api.client import OrderStateUnknown, RoostooClient, RoostooError
from src.api.rules import fmt
from src.execution.paper import PaperBroker
from src.execution.planner import BUY, SELL, SHORT_CLOSE, SHORT_OPEN, Holdings, Order, Quote, ShortPos

QUOTE = "USD"


class ShortsUnreadable(RoostooError):
    """/v6/short_positions answered in a shape we cannot read. The runner then trades long-only."""


def quotes_from_ticker(data: dict) -> dict[str, Quote]:
    out = {}
    for pair, q in data.items():
        bid, ask = float(q.get("MaxBid") or 0.0), float(q.get("MinAsk") or 0.0)
        if bid > 0 and ask >= bid:
            out[pair] = Quote(bid, ask)
    return out


def _pick(d: dict, *names: str):
    low = {k.lower(): v for k, v in d.items()}
    for n in names:
        if n.lower() in low and low[n.lower()] is not None:
            return low[n.lower()]
    return None


def parse_short(p: dict) -> tuple[str, ShortPos]:
    """One entry of /v6/short_positions. Field names beyond Collateral are UNVERIFIED until the test-key
    self-check; anything we cannot read raises, so the bot never trades on a misread position."""
    pair = _pick(p, "Pair", "Symbol")
    qty = _pick(p, "Quantity", "Qty", "Amount", "Size", "OpenQuantity")
    entry = _pick(p, "EntryPrice", "AvgPrice", "OpenPrice", "Price")
    coll = _pick(p, "Collateral")
    if pair is None or qty is None or entry is None or coll is None:
        raise ShortsUnreadable(f"short position fields not recognised: {sorted(p)}")
    return str(pair), ShortPos(float(qty), float(coll), float(entry))


class LiveBroker:
    def __init__(self, client: RoostooClient, log: logging.Logger, order_spacing_s: float = 10.0,
                 sleep: Callable[[float], None] = time.sleep):
        self.c, self.log, self.spacing, self.sleep = client, log, order_spacing_s, sleep

    def quotes(self) -> dict[str, Quote]:
        return quotes_from_ticker(self.c.ticker())

    def holdings(self, with_shorts: bool = True) -> Holdings:
        wallet = self.c.balance()
        usd = wallet.get(QUOTE, {})
        h = Holdings(float(usd.get("Free") or 0.0))
        for coin, b in wallet.items():
            if coin == QUOTE:
                continue
            qty = float(b.get("Free") or 0.0) + float(b.get("Lock") or 0.0)
            if qty > 0:
                h.spot[f"{coin}/{QUOTE}"] = qty
        if with_shorts:
            for p in self.c.short_positions():
                pair, pos = parse_short(p)
                if pos.qty > 0:
                    h.shorts[pair] = pos
        return h

    def execute(self, orders: list[Order], quotes: dict[str, Quote], h: Holdings) -> list[dict]:
        out = []
        for k, o in enumerate(orders):
            if k:
                self.sleep(self.spacing)
            try:
                if o.kind in (BUY, SELL):
                    r = self.c.place_order(o.pair, o.kind, fmt(o.quantity))
                elif o.kind == SHORT_OPEN:
                    r = self.c.short_open(o.pair, fmt(o.collateral))
                elif o.kind == SHORT_CLOSE:
                    r = self.c.short_close(o.pair, close_qty=None if o.quantity is None else fmt(o.quantity))
                else:
                    raise ValueError(o.kind)
                status = str(r.get("Status") or r.get("OrderDetail", {}).get("Status") or "SENT").upper()
                out.append({"order": o, "status": "FILLED" if status in ("FILLED", "SENT") else status, "response": r})
            except OrderStateUnknown as e:
                out.append({"order": o, "status": "UNKNOWN", "error": str(e)})
                self.log.error("order outcome unknown (%s); stopping this batch, the next hour re-plans from the "
                               "holdings", e)
                break
            except RoostooError as e:
                out.append({"order": o, "status": "ERROR", "error": str(e)})
                self.log.warning("order refused: %s %s: %s", o.kind, o.pair, e)
        return out


class PaperAccount:
    """Simulated account at live quotes. `quotes_fn` is the public ticker (no key)."""

    def __init__(self, holdings: Holdings, rules: dict, quotes_fn: Callable[[], dict[str, Quote]], fee: float = 0.001):
        self.h, self.rules, self.quotes_fn, self.fee = holdings, rules, quotes_fn, fee

    def quotes(self) -> dict[str, Quote]:
        return self.quotes_fn()

    def holdings(self, with_shorts: bool = True) -> Holdings:
        return self.h

    def execute(self, orders: list[Order], quotes: dict[str, Quote], h: Holdings) -> list[dict]:
        return PaperBroker(self.h, self.rules, self.fee).execute(orders, quotes)
