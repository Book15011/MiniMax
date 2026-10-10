from dataclasses import replace
import numpy as np
import pandas as pd
from src.contracts import MarketView
from src.models.book._recovery import adjusted, vol_factor, confirm_cash_shorts

def view():
    rng=np.random.default_rng(17)
    ix=pd.date_range("2025-01-01",periods=721,freq="h",tz="UTC")
    rr=rng.normal(0,.001,(720,2))
    rr[-168:]*=4
    px=pd.DataFrame(np.vstack([np.ones(2),np.exp(np.cumsum(rr,axis=0))]),index=ix,columns=["BTCUSDT","ETHUSDT"])
    return MarketView(ix[-1],px,pd.DataFrame(1.,index=ix,columns=px.columns),tuple(px.columns))
P={"fast_days":7,"slow_days":30,"min_complete":.9,"short_confirm_hours":24}
def test_risk_scaling_uses_portfolio_covariance_and_never_increases():
    v=view(); w=pd.Series([.6,-.3],index=v.close.columns)
    r=v.close.pct_change(fill_method=None).iloc[-720:].to_numpy()@w.to_numpy()
    expected=min(1,np.std(r,ddof=1)/np.std(r[-168:],ddof=1))
    assert np.isclose(vol_factor(v,w,P),expected)
    z=adjusted(v,w,P,vol=True,short=False,down_mode=False)
    assert z.abs().sum()<=w.abs().sum()
    assert (np.sign(z)==np.sign(w)).all()
def test_future_prices_do_not_affect_the_factor_or_short_filter():
    v=view(); w=pd.Series([.6,-.3],index=v.close.columns)
    fut=pd.DataFrame(1e6,index=pd.date_range(v.t+pd.Timedelta(hours=1),periods=24,freq="h"),columns=v.close.columns)
    x=replace(v,close=pd.concat([v.close,fut]))
    pd.testing.assert_series_equal(adjusted(v,w,P,vol=True,short=True,down_mode=False),adjusted(x,w,P,vol=True,short=True,down_mode=False))
def test_positive_rebound_removes_only_cash_short_and_missing_is_not_short_signal():
    v=view(); c=v.close.copy(); c.iloc[-1]=c.iloc[-25]*1.01
    v=replace(v,close=c); w=pd.Series([.6,-.3],index=c.columns)
    z=confirm_cash_shorts(v,w,P,down_mode=False)
    assert z.to_dict()=={"BTCUSDT":.6}
    pd.testing.assert_series_equal(confirm_cash_shorts(v,w,P,down_mode=True),w)
    c.iloc[-25,1]=np.nan
    assert "ETHUSDT" not in confirm_cash_shorts(replace(v,close=c),w,P,down_mode=False)
def test_equality_control_and_zero_volatility_delegate_to_parent():
    v=view(); w=pd.Series([.6,-.3],index=v.close.columns)
    pd.testing.assert_series_equal(adjusted(v,w,P,vol=False,short=False,down_mode=False),w)
    flat=replace(v,close=v.close*0+1)
    assert vol_factor(flat,w,P)==1
def test_incomplete_covariance_does_not_invent_risk_information():
    v=view(); c=v.close.copy(); c.iloc[-150:,1]=np.nan
    assert vol_factor(replace(v,close=c),pd.Series([.5,.5],index=c.columns),P)==1

def test_quarter_bound_purges_cross_boundary_outcomes_and_detects_zero_edge():
    from research.book.recovery_study.run import ci_quarters
    t=pd.date_range("2022-01-01",periods=600,freq="D",tz="UTC")
    q=ci_quarters(pd.DataFrame({"start":t,"delta":0.}))
    assert q["lower"]==q["upper"]==0.
    assert q["n_purged_windows"]<len(t)
    q=ci_quarters(pd.DataFrame({"start":t,"delta":.01}))
    assert np.isclose(q["lower"],.01)

def test_registered_models_equal_parent_when_controls_are_disabled():
    from src.models.book._recovery import Recovery
    from src.models.book.book_e20combo_brk_cash import MODEL as BASE
    from src.config import load_config
    from backtest.data import load_market,universe_at
    from backtest.engine import view_frames
    cfg=load_config();mk=load_market(cfg)
    for t in [pd.Timestamp("2024-02-01 16:00",tz="UTC"),pd.Timestamp("2025-07-01 16:00",tz="UTC")]:
        c,q=view_frames(mk.close,mk.quote_volume,t)
        p=cfg["models"]["book_recovery_vol"]
        v=MarketView(t,c,q,universe_at(mk,t),params=p)
        pd.testing.assert_series_equal(Recovery().targets(v),BASE.targets(replace(v,params=p["parent"])))
