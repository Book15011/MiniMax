"""Competition-style score (docs/EVALUATION.md section 3): return gate, CS, HEADLINE, gates, paired comparison.

- Return gate per window: gate_w = 1 if R_w >= max(floor, median of the field's R_w), else 0 (floor 0).
- CS_w(v) = gate_w * Composite_w(v), for every variant v and convention.
- HEADLINE(v) = 0.70 * weighted mean of CS with LIVE-LIKE weights + 0.30 * weighted mean with RECENCY weights.
- Gates G1-G6 (all must pass to be eligible); thresholds in config scoring.gates.
- compare: HEADLINE(primary) difference of two models with a weighted moving-block bootstrap interval.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def field_median(field_R: pd.DataFrame) -> pd.Series:
    """Median of the field's R in each window (rows = windows, columns = benchmarks)."""
    return field_R.median(axis=1)


def return_gate(R: pd.Series, field_med: pd.Series, floor: float = 0.0) -> pd.Series:
    return (R >= np.maximum(floor, field_med)).astype(int)


def weighted_mean(x, w) -> float:
    x, w = np.asarray(x, dtype=float), np.asarray(w, dtype=float)
    return float((x * w).sum() / w.sum())


def headline(cs: pd.Series, w_live: pd.Series, w_rec: pd.Series, split: dict) -> dict:
    """Weights may be unnormalized; each layer divides by its own weight sum (renormalizes over the windows given)."""
    live = weighted_mean(cs, w_live.reindex(cs.index))
    rec = weighted_mean(cs, w_rec.reindex(cs.index))
    return {"headline": split["live_like"] * live + split["recency"] * rec, "live_like": live, "recency": rec}


def regime_grid(R: pd.Series, regime: pd.Series) -> pd.DataFrame:
    """Median R and count per ex-post regime cell (rows: BTC return tercile, columns: volatility tercile)."""
    df = pd.DataFrame({"R": R, "regime": regime}).dropna()
    parts = df.regime.str.split("/", expand=True)
    g = df.assign(ret=parts[0], vol=parts[1]).groupby(["ret", "vol"]).R.agg(["median", "count"])
    rows, cols = ["down", "flat", "up"], ["lowvol", "midvol", "highvol"]
    med = g["median"].unstack().reindex(index=rows, columns=cols)
    cnt = g["count"].unstack().reindex(index=rows, columns=cols).fillna(0).astype(int)
    return pd.concat({"median": med, "count": cnt}, axis=1)


def gates(win: pd.DataFrame, btc: pd.DataFrame, regime: pd.Series, stress: pd.DatetimeIndex, long_only: dict,
          leak: dict, g: dict) -> dict:
    """win, btc: per-window tables (index = window start) of the model and of BTC_HOLD on the same windows."""
    out = {}
    g1 = g["G1"]
    ok = win.active_days >= g1["min_active_days"]
    share = float(ok.mean())
    guard_share = float(win.guard_days.sum() / max(win.active_days.sum(), 1))
    out["G1"] = {"pass": share >= g1["share_of_windows"],
                 "detail": f"{share:.1%} of {len(win)} windows have >= {g1['min_active_days']} active days "
                           f"(need {g1['share_of_windows']:.0%}); worst {int(win.active_days.min())}",
                 "share": share, "min_active_days": int(win.active_days.min()),
                 "guard_share_of_active_days": guard_share,
                 "relies_on_guard": guard_share > g1["guard_flag_share"]}
    worst, bworst = float(win.R.min()), float(btc.R.min())
    out["G2"] = {"pass": worst > bworst, "detail": f"worst 14-day R {worst:+.2%} vs BTC_HOLD {bworst:+.2%} (must be higher)",
                 "worst": worst, "btc_worst": bworst, "worst_start": str(win.R.idxmin())}
    grid = regime_grid(win.R, regime)
    med = grid["median"]
    low = med.stack().min()
    bad = [f"{r}/{c} {med.loc[r, c]:+.1%}" for r in med.index for c in med.columns
           if pd.notna(med.loc[r, c]) and med.loc[r, c] < g["G3"]["min_cell_median_return"]]
    out["G3"] = {"pass": not bad, "detail": (f"cells below {g['G3']['min_cell_median_return']:+.0%}: " + ", ".join(bad))
                 if bad else f"lowest cell median {low:+.2%} (limit {g['G3']['min_cell_median_return']:+.0%})",
                 "lowest_cell_median": float(low), "failing_cells": bad}
    out["G4"] = long_only
    out["G5"] = {"pass": leak["pass"], "detail": _leak_detail(leak), **leak}
    s, bs = win.R.reindex(stress), btc.R.reindex(stress)
    if s.isna().any() or bs.isna().any():
        out["G6"] = {"pass": False, "detail": f"{int(s.isna().sum())} STRESS windows were not scored"}
    else:
        w_ok, m_ok = s.min() >= bs.min(), s.median() >= bs.median()
        out["G6"] = {"pass": bool(w_ok and m_ok),
                     "detail": f"STRESS (n={len(s)}): worst {s.min():+.2%} vs BTC_HOLD {bs.min():+.2%}, "
                               f"median {s.median():+.2%} vs {bs.median():+.2%} (both must be >=)",
                     "worst": float(s.min()), "median": float(s.median()),
                     "btc_worst": float(bs.min()), "btc_median": float(bs.median())}
    for v in out.values():
        v["pass"] = bool(v["pass"])
    return out


def _leak_detail(leak: dict) -> str:
    if leak["pass"]:
        return f"{leak['decisions']} decisions: reproducible, unchanged under future noise, no I/O"
    parts = []
    for k in ("errors", "determinism", "future_noise", "io"):
        if leak.get(k):
            parts.append(f"{k}: {len(leak[k])} ({leak[k][0]})")
    return "; ".join(parts)


def block_bootstrap(d: pd.Series, w_live: pd.Series, w_rec: pd.Series, split: dict, block: int, reps: int,
                    level: float, seed: int) -> dict:
    """Paired HEADLINE difference d = CS_a - CS_b per window (windows in time order). Moving blocks of `block`
    consecutive windows are drawn with replacement until the series is full; each draw recomputes the weighted
    HEADLINE of d with the drawn windows' own weights. Returns the point estimate and the central `level` interval."""
    d = d.sort_index()
    x = d.to_numpy(dtype=float)
    wl = w_live.reindex(d.index).to_numpy(dtype=float)
    wr = w_rec.reindex(d.index).to_numpy(dtype=float)
    n = len(x)
    L = min(block, n)
    rng = np.random.default_rng(seed)
    nb = -(-n // L)
    stats = np.empty(reps)
    for b in range(reps):
        starts = rng.integers(0, n - L + 1, size=nb)
        ix = (starts[:, None] + np.arange(L)[None, :]).ravel()[:n]
        stats[b] = (split["live_like"] * (x[ix] * wl[ix]).sum() / wl[ix].sum()
                    + split["recency"] * (x[ix] * wr[ix]).sum() / wr[ix].sum())
    point = split["live_like"] * weighted_mean(x, wl) + split["recency"] * weighted_mean(x, wr)
    a = (1.0 - level) / 2.0
    lo, hi = np.quantile(stats, [a, 1.0 - a])
    return {"diff": float(point), "lo": float(lo), "hi": float(hi), "level": level, "block": L, "reps": reps,
            "seed": seed, "n_windows": n, "share_above_0": float((stats > 0).mean())}
