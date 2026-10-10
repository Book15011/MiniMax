"""Vectorized minute valuation around the existing shared planner/PaperBroker replay."""
from __future__ import annotations
import numpy as np,pandas as pd
from src.validation import short_competition as shared
def fast_paths(states,book,cfg,extra=()):
 start=pd.Timestamp(cfg["start"]);end=pd.Timestamp(cfg["end"])
 grid=pd.DatetimeIndex(sorted(set(pd.date_range(start,end,freq="min"))|set(extra)|{start,end}))
 times=np.array([pd.Timestamp(t).value for t,_ in states],dtype=np.int64)
 selected=np.searchsorted(times,grid.asi8,side="right")-1
 pi=np.searchsorted(book.pt,grid.asi8,side="right")-1
 age=(grid.asi8-book.pt[np.maximum(pi,0)])/1e9
 if (pi<0).any() or (age>cfg["minute_max_age"]).any():raise ValueError("Missing valuation quote")
 if any(len(z[0]) for z in book.q.values()):raise ValueError("Vectorized path supports declared archive proxies only")
 mid=book.p.iloc[pi][[a+"USDT" for a in cfg["assets"]]].to_numpy(float)
 half=cfg["proxy_half_spread"];bids=mid*(1-half);asks=mid*(1+half)
 cash=[];intercept=[];longs=[];shorts=[]
 for _,h in states:
  cash.append(h.usd_free)
  longs.append([h.spot.get(a+"/USD",0) for a in cfg["assets"]])
  shorts.append([h.shorts[a+"/USD"].qty if a+"/USD" in h.shorts else 0 for a in cfg["assets"]])
  intercept.append(h.usd_free+sum(z.collateral+z.qty*z.entry for z in h.shorts.values()))
 l=np.asarray(longs)[selected];s=np.asarray(shorts)[selected]
 eq=np.asarray(intercept)[selected]+(l*bids-s*asks).sum(axis=1)
 gross=(l*bids+s*asks).sum(axis=1)
 out=pd.DataFrame({"time_utc":grid,"cash":np.asarray(cash)[selected],"equity":eq,"gross":gross,"gross_ratio":gross/eq})
 for j,a in enumerate(cfg["assets"]):out[a]=l[:,j]-s[:,j]
 return out,[]

def replay(weights,prices,cfg,lag_minutes):
 old=shared.paths_from_states
 try:
  shared.paths_from_states=fast_paths
  quotes=pd.DataFrame(columns=["pair","ts_utc","max_bid","min_ask"])
  book=shared.QuoteBook(prices,quotes,cfg)
  return shared.replay_targets(weights,book,cfg,lag_minutes)
 finally:shared.paths_from_states=old

def independent_audit(events,path,prices,cfg,endpoint):
 grid=pd.DatetimeIndex(pd.to_datetime(path.time_utc,utc=True))
 pi=prices.index.searchsorted(grid,side="right")-1
 mid=prices.iloc[pi][[a+"USDT" for a in cfg["assets"]]].to_numpy(float)
 half=cfg["proxy_half_spread"];bids=mid*(1-half);asks=mid*(1+half)
 cash=np.full(len(grid),cfg["seed"]);l=np.zeros_like(mid);s=np.zeros_like(mid);fees=0.
 for r in events[events.phase!="terminal"].itertuples():
  j=cfg["assets"].index(r.asset);i=grid.searchsorted(pd.Timestamp(r.time_utc),side="left")
  expected=mid[i,j]*(1-half if r.action in ("Sell Long","Open Short") else 1+half)
  if abs(expected-r.price_usd)>1e-8:raise ValueError("Execution price mismatch")
  if abs(r.fee-r.quantity*r.price_usd*cfg["fee"])>1e-8:raise ValueError("Fee mismatch")
  sign=1 if r.action in ("Buy Long","Cover Short") else -1
  cash[i:]+=-sign*r.quantity*r.price_usd-r.fee;fees+=r.fee
  if r.action=="Buy Long":l[i:,j]+=r.quantity
  elif r.action=="Sell Long":l[i:,j]-=r.quantity
  elif r.action=="Open Short":s[i:,j]+=r.quantity
  elif r.action=="Cover Short":s[i:,j]-=r.quantity
  else:raise ValueError("Unknown action")
 expected=cash+(l*bids-s*asks).sum(axis=1)
 error=float(np.max(np.abs(expected-path.equity.to_numpy())))
 if error>1e-6 or (l< -1e-7).any() or (s< -1e-7).any():raise ValueError("Independent signed quantity/equity mismatch")
 fee=cfg["fee"]*float((l[-1]*bids[-1]+s[-1]*asks[-1]).sum())
 if abs(expected[-1]-fee-endpoint["full_cost_liquidated_equity"])>1e-6:raise ValueError("Full liquidation mismatch")
 if path.cash.min()<-1e-6 or (path.equity<=0).any():raise ValueError("Invalid collateral equity")
 return {"status":"PASS","max_equity_error_usd":error,"fees_usd":fees,"minimum_cash_usd":float(path.cash.min())}
