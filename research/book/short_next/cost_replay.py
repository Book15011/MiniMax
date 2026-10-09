"""Actual Simulator cost replay on the previous fixed160 case schedule.

This is separate descriptive sensitivity. It never publishes a score/registry.
Decisions are recomputed once to recover source Series order and must exactly
reproduce cached targets. Both cost scenarios use the same frozen decisions.
"""
from __future__ import annotations
import argparse,dataclasses,glob,hashlib,inspect,json,sys
from pathlib import Path
import numpy as np
import pandas as pd

# A standalone process loads the requested frozen model tree. Imports in tests
# use the normal current worktree. Never run different source trees in one process.
if __name__=="__main__" and "--source-worktree" in sys.argv:
    sys.path.insert(0,sys.argv[sys.argv.index("--source-worktree")+1])
from backtest.data import load_market
from backtest.engine import Costs,Simulator,compute_targets
from backtest.evaluate import model_modules,holdout_start
from backtest.scoring.evaluate import first_decisions,run_key
from backtest.scoring.windows import scored_starts
from backtest.scoring.score2 import load_checkpoint,signature
from backtest.scoring.weak_risk import remainder_risk
from backtest.scoring.weak_stats import tail_mean
from src.config import load_config,resolve
from src.models import get

HOURS=228
TOL=1e-12
PROTOCOL="603da2948b68ee0f5c8a"
BASELINE="baitoey_ovl_brk_dual"
BASELINE_KEY="f30fa79cde92399a"

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for x in iter(lambda:f.read(1024*1024),b""):h.update(x)
    return h.hexdigest()

def scaled_market(market,multiplier):
    return dataclasses.replace(market,half_spread=market.half_spread.copy()*multiplier)

def check_equity(actual,expected):
    a,b=np.asarray(actual),np.asarray(expected)
    if a.shape!=b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("original replay/cache equity dimensions or values differ")
    error=float(np.abs(a-b).max())
    if error>TOL:raise ValueError("original replay differs from original published cash-start equity")
    return error

def replay_costs(market,targets,start,hours,band,costs,lag,anchor,guard,keep_alive,guard_utc,first):
    extra=sorted({c for w in first.decisions for c in w.index}) if first is not None else ()
    sim=Simulator(market,targets,band,costs,lag,anchor,guard,keep_alive,
                  guard_utc_day=guard_utc,extra_cols=extra)
    i0=sim.index.get_loc(start)
    f=None if first is None else (np.array([sim.index.get_loc(t) for t in first.times]),
        sim.rows(first.decisions),sim.index.get_loc(first.until) if first.until is not None else i0+hours+1)
    result=sim.run(i0,hours,trace=True,first=f)
    w=result.trace["w_end"].copy()
    assert np.isclose(abs(w).sum(),result.trace["gross"][-1],rtol=0,atol=TOL)
    zero,close_turnover,close_cost,_=sim._trade(w,np.zeros_like(w),exact=True)
    assert not zero.any()
    fee=spread=0.
    for _,_,before,after,eq_before,_ in result.trace["trades"]:
        long=float(np.abs(np.maximum(after,0)-np.maximum(before,0)).sum())
        short=float(np.abs(np.minimum(after,0)-np.minimum(before,0)).sum())
        fee+=(long*costs.taker+short*costs.short)*eq_before
        spread+=float(np.abs(after-before)@sim.half)*eq_before
    terminal_fee=float(np.maximum(w,0).sum()*costs.taker+np.maximum(-w,0).sum()*costs.short)
    terminal_spread=float(abs(w)@sim.half)
    assert np.isclose(terminal_fee+terminal_spread,close_cost,rtol=0,atol=TOL)
    liquidated=result.equity.copy()
    liquidated[-1]*=1-close_cost
    return dict(mark_return=float(result.equity[-1]-1),
        liquidated_return=float(liquidated[-1]-1),
        turnover=result.turnover,turnover_including_liquidation=result.turnover+close_turnover,
        fees_e0=fee+terminal_fee*result.equity[-1],
        spreads_e0=spread+terminal_spread*result.equity[-1],
        active_days=result.active_days,max_gross_after_trade=result.max_gross,
        terminal_gross=float(abs(w).sum()),equity=result.equity,
        liquidated_equity=liquidated,gross=np.asarray(result.trace["gross"]))

def pin_publication(root,name,key,cp):
    records=[json.loads(x) for x in (root/"results/scoring/registry_2.jsonl").read_text().splitlines()]
    entries=[x for x in records if x.get("protocol")==PROTOCOL and x.get("model")==name and x.get("run_key")==key]
    if not entries:raise ValueError("published compatible model attestation required")
    entry=entries[-1]
    for e in entries:
        if e["cache_inputs"]!=entry["cache_inputs"]:raise ValueError("published revision changed cache")
    files={}
    for item in entry["cache_inputs"].values():
        p=Path(item["path"])
        if sha(p)!=item["sha256"]:raise ValueError("published cache hash changed")
        files[str(p)] = item["sha256"]
    sp=Path(entry["artifacts"]["score.json"]["path"])
    if sha(sp)!=entry["source_sha256"]:raise ValueError("published score changed")
    score=json.loads(sp.read_text())
    if signature(score)!=cp["signature"] or score["tool_version"]!=cp["base"]["tool_version"]:
        raise ValueError("published score is incompatible")
    if not score["windows"]["full_run"]:raise ValueError("full run required")
    files[str(sp)]=sha(sp)
    return score,files

