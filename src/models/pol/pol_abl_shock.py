"""Ablation F of Book's hierarchical-orchestrator plan: the daily strategy (baitoey_vt_mom, unchanged, deciding at
16:00 UTC) plus an hourly deterministic shock override: while BTC has fallen at least `shock_4h` over 4 hours at any
hour of the last `cooldown_hours`, hold cash.

Research only (reports/review/20261002-orchestrator-ablation.md). Checked every hour; outside a shock the book is
the latest daily decision, unchanged (so between decisions it trades only if a weight drifts past the band). The
first decision of a window (no previous book) is a daily decision, as the live bot's first hour is.
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey.baitoey_vt_mom import MODEL as VT_MOM

GRID_HOUR = 16


class ShockOverride:
    spec = ModelSpec(name="pol_abl_shock", method="momentum", author="pol", rebalance_hours=1, band=VT_MOM.spec.band,
                     description="ablation F: baitoey_vt_mom daily, cash for cooldown_hours after a BTC 4-hour crash")

    @staticmethod
    def shocked(view: MarketView, p: dict) -> bool:
        n = int(p["cooldown_hours"]) + 4
        if "BTCUSDT" not in view.close.columns:
            return False
        btc = view.close["BTCUSDT"].iloc[-(n + 1):]
        r4 = btc / btc.shift(4) - 1.0
        return bool((r4.iloc[-int(p["cooldown_hours"]):] <= -float(p["shock_4h"])).any())

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        if self.shocked(view, p):
            return pd.Series(dtype=float)
        prev = view.prev_targets[view.prev_targets != 0]
        if view.t.hour == GRID_HOUR or prev.empty:
            return VT_MOM.targets(replace(view, params=p["vt"]))
        return prev[prev.index.isin(list(view.universe))]


MODEL = ShockOverride()
