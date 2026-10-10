"""Research daily directional allocation, calibrated to five observed sessions."""
import numpy as np,pandas as pd
from src.contracts import ModelSpec
from src.config import load_config
def allocate(bank,sigma,p):
 a,b,bias,logclip,power,scale,cap,daily,mix,ratio=p["pars"]
 ema=bank[:,:,0]+a*(bank[:,:,1]-bank[:,:,0])+b*(bank[:,:,2]-bank[:,:,0])
 channel=(1-ratio)*bank[:,:,3]+ratio*bank[:,:,4]
 signal=(1-mix)*ema+mix*channel
 f=np.clip((signal+bias)/np.exp(logclip),-1,1)
 w=np.clip(scale*f/(sigma/p["risk_reference"])**power,-cap,cap)
 w/=np.maximum(1,np.abs(w).sum(axis=1,keepdims=True))
 risk=(np.abs(w)*sigma*np.sqrt(p["hours_per_day"])).sum(axis=1,keepdims=True)
 return w*np.minimum(1,daily/np.maximum(risk,1e-15))
class DailyChannel:
 def __init__(self,p):
  self.spec=ModelSpec(name="book_daily_channel",method="trend",author="book",rebalance_hours=p["rebalance_hours"],band=p["band"],uses_shorts=True,
   description="research: calibrated shared EMA/channel daily allocation; standard 16UTC clock")
 def targets(self,view):
  p=view.params;coins=[s for s in p["coins"] if s in view.universe]
  if not coins:return pd.Series(dtype=float)
  grid=pd.date_range(end=view.t,periods=p["warmup_hours"],freq="h")
  x=view.close.loc[:view.t].reindex(index=grid,columns=coins)
  if not np.isfinite(x.to_numpy()).all() or (x<=0).any().any():return pd.Series(dtype=float)
  sk=view.t-pd.Timedelta(hours=p["signal_lag"]);vk=view.t-pd.Timedelta(hours=p["risk_lag"])
  vals=[]
  for fast,slow in p["ema_pairs"]:
   vals.append((x.ewm(span=fast,adjust=False).mean()/x.ewm(span=slow,adjust=False).mean()-1).loc[sk].to_numpy())
  for n in p["extra"]:
   hi=x.rolling(n,min_periods=n).max();lo=x.rolling(n,min_periods=n).min();width=hi-lo
   loc=(2*(x-(hi+lo)/2)/width.replace(0,np.nan)).mask(width==0,0)
   smooth=max(1,int(n*p["smooth_fraction"]))
   vals.append((loc.ewm(span=smooth,adjust=False).mean()*p["channel_scale"]).loc[sk].to_numpy())
  sigma=np.log(x).diff().ewm(span=p["risk_span"],adjust=False).std().loc[vk].to_numpy()[None,:]
  if not np.isfinite(sigma).all() or (sigma<=p["sigma_floor"]).any():return pd.Series(dtype=float)
  bank=np.stack(vals,axis=-1)[None,:,:]
  w=pd.Series(allocate(bank,sigma,p)[0],index=coins)
  return w[w!=0]
MODEL=DailyChannel(load_config()["models"]["book_daily_channel"])
