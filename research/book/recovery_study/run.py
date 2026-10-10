"""Paired research comparison. Immutable baseline and finite family; no optimizer."""
from __future__ import annotations
import copy, hashlib, json, subprocess, logging
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
from src.config import load_config
from src.models import get
from backtest.data import load_market
from backtest.scoring.evaluate import simulate
from backtest.scoring.windows import pool_starts
from backtest.scoring.metrics import window_metrics, day_points

ROOT=Path(__file__).resolve().parents[3]
MAIN=ROOT.parents[1]
OUT=MAIN/"results/book/20261011-recovery-study-v1"
BASE="book_e20combo_brk_cash"
NAMES=[BASE,"book_recovery_vol","book_recovery_short","book_recovery_both"]
HORIZONS=[168,192,216,228,240,336]
def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,default=str,allow_nan=False))
def hashes():
    tracked=subprocess.check_output(["git","ls-files"],cwd=ROOT,text=True).splitlines()
    paths=[ROOT/p for p in tracked if p.endswith((".py",".yaml")) or "recovery_study" in p]
    paths+=list((MAIN/"data/validation").glob("*.parquet"))
    paths+=[MAIN/"results/book/20261009-weak-eval-v2/cases.parquet"]
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
def job(args):
    name,scenario=args
    cfg=load_config()
    if scenario=="double_cost":
        cfg=copy.deepcopy(cfg)
        cfg["harness"]["fees"]={k:v*2 for k,v in cfg["harness"]["fees"].items()}
        cfg["scoring"]["liquidation_cost"]*=2
    if scenario=="extra_lag":
        cfg=copy.deepcopy(cfg);cfg["harness"]["execution_lag_hours"]+=1
    mk=load_market(cfg)
    if scenario=="double_cost": mk.half_spread*=2
    starts=pool_starts(mk,cfg)
    logging.basicConfig(level=logging.WARNING)
    run=simulate(get(name),mk,cfg,starts,use_cache=True)
    sel=run.windows.index.get_indexer(starts)
    E,G=run.equity[sel],run.gross[sel]
    records=[]
    for h in HORIZONS:
        R=E[:,h]/E[:,0]*(1-cfg["scoring"]["liquidation_cost"]*G[:,h])-1
        DD=(E[:,:h+1]/np.maximum.accumulate(E[:,:h+1],axis=1)-1).min(axis=1)
        pts=day_points(starts[0],h,16)
        CS=window_metrics(E[:,:h+1],G[:,h],cfg["scoring"],points=pts)["FLOORED.V1.composite"].to_numpy()
        records += [{"start":t,"hours":h,"return":float(a),"mdd":float(b),"cs":float(c)} for t,a,b,c in zip(starts,R,DD,CS)]
    frame=pd.DataFrame(records)
    frame.to_parquet(OUT/f"{name}.{scenario}.parquet",index=False)
    meta={"model":name,"scenario":scenario,"run_key":run.key,"windows":len(starts),"notes":mk.notes,
          "max_gross":float(G.max()),"fee":cfg["harness"]["fees"],"lag":cfg["harness"]["execution_lag_hours"],
          "liquidation_cost":cfg["scoring"]["liquidation_cost"],"actual_account":False}
    dump(f"{name}.{scenario}.json",meta)
    print("DONE",name,scenario,run.key,flush=True)
    return meta
def ci_quarters(frame):
    # Purged clusters: a window whose outcome crosses the quarter boundary is removed.
    t=pd.DatetimeIndex(frame.start)
    end=t.tz_localize(None).to_period("Q").end_time.tz_localize("UTC")
    f=frame.loc[(t+pd.Timedelta(hours=336))<=end].copy()
    f["quarter"]=pd.DatetimeIndex(f.start).tz_localize(None).to_period("Q").astype(str)
    g=f.groupby("quarter")["delta"].agg(["sum","count"])
    rng=np.random.default_rng(20261011)
    draw=rng.integers(0,len(g),size=(20000,len(g)))
    boot=g["sum"].to_numpy()[draw].sum(1)/g["count"].to_numpy()[draw].sum(1)
    # simultaneous one-sided family bound, 3 predeclared candidates.
    return {"lower":float(np.quantile(boot,.05/3)),"upper":float(np.quantile(boot,1-.05/3)),
            "n_quarters":len(g),"n_purged_windows":len(f),"project_wide_post_selection_control":False}
