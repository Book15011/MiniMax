"""Live-like weights v1 (PART 0.6-0.9), exactly as pre-registered in reports/live_like_v1.md.

    python -m src.validation.live_like --asof "2026-10-03 16:00" [--work-dir data/validation]

Needs, for the same --asof: the validation build (validation/validation_set_v1.json and the tables in
--work-dir) and the event calendar (python -m src.validation.events).
Writes validation/live_like_v1.json and reports/live_like_v1.md (the pre-registration block is kept verbatim).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import re
import subprocess
import sys
import time

import numpy as np
import pandas as pd

from src.config import REPO_ROOT, load_config, resolve
from src.validation import events as events_mod
from src.validation.crps import GridKernelCRPS, crps_fair, to_grid
from src.validation.features import CORE_GROUPS
from src.validation.outcomes import load_outcomes
from src.validation.selection import PickRules, active_features, mid_rank_pct, pool_index, select_lookalikes
from src.validation.sets import greedy_spaced
from src.validation.walkforward import skill_arrays, test_dates

log = logging.getLogger("live_like")
REPORT = REPO_ROOT / "reports" / "live_like_v1.md"
ARTIFACT = REPO_ROOT / "validation" / "live_like_v1.json"
VALIDATION = REPO_ROOT / "validation" / "validation_set_v1.json"
PREREG_RE = re.compile(r"<!-- PREREG:BEGIN -->.*?<!-- PREREG:END -->", re.S)

YS = ["Y2", "Y5", "Y8"]
HLS = [60, 120, 180, 365, 730, math.inf]
BANDWIDTHS = [0.05, 0.10, 0.15, 0.20]
DEFAULT_B = 0.10
MIN_STATE = 30
STATE_BLOCK = 14
DAY = pd.Timedelta(days=1)


def hl_name(hl: float) -> str:
    return "REC_inf" if not np.isfinite(hl) else f"REC_{int(hl)}"


CANDIDATES = ["LOOK"] + [hl_name(h) for h in HLS] + ["MIX"]


# ---------------------------------------------------------------- weights and densities
def recency_weights(ends: pd.DatetimeIndex, ref: pd.Timestamp, hl: float) -> np.ndarray:
    """0.5^(age/HL), age = days from each window's end to ref; HL = inf -> equal weights. Sums to 1."""
    if not np.isfinite(hl):
        return np.full(len(ends), 1.0 / len(ends))
    age = np.asarray((ref - ends) / DAY, dtype=float)
    w = 0.5 ** (age / hl)
    return w / w.sum()


def ensemble_weights(name: str, pool: pd.DatetimeIndex, look: pd.DatetimeIndex, ref: pd.Timestamp,
                     horizon: pd.Timedelta, hl_star: float | None = None) -> np.ndarray:
    look_w = pool.isin(look).astype(float)
    look_w /= look_w.sum()
    if name == "LOOK":
        return look_w
    if name.startswith("REC_"):
        hl = math.inf if name == "REC_inf" else float(name[4:])
        return recency_weights(pool + horizon, ref, hl)
    if name == "MIX":
        return 0.5 * look_w + 0.5 * recency_weights(pool + horizon, ref, hl_star)
    raise ValueError(name)


def pct_in(ref: np.ndarray, x: np.ndarray) -> np.ndarray:
    return mid_rank_pct(np.asarray(ref, float)[:, None], np.asarray(x, float)[:, None])[:, 0]


def kde_density(points: np.ndarray, members: np.ndarray, omega: np.ndarray, b: float) -> np.ndarray:
    """Product-Gaussian kernel density f(u) = sum_i omega_i prod_d phi((u_d - u_id)/b)/b, at each point."""
    keep = omega > 0
    m, om = members[keep], omega[keep]
    out = np.zeros(len(points))
    for s in range(0, len(points), 256):
        d = (points[s:s + 256, None, :] - m[None, :, :]) / b
        k = np.exp(-0.5 * (d ** 2).sum(axis=2)) / (b * math.sqrt(2 * math.pi)) ** points.shape[1]
        out[s:s + 256] = k @ om
    return out


