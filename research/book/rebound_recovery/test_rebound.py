from dataclasses import replace
import numpy as np
import pandas as pd
from src.contracts import MarketView
from src.models.book._rebound_recovery import adjust,rebounding
P={"confirm_hours":24,"rebound_hours":48,"breadth_majority":.5,"volume_fill_hours":12,
   "vol_days":30,"min_complete":.9,"btc_symbol":"BTCUSDT",
   "breadth":{"liquidity_hours":168,"breadth_top_n":3,"breadth_min_coins":2,"breadth_hours":48}}
def fixture():
    rng=np.random.default_rng(23);n=1440
    x=rng.normal(.0001,.002,(n,3))
    ix=pd.date_range("2024-01-01",periods=n+1,freq="h",tz="UTC")
    c=pd.DataFrame(np.vstack([np.ones(3),np.exp(np.cumsum(x,axis=0))]),index=ix,columns=["BTCUSDT","AAAUSDT","BBBUSDT"])
    c.iloc[-48:]=c.iloc[-49].to_numpy()*np.exp(np.linspace(.001,.05,48))[:,None]
    return MarketView(ix[-1],c,c*0+1,tuple(c.columns))
def test_positive_own_return_covers_main_sleeve_short_and_no_short_is_added():
    v=fixture();w=pd.Series({"AAAUSDT":-.4,"BBBUSDT":.3})
    z=adjust(v,w,P,market=False)
    assert "AAAUSDT" not in z and not (z<0).any() and z.BBBUSDT<=.3
def test_negative_or_missing_short_endpoint_is_retained():
    v=fixture();w=pd.Series({"AAAUSDT":-.4,"BBBUSDT":.3})
    c=v.close.copy();c.loc[v.t,"AAAUSDT"]=c.loc[v.t-pd.Timedelta(hours=24),"AAAUSDT"]*.99
    pd.testing.assert_series_equal(adjust(replace(v,close=c),w,P,market=False),w)
    c.loc[v.t,"AAAUSDT"]=np.nan
    pd.testing.assert_series_equal(adjust(replace(v,close=c),w,P,market=False),w)
def test_market_guard_requires_both_btc_and_majority():
    v=fixture();assert rebounding(v,P)
    w=pd.Series({"AAAUSDT":-.3,"BBBUSDT":-.2})
    assert adjust(v,w,P,market=True).empty
    c=v.close.copy();c.loc[v.t,"BTCUSDT"]=c.loc[v.t-pd.Timedelta(hours=48),"BTCUSDT"]*.99
    assert not rebounding(replace(v,close=c),P)
    c=v.close.copy()
    for coin in ["AAAUSDT","BBBUSDT"]:c.loc[v.t,coin]=c.loc[v.t-pd.Timedelta(hours=48),coin]*.99
    assert not rebounding(replace(v,close=c),P)
def test_missing_selected_breadth_price_is_not_dropped():
    v=fixture();c=v.close.copy();c.loc[v.t,"AAAUSDT"]=np.nan
    assert not rebounding(replace(v,close=c),P)
    q=v.quote_volume.copy();q.iloc[-24:,1:]=np.nan
    assert not rebounding(replace(v,quote_volume=q),P)
def test_covering_hedge_requires_downward_risk_matching():
    v=fixture();c=v.close.copy();c["BBBUSDT"]=c["AAAUSDT"]*2
    v=replace(v,close=c);w=pd.Series({"AAAUSDT":-.4,"BBBUSDT":.4})
    z=adjust(v,w,P,market=False)
    assert z.abs().sum()<1e-6
def test_incomplete_covariance_means_exact_parent_fallback():
    v=fixture();c=v.close.copy();c.iloc[-720:-337,1:]=np.nan
    w=pd.Series({"AAAUSDT":-.4,"BBBUSDT":.3})
    pd.testing.assert_series_equal(adjust(replace(v,close=c),w,P,market=False),w)
def test_future_invisible_order_invariant_and_inputs_not_mutated():
    v=fixture();w=pd.Series({"AAAUSDT":-.4,"BBBUSDT":.3});old=w.copy();c=v.close.copy()
    a=adjust(v,w,P,market=False)
    f=pd.DataFrame(1e10,index=pd.date_range(v.t+pd.Timedelta(hours=1),periods=48,freq="h"),columns=c.columns)
    b=adjust(replace(v,close=pd.concat([c,f]),quote_volume=pd.concat([v.quote_volume,f])),w,P,market=False)
    pd.testing.assert_series_equal(a,b)
    b=adjust(replace(v,close=c[c.columns[::-1]],universe=v.universe[::-1]),w.iloc[::-1],P,market=False)
    pd.testing.assert_series_equal(a.sort_index(),b.sort_index())
    pd.testing.assert_series_equal(w,old);pd.testing.assert_frame_equal(v.close,c)
