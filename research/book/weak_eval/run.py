"""Freeze causal cases before comparing model returns. Run from Book worktree."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from src.config import load_config
from research.book.regime_eval.run import safe_path,sha,dump
from research.book.regime_eval.features import market_outcomes
from .prepare import prepare
from backtest.scoring.weak_stats import select_cases

def build_checkpoint(cfg):
    c=cfg["book_weak_eval"];out=safe_path(c["out_dir"]);out.mkdir(parents=True,exist_ok=True)
    if (out/"artifact_manifest.json").exists():
        existing=json.loads((out/"frozen_config.json").read_text())
        if existing["weak"]!=c or existing["scoring"]!=cfg["scoring"]:raise ValueError("frozen protocol differs")
        for name,d in json.loads((out/"artifact_manifest.json").read_text()).items():
            if sha(out/name)!=d["sha256"]:raise ValueError("checkpoint changed: "+name)
        return out
    old=safe_path(c["source_checkpoint"]);oldc=json.loads((old/"frozen_config.json").read_text())
    entries=json.loads((old/"registered_snapshot.json").read_text())
    inc=next(e for e in entries if e["model"]==oldc["incumbent"])
    source=safe_path(inc["score_json"])
    if sha(source)!=inc["score_sha256"]:raise ValueError("incumbent source changed")
    score=json.loads(source.read_text())
    starts=pd.DatetimeIndex(pd.to_datetime(score["per_window"]["start"],utc=True))
    data=prepare(cfg,starts,archive_evidence=[
      {"symbol":"BTCUSDT","interval":"1h","period":"2026-10-08","status":"HTTP404; unpublished at preparation"},
      {"symbol":"BTCUSDT","interval":"1m","period":"2026-10-08","status":"HTTP404; unpublished at preparation"},
      {"symbol":"BCHUSDT","interval":"1m","period":"2026-10-08","status":"HTTP404; unpublished at preparation"}])
    hist=data["historical_features"]
    outcome=market_outcomes(data["close"],starts,0,max(c["horizons_hours"]),cfg)
    coverage=np.isfinite(outcome.to_numpy()).all(axis=1)
    exclusions=pd.DataFrame({"reason":"BTC maximum-horizon path/endpoints missing"},index=starts[~coverage])
    exclusions.to_csv(out/"coverage_exclusions.csv",index_label="window_start")
    hist=hist.loc[coverage]
    profiles={"weak_archived":(data["query"],c["features"],"weak"),
              "weak_fresh_btc":(data["fresh_query"],c["fresh_features"],"weak"),
              "positive_control":(data["query"],c["features"],"positive")}
    picks={};notes=[]
    for profile,(q,groups,mode) in profiles.items():
        picks[profile]=select_cases(hist,q,c["asof"],max(c["horizons_hours"]),c,mode,groups)
        for k in c["sensitivity_k"]:
            name=profile+"_k"+str(k)
            try:picks[name]=select_cases(hist,q,c["asof"],max(c["horizons_hours"]),c,mode,groups,k)
            except ValueError as exc:notes.append({"profile":name,"status":"INSUFFICIENT","reason":str(exc)})
    union=pd.DatetimeIndex([],tz="UTC")
    for p in picks.values():union=union.union(p.index)
    cases=outcome.loc[union].copy()
    for profile,p in picks.items():
        cases[profile]=cases.index.isin(p.index)
        cases[profile+"_distance"]=p.distance.reindex(cases.index)
        p.to_csv(out/(profile+".csv"),index_label="window_start")
    cases.to_parquet(out/"cases.parquet")
    frozen={"schema_version":2,"weak":c,"scoring":cfg["scoring"],"base":oldc,
            "created_utc":datetime.now(timezone.utc).isoformat(),
            "candidate_comparisons_started":False,
            "initialization":"CASH_AT_T0","historical_start_hour_utc":12,"query_hour_utc":0}
    dump(out/"frozen_config.json",frozen);dump(out/"registered_snapshot.json",entries)
    Path(out/"PROTOCOL.md").write_text(Path("research/book/weak_eval/PROTOCOL.md").read_text())
    clusters={p:len(cases.index[cases[p]].tz_localize(None).to_period("Q").unique()) for p in picks}
    dump(out/"selection_validation.json",{"integrity_pass":True,"future_outcomes_used_in_matching":False,
         "selected_before_candidate_comparison":True,"cases":{p:int(cases[p].sum()) for p in picks},
         "quarter_clusters":clusters,"sensitivity_failures":notes,
         "reference_coverage":data["input_manifest"]["reference_broad_coverage"],
         "fresh_coverage":data["input_manifest"]["fresh_broad_coverage"],
         "fresh_archive_confirmed":data["input_manifest"]["fresh_archive_confirmed"],
         "statistical_activation":"CONDITIONAL_EXPERIMENTAL_RANKING_ONLY"})
    old_artifacts=json.loads((old/"artifact_manifest.json").read_text())
    if sha(old/"cache_inputs.json")!=old_artifacts["cache_inputs.json"]["sha256"]:
        raise ValueError("old cache manifest changed")
    original_pins=json.loads((old/"cache_inputs.json").read_text());pins={}
    for entry in entries:
        name=entry["model"];key=entry["run_key"]
        for item in original_pins[name].values():
            if sha(safe_path(item["path"]))!=item["sha256"]:raise ValueError("old registered cache changed:"+name)
        base=safe_path(Path(oldc["cache_dir"])/name/key)
        files={ext:Path(str(base)+ext) for ext in (".arrays.npz",".windows.parquet",".json",".trades.parquet")}
        pins[name]={"run_key":key,"files":{ext:{"path":str(p),"sha256":sha(p)} for ext,p in files.items()}}
    dump(out/"source_cache_manifest.json",pins)
    files=["source_cache_manifest.json","frozen_config.json","registered_snapshot.json","PROTOCOL.md","selection_validation.json",
           "cases.parquet","coverage_exclusions.csv","input_manifest.json",
           "close_snapshot.parquet","qv_snapshot.parquet","historical_features.parquet","query_features.parquet"]
    dump(out/"artifact_manifest.json",{name:{"sha256":sha(out/name)} for name in files})
    print(json.dumps({"stage":"cases frozen before model comparison","root":str(out),"counts":frozen["weak"]["lookalikes"],"clusters":clusters,"exclusions":len(exclusions)}),flush=True)
    return out

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument("stage",choices=["prepare","compare"]);a=ap.parse_args(argv)
    cfg=load_config()
    if a.stage=="prepare":build_checkpoint(cfg)
    else:
        from backtest.scoring.weak_board import import_registered
        print(import_registered(cfg))
if __name__=="__main__":main()
