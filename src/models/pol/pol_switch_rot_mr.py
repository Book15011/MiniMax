"""Orchestrator (switch): while BTC is in trend hold the momentum rotation (team_rot_ew); otherwise Bollinger + RSI mean reversion on
4-hour bars (baitoey_mr_bbrsi, MR_4h). Decisions every 4 hours. Long only.

Pre-registered in reports/review/20261001-prereg-strict-bar.md before it was scored. The state rule is
team_trend_2's, untuned. Shared logic in src/models/pol/_combo.py; sleeves in config.yaml under `models: pol_switch_rot_mr:`.
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._combo import Combo


class SwitchRotMr(Combo):
    spec = ModelSpec(name="pol_switch_rot_mr", method="selector", author="pol", rebalance_hours=4, band=0.03, uses_shorts=False,
                     description="BTC in trend: momentum rotation; out of trend: 4-hour mean reversion")


MODEL = SwitchRotMr()
