"""Orchestrator: Switch, not blend: while BTC is in trend (team_trend_2's state) hold the momentum rotation (team_rot_ew) in
full; otherwise stay in cash (the engine's keep-alive trade keeps the days active). Long only.

The state rule is team_trend_2's, untuned, fixed before this model was scored. Shared logic in
src/models/pol/_combo.py; sleeves and the switch in config.yaml under `models: pol_switch_rc:`.
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._combo import Combo


class SwitchRC(Combo):
    spec = ModelSpec(name="pol_switch_rc", method="selector", author="pol", rebalance_hours=24, band=0.03, uses_shorts=False,
                     description="BTC in trend: momentum rotation; out of trend: cash")


MODEL = SwitchRC()
