"""Side check, not part of the pre-registered rule: re-score the CORE walk-forward with the fair CRPS.

The build scores each set with the standard sample CRPS, whose spread term divides by n^2. That term is
biased low for small sets, so a 25-window lookalike set is penalized against the ~2,000-window pool
(baseline a). The fair CRPS (Ferro 2014) divides by n(n-1) instead. Comparisons between equal-sized sets
(recent, random) are affected equally on both sides. The choice recorded in reports/validation_set_v1.md
does not change; this only measures how much the skill vs "all of history" moves.

    python -m src.validation.fair_crps       (uses data/validation/features.parquet and outcomes.parquet)

Writes reports/validation_set_v1_fair_crps/<YYYYMMDD-HHMM>.md and .log.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from src.config import REPO_ROOT, load_config
from src.validation import walkforward as wfm
from src.validation.outcomes import load_outcomes
from src.validation.selection import VARIANTS, PickRules

OUT = REPO_ROOT / "data" / "validation"
REPORTS = REPO_ROOT / "reports" / "validation_set_v1_fair_crps"


def crps_fair(sample, y: float) -> float:
    """Fair (unbiased) empirical CRPS: mean|x_i - y| - sum_{i,j}|x_i - x_j| / (2 n (n - 1))."""
    x = np.sort(np.asarray(sample, dtype=float))
    n = len(x)
    if n < 2:
        return float(np.mean(np.abs(x - y)))
    i = np.arange(n)
    pair_sum = 2.0 * np.sum((2 * i - n + 1) * x)
    return float(np.mean(np.abs(x - y)) - pair_sum / (2.0 * n * (n - 1)))


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    REPORTS.mkdir(parents=True, exist_ok=True)
    md, lg = REPORTS / f"{stamp}.md", REPORTS / f"{stamp}.log"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(lg), logging.StreamHandler()])
    log = logging.getLogger("fair_crps")
    t_run = time.time()
    cfg = load_config()
    v = cfg["validation"]
    wf = v["walkforward"]
    t_star = pd.Timestamp(v["live_start"], tz="UTC")
    holdout = t_star - pd.Timedelta(days=v["holdout_days"])
    earliest = pd.Timestamp(v["pool_earliest"] + f" {v['grid_hour_utc']:02d}:00", tz="UTC")
    rules = PickRules(v["k"], v["min_separation_days"], v["span_days"], v["max_per_span"], v["horizon_days"])
    feats = pd.read_parquet(OUT / "features.parquet")
    outcomes = load_outcomes(OUT / "outcomes.parquet")
    dates = wfm.test_dates(wf["start"], holdout, v["horizon_days"], wf["step_days"], v["grid_hour_utc"])
    variants = {"CORE": VARIANTS["CORE"]}
    periods = {"SCREEN": (dates[0], pd.Timestamp(wf["screen_end"] + " 23:59", tz="UTC")),
               "CONFIRM": (pd.Timestamp(wf["confirm_start"], tz="UTC"), dates[-1])}
    results = {}
    standard = wfm.crps
    try:
        for label, fn in (("standard (as in the build)", standard), ("fair", crps_fair)):
            wfm.crps = fn
            cr, _ = wfm.run_walkforward(feats, outcomes, variants, rules, dates, earliest, wf["random_draws"], wf["seed"])
            for base in wfm.BASELINES:
                for p, (lo, hi) in periods.items():
                    results[(label, base, p)] = wfm.skill(cr, "CORE", base, lo, hi, wf["bootstrap_reps"],
                                                          wf["bootstrap_block"], wf["seed"]).loc["MEAN"]
            log.info("scored with %s CRPS", label)
    finally:
        wfm.crps = standard

    lines = ["# Validation set v1: fair-CRPS side check", "",
             "Not part of the pre-registered rule; the recorded choice (CORE) does not change. "
             "Mean skill of CORE over Y1..Y8 [90% block-bootstrap interval]; > 0 means lookalikes beat the baseline.", "",
             "| Scoring | Baseline | SCREEN | CONFIRM |", "|---|---|---|---|"]
    for label in ("standard (as in the build)", "fair"):
        for base, desc in wfm.BASELINES.items():
            cells = []
            for p in periods:
                r = results[(label, base, p)]
                cells.append(f"{r['skill']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}]")
            lines.append(f"| {label} | {desc} | {cells[0]} | {cells[1]} |")
    lines += ["", "Reading: only the rows against baseline (a), all of pool_D, can move much; (b) and (c) use 25-window "
              "sets on both sides, so the bias largely cancels there.", "", f"Runtime {time.time() - t_run:.0f} s."]
    md.write_text("\n".join(lines) + "\n")
    log.info("report: %s", md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
