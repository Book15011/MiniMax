"""Combination: The TEAM_PLAN v1 pair mixed instead of picked: momentum with a 25% short sleeve (pol_mom_ss) and long/short
trend (pol_trend_ls), half each.

Shared logic in src/models/pol/_combo.py; sleeves and weights in config.yaml under `models: pol_combo_ms_tl:`.
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._combo import Combo


class ComboMsTl(Combo):
    spec = ModelSpec(name="pol_combo_ms_tl", method="selector", author="pol", rebalance_hours=24, band=0.03, uses_shorts=True,
                     description="Momentum with short sleeve + long/short trend, 50/50")


MODEL = ComboMsTl()
