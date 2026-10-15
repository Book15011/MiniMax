from decimal import Decimal
import numpy as np
from research.book.gate.simulator_edge.money import break_even,quantity,penalty_gain,resting_hit,trade_pnl

def test_exact_fee_spread_break_even_and_truncate():
    p=break_even(.0364,.001,.0005)
    assert abs(p-.0364*1.001/.9995)<1e-15
    q=quantity(100,.0364,1,.001)
    assert q==float(Decimal(str(q)).quantize(Decimal(".1")))
    assert q*.0364*1.001<=100 and q>=0

def test_market_entry_exit_costs_and_short_symmetry():
    x=trade_pnl(10,100,101,.001,.0005,1)
    assert abs(x-(1010*.9995-1000*1.001))<1e-12
    y=trade_pnl(10,100,99,.001,.001,-1)
    assert abs(y-(1000*.999-990*1.001))<1e-12

def test_bid_touch_is_not_a_strict_maker_buy_and_confirmation():
    assert not resting_hit("BUY",100,100,101,100,"ask",1,2)
    assert not resting_hit("BUY",100,99,100,99,"ask",1,2)
    assert resting_hit("BUY",100,99,100,99,"ask",2,2)
    assert not resting_hit("SELL",101,100,101,101,"ask",2,2)
    assert resting_hit("SELL",101,101,102,101,"ask",2,2)

def test_penalty_denominators_are_not_interchangeable():
    assert abs(penalty_gain(-.16,0,"none")-(1/.84-1))<1e-12
    assert abs(penalty_gain(-.16,0,"subtract_20pp")-(1.2/.84-1))<1e-12
    assert abs(penalty_gain(-.16,0,"equity_haircut20")-(1/.8/.84-1))<1e-12
    assert abs(penalty_gain(-.16,.02,"round_profit_haircut20")-(1.025/.84-1))<1e-12

def test_quantity_bad_data_and_no_negative_funds():
    for price in [0,-1,np.nan,np.inf]:
        assert quantity(100,price,2,.001)==0
    assert quantity(0,1,2,.001)==0
