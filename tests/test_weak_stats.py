"""Weak-market protocol math must not reward outcome cherry-picking."""
import numpy as np
import pandas as pd
import pytest
from backtest.scoring.weak_stats import select_cases, clustered_draws, simultaneous_bounds, tail_mean
CFG={"features":{"FAST":["btc_ret24","btc_ret48"],"TREND":["btc_ma200"],"BREADTH":["breadth48"]},
     "weak":{"ret48_min":-.1,"ret48_max":0.,"breadth_max":.4,"ret24_max":.01},
     "positive":{"ret48_min":0.,"ret48_max":.1,"breadth_min":.6},
     "lookalikes":{"k":3,"min_separation_days":14,"span_days":90,"max_per_span":3},
     "embargo_hours":24}
def panel():
    t=pd.date_range("2020-01-01 12:00",periods=300,freq="D",tz="UTC")
    f=pd.DataFrame({"btc_ret24":-.005,"btc_ret48":-.03,"btc_ma200":.1,"breadth48":.2},index=t)
    return f,f.iloc[0]
def test_selection_is_causal_and_ignores_forward_outcomes():
    f,q=panel()
    f["future_return"]=np.arange(len(f))*100.
    a=select_cases(f,q,pd.Timestamp("2020-12-01",tz="UTC"),240,CFG)
    f.future_return=-f.future_return
    b=select_cases(f,q,pd.Timestamp("2020-12-01",tz="UTC"),240,CFG)
    pd.testing.assert_frame_equal(a,b)
    assert len(a)==3 and (np.diff(a.index.asi8)>=pd.Timedelta(days=14).value).all()
    assert (a.index+pd.Timedelta(hours=264)<=pd.Timestamp("2020-12-01",tz="UTC")).all()
def test_no_threshold_relaxation_or_missing_query_imputation():
    f,q=panel();f.btc_ret48=.05
    with pytest.raises(ValueError,match="insufficient"):select_cases(f,q,pd.Timestamp("2021-01-01",tz="UTC"),240,CFG)
    f,q=panel();q=q.copy();q["breadth48"]=np.nan
    with pytest.raises(ValueError,match="query"):select_cases(f,q,pd.Timestamp("2021-01-01",tz="UTC"),240,CFG)
def test_window_weight_clusters_and_reproducibility():
    t=pd.DatetimeIndex(["2020-01-01","2020-01-20","2020-04-01","2020-07-01"],tz="UTC")
    d,n=clustered_draws(t,1000,123)
    assert n==3 and d.shape==(1000,4) and np.allclose(d.sum(axis=1),1)
    np.testing.assert_array_equal(d,clustered_draws(t,1000,123)[0])
    assert np.allclose(d[:,0],d[:,1])
def test_simultaneous_bounds_include_constant_cash_and_exact_pairing():
    t=pd.date_range("2020-01-01",periods=25,freq="30D",tz="UTC")
    rng=np.random.default_rng(1);x=rng.normal(.02,.03,(4,len(t),3));x[0]=0;x[1]=x[2]
    d,n=clustered_draws(t,3000,42)
    r=simultaneous_bounds(x,1,d,.90)
    assert np.all(r["family_lower"]<=r["mean"]+1e-12)
    np.testing.assert_allclose(r["delta"][2],0,atol=1e-15)
    np.testing.assert_allclose(r["delta_family_lower"][2],0,atol=1e-15)
    np.testing.assert_allclose(r["cash_family_lower"][0],0,atol=1e-15)
    assert r["family_quantile"]>=0
def test_expected_shortfall_uses_fractional_tail_mass():
    assert tail_mean(np.array([-10.,0.,10.]),.5)==pytest.approx(-20/3)
    assert tail_mean(np.ones(10),.1)==1
