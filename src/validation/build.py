"""Build the lookalike validation set (v1).

    python -m src.validation.build --asof "2026-10-03 16:00"      # the Oct 3 rerun
    python -m src.validation.build                                # dry run: as-of = latest complete hour in the data
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import subprocess
import sys

import numpy as np
import pandas as pd

from src.config import REPO_ROOT, load_config, resolve
from src.data import binance_downloader, external_copy, fred
from src.data.binance_downloader import Manifest
from src.data.futures import load_funding, load_open_interest
from src.data.panel import build_hourly_panel
from src.validation import report
from src.validation.features import BTC, FEATURES, GROUPS, MarketData, StateEngine, available_groups
from src.validation.guard import OUTCOME_COLUMNS
from src.validation.outcomes import compute_outcomes, load_outcomes, regime_labels, save_outcomes
from src.validation.selection import (
    DIAGNOSTIC_VARIANTS, MAIN_VARIANTS, VARIANTS, PickRules, active_features, jaccard, mid_rank_pct, pool_index,
    select_lookalikes,
)
from src.validation.walkforward import BASELINES, choose_variant, run_walkforward, skill, test_dates

log = logging.getLogger("validation.build")
OUT = REPO_ROOT / "data" / "validation"
REPORT = REPO_ROOT / "reports" / "validation_set_v1.md"
ARTIFACT = REPO_ROOT / "validation" / "validation_set_v1.json"
PREREG_RE = re.compile(r"<!-- PREREG:BEGIN -->.*?<!-- PREREG:END -->", re.S)
KEY_FEATURES = ["T1", "T2", "C1", "V1", "M1", "M2", "M4"]


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()


def refresh(cfg: dict) -> dict:
    notes: dict = {}
    try:
        res = binance_downloader.run_all(cfg)
    except binance_downloader.AlreadyRunning as e:
        raise SystemExit(f"a downloader is already running ({e}); wait for it to finish, then rerun")
    notes["downloads"] = {k: dict(v) for k, v in res.items()}
    notes["external_copy"] = {k: dict(v) for k, v in external_copy.run(cfg).items()}
    try:
        notes["fred_fetch"] = fred.fetch(cfg)
    except fred.FredUnavailable as e:
        notes["fred_fetch"] = f"unavailable: {e}"
    return notes


def load_market(cfg: dict, notes: dict) -> MarketData:
    panel = build_hourly_panel(cfg)
    panel.save(OUT)
    notes["panel"] = panel.notes
    try:
        funding = load_funding(cfg)
    except Exception as e:  # noqa: BLE001 -- a missing source disables its group; reported
        funding, notes["funding_error"] = None, f"{type(e).__name__}: {e}"
    try:
        oi = load_open_interest(cfg)
        notes["oi_boundary_conflicts_resolved"] = oi.attrs.get("boundary_conflicts_resolved", 0)
    except Exception as e:  # noqa: BLE001
        oi, notes["oi_error"] = None, f"{type(e).__name__}: {e}"
    series, recs = fred.load(cfg)
    notes["fred_used"] = {k: {x: v[x] for x in ("file", "sha256", "first", "last")} for k, v in recs.items()}
    missing = sorted(set(cfg["data"]["fred"]["series"]) - set(series))
    notes["fred_missing"] = missing
    return MarketData(panel.close, panel.quote_volume, funding, oi, series if not missing else None)


def data_manifest_hash(cfg: dict, fred_used: dict) -> tuple[str, dict]:
    lines, counts = [], {}
    manifests = {n: resolve(j["manifest"]) for n, j in cfg["data"]["jobs"].items()}
    manifests["lob_copy"] = resolve(cfg["data"]["external_copy"]["dest"]) / "_manifest.jsonl"
    for name, path in manifests.items():
        ok = [r for r in Manifest(path).latest().values() if r["status"] == "ok"]
        counts[name] = len(ok)
        lines += [f"{name}|{r['file']}|{r['sha256']}" for r in ok]
    lines += [f"fred|{r['file']}|{r['sha256']}" for r in fred_used.values()]
    return hashlib.sha256("\n".join(sorted(lines)).encode()).hexdigest(), counts


def state_time(engine: StateEngine, asof: pd.Timestamp) -> pd.Timestamp:
    """Latest grid time <= asof whose BTC hourly bar (closing exactly at that time) exists."""
    btc = engine.data.close[BTC].dropna().index
    grid = engine.close_d.index[engine.close_d.index <= asof]
    ok = grid[grid.isin(btc)]
    if ok.empty:
        raise SystemExit(f"no complete grid bar at or before {asof}")
    return ok[-1]


def run_pytest() -> dict:
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-rA", "-p", "no:cacheprovider", "tests"],
                       cwd=REPO_ROOT, capture_output=True, text=True)
    lines = p.stdout.splitlines()
    res = {"exit_code": p.returncode, "summary": lines[-1] if lines else "", "tests": {}}
    for ln in lines:
        m = re.match(r"^(PASSED|FAILED|ERROR|SKIPPED)\s+(\S+)", ln)
        if m:
            res["tests"][m.group(2)] = m.group(1)
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--asof", default=None, help='UTC, e.g. "2026-10-03 16:00" (default: latest complete hour)')
    ap.add_argument("--no-refresh", action="store_true", help="skip downloads / FRED fetch; use data on disk")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)

    cfg = load_config()
    v = cfg["validation"]
    hz = pd.Timedelta(days=v["horizon_days"])
    t_star = pd.Timestamp(v["live_start"], tz="UTC")
    holdout = t_star - pd.Timedelta(days=v["holdout_days"])
    earliest = pd.Timestamp(v["pool_earliest"] + f" {v['grid_hour_utc']:02d}:00", tz="UTC")
    rules = PickRules(v["k"], v["min_separation_days"], v["span_days"], v["max_per_span"], v["horizon_days"])
    wf = v["walkforward"]

    prereg = PREREG_RE.search(REPORT.read_text()) if REPORT.exists() else None
    if prereg is None:
        raise SystemExit(f"{REPORT} has no pre-registration block; it must exist before any test is run")

    notes = {} if args.no_refresh else refresh(cfg)
    OUT.mkdir(parents=True, exist_ok=True)
    data = load_market(cfg, notes)
    groups_ok = available_groups(data)
    engine = StateEngine(data, v)

    last_hour = data.close[BTC].last_valid_index()
    asof = pd.Timestamp(args.asof, tz="UTC") if args.asof else last_hour
    t_q = state_time(engine, min(asof, last_hour))
    log.info("asof=%s state time=%s (T*=%s, H=%s)", asof, t_q, t_star, holdout)

    times = engine.close_d.index[(engine.close_d.index >= pd.Timestamp("2020-01-01 16:00", tz="UTC"))
                                 & (engine.close_d.index <= t_q)]
    feats = engine.features(times)
    feats.to_parquet(OUT / "features.parquet")
    uni = pd.DataFrame([(t, s) for t in times[times >= earliest] for s in engine.universe(t)], columns=["t", "series"])
    uni.to_parquet(OUT / "universe.parquet")
    log.info("features: %d grid days x %d features", *feats.shape)

    t0s = feats.index[(feats.index >= earliest) & (feats.index + hz <= holdout)]
    outc = compute_outcomes(engine, t0s, v["horizon_days"])
    outc = outc.join(regime_labels(outc))
    save_outcomes(outc, OUT / "outcomes.parquet")
    outcomes = load_outcomes(OUT / "outcomes.parquet")

    variants = {n: g for n, g in {**VARIANTS, **DIAGNOSTIC_VARIANTS}.items() if all(groups_ok[x] for x in g)}
    unavailable = sorted(set(VARIANTS) - set(variants))
    dates = test_dates(wf["start"], holdout, v["horizon_days"], wf["step_days"], v["grid_hour_utc"])
    cr, audit = run_walkforward(feats, outcomes, variants, rules, dates, earliest, wf["random_draws"], wf["seed"])
    cr.to_parquet(OUT / "walkforward_crps.parquet")
    audit.to_parquet(OUT / "walkforward_audit.parquet")
    okaudit = audit[audit.status == "ok"]
    assert (audit.pool_max_end.dropna() <= audit.D[audit.pool_max_end.notna()]).all(), "pool_D leaks past D"
    assert (okaudit.pick_max_end <= okaudit.D).all(), "lookalike leaks past D"

    periods = {"SCREEN": (dates[0], pd.Timestamp(wf["screen_end"] + " 23:59", tz="UTC")),
               "CONFIRM": (pd.Timestamp(wf["confirm_start"], tz="UTC"), dates[-1])}
    skills = {(var, b, p): skill(cr, var, b, lo, hi, wf["bootstrap_reps"], wf["bootstrap_block"], wf["seed"])
              for var in variants for b in BASELINES for p, (lo, hi) in periods.items()}
    mean_of = {p: {var: float(skills[(var, "all", p)].loc["MEAN", "skill"]) for var in variants} for p in periods}
    main_ok = [x for x in MAIN_VARIANTS if x in variants]
    ok_dates = audit[audit.status == "ok"].groupby("variant").D.apply(set)
    common = set.intersection(*[ok_dates[x] for x in main_ok])
    crc = cr[cr.D.isin(common)]
    common_diag = {
        "n": {p: int(sum(lo <= d <= hi for d in common)) for p, (lo, hi) in periods.items()},
        "skill": {p: {x: skill(crc, x, "all", lo, hi, wf["bootstrap_reps"], wf["bootstrap_block"], wf["seed"])
                      .loc["MEAN"] for x in main_ok} for p, (lo, hi) in periods.items()},
    }
    choice = choose_variant(mean_of["SCREEN"], mean_of["CONFIRM"])
    choice["unavailable_variants"] = unavailable
    chosen = choice["chosen"]
    groups = variants[chosen]
    act = active_features(groups)
    log.info("choice: %s", choice)

    pool = pool_index(feats, groups, holdout, v["horizon_days"], earliest)
    assert ((pool + hz) <= holdout).all(), "pool overlaps the holdout"
    query = feats.loc[t_q]
    main_set, dropped = select_lookalikes(feats.loc[pool, act], query[act], groups, rules)
    assert ((main_set.t0 + hz) <= holdout).all(), "selection overlaps the holdout"

    sens = {}
    for k in v["sensitivity_k"]:
        s, _ = select_lookalikes(feats.loc[pool, act], query[act], groups,
                                 PickRules(k, rules.min_separation_days, rules.span_days, rules.max_per_span,
                                           rules.horizon_days))
        sens[f"K={k}"] = {"n": len(s), "jaccard": jaccard(s.t0, main_set.t0)}
    for g in groups:
        rest = [x for x in groups if x != g]
        if not rest:
            continue
        p2 = pool_index(feats, rest, holdout, v["horizon_days"], earliest)
        a2 = active_features(rest)
        s, _ = select_lookalikes(feats.loc[p2, a2], query[a2], rest, rules)
        sens[f"drop {g}"] = {"n": len(s), "jaccard": jaccard(s.t0, main_set.t0)}

    pct = {}
    for f in FEATURES:
        ref = feats.loc[pool, f].dropna().to_numpy()
        pct[f] = float(mid_rank_pct(ref[:, None], np.array([[query[f]]]))[0, 0]) if len(ref) and np.isfinite(query[f]) else np.nan
    state = pd.DataFrame({"group": [g for g, fs in GROUPS.items() for _ in fs], "value": query[FEATURES],
                          "percentile_in_pool": pd.Series(pct), "active": [f in act for f in FEATURES]}, index=FEATURES)

    fred_used = notes.get("fred_used", {})
    dhash, dcounts = data_manifest_hash(cfg, fred_used)
    head = _git("rev-parse", "HEAD")
    dirty = [ln for ln in _git("status", "--porcelain").splitlines()
             if not ln[3:].startswith(("reports/", "validation/"))]
    prereg_commit = _git("log", "--diff-filter=A", "--format=%H", "--", "reports/validation_set_v1.md").splitlines()
    last_data = {"btc_last_hourly_close": str(last_hour),
                 "funding_last": str(data.funding.index[-1]) if data.funding is not None else None,
                 "oi_last": str(data.oi.index[-1]) if data.oi is not None else None,
                 "fred_last": {k: r["last"] for k, r in fred_used.items()}}

    windows = [{"rank": i + 1, "start": str(r.t0), "end": str(r.t0 + hz), "distance": round(float(r.distance), 6)}
               for i, r in enumerate(main_set.sort_values("distance").itertuples())]
    artifact = {
        "version": "validation_set_v1", "asof_requested": str(asof), "state_time": str(t_q),
        "live_start_T_star": str(t_star), "holdout_H": str(holdout),
        "gap_hours_T_star_minus_state_time": (t_star - t_q) / pd.Timedelta(hours=1),
        "variant": chosen, "groups": groups, "features": act, "query_features_dropped_nan": dropped,
        "choice": choice, "parameters": {"validation": v, "rules": rules.__dict__, "variants": variants},
        "pool": {"n": len(pool), "first_start": str(pool.min()), "last_start": str(pool.max())},
        "windows": windows, "sensitivity": sens,
        "skill_of_chosen": {f"{p} vs {b}": {k: float(x) for k, x in skills[(chosen, b, p)].loc["MEAN"].items()}
                            for p in periods for b in BASELINES},
        "git_commit": head, "git_dirty_paths": dirty, "prereg_commit": prereg_commit[-1] if prereg_commit else None,
        "prereg_sha256": hashlib.sha256(prereg.group(0).encode()).hexdigest(),
        "data_manifest_sha256": dhash, "data_manifest_ok_files": dcounts, "data_last": last_data,
    }
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(artifact, indent=1, default=str))

    tests = run_pytest()
    REPORT.write_text(report.render(
        prereg=prereg.group(0), artifact=artifact, notes=notes, groups_ok=groups_ok, skills=skills,
        periods=periods, variants=variants, main_variants=MAIN_VARIANTS, choice=choice, state=state,
        main_set=main_set, feats=feats, outcomes=outcomes, pool=pool, audit=audit, tests=tests, horizon=hz,
        key_features=[f for f in KEY_FEATURES if f in act] + [f for f in act if f.startswith(("P", "X", "E"))][:4],
        outcome_cols=list(OUTCOME_COLUMNS), baselines=BASELINES, universe=uni, common_diag=common_diag))
    log.info("wrote %s and %s; tests: %s", REPORT, ARTIFACT, tests["summary"])
    return 0 if tests["exit_code"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
