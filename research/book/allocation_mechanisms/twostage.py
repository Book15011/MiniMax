"""Focused two-stage forecast-cap then risk-size mechanism screen."""
import itertools,json,sys
from pathlib import Path
import numpy as np,pandas as pd
from probe import portfolio_features,bounded_weights,CFG

def main():
 sys.path.insert(0,CFG["source_worktree"])
 from src.validation.observed_study import load_market
 out=Path(CFG["output"])
 q,p,h=load_market({"output":CFG["market_output"]})
 actual=pd.read_csv(Path(CFG["market_output"])/"observed_daily_targets.csv").set_index("date")
 cols=[a+"USDT" for a in CFG["assets"]];h=h[cols];obs=actual[cols].to_numpy();fit_n=int(CFG["fit_sessions"])
 times=[pd.Timestamp(d+"T01:00Z") for d in actual.index];records=[];weights={}
 factors=np.geomspace(*CFG["k_factor_grid"]);n=0
 for fast,slow in CFG["twostage"]["ema_pairs"]:
  for lag in CFG["lags"]:
   raw=portfolio_features(h,times,"ema",slow,lag,72,1.,"raw",fast)
   for vol_window in CFG["twostage"]["risk_windows"]:
    vol=np.stack([h.loc[:t-pd.Timedelta(hours=lag)].pct_change(fill_method=None).tail(vol_window).std().values for t in times])
    for forecast_clip,power in itertools.product(CFG["twostage"]["forecast_clips"],CFG["twostage"]["risk_powers"]):
     vec=np.clip(raw/forecast_clip,-1,1)/vol**power
     ks=factors/max(np.median(abs(vec[:fit_n])),1e-10)
     for cap in CFG["twostage"]["position_caps"]:
      w=bounded_weights(vec[None,:,:],ks[:,None,None],cap)
      err=np.abs(w[:,:fit_n]-obs[None,:fit_n]).mean(axis=(1,2));j=int(err.argmin())
      records.append(dict(candidate=n,fast=fast,lookback=slow,lag=lag,vol_window=vol_window,forecast_clip=forecast_clip,power=power,cap=cap,k=float(ks[j]),train_mae=float(err[j]),later_mae=float(np.abs(w[j,fit_n:]-obs[fit_n:]).mean()),train_sign=float((np.sign(w[j,:fit_n])==np.sign(obs[:fit_n])).mean()),later_sign=float((np.sign(w[j,fit_n:])==np.sign(obs[fit_n:])).mean())))
      weights[n]=w[j];n+=1
 table=pd.DataFrame(records).sort_values(["train_mae","candidate"]);table.to_csv(out/"twostage_trials.csv",index=False)
 table.head(CFG["twostage"]["shortlist"]).to_csv(out/"twostage_shortlist.csv",index=False)
 selected=[]
 for _,r in table.head(CFG["twostage"]["shortlist"]).iterrows():
  for d,w in zip(actual.index,weights[int(r.candidate)]):
   selected.append(dict(candidate=int(r.candidate),date=d,**dict(zip(cols,w))))
 pd.DataFrame(selected).to_csv(out/"twostage_weights.csv",index=False)
 print(table.head(CFG["twostage"]["shortlist"]).to_string(index=False))
if __name__=="__main__":main()
