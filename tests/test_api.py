"""Roostoo client, rounding, order planner and paper broker. No network: a fake session stands in for HTTP."""
from __future__ import annotations

from decimal import Decimal

import pytest
import requests

from src.api.client import (Credentials, OrderStateUnknown, RateLimiter, RoostooClient, RoostooError, sign)
from src.api.rules import PairRule, fmt, meets_minimum, quantity_for, truncate
from src.execution.paper import PaperBroker
from src.execution.planner import (BUY, SELL, SHORT_CLOSE, SHORT_OPEN, Holdings, Quote, ShortPos, equity,
                                   plan_orders)

# ---------------- signing and rounding ----------------

DOC_SECRET = "S1XP1e3UZj6A7H5fATj0jNhqPxxdSJYdInClVN65XAbvqqMKjVHjA7PZj4W12oep"   # public example from the API docs


def test_signature_matches_the_documented_example():
    params = {"type": "MARKET", "timestamp": "1580774512000", "side": "BUY", "quantity": "2000", "pair": "BNB/USD"}
    total, sig = sign(params, DOC_SECRET)
    assert total == "pair=BNB/USD&quantity=2000&side=BUY&timestamp=1580774512000&type=MARKET"
    assert sig == "20b7fd5550b67b3bf0c1684ed0f04885261db8fdabd38611e9e6af23c19b7fff"


def test_truncation_and_plain_decimal_strings():
    assert truncate(0.29, 2) == Decimal("0.29")                      # float noise must not turn it into 0.28
    assert truncate(1.23456, 3) == Decimal("1.234")
    assert fmt(truncate(0.00001, 5)) == "0.00001"                  # never '1E-5'
    btc = PairRule("BTC/USD", 2, 5, Decimal("1"))
    q = quantity_for(20, 83000.0, btc)
    assert q == Decimal("0.00024") and meets_minimum(q, 83000.0, btc, 10)
    assert not meets_minimum(Decimal("0.00001"), 83000.0, btc, 10)


def test_rate_limiter_waits_for_a_free_slot():
    now, slept = [0.0], []
    rl = RateLimiter(3, clock=lambda: now[0], sleep=lambda s: (slept.append(s), now.__setitem__(0, now[0] + s)))
    for _ in range(3):
        rl.acquire()
    assert slept == []
    rl.acquire()
    assert slept and 59.9 < slept[0] <= 60.1


# ---------------- client behaviour ----------------

class FakeResponse:
    def __init__(self, status: int, payload: dict):
        self.status_code, self._p, self.text = status, payload, str(payload)

    def json(self):
        return self._p


class FakeSession:
    def __init__(self, script):
        self.script, self.calls = list(script), []

    def request(self, method, url, params=None, data=None, headers=None, timeout=None):
        self.calls.append({"method": method, "url": url, "params": params, "data": data, "headers": headers})
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return FakeResponse(*item)


def client(script, creds=True):
    c = Credentials("KEY", DOC_SECRET, "test") if creds else None
    return RoostooClient("https://x", c, 1000, session=FakeSession(script), clock=lambda: 1580774512.0,
                         sleep=lambda s: None)


def test_orders_are_never_retried_and_flag_unknown_state():
    c = client([requests.Timeout("slow")])
    with pytest.raises(OrderStateUnknown):
        c.place_order("BTC/USD", "BUY", "0.001")
    assert len(c.http.calls) == 1
    c = client([(503, {})])
    with pytest.raises(OrderStateUnknown):
        c.short_open("BTC/USD", "10")
    assert len(c.http.calls) == 1


def test_reads_retry_server_errors():
    c = client([(500, {}), (200, {"Success": True, "Data": {"BTC/USD": {"MaxBid": 1}}})], creds=False)
    assert c.ticker("BTC/USD") == {"BTC/USD": {"MaxBid": 1}}
    assert len(c.http.calls) == 2


def test_success_false_is_an_error_except_documented_empty_results():
    c = client([(200, {"Success": False, "ErrMsg": "no pending order under this account"})])
    assert c.pending_count()["TotalPending"] == 0
    c = client([(200, {"Success": False, "ErrMsg": "no order matched"})])
    assert c.query_order(pair="BTC/USD") == []
    c = client([(200, {"Success": False, "ErrMsg": "insufficient balance"})])
    with pytest.raises(RoostooError, match="insufficient balance"):
        c.place_order("BTC/USD", "BUY", "1")


