"""Reference (ROT_EW): long-only momentum rotation, equal weights, book scaled to a daily volatility target.

Score of a coin = mean over the lookbacks (3, 7, 14 days) of its return over the lookback divided by its own
volatility over the same lookback (hourly standard deviation scaled to the lookback length). Every day at
16:00 UTC: hold the top k by score, keep a holding while it ranks in the top keep_rank, weight equally, then
scale the whole book so its estimated daily volatility (30-day hourly covariance, times 24) is at most the
target. A coin trades only when its weight drifts more than 5 points (spec.band).
ROT_IV (team_rot_iv) is the same with inverse-volatility weights and a lower target.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.contracts import MarketView, ModelSpec


def rotation_targets(view: MarketView, p: dict) -> pd.Series:
    lbs = [int(d) for d in p["lookback_days"]]
    vol_h = int(p["vol_days"]) * 24
    close, _ = view.tail(max(max(lbs) * 24, vol_h) + 1)
    ok = (close.notna().sum() >= p["min_history_days"] * 24) & close.iloc[-1].notna()
    for lb in lbs:
        ok &= close.iloc[-1 - lb * 24].notna()
    close = close.loc[:, ok]
    if close.shape[1] == 0:
        return pd.Series(dtype=float)
    rets = close.pct_change(fill_method=None)
    last = close.iloc[-1]
    terms = [(last / close.iloc[-1 - lb * 24] - 1) / (rets.iloc[-lb * 24:].std() * np.sqrt(lb * 24)) for lb in lbs]
    score = (sum(terms) / len(lbs)).replace([np.inf, -np.inf], np.nan).dropna()
    if score.empty:
        return pd.Series(dtype=float)

    rank = score.rank(ascending=False, method="first")
    held = [c for c, w in view.prev_targets.items() if w > 0 and c in rank.index and rank[c] <= p["keep_rank"]]
    for c in rank.sort_values().index:
        if len(held) >= p["k"]:
            break
        if c not in held:
            held.append(c)
    held = sorted(held)
    recent = rets[held].iloc[-vol_h:]
    if p["weighting"] == "equal":
        w = pd.Series(1.0 / len(held), index=held)
    elif p["weighting"] == "inverse_vol":
        iv = 1.0 / recent.std()
        w = iv / iv.sum()
    else:
        raise ValueError(f"weighting must be 'equal' or 'inverse_vol', not {p['weighting']!r}")
    cov = recent.cov().to_numpy() * 24.0                   # daily covariance from hourly returns
    book_vol = float(np.sqrt(w.to_numpy() @ cov @ w.to_numpy()))
    scale = min(1.0, p["target_daily_vol"] / book_vol) if book_vol > 0 else 1.0
    w = (w * scale).replace([np.inf, -np.inf], np.nan).dropna()
    return w[w > 0]


class RotationEW:
    spec = ModelSpec(name="team_rot_ew", method="reference", author="team", rebalance_hours=24, band=0.05,
                     description="Top-6 risk-adjusted momentum, equal weights, book at <= 3%/day volatility (scoring field)")

    def targets(self, view: MarketView) -> pd.Series:
        return rotation_targets(view, view.params)


MODEL = RotationEW()
