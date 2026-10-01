"""Scores for one 14-day window, under two readings of the (unpublished) competition formula.

Convention A: daily returns, ratios annualized with sqrt(365); Calmar = annualized return / max drawdown.
Convention B: hourly returns, ratios annualized with sqrt(8760); Calmar = raw window return / max drawdown.
Composite = 0.4 * Sortino + 0.3 * Sharpe + 0.3 * Calmar. Sortino's downside deviation is
sqrt(mean(min(r, 0)^2)) over all returns (target 0).
"""
from __future__ import annotations

import numpy as np

MDD_FLOOR = 1e-4   # a window with (almost) no drawdown gets Calmar = return / 0.01%, not infinity


def sharpe(r: np.ndarray, periods_per_year: float) -> float:
    sd = float(np.std(r, ddof=1)) if len(r) > 1 else 0.0
    return float(np.mean(r) / sd * np.sqrt(periods_per_year)) if sd > 0 else 0.0


def sortino(r: np.ndarray, periods_per_year: float) -> float:
    dd = float(np.sqrt(np.mean(np.minimum(r, 0.0) ** 2))) if len(r) else 0.0
    return float(np.mean(r) / dd * np.sqrt(periods_per_year)) if dd > 0 else 0.0


def max_drawdown(equity: np.ndarray) -> float:
    return float((equity / np.maximum.accumulate(equity) - 1.0).min())


def window_metrics(equity: np.ndarray, days: int = 14) -> dict:
    """equity: hourly values, length days * 24 + 1, starting at the window start."""
    e = np.asarray(equity, dtype=float)
    ret = float(e[-1] / e[0] - 1.0)
    mdd = max_drawdown(e)
    daily = e[::24]
    dr = daily[1:] / daily[:-1] - 1.0
    hr = e[1:] / e[:-1] - 1.0
    ann = (1.0 + ret) ** (365.0 / days) - 1.0
    denom = max(abs(mdd), MDD_FLOOR)
    m = {"ret": ret, "mdd": mdd,
         "sharpe_d": sharpe(dr, 365), "sortino_d": sortino(dr, 365), "calmar_ann": ann / denom,
         "sharpe_h": sharpe(hr, 8760), "sortino_h": sortino(hr, 8760), "calmar_raw": ret / denom}
    m["comp_a"] = 0.4 * m["sortino_d"] + 0.3 * m["sharpe_d"] + 0.3 * m["calmar_ann"]
    m["comp_b"] = 0.4 * m["sortino_h"] + 0.3 * m["sharpe_h"] + 0.3 * m["calmar_raw"]
    return m
