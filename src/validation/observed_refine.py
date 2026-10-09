"""Training-only local refinement of EMA family; never loads validation dates."""
from pathlib import Path
import json,itertools
import numpy as np
import pandas as pd
import yaml
from src.validation.observed_study import load_inputs
from src.validation.observed_baseline import signal_vector,simulate,match_events
def main():
    cfg=yaml.safe_load(Path("config.yaml").read_text())["observed_baseline_study"]
    out,e,q,p,h=load_inputs(cfg);dates=["2026-10-06","2026-10-07"]
    cut=pd.Timestamp("2026-10-07T01:00Z");h=h.loc[h.index<=cut]
    actual=pd.read_csv(out/"observed_daily_targets.csv").set_index("date").loc[dates,[a+"USDT" for a in cfg["assets"]]].to_numpy()
    records=[];N=cfg["refine"];clips=np.geomspace(N["clip_min"],N["clip_max"],N["clip_count"])
    # Precompute all EMA histories once. Only three fitting decisions are present.
    emas={span:h.ewm(span=int(span),adjust=False).mean() for span in range(1,N["slow_max"]+1)}
    for fast,slow,lag in itertools.product(range(N["fast_min"],N["fast_max"]+1),range(N["slow_min"],N["slow_max"]+1),N["signal_delay_hours"]):
        if slow<=fast:continue
        times=[pd.Timestamp(d+"T01:00Z")-pd.Timedelta(hours=lag) for d in dates]
        sig=np.stack([(emas[fast].loc[t]/emas[slow].loc[t]-1).to_numpy() for t in times])
        for scale in N["scales"]:
            v=sig.copy()
            if scale!="raw":
                vol=np.stack([h.loc[:t].pct_change(fill_method=None).tail(cfg["search"]["vol_hours"]).std().to_numpy() for t in times])
                v=v/vol**(1 if scale=="vol" else 2)
            for allocation in cfg["search"]["allocations"]:
                z=np.clip(v[None,:,:]/clips[:,None,None],-1,1);tot=np.abs(z).sum(axis=2,keepdims=True)
                div=np.maximum(tot,1) if allocation=="bounded" else np.maximum(tot,1e-15)
                base=z/div
                gross=np.clip((base*actual).sum(axis=(1,2))/(base*base).sum(axis=(1,2)),N["gross_min"],N["gross_max"])
                err=np.abs(base*gross[:,None,None]-actual).mean(axis=(1,2))
                j=int(np.argmin(err))
                records.append(dict(target_mae=float(err[j]),family="ema",fast=fast,lookback=slow,scale=scale,
                                    signal_delay_hours=lag,vol_hours=cfg["search"]["vol_hours"],allocation=allocation,
                                    clip=float(clips[j]),gross=float(gross[j])))
    table=pd.DataFrame(records).sort_values("target_mae");table.to_csv(out/"refine_target_search.csv",index=False)
    # Execute only the predeclared best few target fits on training.
    obs=e[e.date<=cfg["train_last_date"]];execp=p.loc[(p.index>=pd.Timestamp(cfg["start"]))&(p.index<=pd.Timestamp("2026-10-07T01:15Z"))]
    execq=q[(q.ts_utc.dt.hour==1)&q.ts_utc.dt.minute.between(1,9)]
    best=None;trials=[]
    for i,r in table.head(N["shortlist"]).iterrows():
        pars={k:(x.item() if hasattr(x,"item") else x) for k,x in r.to_dict().items() if k!="target_mae"}
        wt={}
        for d in pd.date_range("2026-10-05","2026-10-07",tz="UTC"):
            t=d+pd.Timedelta(hours=1);s=signal_vector(h,t-pd.Timedelta(hours=pars["signal_delay_hours"]),pars)
            s=(s/pars["clip"]).clip(-1,1);total=s.abs().sum()
            wt[t]=s/(max(1,total) if pars["allocation"]=="bounded" else max(1e-15,total))*pars["gross"]
        for delay,band in itertools.product(cfg["search"]["delays_minutes"],cfg["search"]["bands"]):
            c={**cfg,**pars,"end":"2026-10-07T01:15Z","delay_minutes":int(delay),"band":float(band)}
            ev,path=simulate(execp,c,execq,wt);m=match_events(obs,ev,cfg["match_seconds"],cfg["match_quantity_relative"])
            dm=match_events(obs,ev,cfg["match_seconds"],cfg["match_quantity_relative"],False)
            row={**pars,"delay_minutes":delay,"band":band,"strict_f1":m["f1"],"direction_f1":dm["f1"],"matched":m["matched"],"target_mae":float(r.target_mae)}
            trials.append(row);key=(m["f1"],dm["f1"],-float(r.target_mae),-int(delay),-float(band))
            if best is None or key>best[0]:best=(key,{**cfg,**pars,"delay_minutes":int(delay),"band":float(band)},row)
    pd.DataFrame(trials).to_csv(out/"refine_training_trials.csv",index=False)
    # This file is fitted exclusively to Oct5-7; validation must be a separate call.
    (out/"refined_config.yaml").write_text(yaml.safe_dump(best[1],sort_keys=True))
    (out/"refinement_freeze.json").write_text(json.dumps({"selection":best[2],"target_trials":len(records),"execution_trials":len(trials),"clip_candidates_per_trial":len(clips),"sha256":__import__("hashlib").sha256((out/"refined_config.yaml").read_bytes()).hexdigest()},indent=2))
    print(json.dumps(best[2],indent=2))
if __name__=="__main__":main()
