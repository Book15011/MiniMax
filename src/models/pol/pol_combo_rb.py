"""Combination: Core and satellite: half BTC held (team_btc_hold), half cross-sectional momentum (team_rot_ew).

BTC held scored above most active models on 2026-10-01; the rotation adds the daily activity a pure hold lacks
and some of the alt-season upside. Long only.

Shared logic in src/models/pol/_combo.py; sleeves and weights in config.yaml under `models: pol_combo_rb:`.
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._combo import Combo


class ComboRB(Combo):
    spec = ModelSpec(name="pol_combo_rb", method="selector", author="pol", rebalance_hours=24, band=0.03, uses_shorts=False,
                     description="BTC core + momentum rotation satellite, 50/50")


MODEL = ComboRB()
