"""Reproduce a pinned baseline's full target chain and cash-start bootstraps."""
from __future__ import annotations
import argparse,hashlib,inspect,json,sys
from pathlib import Path
import numpy as np
import pandas as pd


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-worktree",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args(argv)
    source=Path(args.source_worktree).resolve()
    project=source.parent.parent
    sys.path.insert(0,str(source))
    from src.config import load_config
    from src.models import get
    from backtest.data import load_market
    from backtest.engine import Simulator,Costs,decide,compute_targets,decision_times
    from backtest.evaluate import model_modules
    name="baitoey_ovl_brk_dual";key="f30fa79cde92399a"
    protocol="603da2948b68ee0f5c8a"
    records=[json.loads(x) for x in (project/"results/scoring/registry_2.jsonl").read_text().splitlines()]
    entry=next(x for x in records if x.get("protocol")==protocol and
               x.get("model")==name and x.get("run_key")==key)
    digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    for item in entry["cache_inputs"].values():
        if digest(item["path"])!=item["sha256"]:raise ValueError("published baseline cache changed")
    score_path=Path(entry["artifacts"]["score.json"]["path"])
    if digest(score_path)!=entry["source_sha256"]:raise ValueError("published baseline score changed")
    score=json.loads(score_path.read_text());params=score["model"]["params"]
    model=get(name);cfg=load_config();market=load_market(cfg);h=cfg["harness"]
    modules=sorted(set(model_modules(model)+model_modules(model.INNER)+["src.models.baitoey."+name]))
    paths={module:Path(inspect.getsourcefile(sys.modules[module])) for module in modules}
    before={m:{"path":str(p),"sha256":digest(p)} for m,p in paths.items()}
    cache=project/"results/scoring/cache"/name/key
    target_path=Path(str(cache)+".targets.parquet")
    target_hash=digest(target_path);targets=pd.read_parquet(target_path)
    starts=pd.DatetimeIndex(pd.to_datetime(score["per_window"]["start"],utc=True))
    expected_times=decision_times(market.close.index,model.spec.rebalance_hours,
        h["grid_hour_utc"],starts[0],starts[-1]+pd.Timedelta(days=h["window_days"]))
    if not targets.index.equals(expected_times):raise ValueError("stored target schedule differs")
    actual=compute_targets(model,market,expected_times,params)
    a=actual.reindex(columns=targets.columns).fillna(0)
    error=float(np.abs(a.to_numpy()-targets.to_numpy()).max())
    if error>1e-12:raise ValueError("complete target chain differs")
    trades=pd.read_parquet(Path(str(cache)+".trades.parquet"))
    sim=Simulator(market,actual,model.spec.band,Costs(h["fees"]["taker"],h["fees"]["short"]),
        h["execution_lag_hours"],h["grid_hour_utc"],h["activity_guard_offset_hours"],
        h.get("keep_alive_weight",0),guard_utc_day=h.get("guard_utc_day",False))
    boot=[]
    for i in np.unique(np.linspace(0,len(starts)-1,120).astype(int)):
        t=starts[i]
        if t+pd.Timedelta(hours=1) not in market.close.index:continue
        wanted=decide(model,market,t,params,pd.Series(dtype=float))
        i0=sim.index.get_loc(t)
        res=sim.run(i0,2,trace=True,first=(np.array([i0]),sim.rows([wanted]),i0+2))
        fills=[r for r in res.trace["trades"] if r[0]==1]
        expected=pd.Series(fills[0][3],index=sim.cols) if fills else pd.Series(dtype=float)
        old=trades.loc[(trades.window_start==t)&(trades.hour==1)]
        got=old.set_index("series").w_after if len(old) else pd.Series(dtype=float)
        cols=expected.index.union(got.index)
        err=float((expected.reindex(cols).fillna(0)-got.reindex(cols).fillna(0)).abs().max()) if len(cols) else 0
        if err>1e-12:raise ValueError("cash-start bootstrap fills differ")
        boot.append({"start":str(t),"post_planner_max_error":err,
                     "requested_target_count":len(wanted),"fills":len(old)})
    if len(boot)<100:raise ValueError("fewer than100bootstrap checks")
    after={m:{"path":str(p),"sha256":digest(p)} for m,p in paths.items()}
    if before!=after or target_hash!=digest(target_path):
        raise ValueError("source or target file changed during audit")
    for item in entry["cache_inputs"].values():
        if digest(item["path"])!=item["sha256"]:raise ValueError("baseline cache changed during audit")
    result={"status":"PASS","model":name,"run_key":key,"protocol":protocol,
        "published_params":params,"published_score_sha256":digest(score_path),
        "parameters_source":str(score_path),"source_manifest_before":before,"source_manifest_after":after,
        "full_shared_decisions":len(targets),"maximum_target_error":error,
        "bootstrap_count":len(boot),"bootstrap_max_error":max(x["post_planner_max_error"] for x in boot),
        "bootstrap_checks":boot,"legacy_model_modules":model_modules(model),
        "legacy_wrapper_and_inner_omitted":True,"stored_target_sha256":target_hash,
        "target_publication_hash_available":False,
        "analysis_source_sha256":digest(__file__),
        "limitations":["This empirical reproduction does not repair the legacy fingerprint omission.",
            "A cash bootstrap can invoke the existing.002BTC keepalive guard; bootstrap comparison includes it.",
            "Published trade/array hashes are checked; targets.parquet has no original publication attestation.",
            "All data are historical and spent; no prospective validation or profit claim."]}
    out=Path(args.out).resolve()
    if project not in out.parents:raise ValueError("output outside remote project")
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k in ["status","full_shared_decisions","maximum_target_error","bootstrap_count","bootstrap_max_error"]}))
if __name__=="__main__":main()
