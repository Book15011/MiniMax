"""Money and causal accounting contracts for the new comparison."""
from decimal import Decimal as D
import pytest
from research.book.gate.directional_benchmark.broker import Portfolio, Order
def test_long_round_trip_fees_and_spread():
    p=Portfolio(D("2000"))
    p.fill(Order("BTC",1,D("1")),D("1000"),D(".001"))
    assert p.cash==D("999")
    assert p.nav({"BTC":(D("999"),D("1000"))})==D("1998")
    p.fill(Order("BTC",-1,D("1")),D("1005"),D(".001"))
    assert p.cash==D("2002.995") and not p.positions
def test_short_proceeds_cannot_fund_extra_exposure():
    p=Portfolio(D("2000"))
    p.fill(Order("BTC",-1,D("1")),D("1000"),D(".001"))
    assert p.cash==D("1999") and p.free_cash()==D("999")
    assert p.nav({"BTC":(D("999"),D("1001"))})==D("1998")
    p.fill(Order("BTC",1,D("1")),D("990"),D(".001"))
    assert p.cash==D("2008.01") and not p.positions
def test_partial_short_close_releases_only_its_collateral():
    p=Portfolio(D("2000"));p.fill(Order("BTC",-1,D("1")),D("1000"),D(".001"))
    p.fill(Order("BTC",1,D(".5")),D("990"),D(".001"))
    assert p.positions["BTC"][0]==D("-.5") and p.free_cash()==D("1503.505")
def test_invalid_and_insufficient_funds_are_atomic():
    p=Portfolio(D("2000"))
    with pytest.raises(ValueError):p.fill(Order("BTC",1,D("3")),D("1000"),D(".001"))
    assert p.cash==D("2000") and not p.positions and p.fees==0
def test_maker_role_depends_on_arrival_not_order_name():
    from research.book.gate.directional_benchmark.broker import role
    assert role(1,D("100"),D("99"),D("100"))=="TAKER"
    assert role(1,D("99"),D("99"),D("100"))=="RESTING"
    assert role(-1,D("100"),D("99"),D("100"))=="RESTING"
    assert role(-1,D("99"),D("99"),D("100"))=="TAKER"
