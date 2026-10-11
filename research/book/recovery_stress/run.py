"""Explicit user-requested stress extension; earlier failed gates are a permanent veto."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import copy,hashlib,json,subprocess,logging,traceback
import numpy as np
import pandas as pd
from src.config import load_config,resolve
from src.models import get
from backtest.data import load_market
from backtest.scoring.windows import pool_starts
from backtest.scoring.evaluate import simulate,run_key
from backtest.scoring.metrics import window_metrics,day_points
from research.book.recovery_stress.metrics import outcome,paired_stability
from research.book.recovery_study import run as inherited

ROOT=Path(__file__).resolve().parents[3]
MAIN=ROOT.parents[1]
OUT=MAIN/"results/book/20261011-recovery-stress-v1"
ORIGINAL=MAIN/"results/book/20261011-rebound-recovery-v1"
BASE="book_e20combo_brk_cash"
NAMES=[BASE,"book_recovery_allshort24","book_recovery_rebound"]
SCENARIOS=["base","double_cost","extra_lag","combined"]
HORIZONS=[120,144,168,192,216,228,240,336]
FROZEN_WTS=["book-book-recovery-study","book-book-high-recovery","book-book-rebound-recovery","pol-live-brk"]
def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False,default=str))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprint():
    out={}
    for wtname in FROZEN_WTS+["book-book-recovery-stress"]:
        wt=MAIN/".worktrees"/wtname
        names=subprocess.check_output(["git","ls-files"],cwd=wt,text=True).splitlines()
        out[wtname]={"head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=wt,text=True).strip(),
                    "status":subprocess.check_output(["git","status","--porcelain"],cwd=wt,text=True),
                    "files":{rel:sha(wt/rel) for rel in names if rel.endswith((".py",".yaml",".json",".md"))}}
    paths=list((MAIN/"data/validation").glob("*.parquet"))
    paths += [MAIN/"results/book/20261009-weak-eval-v2/cases.parquet",
              MAIN/"results/book/20261011-recovery-current-context-v1/btc_only_cases.csv"]
    # Also hash the exact market spread snapshot selected by the unchanged loader.
    paths += list((MAIN/"data").rglob("ticker_20260928T174533Z.json"))
    paths += [p for p in ORIGINAL.iterdir() if p.suffix in [".parquet",".json",".csv"]]
    out["inputs"]={str(p):sha(p) for p in paths if p.is_file()}
    out["main_head"]=subprocess.check_output(["git","rev-parse","main"],cwd=MAIN,text=True).strip()
    return out
def config(scenario):
    cfg=copy.deepcopy(load_config())
    if scenario in ["double_cost","combined"]:
        cfg["harness"]["fees"]={k:v*2 for k,v in cfg["harness"]["fees"].items()}
        cfg["scoring"]["liquidation_cost"]*=2
    if scenario in ["extra_lag","combined"]: cfg["harness"]["execution_lag_hours"]+=1
    if scenario!="base": cfg["scoring"]["cache_dir"]=str(OUT/"cache")
    return cfg
def job(pair):
    name,scenario=pair
    logging.basicConfig(level=logging.WARNING)
    cfg=config(scenario);mk=load_market(cfg)
    if scenario in ["double_cost","combined"]: mk.half_spread*=2
    starts=pool_starts(mk,cfg);model=get(name)
    key=run_key(model,cfg["models"].get(name,{}) or {},False,starts,cfg,mk)
    cdir=resolve(cfg["scoring"]["cache_dir"])/name
    if scenario=="base":
        expected=json.loads((ORIGINAL/f"{name}.base.json").read_text())["run_key"]
        assert key==expected and (cdir/f"{key}.json").is_file(),"frozen base cache missing or changed"
    run=simulate(model,mk,cfg,starts,use_cache=True)
    sel=run.windows.index.get_indexer(starts)
    assert (sel>=0).all()
    E,G=run.equity[sel],run.gross[sel]
    rows=[]
    for h in HORIZONS:
        ret,dd=outcome(E,G,h,cfg["scoring"]["liquidation_cost"])
        cs=window_metrics(E[:,:h+1],G[:,h],cfg["scoring"],points=day_points(starts[0],h,16))["FLOORED.V1.composite"].to_numpy()
        rows.extend({"start":t,"hours":h,"return":float(r),"mdd":float(d),"cs":float(c)} for t,r,d,c in zip(starts,ret,dd,cs))
    pd.DataFrame(rows).to_parquet(OUT/f"{name}.{scenario}.parquet",index=False)
    meta={"model":name,"scenario":scenario,"run_key":key,"windows":len(starts),
          "cache_dir":str(cdir),"fees":cfg["harness"]["fees"],"lag":cfg["harness"]["execution_lag_hours"],
          "liquidation_cost":cfg["scoring"]["liquidation_cost"],"notes":mk.notes,
          "marked_gross_max":float(G.max()),"marked_gross_above_one_window_hours":int((G>1+1e-12).sum()),
          "max_target_gross":float(run.targets.abs().sum(axis=1).max()),
          "runtime":run.meta["runtime_s"],"actual_account":False}
    dump(f"{name}.{scenario}.json",meta)
    print("DONE",name,scenario,key,flush=True)
    return meta
def bound(frame):
    t=pd.DatetimeIndex(frame.start)
    end=t.tz_localize(None).to_period("Q").end_time.tz_localize("UTC")
    f=frame.loc[t+pd.Timedelta(hours=336)<=end].copy()
    f["quarter"]=pd.DatetimeIndex(f.start).tz_localize(None).to_period("Q").astype(str)
    g=f.groupby("quarter").delta.agg(["sum","count"])
    rng=np.random.default_rng(20261011)
    ix=rng.integers(0,len(g),size=(20000,len(g)))
    b=g["sum"].to_numpy()[ix].sum(1)/g["count"].to_numpy()[ix].sum(1)
    return {"lower":float(np.quantile(b,.05/36)),"upper":float(np.quantile(b,1-.05/36)),
            "n_quarters":len(g),"n_purged_windows":len(f),"hypotheses_scenarios":36,
            "project_wide_post_selection_control":False,"historical_reuse":True}
def report():
    inherited.OUT=OUT;inherited.NAMES=NAMES;inherited.HORIZONS=HORIZONS;inherited.ci_quarters=bound
    original=json.loads((ORIGINAL/"decision.base.json").read_text())
    stabilities={}
    for scenario in SCENARIOS:
        gates=inherited.summarize(scenario)
        frames={n:pd.read_parquet(OUT/f"{n}.{scenario}.parquet") for n in NAMES}
        for n in NAMES[1:]:
            for label,after in [("all",None),("recent_2024on",pd.Timestamp("2024-01-01",tz="UTC"))]:
                a=frames[n].loc[frames[n].hours==336];b=frames[BASE].loc[frames[BASE].hours==336]
                if after is not None: a=a.loc[a.start>=after];b=b.loc[b.start>=after]
                stabilities[f"{n}.{scenario}.{label}"]=paired_stability(a,b)
            gates[n]["original_historical_failure_veto"]=not original[n]["historical_gate_pass"]
            gates[n]["production_eligible"]=False
            gates[n]["rejection_only_extension"]=True
        dump(f"decision.{scenario}.json",gates)
    dump("calendar_stability.json",stabilities)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    before=fingerprint();dump("inputs_before.json",before)
    try:
        # Cheap frozen-base read first; no new baseline cache may be created.
        for n in NAMES: job((n,"base"))
        with ProcessPoolExecutor(max_workers=6) as pool:
            pending=[pool.submit(job,(n,s)) for s in SCENARIOS[1:] for n in NAMES]
            for task in as_completed(pending): task.result()
        report()
        after=fingerprint();dump("inputs_after.json",after)
        assert before==after,"frozen source/input changed during stress audit"
        dump("batch_status.json",{"status":"PASS","scenarios":SCENARIOS,"models":NAMES,"workers":6,
             "original_historical_gate_pass":[],"research_promotion":[],"production_eligible":False,
             "rejection_only_extension":True,"actual_holdings_verified":False,"fresh_forward_complete":False})
    except Exception as e:
        dump("batch_status.json",{"status":"FAIL","error":repr(e),"traceback":traceback.format_exc(),"production_eligible":False})
        raise
if __name__=="__main__": main()
