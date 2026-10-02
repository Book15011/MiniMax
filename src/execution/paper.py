"""Paper broker: fills planned orders against live quotes with Roostoo's fee rules. No API keys needed.

Market BUY fills at the ask and SELL at the bid, 0.1% fee on the traded value. SHORT_OPEN fills at the bid with
quantity = collateral / price (truncated to the pair's precision) and a 0.1% fee on the position value;
SHORT_CLOSE fills at the ask, returns the closed share of the collateral plus P&L minus a 0.1% fee.
"""
from __future__ import annotations

from dataclasses import replace

from src.api.rules import PairRule, truncate
from src.execution.planner import BUY, SELL, SHORT_CLOSE, SHORT_OPEN, Holdings, Order, Quote, ShortPos


class PaperBroker:
    def __init__(self, holdings: Holdings, rules: dict[str, PairRule], fee: float = 0.001):
        self.h, self.rules, self.fee = holdings, rules, fee

    def execute(self, orders: list[Order], quotes: dict[str, Quote]) -> list[dict]:
        fills = []
        for o in orders:
            q = quotes[o.pair]
            if o.kind == BUY:
                qty = float(o.quantity)
                cost = qty * q.ask
                if cost * (1 + self.fee) > self.h.usd_free + 1e-9:
                    fills.append({"order": o, "status": "REJECTED", "reason": "insufficient balance"})
                    continue
                self.h.usd_free -= cost * (1 + self.fee)
                self.h.spot[o.pair] = self.h.spot.get(o.pair, 0.0) + qty
                fills.append({"order": o, "status": "FILLED", "price": q.ask, "qty": qty, "fee": cost * self.fee})
            elif o.kind == SELL:
                qty = min(float(o.quantity), self.h.spot.get(o.pair, 0.0))
                value = qty * q.bid
                self.h.usd_free += value * (1 - self.fee)
                self.h.spot[o.pair] = self.h.spot.get(o.pair, 0.0) - qty
                fills.append({"order": o, "status": "FILLED", "price": q.bid, "qty": qty, "fee": value * self.fee})
            elif o.kind == SHORT_OPEN:
                coll = float(o.collateral)
                qty = float(truncate(coll / q.bid, self.rules[o.pair].amount_precision))
                fee = qty * q.bid * self.fee
                if coll + fee > self.h.usd_free + 1e-9:
                    fills.append({"order": o, "status": "REJECTED", "reason": "insufficient balance"})
                    continue
                self.h.usd_free -= coll + fee
                old = self.h.shorts.get(o.pair)
                if old:
                    tq = old.qty + qty
                    self.h.shorts[o.pair] = ShortPos(tq, old.collateral + coll, (old.entry * old.qty + q.bid * qty) / tq)
                else:
                    self.h.shorts[o.pair] = ShortPos(qty, coll, q.bid)
                fills.append({"order": o, "status": "FILLED", "price": q.bid, "qty": qty, "fee": fee})
            elif o.kind == SHORT_CLOSE:
                pos = self.h.shorts[o.pair]
                qty = pos.qty if o.quantity is None else min(float(o.quantity), pos.qty)
                frac = qty / pos.qty
                pnl = qty * (pos.entry - q.ask)
                fee = qty * q.ask * self.fee
                self.h.usd_free += frac * pos.collateral + max(pnl, -frac * pos.collateral) - fee
                if frac >= 1.0 - 1e-12:
                    del self.h.shorts[o.pair]
                else:
                    self.h.shorts[o.pair] = replace(pos, qty=pos.qty - qty, collateral=pos.collateral * (1 - frac))
                fills.append({"order": o, "status": "FILLED", "price": q.ask, "qty": qty, "fee": fee, "pnl": pnl})
        return fills