def mixture_quantiles(members: np.ndarray, omega: np.ndarray, b: float, qs=(0.1, 0.5, 0.9)) -> list[float]:
    """Quantiles of the 1-D mixture sum_i omega_i N(u_i, b^2), by bisection."""
    keep = omega > 0
    u, om = members[keep], omega[keep]
    erf = np.vectorize(math.erf, otypes=[float])

    def cdf(q: float) -> float:
        return float(np.dot(om, 0.5 * (1 + erf((q - u) / (b * math.sqrt(2))))))

    out = []
    for q in qs:
        lo, hi = float(u.min() - 8 * b), float(u.max() + 8 * b)
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if cdf(mid) < q else (lo, mid)
        out.append(0.5 * (lo + hi))
    return out


def pct_to_value(u: float, pool_values: np.ndarray) -> float:
    """Pool's empirical quantile function: linear between sorted values at (k - 1/2)/n, clipped."""
    s = np.sort(pool_values)
    n = len(s)
    return float(np.interp(min(max(u, 0.0), 1.0), (np.arange(n) + 0.5) / n, s))


def direction_normalise(base: np.ndarray, up: np.ndarray, p_up: float) -> np.ndarray:
    """Rescale so up windows sum to p_up and the rest to 1 - p_up (exactly)."""
    w = np.zeros_like(base, dtype=float)
    w[up] = base[up] / base[up].sum() * p_up
    w[~up] = base[~up] / base[~up].sum() * (1.0 - p_up)
    return w


def trend_state(t1: float, t2: float, cuts: np.ndarray) -> tuple[int, bool]:
    return int(1 + (t2 > cuts[0]) + (t2 > cuts[1])), bool(t1 > 0)


def p_up_for(state: tuple[int, bool], ref_t1: np.ndarray, ref_t2: np.ndarray, ref_up_y1: np.ndarray,
             cuts: np.ndarray) -> tuple[float, int, bool, np.ndarray]:
    terc = 1 + (ref_t2 > cuts[0]).astype(int) + (ref_t2 > cuts[1]).astype(int)
    match = (terc == state[0]) & ((ref_t1 > 0) == state[1])
    fallback = int(match.sum()) < MIN_STATE
    if fallback:
        match = terc == state[0]
    return float(ref_up_y1[match].mean()), int(match.sum()), fallback, match


