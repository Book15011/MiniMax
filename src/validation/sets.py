"""Fixed evaluation sets (RECENT, STRESS). STRESS uses outcomes BY DESIGN: it is an evaluation set,
not a selection set, so it lives outside the selection code and its guard."""
from __future__ import annotations

import pandas as pd

DAY = pd.Timedelta(days=1)


def greedy_spaced(ordered: pd.DatetimeIndex, k: int, min_sep_days: int) -> list[pd.Timestamp]:
    """Walk candidates in order; accept one if its start is >= min_sep_days from every accepted start."""
    acc: list[pd.Timestamp] = []
    for t in ordered:
        if all(abs(t - a) >= min_sep_days * DAY for a in acc):
            acc.append(t)
            if len(acc) == k:
                break
    return acc


def stress_sets(pool: pd.DatetimeIndex, y1: pd.Series, btc_daily_close: pd.Series, k: int = 10,
                min_sep_days: int = 14, rebound_dd: float = 0.20, high_days: int = 90) -> dict[str, list[dict]]:
    """DROPS: lowest BTC 14-day return. REBOUNDS: highest BTC 14-day return among starts where BTC is at
    least `rebound_dd` below its `high_days`-day high (daily 16:00 closes up to and including t0)."""
    y = y1.reindex(pool)
    drops = greedy_spaced(y.sort_values(kind="stable").index, k, min_sep_days)
    dd = (btc_daily_close / btc_daily_close.rolling(high_days, min_periods=high_days).max() - 1).reindex(pool)
    eligible = y[dd <= -rebound_dd]
    rebounds = greedy_spaced(eligible.sort_values(ascending=False, kind="stable").index, k, min_sep_days)
    row = lambda t: {"start": str(t), "btc_14d_log_return": float(y[t]), "btc_below_90d_high": float(dd[t])}
    return {"drops": [row(t) for t in drops], "rebounds": [row(t) for t in rebounds],
            "rebound_candidates": int(len(eligible))}