def test_signed_post_sends_exactly_the_signed_body():
    c = client([(200, {"Success": True, "OrderDetail": {"Status": "FILLED"}})])
    c.place_order("BNB/USD", "BUY", "2000")
    call = c.http.calls[0]
    assert call["data"] == "pair=BNB/USD&quantity=2000&side=BUY&timestamp=1580774512000&type=MARKET"
    assert call["headers"]["MSG-SIGNATURE"] == "20b7fd5550b67b3bf0c1684ed0f04885261db8fdabd38611e9e6af23c19b7fff"
    assert call["headers"]["Content-Type"] == "application/x-www-form-urlencoded"


def test_cancel_all_needs_explicit_permission_and_keys_stay_hidden():
    with pytest.raises(ValueError):
        client([]).cancel_order()
    assert "KEY" not in repr(Credentials("KEY", "SECRET", "test"))


# ---------------- planner ----------------

RULES = {"BTC/USD": PairRule("BTC/USD", 2, 5, Decimal("1")), "DOGE/USD": PairRule("DOGE/USD", 5, 0, Decimal("1"))}
QUOTES = {"BTC/USD": Quote(bid=100_000.0, ask=100_010.0), "DOGE/USD": Quote(bid=0.1, ask=0.10001)}


def test_buy_from_cash_is_truncated_to_precision():
    orders, _ = plan_orders({"BTC/USD": 0.5, "DOGE/USD": 0.2}, Holdings(100_000.0), QUOTES, RULES, band=0.02)
    kinds = {o.pair: o for o in orders}
    assert kinds["BTC/USD"].kind == BUY and kinds["BTC/USD"].quantity == quantity_for(50_000, 100_010.0, RULES["BTC/USD"])
    assert kinds["DOGE/USD"].quantity == kinds["DOGE/USD"].quantity.to_integral_value()   # precision 0


def test_band_skips_small_moves_but_exits_always_trade():
    h = Holdings(50_000.0, {"BTC/USD": 0.5})                              # 50% BTC at the bid
    orders, _ = plan_orders({"BTC/USD": 0.51}, h, QUOTES, RULES, band=0.02)
    assert orders == []
    orders, _ = plan_orders({}, h, QUOTES, RULES, band=0.5)
    assert len(orders) == 1 and orders[0].kind == SELL and orders[0].quantity == Decimal("0.5")


def test_exact_mode_trades_small_differences():
    h = Holdings(50_000.0, {"BTC/USD": 0.5})
    orders, _ = plan_orders({"BTC/USD": 0.51}, h, QUOTES, RULES, band=0.02, exact=True)
    assert [o.kind for o in orders] == [BUY]


def test_sells_come_first_and_buys_fit_the_cash():
    h = Holdings(1_000.0, {"BTC/USD": 0.99})                             # ~99% BTC
    orders, notes = plan_orders({"DOGE/USD": 1.0}, h, QUOTES, RULES, band=0.02)
    assert [o.kind for o in orders] == [SELL, BUY]
    buy = orders[1]
    cash = 1_000.0 + float(orders[0].quantity) * 100_000.0 * 0.999 - 0.01 * equity(h, QUOTES)
    assert float(buy.quantity) * 0.10001 * 1.001 <= cash + 1e-6
    assert any("scaled" in n for n in notes)


def test_long_to_short_flip_and_full_short_close():
    h = Holdings(0.0, {"BTC/USD": 1.0})
    orders, _ = plan_orders({"BTC/USD": -0.25}, h, QUOTES, RULES, band=0.02)
    assert [o.kind for o in orders] == [SELL, SHORT_OPEN]
    h2 = Holdings(75_000.0, {}, {"BTC/USD": ShortPos(0.25, 25_000.0, 100_000.0)})
    orders, _ = plan_orders({}, h2, QUOTES, RULES, band=0.5)
    assert len(orders) == 1 and orders[0].kind == SHORT_CLOSE and orders[0].quantity is None


# ---------------- paper broker ----------------

def test_paper_round_trip_costs_fees_and_spread():
    h = Holdings(100_000.0)
    pb = PaperBroker(h, RULES)
    orders, _ = plan_orders({"BTC/USD": 0.5}, h, QUOTES, RULES, band=0.0)
    pb.execute(orders, QUOTES)
    orders, _ = plan_orders({}, h, QUOTES, RULES, band=0.0)
    pb.execute(orders, QUOTES)
    loss = 100_000.0 - h.usd_free
    assert 0 < loss < 50_000 * (0.002 + 0.0002) + 1          # two fees plus the spread, on half the book


def test_paper_short_gains_when_price_falls():
    h = Holdings(100_000.0)
    pb = PaperBroker(h, RULES)
    orders, _ = plan_orders({"BTC/USD": -0.1}, h, QUOTES, RULES, band=0.0)
    pb.execute(orders, QUOTES)
    lower = {"BTC/USD": Quote(bid=90_000.0, ask=90_010.0)}
    assert equity(h, lower) > equity(h, QUOTES)