# ---------------------------------------------------------------- walk-forward
def run_walkforward(feats, outcomes, dates, rules, earliest, horizon, periods, boot):
    act = active_features(CORE_GROUPS)
    cases, skipped = [], []
    for D in dates:
        pool = pool_index(feats, CORE_GROUPS, D, rules.horizon_days, earliest)
        if len(pool) < rules.k or D not in outcomes.index or feats.loc[D, act].isna().any():
            skipped.append((str(D), "pool/state/outcome unavailable"))
            continue
        picks, _ = select_lookalikes(feats.loc[pool, act], feats.loc[D, act], CORE_GROUPS, rules)
        if len(picks) < rules.k:
            skipped.append((str(D), f"only {len(picks)} lookalikes"))
            continue
        cases.append({"D": D, "pool": pool, "look": pd.DatetimeIndex(picks.t0)})
    Dix = pd.DatetimeIndex([c["D"] for c in cases])
    masks = {p: np.asarray((Dix >= lo) & (Dix <= hi)) for p, (lo, hi) in periods.items()}

    def crps_matrix(name: str, hl_star=None) -> np.ndarray:
        M = np.zeros((len(cases), len(YS)))
        for i, c in enumerate(cases):
            w = ensemble_weights(name, c["pool"], c["look"], c["D"], horizon, hl_star)
            keep = w > 0
            for j, y in enumerate(YS):
                x = outcomes.loc[c["pool"], y].to_numpy()
                M[i, j] = crps_fair(x[keep], float(outcomes.at[c["D"], y]), w[keep])
        return M

    L = {n: crps_matrix(n) for n in CANDIDATES if n != "MIX"}
    base = L["REC_inf"]

    def table(M: np.ndarray, B: np.ndarray) -> dict:
        return {p: skill_arrays(M[m], B[m], YS, *boot) for p, m in masks.items()}

    sk = {n: table(L[n], base) for n in L}
    rec = [hl_name(h) for h in HLS]
    hl_star_name = max(rec, key=lambda n: (sk[n]["SCREEN"].loc["MEAN", "skill"], -rec.index(n)))
    hl_star = math.inf if hl_star_name == "REC_inf" else float(hl_star_name[4:])
    L["MIX"] = crps_matrix("MIX", hl_star)
    sk["MIX"] = table(L["MIX"], base)
    best = max(CANDIDATES, key=lambda n: (sk[n]["SCREEN"].loc["MEAN", "skill"], -CANDIDATES.index(n)))
    best_confirm = float(sk[best]["CONFIRM"].loc["MEAN", "skill"])
    chosen = best if best_confirm > 0 else "LOOK"
    reason = (f"{best} had the best SCREEN mean skill and beats the whole pool in CONFIRM ({best_confirm:+.4f})"
              if chosen == best else
              f"{best} had the best SCREEN mean skill but its CONFIRM skill ({best_confirm:+.4f}) is not > 0; "
              "fall back to LOOK")

    # bandwidth, percentile space, chosen ensemble
    K = {b: np.zeros((len(cases), len(YS))) for b in BANDWIDTHS}
    Bp = np.zeros((len(cases), len(YS)))
    for i, c in enumerate(cases):
        n = len(c["pool"])
        w = ensemble_weights(chosen, c["pool"], c["look"], c["D"], horizon, hl_star)
        kernels = {b: GridKernelCRPS(2 * n, b) for b in BANDWIDTHS}
        for j, y in enumerate(YS):
            vals = outcomes.loc[c["pool"], y].to_numpy()
            u = pct_in(vals, vals)
            v = float(pct_in(vals, np.array([outcomes.at[c["D"], y]]))[0])
            pos, obs = to_grid(u, n), int(to_grid(np.array([v]), n)[0])
            Bp[i, j] = crps_fair(u, v)
            for b in BANDWIDTHS:
                K[b][i, j] = kernels[b](pos, w, obs)
    skb = {b: table(K[b], Bp) for b in BANDWIDTHS}
    b_best = max(BANDWIDTHS, key=lambda b: (skb[b]["SCREEN"].loc["MEAN", "skill"], -b))
    b_conf = float(skb[b_best]["CONFIRM"].loc["MEAN", "skill"])
    b_chosen = b_best if b_conf > 0 else DEFAULT_B
    b_reason = (f"b = {b_best} had the best SCREEN mean skill and beats the whole pool in CONFIRM ({b_conf:+.4f})"
                if b_chosen == b_best else
                f"b = {b_best} had the best SCREEN mean skill but its CONFIRM skill ({b_conf:+.4f}) is not > 0; "
                f"default b = {DEFAULT_B}")
    return {"cases": len(cases), "skipped": skipped, "dates": [str(d) for d in Dix],
            "ensemble_skill": sk, "hl_star": hl_star_name, "ensemble_best_screen": best, "ensemble": chosen,
            "ensemble_reason": reason, "hl_star_value": hl_star,
            "bandwidth_skill": skb, "bandwidth_best_screen": b_best, "bandwidth": b_chosen,
            "bandwidth_reason": b_reason}


def direction_test(feats, outcomes, dates, rules, earliest, periods, boot) -> dict:
    rows = []
    for D in dates:
        pool = pool_index(feats, CORE_GROUPS, D, rules.horizon_days, earliest)
        if len(pool) == 0 or D not in outcomes.index or not np.isfinite(feats.loc[D, ["T1", "T2"]]).all():
            continue
        t1, t2, up = (feats.loc[pool, "T1"].to_numpy(), feats.loc[pool, "T2"].to_numpy(),
                      outcomes.loc[pool, "Y1"].to_numpy() > 0)
        cuts = np.quantile(t2, [1 / 3, 2 / 3])
        state = trend_state(feats.at[D, "T1"], feats.at[D, "T2"], cuts)
        p, n, fb, _ = p_up_for(state, t1, t2, up, cuts)
        o = float(outcomes.at[D, "Y1"] > 0)
        rows.append({"D": D, "p_up": p, "base": float(up.mean()), "o": o, "n_state": n, "fallback": fb,
                     "state": f"T2 tercile {state[0]}, T1 {'up' if state[1] else 'down'}"})
    df = pd.DataFrame(rows)
    bs_p, bs_b = ((df.p_up - df.o) ** 2).to_numpy()[:, None], ((df.base - df.o) ** 2).to_numpy()[:, None]
    res = {}
    for p, (lo, hi) in periods.items():
        m = np.asarray((df.D >= lo) & (df.D <= hi))
        res[p] = skill_arrays(bs_p[m], bs_b[m], ["Brier"], *boot).loc["Brier"]
    passed = bool(all(res[p]["skill"] > 0 for p in periods))
    return {"per_period": res, "passed": passed, "n_dates": int(len(df)),
            "fallback_share": float(df.fallback.mean()), "rows": df}


