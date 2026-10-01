"""Orchestrator (switch): while BTC is in trend hold Baitoey's volume-timed momentum (baitoey_vt_mom); otherwise the long/short trend
model (pol_trend_ls).

Pre-registered in reports/review/20261001-prereg-realtest.md before it was scored. State rules untuned. Shared logic
in src/models/pol/_combo.py; sleeves in config.yaml under `models: pol_switch_vt_tl:`.
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._combo import Combo


class SwitchVtTl(Combo):
    spec = ModelSpec(name="pol_switch_vt_tl", method="selector", author="pol", rebalance_hours=24, band=0.03, uses_shorts=True,
                     description="BTC in trend: volume-timed momentum; out of trend: long/short trend")


MODEL = SwitchVtTl()
