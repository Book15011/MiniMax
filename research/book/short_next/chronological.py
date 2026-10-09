"""Independent cache-only chronological diagnostics; never publishes a leaderboard.

The eight folds are descriptive chronological blocks for already fixed models.
All historical observations are spent. No parameters are selected within folds,
and no untouched or prospective holdout claim is made.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import REPO_ROOT, load_config, resolve
from backtest.scoring.score2 import load_checkpoint, signature
from backtest.scoring.weak_risk import remainder_risk
from backtest.scoring.weak_stats import tail_mean
from backtest.scoring.metrics import day_points

ANCHOR = pd.Timestamp("2022-07-01 12:00", tz="UTC")
LAST = pd.Timestamp("2026-06-30 12:00", tz="UTC")
HOURS = 228
E20 = "pol_switch_vt_tl_e20v45"
E20_KEY = "0ec3cf0ca1185b36"
SUFFIXES = (".arrays.npz", ".windows.parquet", ".json", ".trades.parquet")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def select_test_cases(starts, hours=HOURS):
    """One global 14-day schedule; windows crossing fold boundaries are dropped."""
    starts = pd.DatetimeIndex(starts)
    if starts.tz is None:
        raise ValueError("cache starts must be timezone aware")
    if starts.isna().any() or not starts.is_unique:
        raise ValueError("cache starts must be unique valid timestamps")
    if hours != HOURS or isinstance(hours, bool):
        raise ValueError("this frozen chronological diagnostic uses 228 hours")
    starts = starts.tz_convert("UTC")
    scheduled = pd.date_range(ANCHOR, LAST, freq="14D")
    rows = []
    for first in pd.date_range("2022-07-01", "2026-01-01", freq="6MS", tz="UTC"):
        end = first + pd.DateOffset(months=6)
        label = f"{first.year}H{1 if first.month == 1 else 2}"
        for t in scheduled:
            endpoint = t + pd.Timedelta(hours=hours)
            if first <= t and endpoint <= end:
                rows.append(dict(window_start=t, fold=label, fold_start=first,
                                 fold_end=end, endpoint=endpoint))
    cases = pd.DataFrame(rows).set_index("window_start").sort_index()
    if not cases.index.isin(starts).all():
        raise ValueError("cache is missing fixed test starts; refusing to change schedule")
    if (cases.index[1:] - cases.index[:-1] < pd.Timedelta(days=14)).any():
        raise ValueError("fixed cases unexpectedly overlap")
    return cases


def validate_arrays(equity, gross, rows, horizon):
    if equity.shape != (rows, horizon + 1) or gross.shape != equity.shape:
        raise ValueError("full cache dimensions differ from frozen protocol")
    if not np.isfinite(equity).all() or not np.isfinite(gross).all():
        raise ValueError("cache paths must be finite")
    if (equity <= 0).any() or (gross < 0).any():
        raise ValueError("equity must be positive and gross nonnegative")


def ledger_metrics(trades, starts, hours, e0):
    """Truncated activity/costs, never copied from the original 14-day totals.

    Endpoint fills affect equity/cost/turnover but are outside activity day
    buckets, following the existing scorer's endpoint activity convention.
    """
    required = {"window_start", "hour", "time_utc", "kind", "w_before", "w_after",
                "fee_usd", "spread_usd"}
    if not required <= set(trades):
        raise ValueError("cached trade ledger is incomplete")
    if not np.isfinite(e0) or e0 <= 0:
        raise ValueError("positive starting capital required")
    starts = pd.DatetimeIndex(starts)
    frame = trades.copy()
    frame["window_start"] = pd.to_datetime(frame["window_start"], utc=True)
    frame["time_utc"] = pd.to_datetime(frame["time_utc"], utc=True)
    frame = frame.loc[frame.window_start.isin(starts)]
    numeric = frame[["hour", "w_before", "w_after", "fee_usd", "spread_usd"]].to_numpy(float)
    if not np.isfinite(numeric).all():
        raise ValueError("cached ledger must be finite")
    if len(frame) and ((frame.hour != frame.hour.astype(int)).any()
                      or (frame.hour <= 0).any()
                      or (frame.fee_usd < 0).any() or (frame.spread_usd < 0).any()):
        raise ValueError("invalid ledger hours or negative execution costs")
    expected = frame.window_start + pd.to_timedelta(frame.hour, unit="h")
    if not (expected == frame.time_utc).all():
        raise ValueError("ledger fill timestamps differ from clock hours")
    grouped = {t: rows for t, rows in frame.groupby("window_start")}
    result = []
    for t0 in starts:
        part = grouped.get(t0, frame.iloc[:0])
        part = part.loc[part.hour <= hours]
        points = day_points(t0, hours, 16)
        strategy, guard = set(), set()
        for row in part.itertuples():
            if row.hour < hours:
                bucket = int(np.searchsorted(points, row.hour, side="right") - 1)
                (guard if row.kind == "guard" else strategy).add(bucket)
        before, after = part.w_before.to_numpy(float), part.w_after.to_numpy(float)
        result.append(dict(
            window_start=t0, active_days=len(strategy | guard),
            strategy_days=len(strategy), guard_only_days=len(guard - strategy),
            day_buckets=len(points)-1,
            turnover=float(np.abs(after-before).sum()),
            orders=int((np.abs(after-before)>1e-12).sum() + ((before*after)<0).sum()),
            fees_e0=float(part.fee_usd.sum()/e0),
            spread_e0=float(part.spread_usd.sum()/e0),
        ))
    return pd.DataFrame(result).set_index("window_start")


def summarize(frame):
    if frame.empty:
        raise ValueError("empty chronological group")
    r = frame["return"].to_numpy(float)
    return dict(
        n=len(frame), return_mean=float(r.mean()), return_median=float(np.median(r)),
        return_p10=float(np.quantile(r,.1)), tail10_mean=tail_mean(r,.1),
        return_worst=float(r.min()), positive_share=float((r>0).mean()),
        mdd_mean=float(frame.mdd.mean()), mdd_worst=float(frame.mdd.max()),
        CS_mean=float(frame.CS.mean()), CS_UTC_mean=float(frame.CS_UTC.mean()),
        active_days_mean=float(frame.active_days.mean()),
        strategy_days_mean=float(frame.strategy_days.mean()),
        guard_only_days_mean=float(frame.guard_only_days.mean()),
        turnover_mean=float(frame.turnover.mean()), fees_e0_mean=float(frame.fees_e0.mean()),
        spread_e0_mean=float(frame.spread_e0.mean()),
    )


def paired_summaries(windows, candidate_names, baseline_names):
    if windows.duplicated(["model", "window_start"]).any():
        raise ValueError("duplicate model/window row")
    rows = []
    for name in candidate_names:
        a = windows.loc[windows.model == name].set_index("window_start").sort_index()
        for baseline in baseline_names:
            b = windows.loc[windows.model == baseline].set_index("window_start").sort_index()
            if not a.index.equals(b.index) or not a.fold.equals(b.fold):
                raise ValueError("paired case support differs")
            for fold in [*a.fold.unique(), "ALL"]:
                mask = np.ones(len(a), bool) if fold == "ALL" else a.fold.to_numpy() == fold
                delta = (a["return"]-b["return"]).to_numpy()[mask]
                rows.append(dict(model=name, baseline=baseline, fold=fold, n=len(delta),
                    delta_mean=float(delta.mean()), delta_median=float(np.median(delta)),
                    delta_p10=float(np.quantile(delta,.1)),
                    delta_tail10_mean=tail_mean(delta,.1), delta_worst=float(delta.min()),
                    paired_win_share=float((delta>0).mean())))
    return pd.DataFrame(rows)


def parse_model(value):
    match = re.fullmatch(r"([a-z][a-z0-9_]*)=([0-9a-f]{16})", value)
    if not match:
        raise ValueError("use MODEL=16_HEX_RUN_KEY")
    return match.groups()


def source_score(name, key, cp, fixed=False):
    """Require a compatible published score; never import/train a candidate."""
    if fixed:
        entry = next(r for r in cp["snapshots"] if r["model"] == name)
        if entry["run_key"] != key:
            raise ValueError("fixed reference revision differs")
        paths = [resolve(entry["score_json"]).resolve()]
        if sha(paths[0]) != entry["score_sha256"]:
            raise ValueError("fixed reference score changed")
    else:
        root = resolve("results/scoring/score2").resolve() / cp["protocol"] / name
        paths = sorted(root.glob(key+"-*/score.json"))
        if not paths:
            raise FileNotFoundError("candidate lacks immutable score2 evidence; publish it first: "+name)
    found = []
    for path in paths:
        score = json.loads(path.read_text())
        if (score["model"]["name"] != name or score["model"]["run_key"] != key
                or not score["windows"]["full_run"]
                or score["tool_version"] != cp["base"]["tool_version"]
                or signature(score) != cp["signature"]):
            raise ValueError("source score is incompatible")
        starts = pd.DatetimeIndex(pd.to_datetime(score["per_window"]["start"], utc=True))
        if not starts.equals(cp["starts"]):
            raise ValueError("source score window grid differs")
        found.append({"path":str(path),"sha256":sha(path)})
    return found


def published_pin(name, key, cp, hashes):
    records = [json.loads(line) for line in Path(cp["registry"]).read_text().splitlines() if line.strip()]
    matching = [r for r in records if r.get("protocol")==cp["protocol"]
                and r.get("model")==name and r.get("run_key")==key]
    if not matching:
        raise ValueError("candidate cache lacks published hash attestation")
    for entry in matching:
        if entry["cache_inputs"] != hashes:
            raise ValueError("published candidate cache changed")
        item = entry["artifacts"]["score.json"]
        if sha(item["path"]) != item["sha256"] or item["sha256"] != entry["source_sha256"]:
            raise ValueError("published candidate score changed")
    return [{"entry_sha256":hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest(),
             "source_sha256":r["source_sha256"]} for r in matching]


def load_cache(name, key, cp, fixed=False):
    score_sources = source_score(name,key,cp,fixed)
    base = resolve(cp["base"]["cache_dir"]).resolve() / name / key
    paths = {s:Path(str(base)+s) for s in SUFFIXES}
    hashes = {s:{"path":str(p),"sha256":sha(p)} for s,p in paths.items()}
    if fixed:
        pin = cp["source_caches"][name]
        if pin["run_key"] != key or pin["files"] != hashes:
            raise ValueError("fixed reference cache changed")
    attestations = [] if fixed else published_pin(name,key,cp,hashes)
    metadata = json.loads(paths[".json"].read_text())
    if (metadata["key"] != key or metadata["model"] != name
            or metadata["tool_version"] != cp["base"]["tool_version"]
            or metadata.get("long_only",False)):
        raise ValueError("cached metadata incompatible")
    windows = pd.read_parquet(paths[".windows.parquet"])
    if not windows.index.equals(cp["starts"]):
        raise ValueError("cached window grid differs")
    with np.load(paths[".arrays.npz"],allow_pickle=False) as arrays:
        eq,gross = arrays["equity"].copy(),arrays["gross"].copy()
    validate_arrays(eq,gross,len(cp["starts"]),cp["base"]["horizon_hours"])
    for source in score_sources:
        score = json.loads(Path(source["path"]).read_text())
        liquidated = eq[:,-1]*(1-cp["base"]["close_fee"]*gross[:,-1])/eq[:,0]-1
        if not np.allclose(liquidated,score["per_window"]["R_liq"],rtol=0,atol=1e-12):
            raise ValueError("cached liquidation returns differ from published score")
    trades = pd.read_parquet(paths[".trades.parquet"])
    if hashes != {s:{"path":str(p),"sha256":sha(p)} for s,p in paths.items()}:
        raise ValueError("cache changed while loading")
    return eq,gross,trades,{"files":hashes,"score_sources":score_sources,"publication_attestations":attestations}


def input_hashes(cfg,cp):
    saved = cp["input"]["sources"]
    found = {}
    for name in ("historical_close","historical_qv"):
        entry = saved[name]
        digest = sha(entry["path"])
        if digest != entry["sha256"]:
            raise ValueError("historical source changed: "+name)
        found[name] = {"path":entry["path"],"sha256":digest,"matches_frozen":True}
    universe = resolve(cfg["harness"]["panel_dir"]) / "universe.parquet"
    found["historical_universe"] = {"path":str(universe),"sha256":sha(universe),
        "original_frozen_hash_available":False}
    snapshots = sorted(glob.glob(str(resolve(cfg["harness"]["spreads_snapshot_glob"]))))
    if snapshots:
        found["spread_snapshot"] = {"path":snapshots[-1],"sha256":sha(snapshots[-1]),
            "contemporaneous_historical_spreads":False}
    else:
        found["spread_snapshot"] = {"path":None,"default_half_spread_bps":
                                   cfg["harness"]["default_half_spread_bps"]}
    return found


def build_windows(name,role,eq,gross,trades,cases,cp,cfg):
    ix = cp["starts"].get_indexer(cases.index)
    risk = remainder_risk(eq[ix],gross[ix],cases.index,0,HOURS,cfg["scoring"])
    frame = pd.DataFrame(risk,index=cases.index)
    frame = frame.join(cases).join(ledger_metrics(trades,cases.index,HOURS,cfg["scoring"]["e0"]))
    frame["model"],frame["role"] = name,role
    return frame.reset_index()


def run(candidates,out_dir,benchmarks=()):
    cfg = load_config()
    cp = load_checkpoint(cfg)
    cp["registry"] = str(resolve(cfg["book_score2"]["registry"]).resolve())
    before = input_hashes(cfg,cp)
    if cp["base"]["incumbent"] != E20:
        raise ValueError("fixed incumbent name changed")
    inc = next(r for r in cp["snapshots"] if r["model"] == E20)
    if inc["run_key"] != E20_KEY:
        raise ValueError("fixed e20 revision changed")
    cases = select_test_cases(cp["starts"])
    refs = [(E20,E20_KEY,"fixed_e20")]
    for name,role in [("team_btc_hold","btc_hold"),("team_ew_daily","long_negative_control")]:
        entry = next(r for r in cp["snapshots"] if r["model"] == name)
        refs.append((name,entry["run_key"],role))
    refs.extend((name,key,"pinned_additional_comparator") for name,key in benchmarks)
    if len({name for name,_,_ in refs}) != len(refs):
        raise ValueError("duplicate benchmark name")
    if len({name for name,_ in candidates}) != len(candidates):
        raise ValueError("duplicate candidate name")
    if not candidates:
        raise ValueError("at least one explicit candidate key required")
    if set(n for n,_ in candidates) & {n for n,_,_ in refs}:
        raise ValueError("candidate cannot replace fixed comparator")
    frames,cache_manifest = [],{}
    for name,key,role in [*( (n,k,"candidate") for n,k in candidates),*refs]:
        eq,gross,trades,manifest = load_cache(name,key,cp,fixed=role in {"fixed_e20","btc_hold","long_negative_control"})
        cache_manifest[name] = {"run_key":key,**manifest}
        frames.append(build_windows(name,role,eq,gross,trades,cases,cp,cfg))
    windows = pd.concat(frames,ignore_index=True)
    cash = frames[0].copy()
    cash["model"],cash["role"] = "cash","zero_return_control"
    cash.loc[:,["return","mdd","CS","CS_UTC","Sharpe","Sortino","Calmar","active_days",
                "strategy_days","guard_only_days","turnover","orders","fees_e0","spread_e0"]] = 0
    windows = pd.concat([windows,cash],ignore_index=True)
    summaries = []
    for (name,role),part in windows.groupby(["model","role"],sort=True):
        for fold in [*part.fold.unique(),"ALL"]:
            group = part if fold == "ALL" else part.loc[part.fold==fold]
            summaries.append({"model":name,"role":role,"fold":fold,**summarize(group)})
    paired = paired_summaries(windows,[n for n,_ in candidates],
                              ["cash",*[name for name,_,_ in refs]])
    after = input_hashes(cfg,cp)
    if before != after:
        raise ValueError("historical inputs changed during analysis")
    for manifest in cache_manifest.values():
        for item in list(manifest["files"].values())+manifest["score_sources"]:
            if sha(item["path"]) != item["sha256"]:
                raise ValueError("source changed during analysis")
    out = Path(out_dir).resolve()
    project = REPO_ROOT.parent.parent if REPO_ROOT.parent.name==".worktrees" else REPO_ROOT
    book_results = (project/"results"/"book").resolve()
    if book_results not in out.parents or out == book_results:
        raise ValueError("output must be a dedicated directory under project results/book")
    if (out/"manifest.json").exists():
        raise ValueError("analysis directory already contains evidence; use a new directory")
    out.mkdir(parents=True,exist_ok=True)
    cases.to_csv(out/"fixed_cases.csv",index_label="window_start")
    windows.to_csv(out/"window_metrics.csv",index=False)
    summary = pd.DataFrame(summaries)
    summary.to_csv(out/"fold_summary.csv",index=False)
    paired.to_csv(out/"paired_summary.csv",index=False)
    manifest = {
        "schema_version":1,"analysis":"FIXED_MODEL_RETROSPECTIVE_CHRONOLOGICAL_DIAGNOSTIC",
        "protocol":cp["protocol"],"tool_version":cp["base"]["tool_version"],
        "horizon_hours":HOURS,"anchor":str(ANCHOR),"stride_days":14,
        "folds":list(cases.fold.unique()),"fold_counts":cases.fold.value_counts().sort_index().to_dict(),
        "fold_selection":False,"parameter_selection":False,"all_history_spent":True,
        "prospective_validation":False,"additional_benchmarks":dict(benchmarks),"cost_stress":"NOT_RUN; requires separate executable replay",
        "source_inputs":before,"cache_inputs":cache_manifest,
        "analysis_source":{"path":str(Path(__file__).resolve()),"sha256":sha(__file__)},
        "metric_sources":{name:sha(REPO_ROOT/name) for name in [
            "backtest/scoring/metrics.py","backtest/scoring/weak_risk.py",
            "backtest/scoring/weak_stats.py"]},
        "endpoint":"2026-10-18 12:00:00+00:00",
        "endpoint_evidence":"reports/review/20261001-realtest-findings.md:32; dated public competition538 API finding",
        "endpoint_fresh_verification":"HTTP451 on unsigned public listing; not refreshed",
        "limitations":[
            "Fixed models were developed after all historical prices were available.",
            "Folds are descriptive chronology, not nested selection or untouched holdout.",
            "14-day spacing prevents direct return-path overlap; market dependence persists.",
            "No inference interval treats individual trade rows as independent samples.",
            "Cash has no activity; equal-weight long is a negative control for bearish dependence.",
            "Historical spreads are static proxies; minimum-order execution is approximate.",
            "Each model uses its declared cadence and the unchanged hourly scorer's one-hour execution lag.",
            "No current-account switch, minute execution, deployment or competition guarantee.",
        ],
    }
    manifest["outputs"] = {p.name:sha(p) for p in out.glob("*.csv")}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,default=str)+"\n")
    report = ["# Independent chronological cache diagnostics","",
        "Fixed, already developed models; all history is spent. No fold tuning or untouched holdout claim.",
        f"Protocol {cp['protocol']}; {len(cases)} fixed 228-hour cash-start cases across eight half-years.",
        "Fourteen-day starts are anchored globally at 2022-07-01 12UTC. Cross-fold paths are excluded.",
        "Returns pay terminal liquidation once. Activity and turnover use only the truncated trade ledger.",
        "CS uses unchanged FLOORED.V1 daily raw HKT formula; UTC sensitivity is separate.","",
        "Read fold_summary.csv for each half-year and pooled ALL distribution.",
        "Read paired_summary.csv for same-window return advantage against cash, fixed e20, BTC, equal-weight long and any explicitly pinned additional benchmark.",
        "These chronological diagnostics do not replace the frozen weak-market score or create a new rank.","",
        "## Pooled descriptive results","",
        "| Model | Mean | Median | P10 | Tail10 mean | Worst | Mean MDD | Mean CS |",
        "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in summary.loc[summary.fold=="ALL"].itertuples():
        report.append(f"| {row.model} | {row.return_mean:+.2%} | {row.return_median:+.2%} | "
                      f"{row.return_p10:+.2%} | {row.tail10_mean:+.2%} | {row.return_worst:+.2%} | "
                      f"{row.mdd_mean:.2%} | {row.CS_mean:.3f} |")
    report += ["","## Limits","",*["- "+v for v in manifest["limitations"]],
               "","Cost stress was not run: changing fees requires an executable replay, not multiplication of final returns.",
               "Endpoint remains the dated documented October18 12UTC value; fresh unsigned verification returned HTTP451.",
               "Raw historical close/volume hashes match frozen evidence; universe/spread hashes are independently recorded now.",
               "No board, registry, live model or existing checkpoint was changed.",""]
    (out/"REPORT.md").write_text("\n".join(report))
    print(json.dumps({"output":str(out),"cases":len(cases),"models":len(frames),
                      "fold_counts":manifest["fold_counts"]}))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate",action="append",required=True,metavar="MODEL=RUN_KEY")
    ap.add_argument("--benchmark",action="append",default=[],metavar="MODEL=RUN_KEY",
                    help="additional explicit comparator; published cache required")
    ap.add_argument("--out",required=True,help="dedicated project results/book output directory")
    args = ap.parse_args(argv)
    try:
        run([parse_model(x) for x in args.candidate],args.out,[parse_model(x) for x in args.benchmark])
    except (ValueError,FileNotFoundError,KeyError) as exc:
        ap.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
