"""Orchestrator (switch): while BTC is in trend hold the return-first rotation (baitoey_rot_max: top 4, no volatility cap) in full;
otherwise the long/short trend model (pol_trend_ls).

Pre-registered in reports/review/20261001-prereg-strict-bar.md before it was scored. The state rule is
team_trend_2's, untuned. Shared logic in src/models/pol/_combo.py; sleeves in config.yaml under `models: pol_switch_rmax_tl:`.
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._combo import Combo


class SwitchRmaxTl(Combo):
    spec = ModelSpec(name="pol_switch_rmax_tl", method="selector", author="pol", rebalance_hours=24, band=0.03, uses_shorts=True,
                     description="BTC in trend: concentrated fully invested rotation; out of trend: long/short trend")


MODEL = SwitchRmaxTl()
