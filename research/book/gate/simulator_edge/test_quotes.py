import numpy as np
import pandas as pd
from research.book.gate.simulator_edge.quotes import run,features
P={"sample_seconds":30,"lag_samples":1,"capital":100000,"exposure":.99,"taker":.001,"maker":.0005,
"maker_expiry_seconds":120,"maker_confirm_samples":2,"decision_seconds":300,"pause_seconds":60,
"tick_hold_seconds":3600,"stop_ticks":2,"entry_hurdle":.002,"partial_fill_fraction":.5,
"hold_minutes":30,"tick_reversal_hold_minutes":10,"breakout_hold_minutes":60,"leader_hold_minutes":60,
"lookback_minutes":5,"breakout_lookback_minutes":60,"spread_lookback_minutes":30,"reserve_calls_per_minute":4,
"total_calls_per_minute":20}
RULE={"STO/USD":{"PricePrecision":4,"AmountPrecision":1,"MiniOrder":1}}
def data():
    ix=pd.date_range("2026-10-08",periods=121,freq="30s",tz="UTC")
    b=pd.DataFrame(.0363,index=ix,columns=["STO/USD"]);a=b+.0001;l=a.copy()
    return b,a,l
def test_bid_touch_does_not_create_strict_maker_inventory():
    b,a,l=data();z=run("tick_mm",b,a,l,features(b,a,l,RULE,P),RULE,P,b.index[10],b.index[-1])
    assert z["trades"]==0 and z["entry_fills"]==0 and z["return"]==0 and z["entry_attempts"]>0
def test_market_fill_is_delayed_ask_and_terminal_inventory_is_not_omitted():
    b,a,l=data();b.iloc[:21,0]=np.linspace(.03,.0363,21);a=b+.0001;l=a.copy()
    b.iloc[21:,0]=.04;a=b+.0001;l=a.copy()
    z=run("mom5_tt",b,a,l,features(b,a,l,RULE,P),RULE,P,b.index[20],b.index[-1])
    assert z["trades"]>=1
    first=z["trips"][0]
    assert first["entry_time"]>b.index[20].timestamp()
    assert first["entry_price"]==a.iloc[21,0]
    assert z["total_costs"]>0 and all(t["exit_time"]>=t["entry_time"] for t in z["trips"])
def test_future_rows_do_not_change_a_fixed_past_period():
    b,a,l=data();b.iloc[:21,0]=np.linspace(.03,.0363,21);a=b+.0001;l=a.copy()
    f=features(b,a,l,RULE,P)
    x=run("mom5_tt",b,a,l,f,RULE,P,b.index[20],b.index[80])
    b2=b.copy();b2.iloc[81:,0]=1e6;a2=b2+.0001;l2=a2.copy()
    y=run("mom5_tt",b2,a2,l2,features(b2,a2,l2,RULE,P),RULE,P,b.index[20],b.index[80])
    assert x["return"]==y["return"] and x["trips"]==y["trips"]
def test_execution_price_changes_beyond_entry_are_losses_after_costs():
    b,a,l=data();z=run("last_low_tt",b,a,b.copy(),features(b,a,b,RULE,P),RULE,P,b.index[10],b.index[-1])
    assert z["return"]<0 and z["max_calls_minute"]<=20

def test_multiasset_features_align_to_coins_and_market_filter_broadcasts():
    b,a,l=data()
    b["BTC/USD"]=b["STO/USD"]*1e6;a["BTC/USD"]=b["BTC/USD"]+.01;l["BTC/USD"]=a["BTC/USD"]
    rules={**RULE,"BTC/USD":{"PricePrecision":2,"AmountPrecision":6,"MiniOrder":1}}
    f=features(b,a,l,rules,P)
    assert np.isfinite(f["tick_mm"][:,0]).all()
    assert np.isnan(f["tick_mm"][:,1]).all()
    assert f["market60_tt"].shape==b.shape

def test_saved_equity_and_cash_ledger_reconstruct_exactly():
    b,a,l=data();b.iloc[:21,0]=np.linspace(.03,.0363,21);a=b+.0001;l=a.copy()
    z=run("mom5_tt",b,a,l,features(b,a,l,RULE,P),RULE,P,b.index[20],b.index[-1],trace=True)
    e=z["_trace"]["equity"]
    assert abs(z["return"]-sum(x["net_pnl"] for x in z["trips"])/P["capital"])<1e-12
    assert z["mdd"]==float(-(e/np.maximum.accumulate(e)-1).min())
    assert abs(z["total_costs"]-sum(x["entry_fee"]+x["exit_fees"] for x in z["trips"]))<1e-9
