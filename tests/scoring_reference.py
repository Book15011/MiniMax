"""Independent plain-Python implementation of docs/EVALUATION.md section 2 (no numpy, no pandas).

Written from the written definitions, not from backtest/scoring/metrics.py, so the two can check each other.
"""
from __future__ import annotations

import math


def daily_points(E: list[float], hours_per_day: int = 24) -> list[float]:
    return [E[i] for i in range(0, len(E), hours_per_day)]


def simple_returns(x: list[float]) -> list[float]:
    return [x[k] / x[k - 1] - 1.0 for k in range(1, len(x))]


def mean(x: list[float]) -> float:
    return math.fsum(x) / len(x)


def sample_sd(x: list[float]) -> float:
    m = mean(x)
    return math.sqrt(math.fsum((v - m) ** 2 for v in x) / (len(x) - 1))


def downside_dev(x: list[float]) -> float:
    return math.sqrt(math.fsum(min(v, 0.0) ** 2 for v in x) / len(x))


def mdd(E: list[float]) -> float:
    peak, worst = E[0], 0.0
    for v in E:
        peak = max(peak, v)
        worst = max(worst, 1.0 - v / peak)
    return worst


def safe_ratio(num: float, den: float, floor: float) -> float:
    if num == 0.0:
        return 0.0
    if floor > 0.0:
        return num / max(den, floor)
    return num / den if den > 0.0 else 0.0


def metrics(E: list[float], gross_end: float, sc: dict) -> dict:
    """Same keys as backtest.scoring.metrics.window_metrics (one window)."""
    hpd = int(sc["hours_per_day"])
    r = simple_returns(daily_points(E, hpd))
    h = simple_returns(E)
    R = E[-1] / E[0] - 1.0
    out = {"R": R, "R_liq": E[-1] * (1.0 - sc["liquidation_cost"] * gross_end) / E[0] - 1.0, "MDD": mdd(E)}
    series = {"daily": r, "hourly": h}
    for kind, x in series.items():
        out[f"m_{kind}"], out[f"s_{kind}"], out[f"dd_{kind}"] = mean(x), sample_sd(x), downside_dev(x)
    w = sc["composite"]
    for conv, fl in sc["conventions"].items():
        for v, spec in sc["variants"].items():
            kind, a = spec["returns"], float(spec["annualize"])
            m, s, dd = out[f"m_{kind}"], out[f"s_{kind}"], out[f"dd_{kind}"]
            sharpe = safe_ratio(m, s, fl[f"s_{kind}"]) * math.sqrt(a)
            sortino = safe_ratio(m, dd, fl[f"dd_{kind}"]) * math.sqrt(a)
            num = m * a if spec["calmar"] == "mean" else R
            calmar = safe_ratio(num, out["MDD"], fl["mdd"])
            out[f"{conv}.{v}.sharpe"] = sharpe
            out[f"{conv}.{v}.sortino"] = sortino
            out[f"{conv}.{v}.calmar"] = calmar
            out[f"{conv}.{v}.composite"] = w["sortino"] * sortino + w["sharpe"] * sharpe + w["calmar"] * calmar
    return out
