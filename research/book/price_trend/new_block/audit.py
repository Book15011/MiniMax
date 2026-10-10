"""As-of quote and signed-cash checks independent of the shared paper broker."""
import numpy as np,pandas as pd
def sides(quotes,grid,assets,max_age=30):
 bids=[];asks=[];lasts=[];ages=[]
 for asset in assets:
  x=quotes[quotes.pair==asset+"/USD"].sort_values("ts_utc")
  ts=pd.DatetimeIndex(x.ts_utc);ix=ts.searchsorted(grid,side="right")-1
  if (ix<0).any():raise ValueError("No past quote for "+asset)
  age=(grid.asi8-ts.asi8[ix])/1e9
  if (age>max_age).any():raise ValueError("Stale "+asset+" quote: "+str(float(age.max())))
  z=x.iloc[ix]
  b=z.max_bid.to_numpy(float);a=z.min_ask.to_numpy(float);lp=z.last_price.to_numpy(float)
  if (b<=0).any() or (a<b).any() or not np.isfinite([b,a,lp]).all():raise ValueError("Invalid quote")
  bids.append(b);asks.append(a);lasts.append(lp);ages.append(age)
 return np.stack(bids,axis=1),np.stack(asks,axis=1),np.stack(lasts,axis=1),np.stack(ages,axis=1)
def audit(events,path,quotes,assets,fee,seed,endpoint):
 grid=pd.DatetimeIndex(pd.to_datetime(path.time_utc,utc=True))
 bid,ask,_,age=sides(quotes,grid,assets)
 cash=np.full(len(grid),seed);long=np.zeros_like(bid);short=np.zeros_like(bid)
 for r in events[events.phase!="terminal"].itertuples():
  j=assets.index(r.asset);i=grid.searchsorted(pd.Timestamp(r.time_utc))
  price=ask[i,j] if r.action in ("Buy Long","Cover Short") else bid[i,j]
  if abs(r.price_usd-price)>1e-8 or abs(r.fee-r.quantity*price*fee)>1e-8:raise ValueError("Quote/fee mismatch")
  sign=1 if r.action in ("Buy Long","Cover Short") else -1
  cash[i:]-=sign*r.quantity*price+r.fee
  if r.action=="Buy Long":long[i:,j]+=r.quantity
  elif r.action=="Sell Long":long[i:,j]-=r.quantity
  elif r.action=="Open Short":short[i:,j]+=r.quantity
  elif r.action=="Cover Short":short[i:,j]-=r.quantity
  else:raise ValueError("Unknown action")
 expected=cash+(long*bid-short*ask).sum(axis=1)
 error=float(abs(expected-path.equity.to_numpy()).max())
 if error>1e-6 or (long< -1e-7).any() or (short< -1e-7).any():raise ValueError("Independent equity mismatch")
 terminal=fee*float((long[-1]*bid[-1]+short[-1]*ask[-1]).sum())
 if abs(expected[-1]-terminal-endpoint["full_cost_liquidated_equity"])>1e-6:raise ValueError("Terminal liquidation mismatch")
 if path.cash.min()<-1e-6 or (path.equity<=0).any():raise ValueError("Funding failed")
 return dict(status="PASS",max_equity_error_usd=error,max_quote_age_seconds=float(age.max()),min_cash_usd=float(path.cash.min()))
