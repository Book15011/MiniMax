"""Per-window metrics of the competition-style score (docs/EVALUATION.md section 2). All constants: config `scoring:`.

From the engine's hourly equity E_0..E_336 of one window (E_0 = equity before the first trade):
- daily equity D_d = E_(24d), d = 0..14; daily returns r_d = D_d / D_(d-1) - 1; hourly returns h_k = E_k / E_(k-1) - 1
- R = E_336 / E_0 - 1 (mark-to-market, primary); R_liq = (E_336 - liquidation_cost * gross notional at the end) / E_0 - 1
- MDD = max over k of (1 - E_k / max_(j<=k) E_j), E_0 included
For a return series x of length n: m = mean, s = sqrt(sum((x - m)^2) / (n - 1)), dd = sqrt(sum(min(x, 0)^2) / n).
Sharpe = m / s and Sortino = m / dd (risk-free 0), times sqrt(annualize); a ratio is 0 when m = 0.
Calmar = (m * annualize) / MDD ("mean") or R / MDD ("total"). Composite = 0.4 Sortino + 0.3 Sharpe + 0.3 Calmar.
Conventions set the denominators: FLOORED floors s, dd and MDD; POL is backtest/metrics.py's rule (MDD floored at
1e-4, s and dd unfloored, and a zero denominator gives a ratio of 0). A floor of 0 means "no floor".
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RATIOS = ("sharpe", "sortino", "calmar", "composite")
FLOORS = ("s_daily", "dd_daily", "s_hourly", "dd_hourly", "mdd")


def as_matrix(E) -> np.ndarray:
    E = np.asarray(E, dtype=float)
    return E[None, :] if E.ndim == 1 else E


def returns(E: np.ndarray, hours_per_day: int = 24) -> tuple[np.ndarray, np.ndarray]:
    """Daily and hourly returns, one row per window."""
    E = as_matrix(E)
    D = E[:, ::hours_per_day]
    return D[:, 1:] / D[:, :-1] - 1.0, E[:, 1:] / E[:, :-1] - 1.0


def moments(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """m, s (sample, n - 1) and dd (downside, target 0, over all n) of each row."""
    n = x.shape[1]
    m = x.mean(axis=1)
    s = np.sqrt(((x - m[:, None]) ** 2).sum(axis=1) / (n - 1))
    dd = np.sqrt((np.minimum(x, 0.0) ** 2).sum(axis=1) / n)
    return m, s, dd


def max_drawdown(E) -> np.ndarray:
    E = as_matrix(E)
    return (1.0 - E / np.maximum.accumulate(E, axis=1)).max(axis=1)


def ratio(num: np.ndarray, den: np.ndarray, floor: float) -> np.ndarray:
    """num / max(den, floor); with floor 0 a zero denominator gives 0. Always 0 when num is 0."""
    den = np.maximum(den, floor)
    out = np.divide(num, den, out=np.zeros(np.shape(num), dtype=float), where=den > 0)
    return np.where(num == 0.0, 0.0, out)


def floor_hits(den: np.ndarray, floor: float) -> np.ndarray:
    """Windows where the floor changed the denominator (or, unfloored, where the denominator is 0)."""
    return den < floor if floor > 0 else den == 0.0


def window_metrics(E, gross_end, sc: dict) -> pd.DataFrame:
    """One row per window: R, R_liq, MDD, the moments, and every ratio of every variant under every convention
    (columns '<convention>.<variant>.<ratio>'), plus floor hits ('<convention>.hit.<floor>')."""
    E = as_matrix(E)
    r, h = returns(E, int(sc["hours_per_day"]))
    R = E[:, -1] / E[:, 0] - 1.0
    gross_end = np.broadcast_to(np.asarray(gross_end, dtype=float), R.shape)
    R_liq = E[:, -1] * (1.0 - sc["liquidation_cost"] * gross_end) / E[:, 0] - 1.0
    mdd = max_drawdown(E)
    stats = {"daily": moments(r), "hourly": moments(h)}
    out = {"R": R, "R_liq": R_liq, "MDD": mdd}
    for kind, (m, s, dd) in stats.items():
        out.update({f"m_{kind}": m, f"s_{kind}": s, f"dd_{kind}": dd})
    wc = sc["composite"]
    for conv, fl in sc["conventions"].items():
        for v, spec in sc["variants"].items():
            kind, a = spec["returns"], float(spec["annualize"])
            m, s, dd = stats[kind]
            sharpe = ratio(m, s, fl[f"s_{kind}"]) * np.sqrt(a)
            sortino = ratio(m, dd, fl[f"dd_{kind}"]) * np.sqrt(a)
            if spec["calmar"] == "mean":
                calmar = ratio(m * a, mdd, fl["mdd"])
            elif spec["calmar"] == "total":
                calmar = ratio(R, mdd, fl["mdd"])
            else:
                raise ValueError(f"scoring.variants.{v}.calmar must be 'mean' or 'total'")
            out[f"{conv}.{v}.sharpe"] = sharpe
            out[f"{conv}.{v}.sortino"] = sortino
            out[f"{conv}.{v}.calmar"] = calmar
            out[f"{conv}.{v}.composite"] = wc["sortino"] * sortino + wc["sharpe"] * sharpe + wc["calmar"] * calmar
        for f in FLOORS:
            den = mdd if f == "mdd" else out[f]
            out[f"{conv}.hit.{f}"] = floor_hits(den, fl[f])
    return pd.DataFrame(out)
