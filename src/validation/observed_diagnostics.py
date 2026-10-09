"""Post-freeze diagnostics; NEVER changes replica_config or primary selection."""
from pathlib import Path
import itertools,json
import pandas as pd
import numpy as np
import yaml
from src.validation.observed_study import load_inputs
from src.validation.observed_baseline import broker_replay,weights_from_hourly,match_events
def main():
    cfg=yaml.safe_load(Path("config.yaml").read_text())["observed_baseline_study"]
    cfg={**cfg,**cfg["broker"]};out,e,q,p,h=load_inputs(cfg)
    keys=["family","lookback","fast","scale","signal_delay_hours","vol_hours","clip","allocation","gross"]
    pool=pd.read_csv(out/"broker_training_trials.csv")[keys].drop_duplicates()
    qt=q[(q.ts_utc.dt.hour==1)&q.ts_utc.dt.minute.between(1,15)]
    pp=p.loc[p.index>=pd.Timestamp(cfg["start"])];rows=[]
    for i,r in pool.iterrows():
        c={**cfg,**r.to_dict(),"delay_minutes":5}
        wt=weights_from_hourly(h,c)
        for band in [0.,.01]:
            c["band"]=band;ev,path,_=broker_replay(pp,c,qt,wt)
            m=match_events(e,ev,cfg["match_seconds"],cfg["match_quantity_relative"])
            dates=e.date>=cfg["validation_first_date"];pm=ev.time_utc.dt.strftime("%Y-%m-%d")>=cfg["validation_first_date"]
            vm=match_events(e[dates],ev[pm],cfg["match_seconds"],cfg["match_quantity_relative"])
            rows.append({**r.to_dict(),"delay_minutes":5,"band":band,"all_matched":m["matched"],"all_recall":m["recall"],"all_precision":m["precision"],"all_f1":m["f1"],"validation_recall":vm["recall"],"validation_f1":vm["f1"]})
    table=pd.DataFrame(rows).sort_values(["all_matched","all_f1"],ascending=False)
    table.to_csv(out/"postfreeze_diagnostic_sweep.csv",index=False)
    # Daily NET holding directions, not order directions and not quantity matches.
    obs=pd.read_csv(out/"observed_daily_targets.csv").set_index("date")
    path=pd.read_csv(out/"broker_decision_equity.csv");path["date"]=pd.to_datetime(path.time_utc).dt.strftime("%Y-%m-%d")
    records=[]
    for date,row in obs.iterrows():
        pred=path[path.date==date].iloc[0]
        for asset in cfg["assets"]:
            o=float(row[asset+"USDT"]);v=float(pred[asset])
            records.append(dict(date=date,asset=asset,observed_signed_weight=o,predicted_net_quantity=v,direction_match=bool(np.sign(o)==np.sign(v))))
    pd.DataFrame(records).to_csv(out/"daily_net_direction_comparison.csv",index=False)
    (out/"diagnostic_summary.json").write_text(json.dumps({"postfreeze_trials":len(table),"optimistic_best_full_period_match":int(table.iloc[0].all_matched),
        "optimistic_best_full_period_recall":float(table.iloc[0].all_recall),"primary_selection_unchanged":True,
        "net_position_direction_correct":sum(r["direction_match"] for r in records),"net_position_direction_count":len(records),
        "warning":"optimistic post-freeze exploratory diagnostics, NOT validation or model selection"},indent=2))
    print((out/"diagnostic_summary.json").read_text())
if __name__=="__main__":main()
