"""Combination: Cross-sectional momentum (team_rot_ew) and time-series long/short trend (pol_trend_ls), half each.

The two highest-scoring single models of the 2026-10-01 field run, built on different signals (rank among
coins vs each coin's own trend), so their bad windows should overlap less than either's alone.

Shared logic in src/models/pol/_combo.py; sleeves and weights in config.yaml under `models: pol_combo_rt:`.
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._combo import Combo


class ComboRT(Combo):
    spec = ModelSpec(name="pol_combo_rt", method="selector", author="pol", rebalance_hours=24, band=0.03, uses_shorts=True,
                     description="Momentum rotation + long/short trend, 50/50")


MODEL = ComboRT()
