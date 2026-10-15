"""Export only frozen team model source remotely, then generate cold-start target paths."""
from pathlib import Path
import subprocess,tarfile,io,json,hashlib,sys
import pandas as pd,numpy as np,yaml
PROJECT=Path("/home/ubuntu/test/MiniMax")
HERE=Path(__file__).parent;OUT=PROJECT/"results/book/20261015-directional-benchmark-v1"
def main():
    conf=yaml.safe_load((HERE/"config.yaml").read_text());commit=conf["main_model_registry_commit"]
    frozen=OUT/"frozen_B_source";frozen.mkdir(exist_ok=False)
    archive=subprocess.check_output(["git","-C",str(PROJECT),"archive",commit,"src/models","src/contracts.py","src/config.py"])
    with tarfile.open(fileobj=io.BytesIO(archive)) as t:
        assert all(not m.issym() and not m.islnk() and ".." not in Path(m.name).parts for m in t.getmembers())
        t.extractall(frozen)
    (frozen/"src/__init__.py").touch()
    cfg=yaml.safe_load(subprocess.check_output(["git","-C",str(PROJECT),"show",commit+":config.yaml"],text=True))
    params=cfg["models"]["book_orch"]
    print("FROZEN_B_LAYERS",{k:v.get("enabled") for k,v in params.items() if isinstance(v,dict) and "enabled" in v},flush=True)
    if params["forecast_longs"]["enabled"] or params["forecast_shorts"]["enabled"]:raise RuntimeError("Forecast artifact contract must be supplied; do not disable layers")
    # Only selected numeric strategy config is exported; no environment/API files.
    (OUT/"frozen_B_parameters.json").write_text(json.dumps(params,indent=2))
    sys.path.insert(0,str(frozen))
    from src.models.book.book_orch import MODEL
    from src.contracts import MarketView,check_targets
    before={}
    for name in ["close_1h","qv_1h"]:
        src=PROJECT/f"data/live_e20v45/{name}.parquet";data=src.read_bytes()
        before[name]=hashlib.sha256(data).hexdigest();(OUT/f"input_{name}.parquet").write_bytes(data)
    C=pd.read_parquet(OUT/"input_close_1h.parquet");Q=pd.read_parquet(OUT/"input_qv_1h.parquet").reindex_like(C)
    eligible={p.removesuffix("/USD")+"USDT" for p in cfg["universe"]};exists=C.notna();history=exists.cumsum()
    volume=Q.fillna(0).rolling(30*24,min_periods=1).sum()
    universes={}
    for t in C.index[C.index.hour==16]:
        ok=(history.loc[t]>=90*24)&exists.loc[t]&C.columns.isin(eligible)
        rank=volume.loc[t][ok].sort_values(ascending=False,kind="stable")
        universes[t]=tuple(sorted(rank.index[:30]))
    u=pd.Series(universes)
    cases=[]
    end=pd.Timestamp(conf["quote_end_exclusive"],tz="UTC")
    for start in pd.date_range(pd.Timestamp(conf["quote_start"],tz="UTC"),end-pd.Timedelta(hours=conf["primary_horizon_hours"]),freq="D"):
        cases.append((start,conf["primary_horizon_hours"],"50h"))
    for start in pd.date_range(pd.Timestamp(conf["quote_start"],tz="UTC"),end-pd.Timedelta(days=1),freq="D"):
        cases.append((start,24,"24h"))
    rows=[]
    for start,hours,kind in cases:
        previous=pd.Series(dtype=float)
        for t in pd.date_range(start,start+pd.Timedelta(hours=hours),freq="h"):
            pos=u.index.searchsorted(t,side="right")-1;universe=u.iloc[pos] if pos>=0 else ()
            view=MarketView(t=t,close=C.loc[:t],quote_volume=Q.loc[:t],universe=universe,params=params,prev_targets=previous)
            target=check_targets(MODEL.targets(view),view,MODEL.spec);previous=target
            rows.append({"case_start":start,"case_hours":hours,"time":t,"weights":json.dumps({c.removesuffix("USDT"):float(w) for c,w in target.items()})})
        print("B_TARGET",str(start),hours,flush=True)
    pd.DataFrame(rows).to_parquet(OUT/"B_targets.parquet",index=False)
    hashes={str(p.relative_to(frozen)):hashlib.sha256(p.read_bytes()).hexdigest() for p in frozen.rglob("*.py")}
    result={"frozen_B_commit":subprocess.check_output(["git","-C",str(PROJECT),"rev-parse",commit],text=True).strip(),
      "input_hourly_sha256":before,"source_sha256":hashes,"source_model":"book_orch","hourly_view_future_truncated":True,
      "cash_start_target_history_restarted_each_case":True,"cases":len(cases),"actual_EC2_state_used":False,
      "current_pair_metadata_and_paper_hourly_store":True,"original_validation_cache_recent_replay_equivalence":False,
      "forecasts_enabled":False,"point_in_time_universe":"prior daily16UTC, top30 trailing30d volume, at least90d history"}
    (OUT/"B_target_manifest.json").write_text(json.dumps(result,indent=2));print("B_TARGETS_COMPLETE",len(rows),flush=True)
if __name__=="__main__":main()
