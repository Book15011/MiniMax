"""Pure standalone directional shorts after a confirmed failed upward rally."""
import numpy as np,pandas as pd
from src.contracts import ModelSpec
def mean_distance_mark(price,mean,p):
 entry=price*(1-p["halfspread"]);cover=mean*(1+p["halfspread"])
 return (entry-cover-p["fee"]*(entry+cover))/entry
def entry_masks(x,q,sigma,p,family):
 price=x.iloc[-1];prior=x.iloc[-2];mean=x.ewm(span=p["mean_hours"],adjust=False).mean().iloc[-1]
 extension=price/mean-1
 rejection=price/prior-1< -p["rejection_sigma"]*sigma
 room=(extension>=p["entry_extension"])&(mean_distance_mark(price,mean,p)>=p["minimum_distance_mark"])
 shock=prior/x.iloc[-2-p["shock_hours"]]-1>p["shock_sigma"]*sigma*np.sqrt(p["shock_hours"])
 if family=="volume":
  recent=q.iloc[-1-p["shock_hours"]:-1].sum()
  baseline=q.iloc[-1-p["shock_hours"]-p["volume_hours"]:-1-p["shock_hours"]].mean()*p["shock_hours"]
  setup=shock&(baseline>0)&(recent>baseline*p["volume_multiple"])
 elif family=="range":
  resistance=x.iloc[-2-p["range_hours"]:-2].max()
  setup=(prior>resistance*(1+p["range_buffer"]))&(price<resistance)
 elif family=="shock":setup=shock
 else:raise ValueError("Unknown exhaustion family")
 return (setup&rejection&room).fillna(False)
def allocate(sigma,prev,active,entry,p):
 old=prev.reindex(sigma.index).fillna(0.)
 held=(-old).clip(lower=0,upper=p["coin_cap"]).where(active,0.)
 inv=1/sigma;limits=(inv/inv.sum()*p["gross_cap"]).clip(upper=p["coin_cap"])
 budget=max(0,p["gross_cap"]-float(held.sum()));size=held.copy()
 for s in sigma.index:
  if old[s]>=0 and active[s] and entry[s]:
   size[s]=min(float(limits[s]),budget);budget-=size[s]
 gross=float(size.sum());risk=float((size*sigma*np.sqrt(p["hours_per_day"])).sum())
 scale=min(1,p["gross_cap"]/gross if gross else 1,p["target_daily_vol"]/risk if risk else 1)
 w=-size*scale
 return w[w!=0]
def targets(view,family):
 p=view.params;coins=[s for s in p["coins"] if s in view.universe]
 if "BTCUSDT" not in coins:return pd.Series(dtype=float)
 n=max(p["regime_hours"]*p["warmup_multiplier"],p["risk_hours"],p["mean_hours"],p["range_hours"],p["shock_hours"]+p["volume_hours"])+1
 grid=pd.date_range(end=view.t,periods=n,freq="h")
 x=view.close.loc[:view.t].reindex(index=grid,columns=coins);q=view.quote_volume.loc[:view.t].reindex(index=grid,columns=coins)
 if not np.isfinite(x.to_numpy()).all() or (x<=0).any().any() or not np.isfinite(q.to_numpy()).all() or (q<0).any().any():return pd.Series(dtype=float)
 sigma=np.log(x).diff().ewm(span=p["risk_hours"],adjust=False).std().iloc[-1]
 if not np.isfinite(sigma).all() or (sigma<=p["sigma_floor"]).any():return pd.Series(dtype=float)
 price=x.iloc[-1];mean=x.ewm(span=p["mean_hours"],adjust=False).mean().iloc[-1]
 prior_peak=x.iloc[-1-p["stop_hours"]:-1].max()
 active=(price>mean)&(price<=prior_peak*(1+p["stop_buffer_sigma"]*sigma))
 regime=x.ewm(span=p["regime_hours"],adjust=False).mean().iloc[-1]
 weak=price.BTCUSDT<regime.BTCUSDT
 entry=entry_masks(x,q,sigma,p,family)&weak
 # A regime change blocks new entries; existing shorts exit on their own price conditions.
 return allocate(sigma,view.prev_targets,active,entry,p)
class ShortExhaustion:
 def __init__(self,name,family,hours,band):
  self.family=family
  self.spec=ModelSpec(name=name,method="trend",author="book",rebalance_hours=hours,band=band,uses_shorts=True,
   description="research: failed upward rally with cost-distance hurdle and stable held sizing")
 def targets(self,view):return targets(view,self.family)
