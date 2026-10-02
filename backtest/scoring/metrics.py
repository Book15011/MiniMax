"""Per-window metrics of the competition-style score (docs/EVALUATION.md section 2). All constants: config `scoring:`.

From the engine's hourly equity E_0..E_336 of one window (E_0 = equity before the first trade):
- daily equity D_d = E at the day boundaries (day_points: the start, every 16:00 UTC inside the window for HKT days
  or every 00:00 UTC for UTC days, the end; 15 daily returns for a 12:00 UTC start, the first and last partial);
  daily returns r_d = D_d / D_(d-1) - 1; hourly returns h_k = E_k / E_(k-1) - 1
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


def clock_series(values, times: pd.DatetimeIndex, t0: pd.Timestamp, hours: int) -> np.ndarray:
    """Values recorded at `times` (the engine's steps) read at the clock hours t0 + k h, k = 0..hours: each one is the
    last value at or before that time. A missing bar repeats the previous value; steps after t0 + hours are dropped."""
    grid = t0 + pd.to_timedelta(np.arange(hours + 1), unit="h")
    pos = times.searchsorted(grid, side="right") - 1
    if pos[0] < 0 or times[pos[0]] != t0:
        raise ValueError(f"the steps must start at the window start {t0}")
    return np.asarray(values, dtype=float)[pos]


def day_points(t0: pd.Timestamp, hours: int, boundary_hour_utc: int) -> np.ndarray:
    """Clock offsets (hours from t0) of a window's day boundaries: t0, every boundary_hour_utc:00 strictly inside the
    window, and the end. A 12:00 UTC start has 16 points for HKT days (16:00 UTC: buckets of 4 h, 13 x 24 h, 20 h)
    and 16 for UTC days (00:00 UTC: 12 h, 13 x 24 h, 12 h); a start on the boundary hour has 15 (14 x 24 h)."""
    first = (boundary_hour_utc - t0.hour) % 24 or 24
    return np.concatenate([[0], np.arange(first, hours, 24), [hours]]).astype(int)


def returns(E: np.ndarray, hours_per_day: int = 24, points: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Daily and hourly returns, one row per window. E is on the clock grid (clock_series), so E[:, k] is the
    equity at t0 + k h: never a count of bars. Daily returns run between the day boundaries `points`
    (day_points), or every hours_per_day hours from t0 when none are given."""
    E = as_matrix(E)
    D = E[:, ::hours_per_day] if points is None else E[:, np.asarray(points, dtype=int)]
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


def _ratios(stats: dict, R: np.ndarray, mdd: np.ndarray, sc: dict, prefix: str = "") -> dict:
    """Every ratio of every variant under every convention, as columns '<prefix><convention>.<variant>.<ratio>'."""
    out = {}
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
            p = f"{prefix}{conv}.{v}"
            out[f"{p}.sharpe"] = sharpe
            out[f"{p}.sortino"] = sortino
            out[f"{p}.calmar"] = calmar
            out[f"{p}.composite"] = wc["sortino"] * sortino + wc["sharpe"] * sharpe + wc["calmar"] * calmar
    return out


def window_metrics(E, gross_end, sc: dict, points: np.ndarray | None = None,
                   extra_days: dict[str, np.ndarray] | None = None) -> pd.DataFrame:
    """One row per window: R, R_liq, MDD, the moments, and every ratio of every variant under every convention
    (columns '<convention>.<variant>.<ratio>'), plus floor hits ('<convention>.hit.<floor>').
    E: one row per window on the clock grid t0 + k h, k = 0..336 (backtest.scoring.evaluate reads it so).
    points: the day boundaries of the daily returns (day_points; HKT days in the score); without them, every 24 h
    from t0. extra_days: {name: points} adds the same ratios on other day boundaries, as '<name>.<convention>.<variant>
    .<ratio>' and '<name>.m_daily' etc. (UTC days in the score). The hourly variant (V3) is the same under any days."""
    E = as_matrix(E)
    r, h = returns(E, int(sc["hours_per_day"]), points)
    R = E[:, -1] / E[:, 0] - 1.0
    gross_end = np.broadcast_to(np.asarray(gross_end, dtype=float), R.shape)
    R_liq = E[:, -1] * (1.0 - sc["liquidation_cost"] * gross_end) / E[:, 0] - 1.0
    mdd = max_drawdown(E)
    stats = {"daily": moments(r), "hourly": moments(h)}
    out = {"R": R, "R_liq": R_liq, "MDD": mdd}
    for kind, (m, s, dd) in stats.items():
        out.update({f"m_{kind}": m, f"s_{kind}": s, f"dd_{kind}": dd})
    out.update(_ratios(stats, R, mdd, sc))
    for conv, fl in sc["conventions"].items():
        for f in FLOORS:
            den = mdd if f == "mdd" else out[f]
            out[f"{conv}.hit.{f}"] = floor_hits(den, fl[f])
    for name, pts in (extra_days or {}).items():
        rx, _ = returns(E, int(sc["hours_per_day"]), pts)
        sx = {"daily": moments(rx), "hourly": stats["hourly"]}
        m, s, dd = sx["daily"]
        out.update({f"{name}.m_daily": m, f"{name}.s_daily": s, f"{name}.dd_daily": dd})
        out.update(_ratios(sx, R, mdd, sc, prefix=f"{name}."))
    return pd.DataFrame(out)
