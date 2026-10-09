"""Dual momentum: baitoey_vt_mom with an absolute-momentum filter.

Exactly baitoey_vt_mom (the 7/14-day risk-adjusted rotation, top 6 kept while in the top 12, the volume-confirmed
early exit), except that a coin may hold a slot only while its own momentum score is above `min_score`; a held coin
whose score falls to or below it is sold. Each slot is 1/k of the book and a slot with no eligible coin stays in
cash, so in a broad decline the book drains to cash coin by coin. The book is then scaled to at most
target_daily_vol, as in vt_mom. Removing the coins at or below the threshold leaves the ranks of the others
unchanged (they all rank above them), so with every coin eligible the targets are vt_mom's.
Pre-registration: research/baitoey/prereg/20261002-dual-momentum.md.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey._volume_signals import momentum_score, scale_to_daily_vol
from src.models.baitoey.baitoey_vt_mom import MODEL as VT_MOM


class DualMomentum:
    spec = ModelSpec(name="baitoey_vt_dual", method="momentum", author="baitoey", rebalance_hours=24, band=0.05,
                     description="baitoey_vt_mom, but a coin holds a slot only while its own momentum is positive; "
                                 "empty slots stay in cash")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        lbs = [int(d) for d in p["lookback_days"]]
        close, _ = view.tail(max(max(lbs) * 24, int(p["vol_days"]) * 24) + 1)
        score = momentum_score(close, lbs)
        weak = set(score[score <= float(p["min_score"])].index)
        if weak:
            view = replace(view, universe=tuple(c for c in view.universe if c not in weak))
        held = VT_MOM.targets(replace(view, params={**p, "target_daily_vol": np.inf})).index   # vt_mom's picks
        if len(held) == 0:
            return pd.Series(dtype=float)
        w = pd.Series(1.0 / int(p["k"]), index=held)
        return scale_to_daily_vol(w, close, int(p["vol_days"]), float(p["target_daily_vol"]))


MODEL = DualMomentum()
