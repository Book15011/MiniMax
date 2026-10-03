"""Per-coin trend bots with a manager (long-only).

Every coin of the liquid universe (the 20 most traded coins of view.universe over 30 days) has its own trend bot.
Its raw exposure is raw_i = s_i / sigma_i: its trend score (src/models/book/_trend.py: the share of its 5, 10, 20,
30 and 60-day returns that are positive) over its 30-day hourly volatility. The manager divides by the sum of
1 / sigma_j over the universe: w_i = raw_i / sum_j(1 / sigma_j). So the book is fully invested, in inverse-volatility
weights, only when every coin is in a full trend (s_i = 1), and exposure falls coin by coin as trends break. A coin
is capped at 25%; the excess stays in cash. Gross is at most 1 by construction (sum of s_i / sigma_i <= sum of
1 / sigma_j).

Variant 3.2b (`shorts: true`; scratch only, it needs uses_shorts): when breadth (the share of the liquid universe
in an up-trend) is below 0.3, a coin with s_i = 0 is shorted at w_i = -0.5 / sigma_i / sum_j(1 / sigma_j).
A coin without a usable volatility (fewer than 2 hourly returns, or 0) gets no weight and is left out of the sum.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.book._trend import hourly_vol, liquid_universe, trend_scores


class CoinTrend:
    spec = ModelSpec(name="book_coin_trend", method="trend", author="book", rebalance_hours=24, band=0.05,
                     uses_shorts=False,
                     description="Per-coin trend bots on the 20 most traded coins: s_i / vol_i over the sum of "
                                 "1 / vol_j, so fully invested only when every coin trends; 25% cap per coin")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        tp = p["trend"]
        liquid = liquid_universe(view, tp)
        if not liquid:
            return pd.Series(dtype=float)
        s = trend_scores(view.close, view.t, liquid, tp)
        sigma = hourly_vol(view.close, view.t, liquid, p["vol_days"])
        ok = sigma.index[np.isfinite(sigma.to_numpy()) & (sigma.to_numpy() > 0)]
        if len(ok) == 0:
            return pd.Series(dtype=float)
        inv = 1.0 / sigma[ok]
        w = s[ok] * inv / inv.sum()
        if p["shorts"] and float((s >= tp["up_threshold"]).mean()) < p["short_breadth"]:
            broken = s[ok] == 0.0
            w[broken] = -float(p["short_scale"]) * inv[broken] / inv.sum()
        cap = float(p["max_weight"])
        w = w.clip(lower=-cap, upper=cap)
        return w[w != 0.0]


MODEL = CoinTrend()
