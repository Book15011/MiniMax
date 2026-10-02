"""Momentum rotation with volume-confirmed timing.

The core is the team ROT_EW rotation on 7- and 14-day risk-adjusted momentum: the top 6 coins, kept while in the
top 12, equal weights, the book at most 3%/day volatility. Two optional filters remove coins before ranking, so the
next-ranked coin takes the slot:
- early exit: a coin that closed below its lowest close of the previous 24 hours while its 24-hour volume was above
  1.5 times normal is left out for 24 hours;
- no chase: a coin up more than 15% in 24 hours on volume above 3 times normal is left out until it has pulled
  back 5% from its highest close since that spike, or 72 hours have passed.
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey._volume_signals import breakdown_blocked, chase_blocked
from src.models.baselines.team_rot_ew import rotation_targets


class VolumeTimedMomentum:
    spec = ModelSpec(name="baitoey_vt_mom", method="momentum", author="baitoey", rebalance_hours=24, band=0.05,
                     description="ROT_EW-style 7/14-day momentum; skips coins after a volume-confirmed breakdown "
                                 "or a volume spike")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        blocked: set[str] = set()
        if p["early_exit"] or p["no_chase"]:
            need = (p["volume_long_days"] * 24 + max(p["volume_short_hours"], p["chase_return_hours"])
                    + max(p["exit_cooldown_hours"] + p["exit_low_hours"], p["chase_window_hours"]) + 1)
            close, qv = view.tail(need)
            if p["early_exit"]:
                blocked |= breakdown_blocked(close, qv, p)
            if p["no_chase"]:
                blocked |= chase_blocked(close, qv, p)
        if blocked:
            view = replace(view, universe=tuple(c for c in view.universe if c not in blocked))
        return rotation_targets(view, p)


MODEL = VolumeTimedMomentum()
