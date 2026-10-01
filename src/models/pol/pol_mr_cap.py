"""MR_4h (baitoey_mr_4h: Bollinger + RSI mean reversion on 4-hour bars) that enters only on capitulation volume.

Exploratory (reports/review/20261002-volume.md): short-term reversal is about twice as strong among coins trading above
their normal volume (4-hour-ahead rank IC of the 24 h return -0.032 vs -0.016 below normal, 2024-2026), and 24 h
losers on heavy volume did better over the next 72 h than quiet losers. New entries need the coin's last-24-hour quote
volume above cap_volume_ratio times its 7-day normal; coins already held follow the MR exits unchanged. A missing
volume reading means no entry (as in Baitoey's volume signals).
"""
from __future__ import annotations

import dataclasses

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey._volume_signals import volume_ratio
from src.models.baitoey.baitoey_mr_bbrsi import BollingerRsiReversion


class CapitulationReversion(BollingerRsiReversion):
    spec = ModelSpec(name="pol_mr_cap", method="trend", author="pol", rebalance_hours=4, band=0.05,
                     description="MR_4h; new entries only while the coin's 24 h volume is above its 7-day normal")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        hours, days = int(p["cap_volume_hours"]), int(p["cap_volume_days"])
        _, qv = view.tail(days * 24 + hours)
        ratio = volume_ratio(qv, hours, days).iloc[-1]
        held = {c for c, w in view.prev_targets.items() if w > 0}
        allowed = tuple(c for c in view.universe if c in held or ratio.get(c, float("nan")) > p["cap_volume_ratio"])
        return super().targets(dataclasses.replace(view, universe=allowed))


MODEL = CapitulationReversion()
