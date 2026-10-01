"""Build the lookalike validation set (v1).

    python -m src.validation.build --asof "2026-10-03 16:00"      # the Oct 3 rerun
    python -m src.validation.build                                # dry run: as-of = latest complete hour in the data
Options: --no-refresh (use data on disk), --refresh-macro (fetch a new FRED snapshot instead of the pinned one),
         --out-dir (intermediate tables; default data/validation).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

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
    recent_nonoverlapping, select_lookalikes,
)
from src.validation.sets import stress_sets
from src.validation.walkforward import BASELINES, choose_variant, run_walkforward, skill, test_dates

log = logging.getLogger("validation.build")
REPORT = REPO_ROOT / "reports" / "validation_set_v1.md"
ARTIFACT = REPO_ROOT / "validation" / "validation_set_v1.json"
FRED_PINS = REPO_ROOT / "validation" / "fred_pins.json"
PREREG_RE = re.compile(r"<!-- PREREG:BEGIN -->.*?<!-- PREREG:END -->", re.S)
KEY_FEATURES = ["T1", "T2", "C1", "V1", "M1", "M2", "M4"]
# which input sources each feature group reads
GROUP_SOURCES = {"TREND": "spot", "CYCLE": "spot", "VOL": "spot", "STRUCTURE": "spot",
                 "POSITIONING": "futures", "MACRO": "fred", "CALENDAR": None}


def _git(*args: str) -> str:
    # rstrip only: porcelain lines start with a meaningful space
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.rstrip()


def refresh(cfg: dict, refresh_macro: bool) -> dict:
    notes: dict = {}
    try:
        res = binance_downloader.run_all(cfg)
    except binance_downloader.AlreadyRunning as e:
        raise SystemExit(f"a downloader is already running ({e}); wait for it to finish, then rerun")
    notes["downloads"] = {k: dict(v) for k, v in res.items()}
    notes["external_copy"] = {k: dict(v) for k, v in external_copy.run(cfg).items()}
    if refresh_macro:
        try:
            notes["fred_fetch"] = fred.fetch(cfg)
        except fred.FredUnavailable as e:
            notes["fred_fetch"] = f"unavailable: {e}"
    return notes


def load_fred(cfg: dict, asof: pd.Timestamp, refresh_macro: bool, notes: dict) -> dict | None:
    """The FRED snapshot pinned for this as-of (validation/fred_pins.json); pin the newest one if none yet."""
    pins_all = json.loads(FRED_PINS.read_text()) if FRED_PINS.exists() else {}
    key = str(asof)
    pins = None if refresh_macro else pins_all.get(key)
    series, recs = fred.load(cfg, pins)
    used = {k: {x: r[x] for x in ("file", "sha256", "first", "last")} for k, r in recs.items()}
    notes["fred_used"], notes["fred_pinned"] = used, pins is not None
    new_pin = {k: {"file": r["file"], "sha256": r["sha256"]} for k, r in used.items()}
    if pins_all.get(key) != new_pin:
        pins_all[key] = new_pin
        FRED_PINS.write_text(json.dumps(pins_all, indent=1, sort_keys=True) + "\n")
    missing = sorted(set(cfg["data"]["fred"]["series"]) - set(series))
    notes["fred_missing"] = missing
    return series if not missing else None


def _period_start(period: str) -> pd.Timestamp:
    return pd.Timestamp(period + ("-01" if len(period) == 7 else ""), tz="UTC")


def input_lines(cfg: dict, asof: pd.Timestamp, fred_used: dict) -> dict[str, list[str]]:
    """Verified input files per source whose period starts at or before the as-of (later files cannot
    affect anything computed at the as-of)."""
    jobs = cfg["data"]["jobs"]
    out: dict[str, list[str]] = {"spot": [], "futures": [], "fred": []}
    for name, src in (("spot_klines_1m", "spot"), ("spot_klines_1h", "spot"),
                      ("futures_funding", "futures"), ("futures_metrics", "futures")):
        for r in Manifest(resolve(jobs[name]["manifest"])).latest().values():
            if r["status"] == "ok" and _period_start(r["period"]) <= asof:
                out[src].append(f"{name}|{r['file']}|{r['sha256']}")
    lob = resolve(cfg["data"]["external_copy"]["dest"]) / "_manifest.jsonl"
    for r in Manifest(lob).latest().values():
        if r["status"] == "ok" and _period_start(external_copy._period_of(r["file"].split("/")[-1])) <= asof:
            out["futures"].append(f"lob_copy|{r['file']}|{r['sha256']}")
    out["fred"] = [f"fred|{r['file']}|{r['sha256']}" for r in fred_used.values()]
    return {k: sorted(v) for k, v in out.items()}


def sha_lines(lines: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(lines)).encode()).hexdigest()


def state_time(engine: StateEngine, asof: pd.Timestamp) -> pd.Timestamp:
    """Latest grid time <= asof whose BTC hourly bar (closing exactly at that time) exists."""
    btc = engine.data.close[BTC].dropna().index
    grid = engine.close_d.index[engine.close_d.index <= asof]
    ok = grid[grid.isin(btc)]
    if ok.empty:
        raise SystemExit(f"no complete grid bar at or before {asof}")
    return ok[-1]


def run_pytest(out_dir: Path) -> dict:
    env = {**os.environ, "MM_VALIDATION_OUT": str(out_dir)}
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-rA", "-p", "no:cacheprovider", "tests"],
                       cwd=REPO_ROOT, capture_output=True, text=True, env=env)
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
    ap.add_argument("--no-refresh", action="store_true", help="skip downloads; use data on disk")
    ap.add_argument("--refresh-macro", action="store_true", help="fetch a new FRED snapshot instead of the pinned one")
    ap.add_argument("--out-dir", default="data/validation", help="intermediate tables (default data/validation)")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)

    cfg = load_config()
    v = cfg["validation"]
    out = resolve(args.out_dir)
    hz = pd.Timedelta(days=v["horizon_days"])
    t_star = pd.Timestamp(v["live_start"], tz="UTC")
    holdout = t_star - pd.Timedelta(days=v["holdout_days"])
    earliest = pd.Timestamp(v["pool_earliest"] + f" {v['grid_hour_utc']:02d}:00", tz="UTC")
    rules = PickRules(v["k"], v["min_separation_days"], v["span_days"], v["max_per_span"], v["horizon_days"])
    wf = v["walkforward"]

    prereg = PREREG_RE.search(REPORT.read_text()) if REPORT.exists() else None
    if prereg is None:
        raise SystemExit(f"{REPORT} has no pre-registration block; it must exist before any test is run")
    previous = json.loads(ARTIFACT.read_text()) if ARTIFACT.exists() else None

    notes = {} if args.no_refresh else refresh(cfg, args.refresh_macro)
    out.mkdir(parents=True, exist_ok=True)
    panel = build_hourly_panel(cfg)
    panel.save(out)
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

    last_hour = panel.close[BTC].last_valid_index()
    asof = pd.Timestamp(args.asof, tz="UTC") if args.asof else last_hour
    data = MarketData(panel.close, panel.quote_volume, funding, oi,
                      load_fred(cfg, asof, args.refresh_macro, notes))
    groups_ok = available_groups(data)
    engine = StateEngine(data, v)
    t_q = state_time(engine, min(asof, last_hour))
    log.info("asof=%s state time=%s (T*=%s, H=%s)", asof, t_q, t_star, holdout)

    times = engine.close_d.index[(engine.close_d.index >= pd.Timestamp("2020-01-01 16:00", tz="UTC"))
                                 & (engine.close_d.index <= t_q)]
    feats = engine.features(times)
    feats.to_parquet(out / "features.parquet")
    uni = pd.DataFrame([(t, s) for t in times[times >= earliest] for s in engine.universe(t)], columns=["t", "series"])
    uni.to_parquet(out / "universe.parquet")
    log.info("features: %d grid days x %d features", *feats.shape)

    t0s = feats.index[(feats.index >= earliest) & (feats.index + hz <= holdout)]
    outc = compute_outcomes(engine, t0s, v["horizon_days"])
    outc = outc.join(regime_labels(outc))
    save_outcomes(outc, out / "outcomes.parquet")
    outcomes = load_outcomes(out / "outcomes.parquet")

    variants = {n: g for n, g in {**VARIANTS, **DIAGNOSTIC_VARIANTS}.items() if all(groups_ok[x] for x in g)}
    unavailable = sorted(set(VARIANTS) - set(variants))
    dates = test_dates(wf["start"], holdout, v["horizon_days"], wf["step_days"], v["grid_hour_utc"])
    cr, audit = run_walkforward(feats, outcomes, variants, rules, dates, earliest, wf["random_draws"], wf["seed"])
    cr.to_parquet(out / "walkforward_crps.parquet")
    audit.to_parquet(out / "walkforward_audit.parquet")
    okaudit = audit[audit.status == "ok"]
    assert (audit.pool_max_end.dropna() <= audit.D[audit.pool_max_end.notna()]).all(), "pool_D leaks past D"
    assert (okaudit.pick_max_end <= okaudit.D).all(), "lookalike leaks past D"

    periods = {"SCREEN": (dates[0], pd.Timestamp(wf["screen_end"] + " 23:59", tz="UTC")),
               "CONFIRM": (pd.Timestamp(wf["confirm_start"], tz="UTC"), dates[-1])}
    boot = (wf["bootstrap_reps"], wf["bootstrap_block"], wf["seed"])
    skills = {(var, b, p): skill(cr, var, b, lo, hi, *boot)
              for var in variants for b in BASELINES for p, (lo, hi) in periods.items()}
    skills_fair = {(var, b, p): skill(cr, var, b, lo, hi, *boot, fair=True)
                   for var in variants for b in BASELINES for p, (lo, hi) in periods.items()}
    mean_of = {p: {var: float(skills[(var, "all", p)].loc["MEAN", "skill"]) for var in variants} for p in periods}
    main_ok = [x for x in MAIN_VARIANTS if x in variants]
    ok_dates = audit[audit.status == "ok"].groupby("variant").D.apply(set)
    common = set.intersection(*[ok_dates[x] for x in main_ok])
    crc = cr[cr.D.isin(common)]
    common_diag = {
        "n": {p: int(sum(lo <= d <= hi for d in common)) for p, (lo, hi) in periods.items()},
        "skill": {p: {x: skill(crc, x, "all", lo, hi, *boot).loc["MEAN"] for x in main_ok}
                  for p, (lo, hi) in periods.items()},
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
    recent = recent_nonoverlapping(pool, rules)
    stress = stress_sets(pool, outcomes["Y1"], engine.close_d[BTC])

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
    lines = input_lines(cfg, asof, fred_used)
    active_sources = sorted({GROUP_SOURCES[g] for g in groups} - {None})
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
    same_asof = previous is not None and previous.get("asof_requested") == str(asof)
    identical = (sorted(w["start"] for w in windows) == sorted(w["start"] for w in previous["windows"])
                 if same_asof else None)
    artifact = {
        "version": "validation_set_v1", "revision": "1.1 (PART 0: pinned FRED, input hashes, DTWEXBGS lag, "
                                                    "RECENT/STRESS sets, fair-CRPS diagnostics)",
        "asof_requested": str(asof), "state_time": str(t_q),
        "live_start_T_star": str(t_star), "holdout_H": str(holdout),
        "gap_hours_T_star_minus_state_time": (t_star - t_q) / pd.Timedelta(hours=1),
        "variant": chosen, "groups": groups, "features": act, "query_features_dropped_nan": dropped,
        "choice": choice, "parameters": {"validation": v, "rules": rules.__dict__, "variants": variants},
        "pool": {"n": len(pool), "first_start": str(pool.min()), "last_start": str(pool.max())},
        "windows": windows,
        "windows_identical_to_previous_same_asof": identical,
        "recent": [{"start": str(t), "end": str(t + hz)} for t in recent],
        "stress": stress,
        "sensitivity": sens,
        "skill_of_chosen": {f"{p} vs {b}": {k: float(x) for k, x in skills[(chosen, b, p)].loc["MEAN"].items()}
                            for p in periods for b in BASELINES},
        "fair_skill_of_chosen": {f"{p} vs {b}": {k: float(x) for k, x in skills_fair[(chosen, b, p)].loc["MEAN"].items()}
                                 for p in periods for b in BASELINES},
        "git_commit": head, "git_dirty_paths": dirty, "prereg_commit": prereg_commit[-1] if prereg_commit else None,
        "prereg_sha256": hashlib.sha256(prereg.group(0).encode()).hexdigest(),
        "fred_snapshot": {"pinned": notes["fred_pinned"], "files": {k: r["file"] for k, r in fred_used.items()}},
        "inputs_active_sources": active_sources,
        "inputs_sha256_active": sha_lines([ln for s in active_sources for ln in lines[s]]),
        "inputs_sha256_all": sha_lines([ln for s in lines for ln in lines[s]]),
        "inputs_files": {s: len(x) for s, x in lines.items()},
        "data_last": last_data,
    }
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(artifact, indent=1, default=str))

    tests = run_pytest(out)
    REPORT.write_text(report.render(
        prereg=prereg.group(0), artifact=artifact, notes=notes, groups_ok=groups_ok, skills=skills,
        skills_fair=skills_fair, periods=periods, variants=variants, main_variants=MAIN_VARIANTS, choice=choice,
        state=state, main_set=main_set, feats=feats, outcomes=outcomes, pool=pool, audit=audit, tests=tests,
        horizon=hz, key_features=[f for f in KEY_FEATURES if f in act] + [f for f in act if f.startswith(("P", "X", "E"))][:4],
        outcome_cols=list(OUTCOME_COLUMNS), baselines=BASELINES, universe=uni, common_diag=common_diag))
    log.info("wrote %s and %s; windows identical to previous (same as-of): %s; tests: %s",
             REPORT, ARTIFACT, identical, tests["summary"])
    return 0 if tests["exit_code"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
