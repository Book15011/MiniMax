from dataclasses import replace
from pathlib import Path
import numpy as np,pandas as pd,yaml,pytest
from src.contracts import MarketView,check_targets
from src.models.book._bear_exit import targets,BearExit,filter_targets

P=yaml.safe_load(Path('config.yaml').read_text())['models']['book_bear_guard'].copy()
P.update(yaml.safe_load(Path('research/book/bear_exit/config.yaml').read_text())['additional_params'])
def view():
 i=pd.date_range('2025-01-01',periods=900,freq='h',tz='UTC');n=np.arange(len(i))
 b=np.exp(-n*.001+np.sin(n/3)*.001)
 x=pd.DataFrame({s:(100+j*10)*b for j,s in enumerate(P['coins'])},index=i)
 return MarketView(i[-1],x,x*0,tuple(P['coins']),P,pd.Series(dtype=float))

def test_cost_filter_blocks_new_entries_but_does_not_force_existing_exit():
 base=pd.Series({'BTCUSDT':-.05,'ETHUSDT':-.04})
 old=pd.Series({'BTCUSDT':-.05});no=pd.Series(False,index=base.index);yes=~no
 w=filter_targets(base,old,no,yes)
 assert w.to_dict()=={'BTCUSDT':-.05}

def test_exit_wins_even_for_existing_position():
 b=pd.Series({'BTCUSDT':-.05});old=b.copy();yes=pd.Series(True,index=b.index)
 assert filter_targets(b,old,yes,~yes).empty

@pytest.mark.parametrize('family',['cost_guard','fast_exit','trail_exit'])
def test_future_ignored_caps_and_no_io(family,monkeypatch):
 import builtins
 v=view()
 def denied(*a,**kw):raise AssertionError('I/O in targets')
 monkeypatch.setattr(builtins,'open',denied)
 w=targets(v,family)
 assert not w.empty and (w<0).all()
 assert w.abs().sum()<=P['gross_cap']+1e-12 and w.abs().max()<=P['coin_cap']+1e-12
 f=v.close.iloc[-4:].copy();f.index+=pd.Timedelta(hours=4);f*=50
 vv=replace(v,close=pd.concat([v.close,f]))
 pd.testing.assert_series_equal(w,targets(vv,family))
 check_targets(w,v,BearExit('book_bear_'+family,family,1,.01).spec)

def test_low_past_move_cannot_pass_even_when_trend_signal_is_negative():
 v=view();p=P.copy();p['cost_move_multiple']=1e9
 assert targets(replace(v,params=p),'cost_guard').empty

def test_missing_bars_or_btc_mean_cash():
 v=view();x=v.close.drop(v.close.index[-10])
 assert targets(replace(v,close=x),'fast_exit').empty
 assert targets(replace(v,universe=tuple(s for s in v.universe if s!='BTCUSDT')),'trail_exit').empty

def test_unknown_family_rejected():
 with pytest.raises(ValueError):targets(view(),'unknown')
