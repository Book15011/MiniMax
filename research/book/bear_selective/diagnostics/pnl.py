"""Independent actual-fill short PnL at each hypothetical immediate liquidation."""
import numpy as np,pandas as pd
def liquidation_curve(mid,events,fee,halfspread):
 if mid.empty or not mid.index.is_unique or not mid.index.is_monotonic_increasing or not np.isfinite(mid).all() or (mid<=0).any():raise ValueError("Invalid prices")
 cash=np.zeros(len(mid));qty=np.zeros(len(mid))
 for e in events.itertuples():
  t=pd.Timestamp(e.time_utc);i=mid.index.searchsorted(t)
  if i==len(mid) or mid.index[i]!=t:raise ValueError("Fill absent from path")
  if e.quantity<=0 or abs(e.fee-e.quantity*e.price_usd*fee)>1e-8:raise ValueError("Invalid fill/fee")
  if e.action=="Open Short":cash[i:]+=e.quantity*e.price_usd-e.fee;qty[i:]+=e.quantity
  elif e.action=="Cover Short":cash[i:]-=e.quantity*e.price_usd+e.fee;qty[i:]-=e.quantity
  else:raise ValueError("Unexpected short action")
 if (qty< -1e-7).any() or abs(qty[-1])>1e-7:raise ValueError("Invalid completed short quantity")
 ask=mid.to_numpy()*(1+halfspread)
 return pd.Series(cash-qty*ask*(1+fee),index=mid.index)
