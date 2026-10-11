from dataclasses import replace
import numpy as np
import pandas as pd
from src.contracts import MarketView
from src.models.book._residual_recovery import scores,adjust

P={"beta_days":30,"lookback_days":[7,14],"vol_days":30,"min_complete":.9,"k":2,"keep_rank":3,"blend_weight":.5,
   "filter_params":{"early_exit":False,"no_chase":False,"volume_long_days":7,"volume_short_hours":24,
     "exit_cooldown_hours":24,"exit_low_hours":24,"exit_volume_ratio":1.5,"chase_return_hours":24,"chase_window_hours":72},
   "channel_days":20,"scan_days":120}
def fixture():
    rng=np.random.default_rng(42);n=1056
    btc=rng.normal(.0006,.001,n)
    a=3*btc+rng.normal(0,.0002,n)
    b=.3*btc+rng.normal(0,.0002,n)
    a[-336:]-=.0001;b[-336:]+=.0003
    x=np.column_stack([btc,a,b])
    ix=pd.date_range("2024-01-01",periods=n+1,freq="h",tz="UTC")
    c=pd.DataFrame(np.vstack([np.ones(3),np.exp(np.cumsum(x,axis=0))]),index=ix,columns=["BTCUSDT","AAAUSDT","BBBUSDT"])
    return MarketView(ix[-1],c,c*0+1,tuple(c.columns))

def test_market_beta_does_not_masquerade_as_coin_strength():
    v=fixture();beta,resid,raw=scores(v,P)
    assert 2.9<beta.AAAUSDT<3.1 and .2<beta.BBBUSDT<.4
    assert resid.BBBUSDT>resid.AAAUSDT
    assert abs(resid.BTCUSDT)<1e-8

def test_training_ends_before_formation_and_future_rows_are_invisible():
    v=fixture();beta,a,raw=scores(v,P)
    c=v.close.copy();c.iloc[-336:]*=np.linspace(1,2,336)[:,None]
    beta2,_,_=scores(replace(v,close=c),P)
    pd.testing.assert_series_equal(beta,beta2)
    future=pd.DataFrame(1e9,index=pd.date_range(v.t+pd.Timedelta(hours=1),periods=24,freq="h"),columns=c.columns)
    _,b,_=scores(replace(v,close=pd.concat([v.close,future])),P)
    pd.testing.assert_series_equal(a,b)

def test_missing_btc_or_incomplete_training_delegates_parent():
    v=fixture();w=pd.Series({"AAAUSDT":.4,"BBBUSDT":-.2})
    c=v.close.copy();c["BTCUSDT"]=np.nan
    pd.testing.assert_series_equal(adjust(replace(v,close=c),w,P,blend=False,up=True),w)
    c=v.close.copy();c.iloc[:600,0]=np.nan
    pd.testing.assert_series_equal(adjust(replace(v,close=c),w,P,blend=True,up=True),w)

def test_down_mode_and_no_long_budget_are_exact_parent():
    v=fixture();w=pd.Series({"AAAUSDT":.4,"BBBUSDT":-.2})
    pd.testing.assert_series_equal(adjust(v,w,P,blend=True,up=False),w)
    w=w[w<0]
    pd.testing.assert_series_equal(adjust(v,w,P,blend=False,up=True),w)

def test_signed_risk_gross_shorts_and_universe_cannot_expand():
    v=fixture();w=pd.Series({"AAAUSDT":.4,"BTCUSDT":-.2})
    z=adjust(v,w,P,blend=False,up=True)
    assert z.BTCUSDT==-.2 and not (z[z>0].index=="BTCUSDT").any()
    assert z.abs().sum()<=w.abs().sum()+1e-12
    ix=w.index.union(z.index);cov=v.close[ix].pct_change(fill_method=None).iloc[-720:].cov().to_numpy()
    a=w.reindex(ix).fillna(0).to_numpy();b=z.reindex(ix).fillna(0).to_numpy()
    assert b@cov@b<=a@cov@a+1e-12
    assert np.isfinite(z).all() and set(z.index)<=set(v.universe)

def test_coin_order_does_not_change_selection_and_input_is_not_mutated():
    v=fixture();w=pd.Series({"AAAUSDT":.4,"BTCUSDT":-.2});old=w.copy();c=v.close.copy()
    a=adjust(v,w,P,blend=True,up=True)
    b=adjust(replace(v,close=v.close[v.close.columns[::-1]],universe=v.universe[::-1]),w.iloc[::-1],P,blend=True,up=True)
    pd.testing.assert_series_equal(a.sort_index(),b.sort_index())
    pd.testing.assert_series_equal(w,old);pd.testing.assert_frame_equal(v.close,c)
