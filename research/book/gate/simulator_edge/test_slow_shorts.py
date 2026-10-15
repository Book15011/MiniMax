from dataclasses import replace
import numpy as np,pandas as pd
from src.contracts import MarketView,check_targets
from research.book.gate.simulator_edge.slow_shorts import ShortMomentum
def fixture():
    ix=pd.date_range("2024-01-01",periods=420,freq="h",tz="UTC")
    c=pd.DataFrame(np.exp(np.arange(len(ix))[:,None]*np.array([-.001,-.002,.001])[None,:]),index=ix,columns=["AAA","BBB","CCC"])
    return MarketView(ix[-1],c,c*0+1,tuple(c.columns))
def test_negative_selection_and_gross_cap_with_no_mutation():
    v=fixture();before=v.close.copy()
    for L in [24,72,168]:
        m=ShortMomentum(L);w=check_targets(m.targets(v),v,m.spec)
        assert w.to_dict()=={"BBB":-.5} and w.abs().sum()<=.5
    pd.testing.assert_frame_equal(v.close,before)
def test_squeeze_guard_uses_only_current_closed_prices():
    v=fixture();c=v.close.copy();anchor=v.t.floor("4h")
    c.loc[v.t,"BBB"]=c.loc[anchor,"BBB"]*1.09
    assert ShortMomentum(72).targets(replace(v,close=c)).empty
def test_positive_momentum_returns_cash_and_future_is_invisible():
    v=fixture();m=ShortMomentum(72);w=m.targets(v)
    c=pd.concat([v.close,pd.DataFrame(1e9,index=pd.date_range(v.t+pd.Timedelta(hours=1),periods=12,freq="h"),columns=v.close.columns)])
    pd.testing.assert_series_equal(w,m.targets(replace(v,close=c)))
    c=np.exp(-np.log(v.close))
    assert m.targets(replace(v,close=c,universe=("AAA","BBB"))).empty
def test_coin_order_does_not_change_selection():
    v=fixture();m=ShortMomentum(72)
    pd.testing.assert_series_equal(m.targets(v),m.targets(replace(v,close=v.close[v.close.columns[::-1]],universe=v.universe[::-1])))
