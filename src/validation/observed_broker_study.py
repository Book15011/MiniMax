"""Select a collateral-faithful offline replica on fitting dates, freeze, then audit."""
from pathlib import Path
import argparse,hashlib,itertools,json
import numpy as np
import pandas as pd
import yaml
from src.validation.observed_study import load_inputs,score_parts
from src.validation.observed_baseline import broker_replay,weights_from_hourly,match_events

def select(cfg,out,e,q,p,h):
    coarse=pd.read_csv(out/"target_search.csv").head(cfg["search"]["shortlist"])
    refined=pd.read_csv(out/"refine_target_search.csv").head(cfg["refine"]["shortlist"])
    keys=["family","lookback","fast","scale","signal_delay_hours","vol_hours","clip","allocation","gross"]
    pool=pd.concat([coarse[keys],refined[keys]],ignore_index=True).drop_duplicates()
    q=q[(q.ts_utc.dt.hour==1)&q.ts_utc.dt.minute.between(1,15)]
    train={**cfg,**cfg["broker"],"end":cfg["train_last_date"]+"T01:15Z"}
    ph=p.loc[(p.index>=pd.Timestamp(train["start"]))&(p.index<=pd.Timestamp(train["end"]))]
    th=h.loc[h.index<=pd.Timestamp(train["end"])]
    obs=e[e.date<=cfg["train_last_date"]];best=None;trials=[]
    for i,r in pool.iterrows():
        pars={k:(v.item() if hasattr(v,"item") else v) for k,v in r.to_dict().items()}
        c={**train,**pars};wt=weights_from_hourly(th,c)
        for delay,band in itertools.product(cfg["search"]["delays_minutes"],cfg["search"]["bands"]):
            c={**train,**pars,"delay_minutes":int(delay),"band":float(band)}
            ev,path,_=broker_replay(ph,c,q,wt)
            m=match_events(obs,ev,cfg["match_seconds"],cfg["match_quantity_relative"])
            dm=match_events(obs,ev,cfg["match_seconds"],cfg["match_quantity_relative"],False)
            row={**pars,"delay_minutes":int(delay),"band":float(band),"matched":m["matched"],"precision":m["precision"],"recall":m["recall"],"f1":m["f1"],"direction_f1":dm["f1"]}
            trials.append(row)
            key=(m["f1"],dm["f1"],-int(delay),-float(band),-int(i))
            if best is None or key>best[0]:best=(key,c,row)
    pd.DataFrame(trials).sort_values(["f1","direction_f1"],ascending=False).to_csv(out/"broker_training_trials.csv",index=False)
    selected={**best[1],"end":cfg["end"]}
    (out/"replica_config.yaml").write_text(yaml.safe_dump(selected,sort_keys=True))
    freeze=dict(selection=best[2],candidate_pool=len(pool),execution_trials=len(trials),config_sha256=hashlib.sha256((out/"replica_config.yaml").read_bytes()).hexdigest(),
                label="broker v2 corrected retrospective study; selected by Oct5-7 only")
    (out/"broker_selection_freeze.json").write_text(json.dumps(freeze,indent=2))
    return selected

def evaluate(cfg,out,e,q,p,h,label="broker"):
    wt=weights_from_hourly(h,cfg)
    ev,path,decisions=broker_replay(p.loc[p.index>=pd.Timestamp(cfg["start"])],cfg,q,wt)
    ev.to_csv(out/(label+"_events.csv"),index=False);path.to_csv(out/(label+"_decision_equity.csv"),index=False)
    (out/(label+"_decisions.json")).write_text(json.dumps(decisions,indent=2))
    metrics=score_parts(e,ev,cfg);metrics["pass_85"]=all(metrics["validation"][k]>=cfg["target_agreement"] for k in ("precision","recall","f1"))
    metrics["return_to_0115_utc"]=float(path.iloc[-1].equity/cfg["seed"]-1)
    metrics["maximum_recorded_gross_ratio"]=float((path.gross/path.equity).max())
    metrics["minimum_free_cash"]=float(path.cash.min());metrics["source_counts"]=ev.source.value_counts().to_dict()
    metrics["fees"]=float(ev.fee.sum())
    metrics["primary_warning"]="retrospective blocked validation, five dates, hidden strategy not identified"
    # Show same-session action agreement independently of exact timing, without changing primary thresholds.
    sessions=[]
    for date,g in e.groupby("date"):
        pr=ev[ev.time_utc.dt.strftime("%Y-%m-%d")==date]
        strict=match_events(g,pr,cfg["match_seconds"],cfg["match_quantity_relative"])
        daily=match_events(g,pr,3600,cfg["match_quantity_relative"],False)
        qty=match_events(g,pr,3600,cfg["match_quantity_relative"])
        sessions.append(dict(date=date,observed=len(g),predicted=len(pr),strict_matched=strict["matched"],same_session_action_matched=daily["matched"],same_session_quantity_matched=qty["matched"]))
    pd.DataFrame(sessions).to_csv(out/(label+"_session_comparison.csv"),index=False)
    (out/(label+"_metrics.json")).write_text(json.dumps(metrics,indent=2))
    assigned={x["observed_index"]:x["predicted_index"] for x in metrics["all"]["pairs"]}
    comparison=[]
    for i,o in e.iterrows():
        j=assigned.get(i);r=ev.iloc[j] if j is not None else None
        comparison.append(dict(trade_id=o.trade_id,date=o.date,asset=o.asset,action=o.action,observed_time=str(o.time_utc),
                               observed_quantity=o.quantity,strict_match=j is not None,
                               predicted_time=str(r.time_utc) if r is not None else "",predicted_quantity=r.quantity if r is not None else None))
    pd.DataFrame(comparison).to_csv(out/(label+"_event_comparison.csv"),index=False)
    print(json.dumps({k:{x:v for x,v in metrics[k].items() if x!="pairs" and x!="direction_only"} for k in ["all","training","validation"]}|{k:metrics[k] for k in ["pass_85","return_to_0115_utc","maximum_recorded_gross_ratio","minimum_free_cash"]},indent=2))

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--config",default="config.yaml");ap.add_argument("--evaluate-only",action="store_true");a=ap.parse_args()
    cfg=yaml.safe_load(Path(a.config).read_text())
    if not a.evaluate_only:cfg=cfg["observed_baseline_study"]
    out,e,q,p,h=load_inputs(cfg)
    if not a.evaluate_only:cfg=select(cfg,out,e,q,p,h)
    evaluate(cfg,out,e,q,p,h)
if __name__=="__main__":main()
