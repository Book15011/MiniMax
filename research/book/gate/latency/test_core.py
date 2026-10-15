import copy
import numpy as np
import pytest
from research.book.gate.latency.core import causal_asof,gaps,simulate,penalized_round
P={"capital":100000,"taker":.001,"long_exposure":.99,"short_exposure":.5,"min_order":1,
   "hold_seconds":120,"stop_fraction":.02,"cooldown_seconds":12,"basis_seconds":12,"min_basis_observations":2}
RULE={"X":{"AmountPrecision":2,"MiniOrder":1}}
C={"name":"test","directions":[1],"threshold":.0025}
def run(b,a=None,*,short=False,delay=6,end=None):
    b=np.asarray(b,float)[:,None];a=b+.1 if a is None else np.asarray(a,float)[:,None]
    t=np.arange(len(b),dtype=float)*6;g=np.full_like(b,.01)
    return simulate(t,b,a,g,g,RULE,["X"],{**C,"directions":[-1] if short else [1]},P,delay,t[0],t[-1] if end is None else end)
def test_asof_never_reads_unreceived_future_packets_and_expires_old_data():
    z=causal_asof(np.array([0.,2.,4.,10.]),np.array([1.,3.,20.]),np.array([[10.],[20.],[999.]]),3)
    assert np.isnan(z[0,0]) and z[1,0]==10 and z[2,0]==20 and np.isnan(z[3,0])
def test_basis_excludes_current_and_future_rows():
    t=np.arange(6)*6.;b=np.full((6,1),100.);a=b+.1;e=(b+a)/2
    x=gaps(t,b,a,e,e,P)
    altered=e.copy();altered[4:]=1000
    y=gaps(t,b,a,altered,altered,P)
    assert np.allclose(x[2][:5],y[2][:5],equal_nan=True)
    assert np.isnan(x[0][:2]).all()
def test_disappearing_gap_does_not_buy_at_the_earlier_stale_ask():
    z=run([100,110,110])
    assert z["trips"][0]["entry_time"]==6
    assert z["trips"][0]["entry_price"]==110.1
    assert z["return"]<0
def test_flat_price_loses_spread_and_both_taker_fees():
    z=run([100,100,100])
    tr=z["trips"][0];q=tr["qty"]
    assert z["return"]<0 and tr["terminal"]
    assert tr["net_pnl"]==pytest.approx(q*(100-100.1)-q*(100+100.1)*.001,abs=1e-8)
    assert z["fees_usd"]==pytest.approx(tr["entry_fee"]+tr["exit_fee"])
def test_short_uses_bid_entry_ask_cover_and_losing_inventory_counts():
    z=run([100,100,110],short=True);tr=z["trips"][0];q=tr["qty"]
    assert tr["side"]==-1 and tr["entry_price"]==100 and tr["exit_price"]==110.1
    assert tr["net_pnl"]==pytest.approx(q*(100-110.1)-q*(100+110.1)*.001,abs=1e-8)
    assert z["return"]<-.05
def test_unarrived_entry_expires_without_a_fabricated_fill():
    z=run([100,100],delay=30)
    assert z["trades"]==0 and z["expired_entries"]==1 and z["return"]==0 and z["fees_usd"]==0
def test_missing_terminal_quote_does_not_report_zero_loss():
    z=run([100,100,np.nan])
    assert z["return"] is None and z["mdd"] is None and not z["terminal_priced"]
def test_suffix_cannot_change_completed_period():
    x=run([100,100,101,102],end=12)
    y=run([100,100,101,999999],end=12)
    assert x["return"]==y["return"] and x["trips"]==y["trips"]
def test_quantity_precision_and_long_cash_reserve():
    z=run([100,100,100]);tr=z["trips"][0]
    assert abs(tr["qty"]*100-round(tr["qty"]*100))<1e-7
    assert tr["entry_cash_after"]>=999
def test_minimum_order_is_not_invented():
    b=np.full((3,1),100.);g=np.ones_like(b)
    p={**P,"capital":.5}
    z=simulate(np.array([0.,6.,12.]),b,b+.1,g,g,RULE,["X"],C,p,6,0,12)
    assert z["trades"]==0 and z["return"]==0
def test_penalty_denominators_differ_and_do_not_discount_losses():
    assert penalized_round(.5,"none")==pytest.approx(.26)
    assert penalized_round(.5,"subtract_20pp")==pytest.approx(.06)
    assert penalized_round(.5,"equity_haircut20")==pytest.approx(.008)
    assert penalized_round(.5,"round_profit_haircut20")==pytest.approx(.208)
    assert penalized_round(.5,"incremental_profit_haircut20")==pytest.approx(.176)
    assert penalized_round(-.1,"round_profit_haircut20")==pytest.approx(-.244)
