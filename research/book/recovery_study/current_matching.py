"""Current BTC-only matching diagnostic. No outcome reads, no adaptive activation."""
from pathlib import Path
import importlib.util,json,hashlib,yaml
import pandas as pd,numpy as np
from src.config import load_config
from src.validation.selection import PickRules
ROOT=Path(__file__).resolve().parents[3];MAIN=ROOT.parents[1]
OUT=MAIN/"results/book/20261011-recovery-current-context-v1"
def main():
    OUT.mkdir(exist_ok=True)
    old=MAIN/".worktrees/book-book-bear-eval"
    hp=MAIN/"results/book/20261009-weak-eval-v2/historical_features.parquet"
    history=pd.read_parquet(hp)
    fp=old/"research/book/regime_eval/features.py"
    spec=importlib.util.spec_from_file_location("book_existing_matching_features",fp)
    fm=importlib.util.module_from_spec(spec);spec.loader.exec_module(fm)
    cfg=load_config();settings=yaml.safe_load((old/"config.yaml").read_text())["book_regime_eval"]
    asof=pd.Timestamp("2026-10-10 17:00",tz="UTC");settings={**settings,"state_grid_hour_utc":asof.hour}
    d=MAIN/"results/book/shadow/h1";files=[d/"close_1h.parquet",d/"qv_1h.parquet"]
    before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    c=pd.read_parquet(files[0]).loc[:asof];q=pd.read_parquet(files[1]).loc[:asof]
    assert before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    query=fm.build_features(c,q,pd.DatetimeIndex([asof]),cfg["validation"],settings).iloc[0]
    groups={k:v for k,v in settings["features"].items() if k!="BREADTH"}
    fields=[x for g in groups.values() for x in g]
    eligible=np.isfinite(history[fields]).all(axis=1)
    pool=history.loc[eligible]
    assert np.isfinite(query[fields]).all() and np.isfinite(pool[fields]).all().all()
    rules=PickRules(**settings["lookalikes"])
    matched=fm.match_windows(pool,query,groups,rules)
    ix=pd.DatetimeIndex(matched.t0).sort_values()
    assert np.diff(ix.values).astype("timedelta64[h]").astype(int).min()>=14*24
    assert len(ix)==25
    c[["BTCUSDT"]].to_parquet(OUT/"btc_input_snapshot.parquet")
    query[fields].to_frame().T.to_parquet(OUT/"query_features.parquet")
    matched.to_csv(OUT/"btc_only_cases.csv",index=False)
    history.loc[~eligible,fields].to_csv(OUT/"excluded_incomplete_historical_features.csv")
    oldquery=pd.read_parquet(MAIN/"results/book/20261009-weak-eval-v2/query_features.parquet")
    pd.concat([oldquery[fields],query[fields].to_frame().T]).to_csv(OUT/"query_comparison.csv")
    manifest={"status":"DIAGNOSTIC_ONLY","asof":str(asof),"query_columns":fields,"query":query[fields].to_dict(),
      "snapshot_source_hashes":before,"feature_source":str(fp),"feature_source_sha256":hashlib.sha256(fp.read_bytes()).hexdigest(),
      "historical_source":str(hp),"historical_sha256":hashlib.sha256(hp.read_bytes()).hexdigest(),
      "historical_eligible_n":len(pool),"historical_incomplete_excluded":int((~eligible).sum()),
      "coverage_threshold_unchanged":settings["minimum_hour_coverage"],"selection_rules":settings["lookalikes"],
      "selected_n":len(matched),"outcome_columns_used":[],"strict_broad_universe_pass":False,
      "strict_broad_failure":"BCH absent from original30 competition endpoints;29/30",
      "adaptive_activation":False,"production_eligible":False,"actual_account":False,
      "limits":["BTC-only matching omits alt breadth; no validated new broad ranking",
        "all historical returns are spent research evidence",
        "current supported29 differs from original broad30; reselected engine breadth is NOT used",
        "hour17 fresh ticker-assisted query compared with frozen hour12 historical states"]}
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2,allow_nan=False))
    print("DIAGNOSTIC_ONLY",len(matched),"eligible",len(pool),"max distance",matched.distance.max())
if __name__=="__main__":main()
