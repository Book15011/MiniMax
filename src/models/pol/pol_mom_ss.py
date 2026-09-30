"""Momentum rotation with a short sleeve.

Rank the most liquid coins by risk-adjusted momentum (mean of several lookback returns divided by the
coin's own volatility). Hold the strongest few long, keep a holding while it stays near the top, and
short the weakest coins that are actually falling with a small slice of the book. The long book is
volatility-capped with a conservative bound (all coins assumed perfectly correlated).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.contracts import MarketView, ModelSpec

HOURS_PER_YEAR = 24 * 365


class MomentumShortSleeve:
    spec = ModelSpec(name="pol_mom_ss", method="momentum", author="pol", rebalance_hours=24, band=0.03,
                     uses_shorts=True,
                     description="Top-k risk-adjusted momentum long (sticky), weakest falling coins short, long book vol-capped")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        lbs = [int(d) for d in p["lookback_days"]]
        close, qv = view.tail((max(max(lbs), p["vol_days"]) + 1) * 24)
        ok = close.notna().sum() >= p["min_history_days"] * 24          # enough history in the window
        close, qv = close.loc[:, ok], qv.loc[:, ok]
        if close.shape[1] < p["min_coins"]:
            return pd.Series(dtype=float)
        liquid = qv.iloc[-p["vol_days"] * 24:].sum().sort_values(ascending=False).index[: p["top_n"]]
        close = close[liquid]
        last = close.iloc[-1]
        mom = sum(last / close.iloc[-1 - lb * 24] - 1 for lb in lbs) / len(lbs)
        vol = close.pct_change(fill_method=None).iloc[-p["vol_days"] * 24:].std() * np.sqrt(HOURS_PER_YEAR)
        score = (mom / vol).replace([np.inf, -np.inf], np.nan).dropna()
        if score.empty:
            return pd.Series(dtype=float)

        rank = score.rank(ascending=False)
        prev_long = [c for c, w in view.prev_targets.items() if w > 0]
        held = [c for c in prev_long if c in rank.index and rank[c] <= p["keep_rank"] and score[c] > 0]
        for c in rank.sort_values().index:
            if len(held) >= p["k"]:
                break
            if c not in held and score[c] > 0:
                held.append(c)

        w = pd.Series(0.0, index=score.index)
        if held:
            ew = 1.0 / len(held)
            cap = min(1.0, p["long_vol_cap"] / float((ew * vol[held]).sum()))
            w[held] = ew * cap * p["long_gross"]
        losers = score[score < 0].sort_values().index[: p["short_k"]]
        losers = [c for c in losers if c not in held]
        if losers and p["short_gross"] > 0:
            iv = 1.0 / vol[losers]
            w[losers] = -(iv / iv.sum()) * p["short_gross"]
        return w[w != 0.0]


MODEL = MomentumShortSleeve()