def state_interval(up_state: np.ndarray, seed: int, reps: int = 2000) -> tuple[float, float]:
    n = len(up_state)
    blk = min(STATE_BLOCK, n)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / blk))
    starts = rng.integers(0, n - blk + 1, size=(reps, nb))
    idx = (starts[:, :, None] + np.arange(blk)).reshape(reps, -1)[:, :n]
    means = up_state[idx].mean(axis=1)
    return float(np.percentile(means, 5)), float(np.percentile(means, 95))


# ---------------------------------------------------------------- report helpers
def _cell(r) -> str:
    return "—" if not np.isfinite(r["skill"]) else f"{r['skill']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}]"


def _md(df: pd.DataFrame) -> str:
    cols = [df.index.name or ""] + [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for i, r in df.iterrows():
        cells = [str(i)] + [f"{x:.4f}" if isinstance(x, (float, np.floating)) else str(x) for x in r.tolist()]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.rstrip()


def _sha_obj(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


# ---------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--asof", required=True, help='UTC, e.g. "2026-10-03 16:00"; must match the validation artifact')
    ap.add_argument("--work-dir", default="data/validation", help="the validation build's --out-dir")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    t_run = time.time()

    prereg = PREREG_RE.search(REPORT.read_text()) if REPORT.exists() else None
    if prereg is None:
        raise SystemExit(f"{REPORT} has no pre-registration block")
    va = json.loads(VALIDATION.read_text())
    asof = pd.Timestamp(args.asof, tz="UTC")
    if va["asof_requested"] != str(asof):
        raise SystemExit(f"validation artifact is for as-of {va['asof_requested']}, not {asof}: rerun the build first")
    if not events_mod.OUT.exists():
        raise SystemExit("validation/event_calendar_v1.csv is missing: run python -m src.validation.events")

    cfg = load_config()
    v = cfg["validation"]
    wf = v["walkforward"]
    work = resolve(args.work_dir)
    feats = pd.read_parquet(work / "features.parquet")
    outcomes = load_outcomes(work / "outcomes.parquet")
    t_star, holdout = pd.Timestamp(va["live_start_T_star"]), pd.Timestamp(va["holdout_H"])
    state_t = pd.Timestamp(va["state_time"])
    horizon = pd.Timedelta(days=v["horizon_days"])
    earliest = pd.Timestamp(v["pool_earliest"] + f" {v['grid_hour_utc']:02d}:00", tz="UTC")
    rules = PickRules(v["k"], v["min_separation_days"], v["span_days"], v["max_per_span"], v["horizon_days"])
    dates = test_dates(wf["start"], holdout, v["horizon_days"], wf["step_days"], v["grid_hour_utc"])
    periods = {"SCREEN": (dates[0], pd.Timestamp(wf["screen_end"] + " 23:59", tz="UTC")),
               "CONFIRM": (pd.Timestamp(wf["confirm_start"], tz="UTC"), dates[-1])}
    boot = (wf["bootstrap_reps"], wf["bootstrap_block"], wf["seed"])

    pool = pool_index(feats, CORE_GROUPS, holdout, v["horizon_days"], earliest)
    if len(pool) != va["pool"]["n"] or str(pool.max()) != va["pool"]["last_start"]:
        raise SystemExit("pool differs from the validation artifact: rebuild with the same --asof")
    look = pd.DatetimeIndex(pd.to_datetime([w["start"] for w in va["windows"]]))
    assert look.isin(pool).all() and ((pool + horizon) <= holdout).all()

    log.info("0.6 walk-forward over %d test dates", len(dates))
    wfres = run_walkforward(feats, outcomes, dates, rules, earliest, horizon, periods, boot)
    log.info("ensemble %s (%s); bandwidth %s", wfres["ensemble"], wfres["ensemble_reason"], wfres["bandwidth"])
    log.info("0.7 direction test")
    dres = direction_test(feats, outcomes, dates, rules, earliest, periods, boot)

    # ---- at T*
    b, ens = wfres["bandwidth"], wfres["ensemble"]
    omega = ensemble_weights(ens, pool, look, t_star, horizon, wfres["hl_star_value"])
    U = np.column_stack([pct_in(outcomes.loc[pool, y].to_numpy(), outcomes.loc[pool, y].to_numpy()) for y in YS])
    forecast = {}
    for j, y in enumerate(YS):
        q10, q50, q90 = mixture_quantiles(U[:, j], omega, b)
        vals = outcomes.loc[pool, y].to_numpy()
        forecast[y] = {"p10_pct": min(max(q10, 0), 1), "median_pct": min(max(q50, 0), 1), "p90_pct": min(max(q90, 0), 1),
                       "p10": pct_to_value(q10, vals), "median": pct_to_value(q50, vals),
                       "p90": pct_to_value(q90, vals), "pool_median": float(np.median(vals))}

    t1p, t2p = feats.loc[pool, "T1"].to_numpy(), feats.loc[pool, "T2"].to_numpy()
    upp = outcomes.loc[pool, "Y1"].to_numpy() > 0
    cuts = np.quantile(t2p, [1 / 3, 2 / 3])
    st = trend_state(feats.at[state_t, "T1"], feats.at[state_t, "T2"], cuts)
    p_up, n_state, fb, match = p_up_for(st, t1p, t2p, upp, cuts)
    p_lo, p_hi = state_interval(upp[match].astype(float), wf["seed"])

    base = kde_density(U, U, omega, b)
    w = direction_normalise(base, upp, p_up) if dres["passed"] else base / base.sum()
    eff_n = float(w.sum() ** 2 / (w ** 2).sum())
    ws = pd.Series(w, index=pool)
    top = greedy_spaced(ws.sort_values(ascending=False, kind="stable").index, 25, v["min_separation_days"])

    ev = events_mod.load()
    ev_status = json.loads(events_mod.STATUS.read_text()) if events_mod.STATUS.exists() else {}
    live_ev = ev[(ev.time_utc > t_star) & (ev.time_utc <= t_star + horizon)]

    def events_in(t0):
        e = ev[(ev.time_utc > t0) & (ev.time_utc <= t0 + horizon)]
        return {"CPI": int((e.event == "CPI").sum()), "FOMC_MINUTES": int((e.event == "FOMC_MINUTES").sum())}

    top_rows = [{"rank": i + 1, "start": str(t), "end": str(t + horizon), "weight": float(ws[t]),
                 "btc_up": bool(outcomes.at[t, "Y1"] > 0), **{y: float(outcomes.at[t, y]) for y in ["Y1", *YS]},
                 **events_in(t)} for i, t in enumerate(top)]

    def sk_json(tbl):
        return {p: {k: {c: float(x) for c, x in r.items()} for k, r in t.iterrows()} for p, t in tbl.items()}

    head = _git("rev-parse", "HEAD")
    prereg_commit = _git("log", "--diff-filter=A", "--format=%H", "--", "reports/live_like_v1.md").splitlines()
    dirty = [ln for ln in _git("status", "--porcelain").splitlines()
             if not ln[3:].startswith(("reports/", "validation/"))]
    inputs = {
        "validation_artifact_sha256": hashlib.sha256(VALIDATION.read_bytes()).hexdigest(),
        "outcomes_sha256": _sha_obj(outcomes.loc[pool, ["Y1", *YS]].round(12).to_numpy().tolist()),
        "trend_features_sha256": _sha_obj(feats.loc[pool.union(pd.DatetimeIndex(dates)).intersection(feats.index),
                                                    ["T1", "T2"]].round(12).to_numpy().tolist()),
        "event_calendar_sha256": hashlib.sha256(events_mod.OUT.read_bytes()).hexdigest(),
    }
    artifact = {
        "version": "live_like_v1", "asof": str(asof), "state_time": str(state_t), "T_star": str(t_star),
        "holdout_H": str(holdout), "git_commit": head, "git_dirty_paths": dirty,
        "prereg_commit": prereg_commit[-1] if prereg_commit else None,
        "prereg_sha256": hashlib.sha256(prereg.group(0).encode()).hexdigest(), "inputs": inputs,
        "rules": {"outcomes_forecast": YS, "half_lives_days": [str(h) for h in HLS], "bandwidths": BANDWIDTHS,
                  "default_bandwidth": DEFAULT_B, "min_state_windows": MIN_STATE, "k": rules.k,
                  "periods": {p: [str(a), str(b_)] for p, (a, b_) in periods.items()},
                  "bootstrap": {"reps": boot[0], "block": boot[1], "seed": boot[2]}, "crps": "weighted fair"},
        "walkforward": {"test_dates_used": wfres["cases"], "skipped": wfres["skipped"]},
        "ensemble": {"skill": {n: sk_json(t) for n, t in wfres["ensemble_skill"].items()},
                     "hl_star": wfres["hl_star"], "best_screen": wfres["ensemble_best_screen"],
                     "chosen": ens, "reason": wfres["ensemble_reason"]},
        "bandwidth": {"skill": {str(k): sk_json(t) for k, t in wfres["bandwidth_skill"].items()},
                      "best_screen": wfres["bandwidth_best_screen"], "chosen": b, "reason": wfres["bandwidth_reason"]},
        "forecast": forecast,
        "direction": {"brier_skill": {p: {c: float(x) for c, x in r.items()} for p, r in dres["per_period"].items()},
                      "passed": dres["passed"], "used": dres["passed"], "n_test_dates": dres["n_dates"],
                      "fallback_share_in_test": dres["fallback_share"],
                      "at_state_time": {"state": f"T2 tercile {st[0]}, T1 {'up' if st[1] else 'down'}",
                                        "p_up": p_up, "n_windows": n_state, "tercile_only_fallback": fb,
                                        "interval_90": [p_lo, p_hi], "unconditional_up_share": float(upp.mean())}},
        "events": {"calendar_rows": int(len(ev)), "status": ev_status,
                   "in_live_window": [{"event": r.event, "time_utc": str(r.time_utc), "local": r.local}
                                      for r in live_ev.itertuples()],
                   "used_in_weights": False},
        "weights": {"effective_n": eff_n, "n_windows": int(len(ws)), "direction_factor_applied": dres["passed"],
                    "top25": top_rows, "all": {str(t): float(x) for t, x in ws.items()}},
    }
    artifact["sha256"] = _sha_obj({k: x for k, x in artifact.items() if k != "sha256"})
    ARTIFACT.write_text(json.dumps(artifact, indent=1, default=str) + "\n")

    # ---- report
    o = ["# Live-like weights v1", "",
         f"As-of **{asof}** · state time {state_t} · T* = {t_star} · H = {holdout} · code `{head[:12]}` · "
         f"pre-registration `{(artifact['prereg_commit'] or '?')[:12]}` · artifact sha256 `{artifact['sha256'][:12]}`. "
         "Generated by `python -m src.validation.live_like`; do not edit by hand.", "", prereg.group(0), "",
         "## 0.6 Forecast ensemble (weighted fair CRPS)", "",
         f"Test dates used: {wfres['cases']} (skipped {len(wfres['skipped'])}: LOOK could not pick 25 or no data). "
         "Mean skill over Y2, Y5, Y8 vs the whole pool [90% block-bootstrap interval]; > 0 = better than the whole pool.", ""]
    t = pd.DataFrame({n: {f"{p} mean": _cell(wfres["ensemble_skill"][n][p].loc["MEAN"]) for p in periods}
                      | {f"CONFIRM {y}": _cell(wfres["ensemble_skill"][n]["CONFIRM"].loc[y]) for y in YS}
                      for n in CANDIDATES}).T
    t.index.name = "candidate"
    o += [_md(t), "", f"- Best half-life in SCREEN (for MIX): **{wfres['hl_star']}**.",
          f"- Chosen ensemble: **{ens}** — {wfres['ensemble_reason']}.", ""]
    t = pd.DataFrame({f"b = {k}": {f"{p} mean": _cell(wfres["bandwidth_skill"][k][p].loc["MEAN"]) for p in periods}
                      for k in BANDWIDTHS}).T
    t.index.name = "bandwidth (kernel fair CRPS, percentile space)"
    o += [_md(t), "", f"- Chosen bandwidth: **{b}** — {wfres['bandwidth_reason']}.", ""]
    t = pd.DataFrame({y: {"median (pct)": f"{forecast[y]['median']:.4f} ({forecast[y]['median_pct']:.0%})",
                          "10% (pct)": f"{forecast[y]['p10']:.4f} ({forecast[y]['p10_pct']:.0%})",
                          "90% (pct)": f"{forecast[y]['p90']:.4f} ({forecast[y]['p90_pct']:.0%})",
                          "pool median": f"{forecast[y]['pool_median']:.4f}"} for y in YS}).T
    t.index = ["Y2 BTC realised vol (ann.)", "Y5 dispersion (14d)", "Y8 BTC max rebound"]
    t.index.name = f"forecast for {t_star:%Y-%m-%d} + 14 d"
    o += [_md(t), "", "Percentiles are within the whole pool (all history before H).", ""]

    o += ["## 0.7 Direction mix (Brier test)", ""]
    t = pd.DataFrame({p: {"Brier skill of trend-state p_up vs unconditional": _cell(r)}
                      for p, r in dres["per_period"].items()}).T
    t.index.name = "period"
    o += [_md(t), "",
          f"- Test dates: {dres['n_dates']}; tercile-only fallback used at {dres['fallback_share']:.0%} of them.",
          f"- Verdict: **{'PASS — p_up is used' if dres['passed'] else 'FAIL — no direction reweighting'}** "
          "(rule: Brier skill > 0 in both SCREEN and CONFIRM).",
          f"- At the state time: {artifact['direction']['at_state_time']['state']}; p_up = {p_up:.3f} "
          f"[{p_lo:.3f}, {p_hi:.3f}] from {n_state} windows{' (tercile only)' if fb else ''}; unconditional "
          f"{upp.mean():.3f}. {'Used.' if dres['passed'] else 'Reported only; not used.'}", ""]

    o += ["## 0.8 Event calendar (proposed view field; not used in the weights)", ""]
    evs = ev_status
    o += [f"- BLS CPI schedule ({events_mod.BLS_URL}): **{evs.get('bls', '?')}** from this server — not reachable, "
          "so CPI dates/times come from the St. Louis Fed FRED release calendar (release 10, US Central Time). "
          f"Coverage: {evs.get('cpi_coverage', '?')}.",
          "- FOMC minutes (Federal Reserve Board): dates from the FOMC calendars' \"Minutes (Released …)\" notes, "
          "times from each minutes press release, not-yet-released minutes from the monthly event calendars. "
          f"Cross-check: {evs.get('fomc_cross_check')}.",
          f"- Rows: {evs.get('rows')} ({evs.get('counts')}); problems: {evs.get('problems') or 'none'}.",
          f"- Checks: {evs.get('checks')}.",
          "- In the live window: " + ("; ".join(f"{r.event} {r.time_utc:%Y-%m-%d %H:%M} UTC ({r.local})"
                                             for r in live_ev.itertuples()) or "none"), ""]

    o += ["## 0.9 Live-like weights", "",
          f"- Windows: {len(ws)} (every pool window; no CPI filter). Direction factor applied: {dres['passed']}.",
          f"- Effective number of windows (Σw)²/Σw²: **{eff_n:.1f}**.", ""]
    t = pd.DataFrame(top_rows).set_index("rank")
    t["start"] = pd.to_datetime(t["start"]).dt.strftime("%Y-%m-%d")
    t["end"] = pd.to_datetime(t["end"]).dt.strftime("%Y-%m-%d")
    t["weight"] = t["weight"] * 1000
    t = t.rename(columns={"weight": "weight ‰"})
    t.index.name = "#"
    o += ["Top 25 by weight (greedy, starts ≥ 14 days apart):", "", _md(t), "",
          f"Runtime {time.time() - t_run:.0f} s.", ""]
    REPORT.write_text("\n".join(o))
    log.info("wrote %s and %s (sha256 %s)", ARTIFACT, REPORT, artifact["sha256"][:12])
    return 0


if __name__ == "__main__":
    sys.exit(main())
