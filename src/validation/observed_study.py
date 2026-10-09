"""Offline fit/validate CLI for a neutral observed five-asset baseline."""
from __future__ import annotations
import argparse,hashlib,itertools,json
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from src.validation.observed_baseline import ledger,closed_minutes,signal_vector,simulate,match_events

def load_market(cfg):
    out=Path(cfg["output"])
    q=pd.read_parquet(out/"quotes.parquet");q["ts_utc"]=pd.to_datetime(q.ts_utc,utc=True)
    a=pd.read_parquet(out/"archive_minutes.parquet")
    ap=a.pivot(index="timestamp",columns="symbol",values="close")
    qp=closed_minutes(q)
    p=qp.combine_first(ap).sort_index()
    h=pd.read_parquet(out/"warmup_hourly.parquet")
    h=p.resample("h",closed="right",label="right").last().combine_first(h)
    return q,p,h

def load_inputs(cfg):
    out=Path(cfg["output"]);e=pd.read_csv(cfg["input"])
    e["time_utc"]=[pd.Timestamp(r.date+" "+r.time,tz="Asia/Hong_Kong").tz_convert("UTC") if isinstance(r.time,str) else pd.NaT for _,r in e.iterrows()]
    q,p,h=load_market(cfg)
    return out,e,q,p,h

def observed_targets(e,states,assets):
    records=[]
    for date,g in e.groupby("date",sort=True):
        i=g.index[-1];state=states[i];marks={}
        for a in assets:
            known=e.loc[:i];known=known[known.asset==a]
            marks[a]=float(known.iloc[-1].price_usd)
        eq=state["cash"]+sum((state["long"].get(a,0)-state["short"].get(a,0))*marks[a] for a in assets)
        w={a+"USDT":(state["long"].get(a,0)-state["short"].get(a,0))*marks[a]/eq for a in assets}
        records.append({"date":date,"equity":eq,"gross_ratio":state["gross"]/eq,**w})
    return pd.DataFrame(records).set_index("date")

def candidates(cfg,h,dates):
    search=cfg["search"];ranked=[];vectors={}
    specs=[]
    for family in search["families"]:
        pairs=search["ema_pairs"] if family=="ema" else [(0,lb) for lb in search["lookbacks"]]
        for fast,lb in pairs:
            for scale,lag in itertools.product(search["scales"],search["signal_delay_hours"]):
                base=dict(family=family,lookback=lb,fast=fast,scale=scale,signal_delay_hours=lag,vol_hours=search["vol_hours"])
                arr=np.stack([signal_vector(h,pd.Timestamp(d+"T01:00Z")-pd.Timedelta(hours=lag),base).to_numpy() for d in dates])
                key=json.dumps(base,sort_keys=True);vectors[key]=arr;specs.append((base,arr))
    return specs

def score_parts(e,events,cfg):
    cut=cfg["train_last_date"];vfirst=cfg["validation_first_date"]
    masks=[("all",e.index==e.index,events.index==events.index),
           ("training",e.date<=cut,events.time_utc.dt.strftime("%Y-%m-%d")<=cut),
           ("validation",e.date>=vfirst,events.time_utc.dt.strftime("%Y-%m-%d")>=vfirst)]
    output={}
    for name,om,pm in masks:
        o=e.loc[om];p=events.loc[pm]
        output[name]=match_events(o,p,cfg["match_seconds"],cfg["match_quantity_relative"])
        output[name]["direction_only"]=match_events(o,p,cfg["match_seconds"],cfg["match_quantity_relative"],False)
    return output

