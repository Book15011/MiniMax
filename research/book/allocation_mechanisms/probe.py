"""Retrospective, bounded allocation mechanism screen; not an execution clone.

No log is used by portfolio_features or bounded_weights. Three dates select shared
parameters; later dates are diagnostic and have already been seen.
"""
import json,itertools,sys,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
CFG=yaml.safe_load((Path(__file__).parent/'config.yaml').read_text())

def shrunk_cov(r,shrink):
 c=np.cov(r,rowvar=False,ddof=1)
 c=(1-float(shrink))*c+float(shrink)*np.diag(np.diag(c))
 floor=max(float(np.trace(c))/len(c)*CFG["covariance_floor_fraction"],CFG["covariance_floor_minimum"])
 return c+np.eye(len(c))*floor

def bounded_weights(v,k,cap,gross=1.):
 w=np.clip(np.asarray(v)*np.asarray(k),-float(cap),float(cap))
 return w/np.maximum(1,np.abs(w).sum(axis=-1,keepdims=True)/float(gross))

def portfolio_features(h,times,family,lookback,lag,vol_window,shrink,transform,fast=6):
 values=[]
 for t in times:
  x=h.loc[:t-pd.Timedelta(hours=lag)].dropna()
  if family=="momentum":v=(x.iloc[-1]/x.iloc[-1-lookback]-1).to_numpy()
  elif family=="ema":v=(x.ewm(span=fast,adjust=False).mean().iloc[-1]/x.ewm(span=lookback,adjust=False).mean().iloc[-1]-1).to_numpy()
  else:raise ValueError(family)
  r=x.pct_change(fill_method=None).tail(vol_window).dropna().to_numpy()
  if transform=="ivol":v=v/r.std(axis=0,ddof=1)
  elif transform=="ivar":v=v/r.var(axis=0,ddof=1)
  elif transform=="cov":v=np.linalg.solve(shrunk_cov(r,shrink),v)
  elif transform!="raw":raise ValueError(transform)
  values.append(v)
 return np.stack(values)

def main():
 sys.path.insert(0,CFG["source_worktree"])
 from src.validation.observed_study import load_market
 out=Path(CFG["output"]);out.mkdir(parents=True,exist_ok=True)
 q,p,h=load_market({"output":CFG["market_output"]})
 actual=pd.read_csv(Path(CFG["market_output"])/"observed_daily_targets.csv").set_index("date")
 cols=[a+"USDT" for a in CFG["assets"]]
 h=h[cols];obs=actual[cols].to_numpy();fit_n=int(CFG["fit_sessions"])
 times=[pd.Timestamp(d+"T01:00Z") for d in actual.index]
 records=[];weights={}
 caps=CFG["position_caps"]
 factors=np.geomspace(*CFG["k_factor_grid"])
 bases=[("momentum",0,lb) for lb in CFG["momentum_lookbacks"]]+[("ema",f,s) for f,s in CFG["ema_pairs"]]
 risks=[("raw",72,1.)]+[(x,v,1.) for x in ("ivol","ivar") for v in CFG["risk_windows"]]+[("cov",v,s) for v in CFG["risk_windows"] for s in CFG["covariance_shrinkages"]]
 n=0
 for (family,fast,lb),lag,(transform,vwin,shrink) in itertools.product(bases,CFG["lags"],risks):
  vec=portfolio_features(h,times,family,lb,lag,vwin,shrink,transform,fast)
  den=max(np.median(np.abs(vec[:fit_n])),1e-10);ks=factors/den
  for cap in caps:
   w=bounded_weights(vec[None,:,:],ks[:,None,None],cap)
   err=np.abs(w[:,:fit_n,:]-obs[None,:fit_n,:]).mean(axis=(1,2));j=int(err.argmin())
   row=dict(candidate=n,family=family,fast=fast,lookback=lb,lag=lag,transform=transform,vol_window=vwin,shrink=shrink,cap=cap,k=float(ks[j]),train_mae=float(err[j]),later_mae=float(np.abs(w[j,fit_n:]-obs[fit_n:]).mean()),all_mae=float(np.abs(w[j]-obs).mean()),train_sign=float((np.sign(w[j,:fit_n])==np.sign(obs[:fit_n])).mean()),later_sign=float((np.sign(w[j,fit_n:])==np.sign(obs[fit_n:])).mean()))
   records.append(row);weights[n]=w[j];n+=1
 table=pd.DataFrame(records).sort_values(["train_mae","candidate"])
 table.to_csv(out/"allocation_trials.csv",index=False)
 selected=table.groupby("transform",sort=False).head(CFG["shortlist_per_transform"]).sort_values("train_mae")
 selected.to_csv(out/"mechanism_shortlist.csv",index=False)
 picked=[]
 for _,r in selected.iterrows():
  for d,w in zip(actual.index,weights[int(r.candidate)]):
   picked.append(dict(candidate=int(r.candidate),date=d,**dict(zip(cols,w))))
 pd.DataFrame(picked).to_csv(out/"mechanism_weights.csv",index=False)
 diag=[]
 for t,(date,a) in zip(times,actual.iterrows()):
  x=h.loc[:t];ab=a[cols].abs().to_numpy();actualmix=ab/ab.sum()
  row=dict(date=date,gross=float(ab.sum()),max_weight=float(ab.max()),abs_equal_weight_mae=float(np.abs(actualmix-.2).mean()))
  for vwin in CFG["risk_windows"]:
   r=x.pct_change(fill_method=None).tail(vwin).dropna().to_numpy();vol=r.std(axis=0,ddof=1);cov=shrunk_cov(r,.5)
   inv=1/vol;inv/=inv.sum()
   row["inverse_vol_mae_"+str(vwin)]=float(np.abs(actualmix-inv).mean())
   rc=ab*(cov@ab);rc/=rc.sum()
   row["risk_contribution_cv_"+str(vwin)]=float(np.std(rc)/np.mean(rc))
  diag.append(row)
 pd.DataFrame(diag).to_csv(out/"risk_budget_diagnostics.csv",index=False)
 # Exact same-dollar clusters can signal clipping/capital fit, not proof of source rules.
 cluster=[]
 for date,a in actual.iterrows():
  for i,j in itertools.combinations(cols,2):
   wi,wj=abs(a[i]),abs(a[j])
   if min(wi,wj)>CFG["same_dollar_minimum_weight"] and abs(wi/wj-1)<CFG["same_dollar_relative_tolerance"]:
    cluster.append(dict(date=date,asset1=i,asset2=j,weight1=wi,weight2=wj,relative_gap=abs(wi/wj-1)))
 pd.DataFrame(cluster).to_csv(out/"same_dollar_clusters.csv",index=False)
 summary=dict(target_candidates=len(table),k_grid_per_cap=len(factors),fit_dates=list(actual.index[:fit_n]),later_dates=list(actual.index[fit_n:]),later_status="previously inspected retrospective diagnostics",selection_criterion="mean absolute daily target weight error on Oct5-7 only",initial_bootstrap=False,log_sha256=hashlib.sha256((Path(CFG["market_output"])/"observed_trades.csv").read_bytes()).hexdigest(),top=table.head(5).to_dict("records"))
 (out/"summary.json").write_text(json.dumps(summary,indent=2))
 print(selected.to_string(index=False));print(pd.DataFrame(diag).to_string(index=False))
if __name__=="__main__":main()
