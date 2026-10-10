"""Pure selective bearish targets with explicit cash and rebound exits."""
from __future__ import annotations
import numpy as np,pandas as pd
from src.contracts import ModelSpec
def inputs(view):
 p=view.params;coins=[s for s in p["coins"] if s in view.universe]
 n=max(p["warmup_multiplier"]*p["regime_hours"],p["risk_hours"],p["range_hours"],p["return_hours"])+1
 idx=pd.date_range(view.t-pd.Timedelta(hours=n-1),view.t,freq="h")
 x=view.close.loc[:view.t].reindex(index=idx,columns=coins)
 if not coins or not np.isfinite(x.to_numpy()).all() or (x<=0).any().any():return x.iloc[:0]
 return x
def allocate(strength,sigma,prev,active,entry,p):
 inv=1/sigma;limit=(inv/inv.sum()*p["gross_cap"]).clip(upper=p["coin_cap"])*strength.clip(0,1)
 old=prev.reindex(sigma.index).fillna(0.)
 keep=(old<0)&active
 new=(old>=0)&entry&active
 size=pd.Series(0.,index=sigma.index)
 size.loc[keep]=np.minimum(-old.loc[keep],limit.loc[keep])
 size.loc[new]=limit.loc[new]
 gross=float(size.sum());risk=float((size*sigma*np.sqrt(p["hours_per_day"])).sum())
 scale=min(1.,p["gross_cap"]/gross if gross else 1.,p["target_daily_vol"]/risk if risk else 1.)
 w=-size*scale
 return w[w!=0]
def targets(view,family):
 p=view.params;x=inputs(view)
 if x.empty:return pd.Series(dtype=float)
 sigma=np.log(x).diff().ewm(span=p["risk_hours"],adjust=False).std().iloc[-1]
 if not np.isfinite(sigma).all() or (sigma<=p["sigma_floor"]).any():return pd.Series(dtype=float)
 fast=x.ewm(span=p["fast_hours"],adjust=False).mean();slow=x.ewm(span=p["slow_hours"],adjust=False).mean()
 z=(fast.iloc[-1]/slow.iloc[-1]-1)/sigma
 conviction=(-z/p["forecast_scale"]).clip(0,1).mask(z.abs()<p["deadzone_z"],0.)
 yes=conviction>0
 if family=="trend_control":
  return allocate(conviction,sigma,pd.Series(dtype=float),yes,yes,p)
 if "BTCUSDT" not in x:return pd.Series(dtype=float)
 regime=x.ewm(span=p["regime_hours"],adjust=False).mean()
 ret24=x.iloc[-1]/x.iloc[-1-p["return_hours"]]-1
 breadth=float((x.iloc[-1]>slow.iloc[-1]).mean())
 weak=(x.iloc[-1].BTCUSDT<regime.iloc[-1].BTCUSDT and ret24.BTCUSDT<0 and breadth<=p["breadth_max"])
 if not weak:return pd.Series(dtype=float)
 exit_ema=x.ewm(span=p["exit_hours"],adjust=False).mean().iloc[-1]
 bounce=x.iloc[-1]/x.tail(p["trail_hours"]).min()-1
 # Existing positions have a less strict trend threshold; confirmed rebound exits still apply.
 active=(z<-p["exit_z"])&(x.iloc[-1]<exit_ema)&(bounce<=p["max_bounce_sigma"]*sigma*np.sqrt(p["trail_hours"]))
 entry=(z<-p["entry_z"])&(x.iloc[-1]<fast.iloc[-1])
 if family=="pullback":
  prior=x.iloc[-2]/x.iloc[-2-p["pullback_hours"]]-1
  last=x.iloc[-1]/x.iloc[-2]-1
  entry &= (prior>p["pullback_sigma"]*sigma*np.sqrt(p["pullback_hours"]))&(last< -p["rejection_sigma"]*sigma)
 elif family=="breakdown":
  low=x.iloc[-1-p["range_hours"]:-1].min()
  extension=(slow.iloc[-1]/x.iloc[-1]-1)/(sigma*np.sqrt(p["slow_hours"]))
  entry &= (x.iloc[-1]<low*(1-p["break_buffer"]))&(extension<p["max_extension_sigma"])
 elif family!="guard":raise ValueError("Unknown selective short family")
 return allocate(conviction,sigma,view.prev_targets,active,entry,p)
class BearSelective:
 def __init__(self,name,family,rebalance_hours,band):
  self.family=family
  self.spec=ModelSpec(name=name,method="trend",author="book",rebalance_hours=rebalance_hours,band=band,uses_shorts=True,
   description="research: capped bearish "+family+" with hourly decisions and cash exits")
 def targets(self,view):return targets(view,self.family)
