"""Money and causality tests for selective short targets."""
from pathlib import Path
import numpy as np,pandas as pd,yaml,pytest
from src.contracts import MarketView,check_targets
from src.models.book._bear_selective import BearSelective,targets,allocate
CFG=yaml.safe_load(Path("config.yaml").read_text())["models"]
P=CFG["book_bear_guard"]
def view():
 i=pd.date_range("2025-01-01",periods=900,freq="h",tz="UTC")
 n=np.arange(len(i));b=np.exp(-n*.0005+np.sin(n/3)*.001)
 x=pd.DataFrame({s:(100+j*10)*b for j,s in enumerate(P["coins"])},index=i)
 return MarketView(i[-1],x,x*0,tuple(P["coins"]),P,pd.Series(dtype=float))
def test_cash_start_cannot_skip_entry():
 idx=P["coins"];sig=pd.Series(.005,index=idx);strength=pd.Series(1.,index=idx)
 no=pd.Series(False,index=idx);yes=~no
 assert allocate(strength,sig,pd.Series(dtype=float),yes,no,P).empty
 kept=allocate(strength,sig,pd.Series({idx[0]:-.06}),yes,no,P)
 assert kept.to_dict()=={idx[0]:-.06}
 assert allocate(strength,sig,pd.Series({idx[0]:-.06}),no,yes,P).empty
def test_risk_and_gross_under_unequal_volatility():
 idx=P["coins"];sig=pd.Series([.001,.01,.003,.04],index=idx);strength=pd.Series(1.,index=idx);yes=strength>0
 w=allocate(strength,sig,pd.Series(dtype=float),yes,yes,P)
 assert (w<0).all() and w.abs().sum()<=P["gross_cap"]+1e-12 and w.abs().max()<=P["coin_cap"]+1e-12
 assert (w.abs()*sig*np.sqrt(P["hours_per_day"])).sum()<=P["target_daily_vol"]+1e-12
@pytest.mark.parametrize("family",["trend_control","guard","pullback","breakdown"])
def test_future_prices_do_not_change_targets(family):
 v=view();before=targets(v,family)
 future=v.close.iloc[-4:].copy();future.index+=pd.Timedelta(hours=4);future*=20
 vv=MarketView(v.t,pd.concat([v.close,future]),v.quote_volume,v.universe,v.params,v.prev_targets)
 pd.testing.assert_series_equal(before,targets(vv,family))
 check_targets(before,v,BearSelective("book_bear_"+family,family,1,.01).spec)
def test_missing_market_gate_coin_means_cash():
 v=view();u=tuple(s for s in v.universe if s!="BTCUSDT")
 assert targets(MarketView(v.t,v.close,v.quote_volume,u,P,v.prev_targets),"guard").empty
def test_bad_or_missing_closed_bar_means_cash():
 v=view();v.close.iloc[-10,0]=np.nan
 assert targets(v,"guard").empty
 v=view();v.close.drop(v.close.index[-10],inplace=True)
 assert targets(v,"guard").empty
def test_uniform_uptrend_never_shorts():
 v=view();v.close.iloc[:]=np.exp(np.arange(len(v.close))[:,None]*.001)*np.ones((len(v.close),len(v.close.columns)))*100
 for f in ["trend_control","guard","pullback","breakdown"]:assert targets(v,f).empty
def test_no_trade_signal_does_not_add_to_existing_short():
 idx=P["coins"];sig=pd.Series(.005,index=idx);one=pd.Series(1.,index=idx);yes=one>0;no=~yes
 old=pd.Series({idx[0]:-.03})
 w=allocate(one,sig,old,yes,no,P)
 assert w.iloc[0]==-.03 and len(w)==1

def test_guard_is_active_in_persistent_decline_and_targets_are_pure(monkeypatch):
 import builtins
 v=view()
 def denied(*args,**kwargs):raise AssertionError("I/O in strategy")
 monkeypatch.setattr(builtins,"open",denied)
 w=targets(v,"guard")
 assert not w.empty and (w<0).all()
 pd.testing.assert_series_equal(w,targets(v,"guard"))
def test_registration_uses_declared_cadence_and_band():
 from src.models import get
 for name,p in CFG.items():
  if not name.startswith("book_bear_"):continue
  m=get(name)
  assert m.spec.rebalance_hours==p["rebalance_hours"] and m.spec.band==p["band"]
