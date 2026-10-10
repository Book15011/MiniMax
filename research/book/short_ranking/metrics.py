"""Descriptive opportunity F1 and sample-aware accuracy, never future predictors."""
from statistics import NormalDist
import numpy as np,pandas as pd
def confusion(positive,predicted):
 y=np.asarray(positive,bool);p=np.asarray(predicted,bool)
 if y.shape!=p.shape:raise ValueError("Classification shapes differ")
 tp=int((y&p).sum());fp=int((~y&p).sum());fn=int((y&~p).sum());tn=int((~y&~p).sum())
 return dict(tp=tp,fp=fp,fn=fn,tn=tn,precision=tp/(tp+fp) if tp+fp else 0.,recall=tp/(tp+fn) if tp+fn else 0.,f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.)
def wilson_lower(wins,n,confidence):
 if n==0:return 0.
 if not 0<=wins<=n or not .5<confidence<1:raise ValueError("Invalid binomial summary")
 z=NormalDist().inv_cdf(confidence);p=wins/n
 return float((p+z*z/(2*n)-z*np.sqrt(p*(1-p)/n+z*z/(4*n*n)))/(1+z*z/n))
def combined_scores(frame,cfg):
 if not np.isclose(sum(cfg[k] for k in ["return_weight","f1_weight","accuracy_weight"]),1):raise ValueError("Weights must sum to one")
 x=frame.copy()
 x["return_component"]=(x.selection_lower90.rank(method="average",ascending=True)-1)/max(1,len(x)-1)
 for n in ["f1_lower90","accuracy_reliability"]:
  if not np.isfinite(x[n]).all() or not x[n].between(0,1).all():raise ValueError("Invalid score component")
 x["return_points"]=100*cfg["return_weight"]*x.return_component
 x["f1_points"]=100*cfg["f1_weight"]*x.f1_lower90
 x["accuracy_points"]=100*cfg["accuracy_weight"]*x.accuracy_reliability
 x["score"]=x.return_points+x.f1_points+x.accuracy_points
 x=x.sort_values(["score","selection_lower90","model"],ascending=[False,False,True])
 x["rank"]=range(1,len(x)+1);return x
def block_rows(path,prices,start,end,assets,cfg):
 start=pd.Timestamp(start);end=pd.Timestamp(end);horizon=pd.Timedelta(hours=cfg["horizon_hours"])
 times=pd.date_range(start+pd.Timedelta(minutes=cfg["lag_minutes"]+cfg["settlement_minutes"]),end,freq=horizon)
 ix=pd.DatetimeIndex(pd.to_datetime(path.time_utc,utc=True))
 if not ix.is_monotonic_increasing or not ix.is_unique:raise ValueError("Invalid audited path clock")
 rows=[];censored=0
 for t in times:
  finish=t+horizon
  if finish>end:censored+=len(assets);continue
  pi=ix.searchsorted(t,side="right")-1
  if pi<0 or (t-ix[pi]).total_seconds()>60:raise ValueError("Stale holdings path")
  state=path.iloc[pi];eq=float(state.equity)
  if not np.isfinite(eq) or eq<=0:raise ValueError("Invalid equity")
  for a in assets:
   begin=float(prices.at[t,a+"USDT"]);last=float(prices.at[finish,a+"USDT"])
   if not np.isfinite([begin,last]).all() or min(begin,last)<=0:raise ValueError("Missing complete opportunity price")
   bid=begin*(1-cfg["halfspread"]);ask=last*(1+cfg["halfspread"])
   mark=(bid-ask-cfg["fee"]*(bid+ask))/bid
   qty=float(state[a])
   # These audited cohorts are short-only; simultaneous long/short offsets are excluded.
   if qty>1e-7:raise ValueError("Long quantity in short-only diagnostic")
   weight=max(0.,-qty)*begin*(1+cfg["halfspread"])/eq
   rows.append(dict(block_start=str(t),block_end=str(finish),asset=a,positive=bool(mark>0),predicted=bool(weight>=cfg["minimum_short_weight"]),short_weight=weight,after_cost_mark=mark))
 return pd.DataFrame(rows),censored
def f1_interval(cases,cfg):
 quarter=pd.to_datetime(cases.start,utc=True).dt.tz_localize(None).dt.to_period("Q")
 z=cases.assign(quarter=quarter).groupby("quarter")[["tp","fp","fn"]].sum()
 rng=np.random.default_rng(cfg["seed"]);draw=rng.integers(0,len(z),size=(cfg["bootstrap_reps"],len(z)))
 vals=z.to_numpy()[draw].sum(axis=1);den=2*vals[:,0]+vals[:,1]+vals[:,2]
 f=np.divide(2*vals[:,0],den,out=np.zeros(len(den)),where=den>0)
 return float(np.quantile(f,1-cfg["confidence"])),float(np.quantile(f,cfg["confidence"]))
