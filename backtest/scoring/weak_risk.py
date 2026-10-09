"""Net remaining-horizon risk using the configured competition CS formulas.

Cached paths already contain ordinary execution costs. Liquidation at the chosen
remaining endpoint is charged once, at that endpoint; the resulting loss enters
both drawdown and the final daily return. FLOORED.V1 is the competition-style
daily-raw CS, evaluated on HKT 16:00 UTC days plus a UTC-clock sensitivity.
First and last partial days retain the same treatment as the original scorer.
"""
from __future__ import annotations

from numbers import Integral
import numpy as np
import pandas as pd

from backtest.scoring.metrics import day_points, window_metrics


def remainder_risk(equity, gross, starts, prefix_hours, hours, scoring):
    """Return one array per window: return, mdd, CS, CS_UTC and three CS ratios.

    equity/gross are matching two-dimensional hourly cached paths, including t0.
    starts supplies each path's original start (naive timestamps mean UTC).
    The remaining path starts at starts + prefix_hours and has hours steps.
    Equity must be strictly positive before endpoint liquidation, gross must be
    nonnegative, and gross drift above one is accepted. A liquidation reducing
    terminal equity below zero is rejected; exactly zero records a total loss.
    Each day-clock requires at least two return buckets for sample deviation.
    Nothing is inferred about actual holdings or a common-incumbent transition.
    """
    if (not isinstance(prefix_hours, Integral) or isinstance(prefix_hours, (bool, np.bool_))
            or not isinstance(hours, Integral) or isinstance(hours, (bool, np.bool_))):
        raise ValueError("prefix_hours and hours must be integer clock hours")
    prefix_hours, hours = int(prefix_hours), int(hours)
    if prefix_hours < 0 or hours < 2:
        raise ValueError("prefix_hours must be nonnegative and hours at least two")
    try:
        eq, gr = np.asarray(equity, dtype=float), np.asarray(gross, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("equity and gross must be numeric matrices") from exc
    if (eq.ndim != 2 or gr.ndim != 2 or eq.shape != gr.shape or not eq.shape[0]
            or eq.shape[1] < 3):
        raise ValueError("equity and gross must be matching nonempty hourly matrices")
    if prefix_hours + hours >= eq.shape[1]:
        raise ValueError("remaining endpoint falls outside the cached path")
    if not np.isfinite(eq).all() or not np.isfinite(gr).all():
        raise ValueError("equity and gross must be finite")
    if (eq <= 0).any() or (gr < 0).any():
        raise ValueError("equity must be positive and gross must be nonnegative")
    try:
        times = pd.DatetimeIndex(pd.to_datetime(starts, utc=True))
    except (TypeError, ValueError) as exc:
        raise ValueError("starts must contain valid UTC timestamps") from exc
    if len(times) != eq.shape[0] or times.isna().any():
        raise ValueError("one valid start timestamp is required per path")
    if not (times == times.floor("h")).all():
        raise ValueError("starts must lie on the hourly UTC clock")
    try:
        fee = float(scoring["liquidation_cost"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("scoring requires a finite nonnegative liquidation_cost") from exc
    if not np.isfinite(fee) or fee < 0:
        raise ValueError("liquidation_cost must be finite and nonnegative")

    endpoint = prefix_hours + hours
    net = eq[:, prefix_hours:endpoint + 1].copy() / eq[:, prefix_hours, None]
    net[:, -1] *= 1. - fee * gr[:, endpoint]
    if (net[:, -1] < 0).any():
        raise ValueError("liquidation would create negative terminal equity")

    names = {"return": "R", "mdd": "MDD", "CS": "FLOORED.V1.composite",
             "CS_UTC": "UTC.FLOORED.V1.composite", "Sharpe": "FLOORED.V1.sharpe",
             "Sortino": "FLOORED.V1.sortino", "Calmar": "FLOORED.V1.calmar"}
    out = {name: np.empty(eq.shape[0], dtype=float) for name in names}
    remaining = times + pd.Timedelta(hours=prefix_hours)
    # Clock buckets depend on the start hour; batch equal clocks together.
    for hour in np.unique(remaining.hour):
        indices = np.flatnonzero(remaining.hour == hour)
        start = remaining[indices[0]]
        hkt_points = day_points(start, hours, 16)
        utc_points = day_points(start, hours, 0)
        if len(hkt_points) < 3 or len(utc_points) < 3:
            raise ValueError("remaining horizon needs at least two daily return buckets per clock")
        # The adjusted endpoint already paid liquidation; gross_end=0 prevents
        # window_metrics from charging a second endpoint fee in R_liq.
        measured = window_metrics(net[indices], 0., scoring, points=hkt_points,
                                  extra_days={"UTC": utc_points})
        try:
            for name, column in names.items():
                out[name][indices] = measured[column].to_numpy(dtype=float)
        except KeyError as exc:
            raise ValueError("scoring must define the FLOORED.V1 CS formulas") from exc
    if not all(np.isfinite(value).all() for value in out.values()):
        raise ValueError("remaining risk metrics are not finite")
    return out
