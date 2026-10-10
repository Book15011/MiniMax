from dataclasses import replace
import numpy as np,pandas as pd
from src.contracts import MarketView
from src.config import load_config
from src.models.book.book_daily_channel import MODEL,allocate
def view():
 t=pd.Timestamp("2026-10-05 01:00",tz="UTC");p=load_config()["models"]["book_daily_channel"]
 ix=pd.date_range(end=t+pd.Timedelta(hours=3),periods=p["warmup_hours"]+4,freq="h")
 rng=np.random.default_rng(11);x=pd.DataFrame(np.exp(np.cumsum(rng.normal(.00005,.002,(len(ix),5)),axis=0))*100,index=ix,columns=p["coins"])
 return MarketView(t,x,x*0,tuple(p["coins"]),p)
def test_future_prices_cannot_change_targets():
 v=view();changed=v.close.copy();changed.loc[changed.index>v.t]*=3
 pd.testing.assert_series_equal(MODEL.targets(v),MODEL.targets(replace(v,close=changed)))
def test_direction_and_budget():
 v=view();w=MODEL.targets(v);assert w.abs().sum()<=1+1e-12
 for sign in [-1,1]:
  s=np.full((1,5,5),.01*sign);sigma=np.full((1,5),.004)
  a=allocate(s,sigma,v.params)
  assert np.sign(a).tolist()==[[sign]*5] and abs(a).sum()<=1+1e-12
def test_incomplete_selected_history_returns_cash():
 v=view();x=v.close.copy();x.loc[v.t,v.universe[0]]=np.nan
 assert MODEL.targets(replace(v,close=x)).empty
def test_exact_research_allocation_reference():
 import importlib.util,sys
 root="/home/ubuntu/test/MiniMax/.worktrees/book-book-clone-reconcile"
 spec=importlib.util.spec_from_file_location("reference_daily_allocation",root+"/research/book/clone_multiscale/model.py")
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 from pathlib import Path
 import json
 z=json.loads(Path(root+"/results/book/20261010-clone-inverse-v1/selection_freeze.json").read_text());p=view().params
 rng=np.random.default_rng(3);bank=rng.normal(0,.004,(5,5,5));risk=rng.uniform(.001,.01,(5,5))
 a,b,_,_,_,_,_,_,mix,ratio=z["pars"]
 ema=bank[:,:,0]+a*(bank[:,:,1]-bank[:,:,0])+b*(bank[:,:,2]-bank[:,:,0])
 channel=(1-ratio)*bank[:,:,3]+ratio*bank[:,:,4]
 signal=(1-mix)*ema+mix*channel
 expected=module.allocations(np.repeat(signal[:,:,None],3,axis=-1),risk,z["pars"][:8],p["risk_reference"])
 np.testing.assert_array_equal(allocate(bank,risk,p),expected)