def source_hashes(source,model,cfg,cp):
    modules=set(model_modules(model))
    if model.spec.name==BASELINE:
        modules.update(model_modules(model.INNER))
        modules.add("src.models.baitoey."+BASELINE)
    paths={m:Path(inspect.getsourcefile(sys.modules[m])) for m in sorted(modules)}
    out={m:{"path":str(p),"sha256":sha(p)} for m,p in paths.items()}
    for rel in ("config.yaml","backtest/engine.py","backtest/data.py",
                "backtest/scoring/evaluate.py","backtest/scoring/windows.py",
                "backtest/scoring/weak_risk.py","backtest/scoring/metrics.py","src/contracts.py"):
        p=source/rel;out[rel]={"path":str(p),"sha256":sha(p)}
    for label in ("historical_close","historical_qv"):
        item=cp["input"]["sources"][label]
        if sha(item["path"])!=item["sha256"]:
            raise ValueError("frozen historical input changed: "+label)
        out["input:"+label]={"path":item["path"],"sha256":item["sha256"],"matches_frozen":True}
    panel=resolve(cfg["harness"]["panel_dir"])
    for filename in ("universe.parquet","panel_notes.json"):
        p=panel/filename
        out["input:"+filename]={"path":str(p),"sha256":sha(p)}
    spreads=sorted(glob.glob(str(resolve(cfg["harness"]["spreads_snapshot_glob"]))))
    if spreads:
        out["input:spread"]={"path":spreads[-1],"sha256":sha(spreads[-1]),
                            "historical_bid_ask":False}
    return out

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-worktree",required=True)
    ap.add_argument("--model",required=True)
    ap.add_argument("--key",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--baseline-evidence",required=True)
    a=ap.parse_args(argv)
    source=Path(a.source_worktree).resolve();root=source.parent.parent
    out=Path(a.out).resolve()
    if (root/"results/book") not in out.parents:raise ValueError("dedicated Book results directory required")
    marker=out/("manifest."+a.model+".json")
    if marker.exists():raise ValueError("preserve prior replay; use a new output directory")
    cfg=load_config();cp=load_checkpoint(cfg)
    if cp["protocol"]!=PROTOCOL:raise ValueError("frozen primary protocol changed")
    score,pins=pin_publication(root,a.model,a.key,cp)
    params=score["model"]["params"]
    model=get(a.model);market=load_market(cfg);h=cfg["harness"]
    before=source_hashes(source,model,cfg,cp)
    if a.model==BASELINE:
        proof=json.loads(Path(a.baseline_evidence).read_text())
        if proof["status"]!="PASS" or proof["run_key"]!=BASELINE_KEY or a.key!=BASELINE_KEY:
            raise ValueError("exact baseline reproduction proof required")
        for m,item in proof["source_manifest_before"].items():
            if before[m]["sha256"]!=item["sha256"]:raise ValueError("baseline source differs from reproduced revision")
    old=root/"results/book/20261009-short-cost-stress/manifest.book_short_trend.json"
    old_manifest=json.loads(old.read_text())
    starts=pd.date_range("2020-06-01T12:00:00Z",periods=160,freq="14D")
    if [str(t) for t in starts]!=old_manifest["starts"]:raise ValueError("original160 case schedule differs")
    if starts[-1]+pd.Timedelta(hours=HOURS)>holdout_start(cfg):raise ValueError("sealed period reached")
    pool=scored_starts(market,cfg)
    if not starts.isin(pool).all():raise ValueError("fixed starts missing")
    computed_key=run_key(model,params,False,pool,cfg,market)
    if computed_key!=a.key:raise ValueError("current model/params no longer reproduce published identity")
    cache=root/"results/scoring/cache"/a.model/a.key
    paths={s:Path(str(cache)+"."+s) for s in ("json","targets.parquet","windows.parquet","arrays.npz","trades.parquet")}
    cache_before={str(p):sha(p) for p in paths.values()}
    meta=json.loads(paths["json"].read_text())
    if meta["key"]!=a.key or meta["tool_version"]!=cp["base"]["tool_version"] or meta.get("long_only"):
        raise ValueError("cache identity differs")
    old_starts=pd.read_parquet(paths["windows.parquet"]).index
    if not old_starts.equals(pool) or not old_starts.equals(cp["starts"]):raise ValueError("cache grid differs")
    ix=old_starts.get_indexer(starts)
    targets=pd.read_parquet(paths["targets.parquet"])
    # Recompute once, no fitting or tuning, to restore exact raw Series order.
    # Parquet column order alone loses dynamic coin order and can change the
    # first_decisions convergence check and previous-target hysteresis.
    actual,shared=compute_targets(model,market,targets.index,params,keep_raw=True)
    max_target_error=float(np.abs(actual.reindex(columns=targets.columns).to_numpy()-targets.to_numpy()).max())
    if max_target_error>TOL:raise ValueError("source no longer reproduces full cached target chain")
    firsts=first_decisions(model,market,starts,targets.index,shared,params,HOURS)
    with np.load(paths["arrays.npz"],allow_pickle=False) as arr:
        expected=arr["equity"][ix,:HOURS+1].copy()
    original=Costs(h["fees"]["taker"],h["fees"]["short"])
    doubled=Costs(original.taker*2,original.short*2)
    smarket=scaled_market(market,2)
    rows=[];curves={};max_equity_error=0.
    for i,t in enumerate(starts):
        pairs={}
        for scenario,m,c in (("original",market,original),("doubled",smarket,doubled)):
            r=replay_costs(m,targets,t,HOURS,model.spec.band,c,h["execution_lag_hours"],h["grid_hour_utc"],
                h["activity_guard_offset_hours"],float(h.get("keep_alive_weight",0)),
                bool(h.get("guard_utc_day",False)),firsts[t])
            if scenario=="original":
                max_equity_error=max(max_equity_error,check_equity(r["equity"],expected[i]))
            liquidated=r.pop("liquidated_equity")
            # Endpoint already paid both fees AND spread; use zero extra close
            # fee, retaining exactly the same CS formula/day buckets/floors.
            riskcfg=dict(cfg["scoring"],liquidation_cost=0.)
            risk=remainder_risk(liquidated[None,:],np.zeros((1,HOURS+1)),pd.DatetimeIndex([t]),0,HOURS,riskcfg)
            r["MDD"]=float(risk["mdd"][0]);r["CS"]=float(risk["CS"][0])
            curves.setdefault(scenario,[]).append(r.pop("equity"))
            r.pop("gross")
            pairs.update({scenario+"_"+k:v for k,v in r.items()})
        rows.append(dict(model=a.model,start=str(t),end=str(t+pd.Timedelta(hours=HOURS)),**pairs))
        if i%40==0:print(a.model,i+1,"/160",flush=True)
    if before!=source_hashes(source,model,cfg,cp):raise ValueError("source changed during cost replay")
    if cache_before!={str(p):sha(p) for p in paths.values()}:raise ValueError("cache changed during cost replay")
    if any(sha(p)!=digest for p,digest in pins.items()):raise ValueError("published inputs changed")
    frame=pd.DataFrame(rows);out.mkdir(parents=True,exist_ok=True)
    frame.to_csv(out/("paired_windows."+a.model+".csv"),index=False)
    np.savez_compressed(out/("curves."+a.model+".npz"),**{k:np.stack(v) for k,v in curves.items()})
    summary=[]
    for scenario in ("original","doubled"):
        r=frame[scenario+"_liquidated_return"].to_numpy()
        summary.append(dict(model=a.model,scenario=scenario,n=len(r),mean=float(r.mean()),
            median=float(np.median(r)),p10=float(np.quantile(r,.1)),tail10_mean=tail_mean(r,.1),worst=float(r.min()),
            mean_MDD=float(frame[scenario+"_MDD"].mean()),mean_CS=float(frame[scenario+"_CS"].mean()),
            mean_turnover=float(frame[scenario+"_turnover_including_liquidation"].mean()),
            mean_fees=float(frame[scenario+"_fees_e0"].mean()),mean_spreads=float(frame[scenario+"_spreads_e0"].mean())))
    pd.DataFrame(summary).to_csv(out/("summary."+a.model+".csv"),index=False)
    manifest=dict(identity="short_next_cost_v1_same160_228h",model=a.model,run_key=a.key,
        source_worktree=str(source),source_hashes=before,cache_hashes=cache_before,
        publication_hashes=pins,published_params=params,starts=[str(t) for t in starts],
        schedule_source={"path":str(old),"sha256":sha(old)},horizon_hours=HOURS,
        original_tool_version=meta["tool_version"],protocol=PROTOCOL,
        maximum_target_error=max_target_error,maximum_original_equity_error=max_equity_error,
        raw_decision_order="source compute_targets(keep_raw=True), full cache matrix reproduced",
        fee_multiplier=2,half_spread_multiplier=2,parameters_changed=False,
        terminal_liquidation="Simulator._trade final holdings, fees and spread, charged once",
        CS="unchanged FLOORED.V1; true fee+spread liquidation enters endpoint once",
        primary_compatible=False,published=False,all_history_spent=True,
        analysis_source={"path":str(Path(__file__).resolve()),"sha256":sha(__file__)})
    marker.write_text(json.dumps(manifest,indent=2))
    print(pd.DataFrame(summary).to_string(index=False),flush=True)
if __name__=="__main__":main()