def run(cfg):
    out,e,q,p,h=load_inputs(cfg)
    states=ledger(e,cfg["seed"],cfg["fee"]);assets=cfg["assets"]
    targets=observed_targets(e,states,assets);targets.to_csv(out/"observed_daily_targets.csv")
    problems=[]
    for i,r in e.iterrows():
        st=states[i];a=r.asset
        for col,actual in [("long_position_after",st["long"].get(a,0)),("short_position_after",st["short"].get(a,0)),
                           ("net_position_after",st["long"].get(a,0)-st["short"].get(a,0)),
                           ("cumulative_fifo_gross_realized_pnl_usd",st["gross_realized"])]:
            if abs(actual-float(r[col]))>1e-6:problems.append({"trade":r.trade_id,"field":col,"computed":actual,"input":float(r[col])})
    audit=dict(accounting_convention="synthetic signed cash and FIFO lots; cash is NOT Roostoo free USD",
               fee_assumption="all taker 0.1%; spot order type is missing, maker-fee scenario can avoid initial deficit",
               small_close_note="sub-$1 partial short covers are supported by documented close_qty; not proven violations",
               trades=len(e),assets=assets,decision_dates=int(e.date.nunique()),missing_time=e.loc[e.time_utc.isna(),"trade_id"].tolist(),
               violations=[dict(trade_id=e.iloc[i].trade_id,cash=s["cash"],gross=s["gross"],equity=s["equity_at_marks"])
                           for i,s in enumerate(states) if s["cash_negative"] or s["gross_exceeds_equity"]],
               below_min_order=e.loc[e.quantity*e.price_usd<cfg["min_order"],["trade_id","quantity","price_usd"]].to_dict("records"),
               input_consistency_errors=problems,final=states[-1],user_confirmed_timezone="HKT",user_confirmed_complete=True)
    (out/"ledger_audit.json").write_text(json.dumps(audit,indent=2))
    pd.DataFrame([{**{k:v for k,v in st.items() if k not in ("long","short")},"trade_id":e.iloc[i].trade_id} for i,st in enumerate(states)]).to_csv(out/"observed_ledger.csv",index=False)
    # Only fitting dates enter search/selection; validation is evaluated later.
    dates=[d for d in targets.index if d<=cfg["train_last_date"] and d>str(pd.Timestamp(cfg["first_decision"]).date())]
    actual=targets.loc[dates,[a+"USDT" for a in assets]].to_numpy()
    ranked=[];trial=0
    for base,vec in candidates(cfg,h,dates):
        for clip,allocation,gross in itertools.product(cfg["search"]["clips"][base["scale"]],cfg["search"]["allocations"],cfg["search"]["gross"]):
            s=np.clip(vec/clip,-1,1);tot=np.abs(s).sum(axis=1,keepdims=True)
            denom=np.maximum(tot,1) if allocation=="bounded" else np.maximum(tot,1e-15)
            w=s/denom*gross;err=float(np.abs(w-actual).mean())
            direction=float((np.sign(w)==np.sign(actual)).mean())
            trial+=1
            ranked.append(dict(candidate=trial,target_mae=err,direction_accuracy=direction,
                               **base,clip=clip,allocation=allocation,gross=gross))
    table=pd.DataFrame(ranked).sort_values(["target_mae","candidate"])
    table.to_csv(out/"target_search.csv",index=False)
    table=table.drop_duplicates(["family","lookback","fast","scale","signal_delay_hours","clip","allocation","gross"]).head(cfg["search"]["shortlist"])
    best=None;trials=[]
    # Training execution rows only; exclude validation prices from the selection simulation.
    training_cfg={**cfg,"end":cfg["train_last_date"]+"T01:15:00Z"}
    masks=(p.index>=pd.Timestamp(cfg["start"]))&(p.index<=pd.Timestamp(cfg["end"]))
    # Keep all minutes for the final path; simulator marks only at its decision/execution dates.
    execution=p.loc[masks]
    trainobs=e[e.date<=cfg["train_last_date"]]
    for _,r in table.iterrows():
        params={k:(v.item() if hasattr(v,"item") else v) for k,v in r.to_dict().items() if k not in ("target_mae","direction_accuracy","candidate")}
        wt={}
        for d in pd.date_range(pd.Timestamp(cfg["first_decision"]).normalize(),pd.Timestamp(training_cfg["end"]).normalize()):
            t=d+pd.Timedelta(hours=cfg["decision_hour"])
            v=signal_vector(h,t-pd.Timedelta(hours=params["signal_delay_hours"]),params)
            v=(v/params["clip"]).clip(-1,1);tot=v.abs().sum()
            denom=max(1,tot) if params["allocation"]=="bounded" else max(1e-15,tot)
            wt[t]=v/denom*params["gross"]
        for delay,band in itertools.product(cfg["search"]["delays_minutes"],cfg["search"]["bands"]):
            param={**training_cfg,**params,"delay_minutes":int(delay),"band":float(band)}
            events,path=simulate(execution,param,q,wt)
            m=match_events(trainobs,events,cfg["match_seconds"],cfg["match_quantity_relative"])
            dm=match_events(trainobs,events,cfg["match_seconds"],cfg["match_quantity_relative"],False)
            row=dict(candidate=int(r.candidate),delay_minutes=int(delay),band=float(band),strict_f1=m["f1"],
                     strict_recall=m["recall"],strict_precision=m["precision"],matched=m["matched"],
                     direction_f1=dm["f1"],target_mae=float(r.target_mae))
            trials.append(row)
            # Strict quantity/time match is primary; no validation results enter this ordering.
            key=(m["f1"],dm["f1"],-float(r.target_mae),-int(delay),-float(band),-int(r.candidate))
            if best is None or key>best[0]:best=(key,{**cfg,**params,"delay_minutes":int(delay),"band":float(band)},row)
    pd.DataFrame(trials).sort_values(["strict_f1","direction_f1","target_mae"],ascending=[False,False,True]).to_csv(out/"training_trials.csv",index=False)
    chosen=best[1]
    (out/"selected_config.yaml").write_text(yaml.safe_dump(chosen,sort_keys=True))
    frozen_hash=hashlib.sha256((out/"selected_config.yaml").read_bytes()).hexdigest()
    # Freeze before evaluating validation.
    (out/"selection_freeze.json").write_text(json.dumps({"config_sha256":frozen_hash,"target_candidates":trial,"execution_trials":len(trials),"selection":best[2]},indent=2))
    wt={}
    for d in pd.date_range(pd.Timestamp(cfg["first_decision"]).normalize(),pd.Timestamp(cfg["end"]).normalize()):
        t=d+pd.Timedelta(hours=cfg["decision_hour"])
        v=signal_vector(h,t-pd.Timedelta(hours=chosen["signal_delay_hours"]),chosen)
        v=(v/chosen["clip"]).clip(-1,1);tot=v.abs().sum()
        denom=max(1,tot) if chosen["allocation"]=="bounded" else max(1e-15,tot)
        wt[t]=v/denom*chosen["gross"]
    events,path=simulate(execution,chosen,q,wt)
    events.to_csv(out/"replica_events.csv",index=False);path.to_csv(out/"replica_decision_equity.csv",index=False)
    metrics=score_parts(e,events,cfg)
    metrics["selection"]={"params":{k:chosen[k] for k in ["family","lookback","fast","scale","clip","allocation","gross","signal_delay_hours","delay_minutes","band"]},
                          "config_sha256":frozen_hash,"target_candidates":trial,"execution_trials":len(trials)}
    metrics["pass_85"]=all(metrics["validation"][k]>=cfg["target_agreement"] for k in ("precision","recall","f1"))
    metrics["gross_return_to_last_mark"]=float(path.iloc[-1].equity/cfg["seed"]-1)
    metrics["source_counts"]=events.source.value_counts().to_dict()
    metrics["label"]="retrospective blocked validation; not prospective"
    (out/"replication_metrics.json").write_text(json.dumps(metrics,indent=2))
    # Per-event evidence and same-day holdings make failures inspectable.
    assignments={x["observed_index"]:x["predicted_index"] for x in metrics["all"]["pairs"]}
    compare=[]
    for i,o in e.iterrows():
        j=assignments.get(i);r=events.iloc[j] if j is not None else None
        compare.append(dict(trade_id=o.trade_id,date=o.date,asset=o.asset,action=o.action,observed_time=str(o.time_utc),
                            observed_quantity=o.quantity,matched=j is not None,predicted_time=str(r.time_utc) if r is not None else "",
                            predicted_quantity=r.quantity if r is not None else None))
    pd.DataFrame(compare).to_csv(out/"event_comparison.csv",index=False)
    predtargets=pd.DataFrame([{ "date":str(t.date()),**{s:float(v) for s,v in w.items()}} for t,w in wt.items()])
    predtargets.to_csv(out/"replica_daily_targets.csv",index=False)
    print(json.dumps({k:metrics[k] for k in ("selection","all","training","validation","pass_85","gross_return_to_last_mark")},indent=2))

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--config",default="config.yaml");ap.add_argument("--run-selected",action="store_true")
    a=ap.parse_args()
    if a.run_selected:
        cfg=yaml.safe_load(Path(a.config).read_text())
        out,e,q,p,h=load_inputs(cfg);wt={}
        for d in pd.date_range(pd.Timestamp(cfg["first_decision"]).normalize(),pd.Timestamp(cfg["end"]).normalize()):
            t=d+pd.Timedelta(hours=cfg["decision_hour"]);v=signal_vector(h,t-pd.Timedelta(hours=cfg["signal_delay_hours"]),cfg)
            s=(v/cfg["clip"]).clip(-1,1);tot=s.abs().sum()
            wt[t]=s/(max(1,tot) if cfg["allocation"]=="bounded" else max(1e-15,tot))*cfg["gross"]
        ev,path=simulate(p.loc[p.index>=pd.Timestamp(cfg["start"])],cfg,q,wt)
        ev.to_csv(out/"rerun_replica_events.csv",index=False)
        print(json.dumps(score_parts(e,ev,cfg),indent=2))
    else:run(yaml.safe_load(Path(a.config).read_text())["observed_baseline_study"])
if __name__=="__main__":main()
