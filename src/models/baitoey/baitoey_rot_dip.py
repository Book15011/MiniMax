"""Momentum rotation that buys its leaders on a dip.

The core is the team ROT_EW rotation (3, 7 and 14-day risk-adjusted momentum, top 6, kept while in the top 12, equal
weights, book at most 3%/day volatility). With the dip filter on, a coin not already held may only be bought when its
14-bar RSI on bars of bar_hours is below dip_rsi, so the bot waits for a pullback instead of chasing a coin that just
ran up; the slot goes to the next-ranked coin that qualifies. Coins already held are kept by the usual rule.
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey._bar_signals import rsi, sample_bars
from src.models.baselines.team_rot_ew import rotation_targets


class DipEntryRotation:
    spec = ModelSpec(name="baitoey_rot_dip", method="momentum", author="baitoey", rebalance_hours=24, band=0.05,
                     description="ROT_EW rotation; new entries only when the coin's RSI shows a pullback")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        if p["dip_filter"]:
            bh, n = int(p["bar_hours"]), int(p["rsi_bars"])
            close, _ = view.tail(n * bh + 1)
            r = rsi(sample_bars(close, bh, n + 1), n).iloc[-1]
            held = {c for c, w in view.prev_targets.items() if w > 0}
            keep = tuple(c for c in view.universe if c in held or r.get(c, float("nan")) < p["dip_rsi"])
            view = replace(view, universe=keep)
        return rotation_targets(view, p)


MODEL = DipEntryRotation()
