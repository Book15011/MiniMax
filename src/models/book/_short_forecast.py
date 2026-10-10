"""Pure directional shorts from past, fully matured market-state examples."""
from __future__ import annotations
import numpy as np,pandas as pd
from src.contracts import ModelSpec
from ._bear_selective import allocate
def short_mark(forward_return,p):
 entry=1-p['halfspread'];cover=(1+np.asarray(forward_return))*(1+p['halfspread'])
 return (entry-cover-p['fee']*(entry+cover))/entry
def training_samples(close,t,p):
 coins=[s for s in p['coins'] if s in close]
 if 'BTCUSDT' not in coins:raise ValueError('BTC context unavailable')
 warm=max(max(p['returns_hours']),p['gap_hours'],p['risk_hours'])
 n=p['training_hours']+warm+p['horizon_hours']+p['execution_lag_hours']+1
 grid=pd.date_range(t-pd.Timedelta(hours=n-1),t,freq='h')
 x=close.loc[:t].reindex(index=grid,columns=coins)
 if not np.isfinite(x.to_numpy()).all() or (x<=0).any().any():raise ValueError('Incomplete training market')
 sigma=np.log(x).diff().rolling(p['risk_hours'],min_periods=p['risk_hours']).std()
 vals=[]
 for h in p['returns_hours']:vals.append((x/x.shift(h)-1)/(sigma*np.sqrt(h)))
 gap=(x/x.rolling(p['gap_hours'],min_periods=p['gap_hours']).mean()-1)/(sigma*np.sqrt(p['gap_hours']))
 vals+=[gap,np.log(sigma/p['risk_reference'])]
 bh=max(p['returns_hours']);btc=((x.BTCUSDT/x.BTCUSDT.shift(bh)-1)/(sigma.BTCUSDT*np.sqrt(bh)))
 vals.append(pd.DataFrame(np.repeat(btc.to_numpy()[:,None],len(coins),axis=1),index=x.index,columns=coins))
 bank=np.stack([v.to_numpy() for v in vals],axis=-1)
 lag=p['execution_lag_hours'];h=p['horizon_hours']
 future=x.shift(-lag-h)/x.shift(-lag)-1
 y=short_mark(future.to_numpy(),p)
 # Anchors are aligned to UTC and their entire lag+holding interval must have ended.
 eligible=(x.index>=t-pd.Timedelta(hours=p['training_hours']))&(x.index<=t-pd.Timedelta(hours=lag+h))&(x.index.hour%p['training_stride']==0)
 ready=eligible&np.isfinite(bank).all(axis=(1,2))&np.isfinite(y).all(axis=1)
 if int(ready.sum())<p['min_training_anchors']:raise ValueError('Insufficient matured anchors')
 X=bank[ready].reshape(-1,bank.shape[-1]);Y=y[ready].reshape(-1)
 anchors=pd.DatetimeIndex(np.repeat(x.index[ready].to_numpy(),len(coins)))
 query=bank[-1];risk=sigma.iloc[-1].to_numpy()
 if not np.isfinite(query).all() or not np.isfinite(risk).all() or (risk<=p['sigma_floor']).any():raise ValueError('Invalid latest state')
 return X,Y,anchors,query,risk
def forecast(close,t,p,family):
 X,y,anchors,q,sigma=training_samples(close,t,p)
 mu=X.mean(axis=0);sd=np.maximum(X.std(axis=0),p['scale_floor'])
 a=(X-mu)/sd;b=(q-mu)/sd
 if family=='analogue':
  edge=[];hit=[]
  for row in b:
   distance=((a-row)**2).mean(axis=1);order=np.argsort(distance,kind='stable')[:min(p['neighbors'],len(y))]
   if anchors[order].nunique()<p['min_neighbor_anchors']:edge.append(np.nan);hit.append(np.nan);continue
   edge.append(float(y[order].mean()));hit.append(float((y[order]>0).mean()))
  return np.asarray(edge),np.asarray(hit),sigma
 if family=='ridge':
  if p['quadratic']:a=np.concatenate([a,a*a],axis=1);b=np.concatenate([b,b*b],axis=1)
  a=np.column_stack([np.ones(len(a)),a]);b=np.column_stack([np.ones(len(b)),b])
  penalty=np.eye(a.shape[1])*p['ridge_penalty'];penalty[0,0]=0
  beta=np.linalg.solve(a.T@a/len(a)+penalty,a.T@y/len(a))
  edge=b@beta;residual=y-a@beta
  hit=np.asarray([(z+residual>0).mean() for z in edge])
  return edge,hit,sigma
 raise ValueError('Unknown short forecast family')
def targets(view,family):
 p=view.params;coins=[s for s in p['coins'] if s in view.universe]
 if 'BTCUSDT' not in coins:return pd.Series(dtype=float)
 local={**p,'coins':coins}
 try:edge,hit,risk=forecast(view.close,view.t,local,family)
 except (ValueError,np.linalg.LinAlgError):return pd.Series(dtype=float)
 sigma=pd.Series(risk,index=coins);edge=pd.Series(edge,index=coins);hit=pd.Series(hit,index=coins)
 strength=((edge-p['exit_edge'])/p['edge_scale']).clip(0,1).fillna(0)
 active=edge>p['exit_edge'];entry=(edge>=p['entry_edge'])&(hit>=p['min_win_fraction'])
 return allocate(strength,sigma,view.prev_targets,active,entry,p)
class ShortForecast:
 def __init__(self,name,family,rebalance_hours,band):
  self.family=family
  self.spec=ModelSpec(name=name,method='trend',author='book',rebalance_hours=rebalance_hours,band=band,uses_shorts=True,
   description='research: past-state short forecast with purged labels and fee hurdle')
 def targets(self,view):return targets(view,self.family)