def summarize(scenario="base"):
    files={n:pd.read_parquet(OUT/f"{n}.{scenario}.parquet") for n in NAMES if (OUT/f"{n}.{scenario}.parquet").exists()}
    base=files[BASE]
    cases=pd.read_parquet(MAIN/"results/book/20261009-weak-eval-v2/cases.parquet")
    rows=[]; decisions={}
    for n,f in files.items():
        context={}
        for h in HORIZONS:
            a=f[f.hours==h].set_index("start");b=base[base.hours==h].set_index("start")
            for label,ix in [("all",a.index),("recent_2024on",a.index[a.index>=pd.Timestamp("2024-01-01",tz="UTC")]),
                             ("weak_archived",cases.index[cases.weak_archived.astype(bool)]),
                             ("weak_fresh_btc",cases.index[cases.weak_fresh_btc.astype(bool)])]:
                aa=a.loc[ix];bb=b.loc[ix];d=aa["return"]-bb["return"]
                row={"model":n,"scenario":scenario,"context":label,"hours":h,"n":len(aa),
                     "mean":float(aa["return"].mean()),"median":float(aa["return"].median()),
                     "p10":float(aa["return"].quantile(.1)),"worst":float(aa["return"].min()),
                     "positive":float((aa["return"]>0).mean()),"mean_mdd":float(-aa.mdd.mean()),
                     "worst_mdd":float(-aa.mdd.min()),"cs_mean":float(aa.cs.mean()),
                     "mean_delta":float(d.mean()),"median_delta":float(aa["return"].median()-bb["return"].median()),
                     "p10_delta":float(aa["return"].quantile(.1)-bb["return"].quantile(.1)),
                     "mean_mdd_delta":float(bb.mdd.mean()-aa.mdd.mean()),
                     "worst_mdd_delta":float(bb.mdd.min()-aa.mdd.min())}
                rows.append(row);context[(label,h)]=row
        if n==BASE: continue
        x=context["all",336]
        paired=f[f.hours==336][["start","return"]].merge(base[base.hours==336][["start","return"]],on="start",suffixes=("_new","_base"))
        paired["delta"]=paired.return_new-paired.return_base
        bound=ci_quarters(paired)
        gates={"full_mean":x["mean_delta"]>=-1e-12,"full_median":x["median_delta"]>=-1e-12,
               "full_p10":x["p10_delta"]>=-1e-12,"mean_mdd":x["mean_mdd_delta"]<=1e-12,
               "worst_mdd":x["worst_mdd_delta"]<=1e-12,"quarter_lower_positive":bound["lower"]>0,
               "recent_mean":context["recent_2024on",336]["mean_delta"]>=-1e-12,
               "weak_six_means":all(context[p,h]["mean_delta"]>=-1e-12 for p in ["weak_archived","weak_fresh_btc"] for h in [216,228,240]),
               "current_horizon_means_p10":all(context[p,h]["mean_delta"]>=-1e-12 and context[p,h]["p10_delta"]>=-1e-12 for p in ["weak_archived","weak_fresh_btc"] for h in [168,192])}
        decisions[n]={"gates":gates,"historical_gate_pass":all(gates.values()),"paired_quarter_bound":bound,
                      "production_eligible":False,"actual_switch_validated":False,"fresh_forward_evidence":False}
    pd.DataFrame(rows).to_csv(OUT/f"comparison.{scenario}.csv",index=False)
    dump(f"decision.{scenario}.json",decisions)
    return decisions
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    before=hashes();dump("inputs_before.json",before)
    dump("run_source.json",{"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
         "protocol_sha256":hashlib.sha256((ROOT/"research/book/recovery_study/PROTOCOL.md").read_bytes()).hexdigest(),
         "new_hypotheses":3,"baseline":BASE})
    with ProcessPoolExecutor(max_workers=3) as pool: list(pool.map(job,[(n,"base") for n in NAMES]))
    decisions=summarize()
    passing=[n for n,d in decisions.items() if d["historical_gate_pass"]]
    # Stress only passes; preserve the finite search stopping rule.
    if passing:
        for sc in ["double_cost","extra_lag"]:
            with ProcessPoolExecutor(max_workers=3) as pool: list(pool.map(job,[(n,sc) for n in [BASE]+passing]))
            summarize(sc)
    after=hashes();dump("inputs_after.json",after)
    assert before==after,"source or input changed during study"
    dump("complete.json",{"status":"PASS","historical_gate_pass":passing,"input_hashes_unchanged":True,
                           "actual_holdings_verified":False,"production_eligible":False,
                           "prospective_start":"2026-10-11 00:00 UTC","prospective_end":"2026-10-14 00:00 UTC"})
if __name__=="__main__":main()
