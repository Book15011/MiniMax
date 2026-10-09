"""Behavioral tests for research-frozen directional candidates."""
import numpy as np
import pandas as pd
import pytest
from src.config import load_config
from src.contracts import MarketView, check_targets
from src.models import get

NAMES = ["book_short_trend", "book_short_rebound", "book_short_breakdown"]
COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

def view(direction=-1, hour=1, prev=None, rebound=False, volume=False):
    idx = pd.date_range(end=pd.Timestamp("2026-01-20", tz="UTC") + pd.Timedelta(hours=hour),
                        periods=410, freq="h")
    x = np.arange(len(idx))
    price = 100 * np.exp(direction * .001*x + .0001*np.sin(x))
    if rebound:
        price[-1] = price[-25:-1].max() * 1.01
    close = pd.DataFrame({c:price*(i+1) for i,c in enumerate(COINS)}, index=idx)
    qv = pd.DataFrame(100., index=idx, columns=COINS)
    if volume:
        qv.iloc[-24:] = 200.
    return MarketView(idx[-1], close, qv, tuple(COINS), {}, pd.Series(dtype=float) if prev is None else prev)

def configured(name, **kw):
    v = view(**kw)
    return MarketView(v.t,v.close,v.quote_volume,v.universe,load_config()["models"][name],v.prev_targets)

@pytest.mark.parametrize("name",NAMES)
def test_contract_and_causal_no_future(name):
    m=get(name);v=configured(name,volume=True)
    w=check_targets(m.targets(v),v,m.spec)
    assert float(w.abs().sum()) <= 1
    assert float(w.abs().max()) <= .25
    future=v.close.iloc[[-1]].copy()
    future.index += pd.Timedelta(hours=1)
    future *= 1000
    f=MarketView(v.t,pd.concat([v.close,future]),v.quote_volume,v.universe,v.params,v.prev_targets)
    pd.testing.assert_series_equal(w,m.targets(f)[lambda z:z!=0])

@pytest.mark.parametrize("name",NAMES)
def test_missing_current_fails_closed(name):
    m=get(name);v=configured(name,volume=True)
    v.close.iloc[-1]=np.nan
    assert m.targets(v).abs().sum()==0

def test_signed_trend_and_volatility_budget():
    m=get(NAMES[0])
    for d in [-1,1]:
        v=configured(NAMES[0],direction=d)
        w=m.targets(v)
        assert (d*w>0).all()
        sig=np.log(v.close).diff().tail(v.params["vol_hours"]).std()
        assert float((w.abs()*sig*np.sqrt(24)).sum()) <= v.params["target_daily_vol"]+1e-12

@pytest.mark.parametrize("name",NAMES[:2])
def test_no_bootstrap_before_configured_daily_hour(name):
    v=configured(name,hour=2)
    assert get(name).targets(v).empty

def test_daily_holds_until_next_decision():
    prior=pd.Series(-.1,index=COINS)
    v=configured(NAMES[0],hour=7,prev=prior,rebound=True)
    pd.testing.assert_series_equal(get(NAMES[0]).targets(v),prior)

def test_rebound_exits_before_reentry():
    m=get(NAMES[1]);prior=pd.Series(-.1,index=COINS)
    v=configured(NAMES[1],hour=7,prev=prior,rebound=True)
    assert m.targets(v).abs().sum()==0
    v=configured(NAMES[1],hour=8,prev=pd.Series(dtype=float))
    assert m.targets(v).empty
    v=configured(NAMES[1],hour=1,prev=prior,rebound=True)
    assert (m.targets(v)>=0).all()

def test_breakdown_requires_volume_and_weak_breadth():
    m=get(NAMES[2])
    assert m.targets(configured(NAMES[2],volume=False)).abs().sum()==0
    assert (m.targets(configured(NAMES[2],volume=True))<0).all()
    assert m.targets(configured(NAMES[2],direction=1,volume=True)).abs().sum()==0

def test_breakdown_exit_priority_and_existing_hold():
    m=get(NAMES[2]);prior=pd.Series(-.1,index=COINS)
    assert m.targets(configured(NAMES[2],hour=7,prev=prior,rebound=True,volume=True)).abs().sum()==0
    v=configured(NAMES[2],hour=8,prev=prior,rebound=True,volume=True)
    pd.testing.assert_series_equal(m.targets(v),prior)

def test_bad_volatility_excluded_and_universe_respected():
    m=get(NAMES[0]);v=configured(NAMES[0])
    v.close["BTCUSDT"]=100.
    v=MarketView(v.t,v.close,v.quote_volume,tuple(COINS[:-1]),v.params,pd.Series(dtype=float))
    w=m.targets(v)
    assert "BTCUSDT" not in w and "XRPUSDT" not in w
