from dataclasses import replace
import numpy as np,pandas as pd
from src.contracts import MarketView
from src.models.book._recovery_selection import adjust_selection
def fixture():
    rng=np.random.default_rng(19); ix=pd.date_range("2024-01-01",periods=721,freq="h",tz="UTC")
    x=rng.normal(.0002,.001,(720,3))*[1,2,4]
    c=pd.DataFrame(np.vstack([np.ones(3),np.exp(np.cumsum(x,axis=0))]),index=ix,columns=["BTCUSDT","ETHUSDT","SOLUSDT"])
    v=MarketView(ix[-1],c,c*0+1,tuple(c.columns))
    return v,pd.Series([.3,.3,-.2],index=c.columns)
P={"lookback_days":[7,14],"vol_days":30,"coin_cap":.25,"min_complete":.9}
def test_inverse_vol_keeps_shorts_bounds_gross_and_not_raise_estimated_long_risk():
    v,w=fixture(); z=adjust_selection(v,w,P,absolute=False,inverse=True,up=True)
    assert z.SOLUSDT==w.SOLUSDT
    assert z[z>0].max()<=.25+1e-12
    assert z.abs().sum()<=w.abs().sum()+1e-12
    cov=v.close.pct_change(fill_method=None).iloc[-720:].cov()
    a=w.clip(lower=0);b=z.reindex(a.index).fillna(0).clip(lower=0)
    assert b.to_numpy()@cov.to_numpy()@b.to_numpy()<=a.to_numpy()@cov.to_numpy()@a.to_numpy()+1e-12
def test_no_positive_momentum_means_cash_not_new_shorts():
    v,w=fixture(); c=v.close.copy();c.iloc[-1]=c.iloc[-337]*.5
    z=adjust_selection(replace(v,close=c),w,P,absolute=True,inverse=False,up=True)
    assert z.to_dict()=={"SOLUSDT":-.2}
def test_disabled_control_and_down_mode_are_exact_parent():
    v,w=fixture()
    for up,absolute,inverse in [(False,True,True),(True,False,False)]:
        pd.testing.assert_series_equal(adjust_selection(v,w,P,absolute=absolute,inverse=inverse,up=up),w)
def test_future_prices_and_column_order_do_not_change_decisions():
    v,w=fixture();future=pd.DataFrame(1e6,index=pd.date_range(v.t+pd.Timedelta(hours=1),periods=24,freq="h"),columns=v.close.columns)
    a=adjust_selection(v,w,P,absolute=True,inverse=True,up=True)
    b=adjust_selection(replace(v,close=pd.concat([v.close,future])),w,P,absolute=True,inverse=True,up=True)
    pd.testing.assert_series_equal(a.sort_index(),b.sort_index())
    b=adjust_selection(replace(v,close=v.close[v.close.columns[::-1]]),w.iloc[::-1],P,absolute=True,inverse=True,up=True)
    pd.testing.assert_series_equal(a.sort_index(),b.sort_index())
def test_no_data_does_not_increase_a_position_or_create_nan():
    v,w=fixture(); c=v.close.copy();c.iloc[-500:,0]=np.nan
    z=adjust_selection(replace(v,close=c),w,P,absolute=True,inverse=True,up=True)
    assert np.isfinite(z).all()
    assert "BTCUSDT" not in z
