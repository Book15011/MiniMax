import importlib
from dataclasses import replace
import numpy as np,pandas as pd,pytest
from src.contracts import MarketView,check_targets
from src.config import load_config
T=pd.Timestamp("2026-01-20T16:00Z")
@pytest.fixture
def case(monkeypatch):
 h=importlib.import_module("src.models.book._transition_short")
 model=importlib.import_module("src.models.book.book_transition_short").MODEL
 cols=["BTCUSDT"]+[f"C{i:02}USDT" for i in range(24)]
 ix=pd.date_range(end=T,periods=1500,freq="h")
 steps=np.arange(len(ix))
 close=pd.DataFrame({c:100*np.exp(-.0007*steps+.004*np.sin(steps*(.7+.01*i))) for i,c in enumerate(cols)},index=ix)
 q=pd.DataFrame(100.,index=ix,columns=cols)
 longs=pd.Series({"C00USDT":.30,"C01USDT":.25})
 class Base:
  def targets(self,view):
   assert not (view.prev_targets<0).any()
   return longs.copy()
 monkeypatch.setattr(h,"BASE",Base())
 p=load_config()["models"]["book_transition_short"]
 return h,model,MarketView(T,close,q,tuple(cols),p,pd.Series(dtype=float)),longs

def test_weak_market_reduces_long_risk_and_caps_all_short_risks(case):
 h,m,v,longs=case;w=check_targets(m.targets(v),v,m.spec)
 assert w[w>0].equals(longs*.5)
 assert (w[w<0].index.isin(longs.index)==False).all()
 assert len(w[w<0])<=3 and w[w<0].abs().sum()<=.25+1e-12
 assert w[w<0].abs().max()<=.10+1e-12 and w.abs().sum()<=1
 sigma=v.close[w[w<0].index].pct_change(fill_method=None).iloc[-720:].std()*np.sqrt(24)
 assert (w[w<0].abs()*sigma).sum()<=.01+1e-12

def test_future_rows_do_not_change_targets(case):
 h,m,v,_=case;a=m.targets(v)
 future=pd.date_range(T+pd.Timedelta(hours=1),periods=5,freq="h")
 c=pd.concat([v.close,pd.DataFrame(1e6,index=future,columns=v.close.columns)])
 q=pd.concat([v.quote_volume,pd.DataFrame(1e12,index=future,columns=v.close.columns)])
 pd.testing.assert_series_equal(a,m.targets(replace(v,close=c,quote_volume=q)))

def test_missing_selected_price_disables_regime_without_lowering_threshold(case):
 h,m,v,longs=case;c=v.close.copy();c.loc[T-pd.Timedelta(hours=48),"C05USDT"]=np.nan
 pd.testing.assert_series_equal(m.targets(replace(v,close=c)),longs)

def test_nonweak_btc_keeps_original_long_targets(case):
 h,m,v,longs=case;c=v.close.copy();c["BTCUSDT"]=np.arange(len(c))+100
 pd.testing.assert_series_equal(m.targets(replace(v,close=c,prev_targets=pd.Series({"C00USDT":.2,"C02USDT":-.1}))),longs)

def test_positive_rebound_blocks_new_short_but_small_rebound_retains_existing(case):
 h,m,v,_=case;c=v.close.copy();c.loc[T,"C02USDT"]=c.loc[T-pd.Timedelta(hours=4),"C02USDT"]*1.01
 recent=float(c.loc[T,"C02USDT"]/c.loc[T-pd.Timedelta(hours=4),"C02USDT"]-1)
 assert 0<recent<.02
 fresh=h.short_sleeve(replace(v,close=c),pd.Series(dtype=float),["C02USDT"])
 held=h.short_sleeve(replace(v,close=c,prev_targets=pd.Series({"C02USDT":-.05})),pd.Series(dtype=float),["C02USDT"])
 assert fresh.empty and "C02USDT" in held
 c.loc[T,"C02USDT"]=c.loc[T-pd.Timedelta(hours=4),"C02USDT"]*1.03
 stopped=h.short_sleeve(replace(v,close=c,prev_targets=pd.Series({"C02USDT":-.05})),pd.Series(dtype=float),["C02USDT"])
 assert stopped.empty
