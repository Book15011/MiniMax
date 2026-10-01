"""Combination: Every existing directional model in equal sevenths: BTC held, equal weight, two momentum rotations, slow
BTC/ETH trend, momentum with a short sleeve and long/short trend. The most diversified mix, as a reference
for the narrower ones.

Shared logic in src/models/pol/_combo.py; sleeves and weights in config.yaml under `models: pol_combo_all:`.
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._combo import Combo


class ComboAll(Combo):
    spec = ModelSpec(name="pol_combo_all", method="selector", author="pol", rebalance_hours=24, band=0.03, uses_shorts=True,
                     description="Every existing method, equal weights")


MODEL = ComboAll()
