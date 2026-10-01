"""Combination: Three methods in equal thirds: cross-sectional momentum (team_rot_ew), long/short trend on the liquid alts
(pol_trend_ls) and slow BTC/ETH trend (team_trend_2).

Shared logic in src/models/pol/_combo.py; sleeves and weights in config.yaml under `models: pol_combo_rtt:`.
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._combo import Combo


class ComboRTT(Combo):
    spec = ModelSpec(name="pol_combo_rtt", method="selector", author="pol", rebalance_hours=24, band=0.03, uses_shorts=True,
                     description="Momentum rotation + long/short trend + BTC/ETH trend, thirds")


MODEL = ComboRTT()
