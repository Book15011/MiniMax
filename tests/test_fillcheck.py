"""fillcheck --limit: passive prices, waiting, cancelling and ending flat. Fake exchange, no network."""
import logging
from decimal import Decimal

from src.api.rules import PairRule
from src.live import fillcheck

LOG = logging.getLogger("test_fillcheck")
RULE = PairRule("BTC/USD", 2, 5, Decimal(1))


class FakeExchange:
    """BUY limits fill after `buy_polls` queries; SELL limits never fill (so the remainder is market-sold)."""

    def __init__(self, buy_polls: int = 1):
        self.orders, self.calls, self.buy_polls, self.coins = {}, [], buy_polls, Decimal(0)

    def ticker(self, pair=None):
        return {"BTC/USD": {"MaxBid": "100000.004", "MinAsk": "100000.016"}}

    def place_order(self, pair, side, quantity, order_type="MARKET", price=None):
        oid = len(self.orders) + 1
        self.calls.append((side, order_type, quantity, price))
        o = {"OrderID": oid, "Side": side, "Type": order_type, "Quantity": float(quantity), "Price": float(price or 0),
             "Status": "PENDING", "Role": "MAKER", "FilledQuantity": 0.0, "FilledAverPrice": 0.0,
             "CommissionChargeValue": 0.0, "polls": 0}
        if order_type == "MARKET":
            o.update(Status="FILLED", Role="TAKER", FilledQuantity=float(quantity), FilledAverPrice=100000.0)
            self.coins -= Decimal(quantity) if side == "SELL" else -Decimal(quantity)
        self.orders[oid] = o
        return dict(o)

    def query_order(self, order_id=None, **kw):
        o = self.orders[order_id]
        o["polls"] += 1
        if o["Status"] == "PENDING" and o["Side"] == "BUY" and o["polls"] >= self.buy_polls:
            o.update(Status="FILLED", FilledQuantity=o["Quantity"], FilledAverPrice=o["Price"],
                     CommissionChargeValue=o["Quantity"] * o["Price"] * 0.0005)
            self.coins += Decimal(str(o["Quantity"]))
        return [dict(o)]

    def cancel_order(self, order_id=None, pair=None):
        self.orders[order_id]["Status"] = "CANCELED"
        return [order_id]


def test_passive_prices_never_cross_the_book():
    assert fillcheck.passive_price(100000.004, 2, "BUY") == Decimal("100000.00")
    assert fillcheck.passive_price(100000.016, 2, "SELL") == Decimal("100000.02")


def test_limit_check_waits_cancels_and_ends_flat(monkeypatch):
    monkeypatch.setattr(fillcheck.time, "sleep", lambda s: None)
    ex = FakeExchange(buy_polls=1)                          # BUY fills on the first query; SELL never
    lines = fillcheck.limit_check(ex, RULE, "BTC/USD", [100.0], wait_s=0.0, poll_s=0.0, log=LOG)
    kinds = [(side, typ) for side, typ, *_ in ex.calls]
    assert kinds == [("BUY", "LIMIT"), ("SELL", "LIMIT"), ("SELL", "MARKET")]
    assert ex.calls[0][3] == "100000.00" and ex.calls[1][3] == "100000.02"
    assert ex.coins == 0                                     # flat at the end
    assert any("| BUY |" in ln and "FILLED" in ln and "0.0500%" in ln for ln in lines)
    assert any("| SELL |" in ln and "CANCELED" in ln for ln in lines)


def test_an_unfilled_buy_is_cancelled_and_nothing_is_sold(monkeypatch):
    monkeypatch.setattr(fillcheck.time, "sleep", lambda s: None)
    ex = FakeExchange(buy_polls=99)
    lines = fillcheck.limit_check(ex, RULE, "BTC/USD", [100.0], wait_s=0.0, poll_s=0.0, log=LOG)
    assert [(side, typ) for side, typ, *_ in ex.calls] == [("BUY", "LIMIT")] and ex.coins == 0
    assert ex.orders[1]["Status"] == "CANCELED" and any("0 of 1 limit orders filled" in ln for ln in lines)
