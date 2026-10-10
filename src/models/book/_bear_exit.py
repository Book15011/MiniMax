"""Pure cost-filtered shorts with completed-price reversal exits."""
from __future__ import annotations
import numpy as np,pandas as pd
from src.contracts import ModelSpec
from ._bear_selective import inputs,targets as guard_targets

def filter_targets(base,prev,entry_allowed,active):
 old=prev.reindex(base.index).fillna(0.)
 keep=active.reindex(base.index).fillna(False)&((old<0)|entry_allowed.reindex(base.index).fillna(False))
 return base[keep]

def targets(view,family):
 if family not in ('cost_guard','fast_exit','trail_exit'):raise ValueError('Unknown short exit family')
 p=view.params;x=inputs(view)
 if x.empty:return pd.Series(dtype=float)
 base=guard_targets(view,'guard')
 if base.empty:return base
 past_decline=1-x.iloc[-1]/x.iloc[-1-p['cost_lookback_hours']]
 cost=2*(p['estimated_fee']+p['estimated_halfspread'])
 allowed=past_decline>=p['cost_move_multiple']*cost
 active=pd.Series(True,index=x.columns)
 if family=='fast_exit':
  ema=x.ewm(span=p['fast_exit_hours'],adjust=False).mean().iloc[-1]
  recent=x.iloc[-1]/x.iloc[-1-p['fast_return_hours']]-1
  active=(x.iloc[-1]<ema)&(recent<0)
 elif family=='trail_exit':
  sigma=np.log(x).diff().ewm(span=p['risk_hours'],adjust=False).std().iloc[-1]
  if not np.isfinite(sigma).all():return pd.Series(dtype=float)
  rebound=x.iloc[-1]/x.tail(p['rebound_window_hours']).min()-1
  bound=(p['rebound_sigma']*sigma*np.sqrt(p['rebound_sigma_hours'])).clip(lower=p['rebound_floor'])
  active=rebound<bound
 return filter_targets(base,view.prev_targets,allowed,active)

class BearExit:
 def __init__(self,name,family,rebalance_hours,band):
  self.family=family
  self.spec=ModelSpec(name=name,method='trend',author='book',rebalance_hours=rebalance_hours,band=band,uses_shorts=True,
   description='research: cost-filtered bearish entries with '+family+' completed-price exits')
 def targets(self,view):return targets(view,self.family)
