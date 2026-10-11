from dataclasses import replace
import copy
import numpy as np
import pandas as pd
from src.contracts import MarketView
from src.models.book._quality_recovery import scores,adjust
from research.book.high_recovery.test_high import P as OLD_P

P={**copy.deepcopy(OLD_P),"momentum_pool":12,"formation_min_return":0.0}

def fixture():
    days=60;ix=pd.date_range("2024-01-01",periods=days*24+1,freq="h",tz="UTC")
    daily=np.column_stack([np.full(days,.001),np.where(np.arange(days)%2==0,.03,-.012),np.full(days,.003)])
    r=np.repeat(daily/24,24,axis=0)
    # Small deterministic intraday movement keeps hourly variances finite.
    noise=np.sin(np.arange(len(r)))[:,None]*np.array([.00002,.0002,.00001])[None,:]
    c=pd.DataFrame(np.vstack([np.ones(3),np.exp(np.cumsum(r+noise,axis=0))]),index=ix,columns=["BTCUSDT","AAAUSDT","BBBUSDT"])
    return MarketView(ix[-1],c,c*0+1,tuple(c.columns))

def test_quality_matches_daily_sign_formula_and_prefers_steady_positive_paths():
    v=fixture();q,raw=scores(v,P)
    assert q.BBBUSDT>q.AAAUSDT and "AAAUSDT" in raw
    expected=np.mean([np.sign(v.close.AAAUSDT.iloc[-(d*24+1)::24].pct_change(fill_method=None).iloc[1:]).mean() for d in [7,14]])
    assert abs(q.AAAUSDT-expected)<1e-14 and q.BBBUSDT==1.

def test_positive_condition_and_zero_days_denominator():
    v=fixture();c=v.close.copy()
    c["AAAUSDT"]=np.exp(-np.arange(len(c))*.0001);c["BTCUSDT"]=1.
    # One positive day then13 zero days: quality is not1.
    c["BBBUSDT"]=1.;c.loc[c.index[-8*24]:,"BBBUSDT"]=1.1
    q,raw=scores(replace(v,close=c),P)
    assert q.empty # last7-day formation is flat, despite14-day positive
    c.loc[c.index[-24]:,"BBBUSDT"]=1.2
    q,raw=scores(replace(v,close=c),P)
    assert q.index.tolist()==["BBBUSDT"]
    assert q.BBBUSDT==np.mean([1/7,2/14])

def test_missing_hour_bad_price_future_and_outside_universe():
    v=fixture();a,_=scores(v,P)
    for bad in [np.nan,0.,np.inf,-1.]:
        c=v.close.copy();c.iloc[-24,1]=bad
        b,_=scores(replace(v,close=c),P);assert "AAAUSDT" not in b
    b,_=scores(replace(v,close=v.close.drop(v.close.index[-12])),P);assert b.empty
    future=pd.DataFrame(1e9,index=pd.date_range(v.t+pd.Timedelta(hours=1),periods=24,freq="h"),columns=v.close.columns)
    b,_=scores(replace(v,close=pd.concat([v.close,future])),P);pd.testing.assert_series_equal(a,b)
    b,_=scores(replace(v,universe=("BBBUSDT",)),P);assert b.index.tolist()==["BBBUSDT"]

def test_no_eligible_features_and_incomplete_risk_exact_parent():
    v=fixture();w=pd.Series({"AAAUSDT":.4,"BTCUSDT":-.2})
    pd.testing.assert_series_equal(adjust(replace(v,close=v.close*float("nan")),w,P,blend=False,up=True),w)
    c=v.close.copy();c.iloc[-720:-337,:]=np.nan
    pd.testing.assert_series_equal(adjust(replace(v,close=c),w,P,blend=True,up=True),w)

def test_down_mode_and_no_long_exact_parent():
    v=fixture();w=pd.Series({"AAAUSDT":.4,"BTCUSDT":-.2})
    pd.testing.assert_series_equal(adjust(v,w,P,blend=True,up=False),w)
    w=w[w<0];pd.testing.assert_series_equal(adjust(v,w,P,blend=False,up=True),w)

def test_reselection_is_real_and_signed_risk_gross_shorts_are_preserved():
    v=fixture();w=pd.Series({"AAAUSDT":.4,"BTCUSDT":-.2})
    p={**P,"k":1}
    z=adjust(v,w,p,blend=False,up=True)
    assert "BBBUSDT" in z and z.BBBUSDT>0 and "AAAUSDT" not in z
    assert z.BTCUSDT==-.2 and z.abs().sum()<=w.abs().sum()+1e-12
    ix=w.index.union(z.index);cov=v.close[ix].pct_change(fill_method=None).iloc[-720:].cov().to_numpy()
    a=w.reindex(ix).fillna(0).to_numpy();b=z.reindex(ix).fillna(0).to_numpy()
    assert b@cov@b<=a@cov@a+1e-12 and np.isfinite(z).all()
    assert set(z.index)<=set(v.universe)

def test_pool_conditions_on_parent_momentum_before_quality():
    v=fixture();w=pd.Series({"AAAUSDT":.4,"BTCUSDT":-.2})
    # With one candidate in the momentum pool, it must be the top raw-score coin.
    q,raw=scores(v,P)
    eligible=raw.drop("BTCUSDT").sort_index().sort_values(ascending=False,kind="stable")
    z=adjust(v,w,{**P,"momentum_pool":1,"k":1},blend=False,up=True)
    assert set(z[z>0].index)=={eligible.index[0]}

def test_order_invariance_no_mutation_blend_determinism_and_wrapper(monkeypatch):
    v=fixture();w=pd.Series({"AAAUSDT":.4,"BTCUSDT":-.2});old=w.copy();c=v.close.copy();params=copy.deepcopy(P)
    a=adjust(v,w,P,blend=True,up=True)
    b=adjust(replace(v,close=v.close[v.close.columns[::-1]],universe=v.universe[::-1]),w.iloc[::-1],P,blend=True,up=True)
    pd.testing.assert_series_equal(a.sort_index(),b.sort_index())
    pd.testing.assert_series_equal(w,old);pd.testing.assert_frame_equal(v.close,c);assert P==params
    from src.models.book import _quality_recovery as impl
    monkeypatch.setattr(impl.BASE,"targets",lambda view:w.copy())
    monkeypatch.setattr(impl.Combo,"state",lambda view,p:"up")
    from src.models import get
    for name,blend in [("book_recovery_quality",False),("book_recovery_quality_blend",True)]:
        z=get(name).targets(replace(v,params={**P,"parent":{"base":{"vt":{}}}}))
        expected=adjust(v,w,P,blend=blend,up=True)
        pd.testing.assert_series_equal(z,expected)

def test_stable_ties():
    v=fixture();c=v.close.copy()
    c.loc[:,:]=np.exp(np.arange(len(c))[:,None]*.0001)
    q,raw=scores(replace(v,close=c),P)
    assert (q==1).all() and q.index.tolist()==sorted(v.universe)
