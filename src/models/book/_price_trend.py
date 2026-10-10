"""Price-only directional research, fixed protocol and shared risk constraints."""
from __future__ import annotations
import numpy as np,pandas as pd
from src.contracts import MarketView,ModelSpec

def inputs(view):
 p=view.params;coins=[c for c in p["coins"] if c in view.universe]
 n=max(p["warmup_multiplier"]*p["slow_hours"],p["risk_hours"],p["channel_hours"])+1
 idx=pd.date_range(view.t-pd.Timedelta(hours=n-1),view.t,freq="h")
 x=view.close.loc[:view.t].reindex(index=idx,columns=coins)
 if not coins or not np.isfinite(x.to_numpy()).all() or (x<=0).any().any():return x.iloc[:0]
 return x

def forecast(close,p,family):
 sigma=np.log(close).diff().ewm(span=p["risk_hours"],adjust=False).std().iloc[-1]
 if family=="channel":
  tail=close.tail(p["channel_hours"])
  hi=tail.max();lo=tail.min();rng=(hi-lo).replace(0,np.nan)
  f=(2*(close.iloc[-1]-lo)/rng-1).fillna(0)
 else:
  fast=close.ewm(span=p["fast_hours"],adjust=False).mean().iloc[-1]
  slow=close.ewm(span=p["slow_hours"],adjust=False).mean().iloc[-1]
  z=(fast/slow-1)/sigma.replace(0,np.nan)
  f=(z/p["forecast_scale"]).clip(-1,1).mask(z.abs()<p["deadzone_z"],0.).fillna(0)
 return f,sigma

def targets(view,family,short_only):
 p=view.params;x=inputs(view)
 if x.empty:return pd.Series(dtype=float)
 f,sigma=forecast(x,p,family)
 if short_only:f=f.clip(upper=0)
 valid=np.isfinite(sigma)&(sigma>p["sigma_floor"])
 if not valid.all():return pd.Series(dtype=float)
 inv=1/sigma
 base=(inv/inv.sum()*p["gross_cap"]).clip(upper=p["coin_cap"])
 w=base*f
 gross=float(w.abs().sum());risk=float((w.abs()*sigma*np.sqrt(24)).sum())
 scale=min(1.,p["gross_cap"]/gross if gross else 1.,p["target_daily_vol"]/risk if risk else 1.)
 return (w*scale)[lambda z:z!=0]

class PriceTrend:
 def __init__(self,name,family,short_only):
  self.family=family;self.short_only=short_only
  self.spec=ModelSpec(name=name,method="trend",author="book",rebalance_hours=4,band=.05,uses_shorts=True,
   description="research: price-only "+family+(" short-only" if short_only else " long/short")+" with capped inverse volatility")
 def targets(self,view):return targets(view,self.family,self.short_only)
