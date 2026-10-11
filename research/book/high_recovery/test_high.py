from dataclasses import replace
import copy
import numpy as np
import pandas as pd
from src.contracts import MarketView
from src.models.book._high_recovery import scores,adjust

P={"lookback_days":[7,14],"vol_days":30,"min_complete":.9,"k":2,"keep_rank":3,"blend_weight":.5,
   "filter_params":{"early_exit":False,"no_chase":False,"volume_long_days":7,"volume_short_hours":24,
     "exit_cooldown_hours":24,"exit_low_hours":24,"exit_volume_ratio":1.5,"chase_return_hours":24,"chase_window_hours":72},
   "channel_days":20,"scan_days":120}
def fixture():
    rng=np.random.default_rng(42);n=1440
    btc=rng.normal(.0002,.001,n)
    a=3*btc+rng.normal(0,.0002,n)
    b=.3*btc+rng.normal(0,.0002,n)
    x=np.column_stack([btc,a,b])
    ix=pd.date_range("2024-01-01",periods=n+1,freq="h",tz="UTC")
    c=pd.DataFrame(np.vstack([np.ones(3),np.exp(np.cumsum(x,axis=0))]),index=ix,columns=["BTCUSDT","AAAUSDT","BBBUSDT"])
    return MarketView(ix[-1],c,c*0+1,tuple(c.columns))

def test_faded_rally_loses_to_coin_holding_its_high_and_formula_is_exact():
    v=fixture();c=v.close.copy()
    for coin,scale in [("AAAUSDT",1),("BBBUSDT",2)]:
        c.loc[c.index[-337:],coin]=scale*np.exp(np.linspace(0,.1,337))
    c.iloc[-80,c.columns.get_loc("AAAUSDT")]=1.5
    c.iloc[-1,c.columns.get_loc("AAAUSDT")]=1.2
    a,raw=scores(replace(v,close=c),P)
    expected=np.mean([np.log(c.AAAUSDT.iloc[-1]/c.AAAUSDT.iloc[-(d*24+1):].max()) for d in [7,14]])
    assert abs(a.AAAUSDT-expected)<1e-14
    assert a.BBBUSDT==0 and a.AAAUSDT<0
    assert a.BBBUSDT>a.AAAUSDT

def test_missing_hour_or_bad_price_excludes_coin_and_future_is_invisible():
    v=fixture();a,raw=scores(v,P)
    c=v.close.copy();c.iloc[-24,1]=np.nan
    b,_=scores(replace(v,close=c),P);assert "AAAUSDT" not in b
    c=v.close.copy();c.iloc[-24,1]=0
    b,_=scores(replace(v,close=c),P);assert "AAAUSDT" not in b
    b,_=scores(replace(v,close=v.close.drop(v.close.index[-12])),P);assert b.empty
    future=pd.DataFrame(1e9,index=pd.date_range(v.t+pd.Timedelta(hours=1),periods=24,freq="h"),columns=c.columns)
    b,_=scores(replace(v,close=pd.concat([v.close,future])),P)
    pd.testing.assert_series_equal(a,b)

def test_no_eligible_features_and_incomplete_risk_are_parent_fallbacks():
    v=fixture();w=pd.Series({"AAAUSDT":.4,"BTCUSDT":-.2})
    c=v.close*float("nan")
    pd.testing.assert_series_equal(adjust(replace(v,close=c),w,P,blend=False,up=True),w)
    c=v.close.copy();c.iloc[-720:-337,:]=np.nan
    pd.testing.assert_series_equal(adjust(replace(v,close=c),w,P,blend=True,up=True),w)

def test_down_mode_and_no_long_budget_are_exact_parent():
    v=fixture();w=pd.Series({"AAAUSDT":.4,"BTCUSDT":-.2})
    pd.testing.assert_series_equal(adjust(v,w,P,blend=True,up=False),w)
    w=w[w<0]
    pd.testing.assert_series_equal(adjust(v,w,P,blend=False,up=True),w)

def test_actual_reselection_and_signed_risk_gross_shorts_universe_constraints():
    v=fixture();w=pd.Series({"AAAUSDT":.4,"BTCUSDT":-.2})
    z=adjust(v,w,P,blend=False,up=True)
    assert "BBBUSDT" in z and z.BBBUSDT>0
    assert z.BTCUSDT==-.2 and "BTCUSDT" not in z[z>0].index
    assert z.abs().sum()<=w.abs().sum()+1e-12
    ix=w.index.union(z.index);cov=v.close[ix].pct_change(fill_method=None).iloc[-720:].cov().to_numpy()
    a=w.reindex(ix).fillna(0).to_numpy();b=z.reindex(ix).fillna(0).to_numpy()
    assert b@cov@b<=a@cov@a+1e-12
    assert np.isfinite(z).all() and set(z.index)<=set(v.universe)

def test_coin_order_invariance_and_no_input_mutation():
    v=fixture();w=pd.Series({"AAAUSDT":.4,"BTCUSDT":-.2});old=w.copy();c=v.close.copy();params=copy.deepcopy(P)
    a=adjust(v,w,P,blend=True,up=True)
    b=adjust(replace(v,close=v.close[v.close.columns[::-1]],universe=v.universe[::-1]),w.iloc[::-1],P,blend=True,up=True)
    pd.testing.assert_series_equal(a.sort_index(),b.sort_index())
    pd.testing.assert_series_equal(w,old);pd.testing.assert_frame_equal(v.close,c);assert P==params

def test_single_complete_coin_and_ties_are_deterministic():
    v=fixture();c=v.close.copy();c["AAAUSDT"]=np.nan;c["BTCUSDT"]=np.nan
    a,_=scores(replace(v,close=c),P)
    assert a.index.tolist()==["BBBUSDT"]
    c=v.close.copy();c.loc[:,:]=1.
    a,_=scores(replace(v,close=c),P)
    assert (a==0).all() and a.index.tolist()==sorted(v.universe)
