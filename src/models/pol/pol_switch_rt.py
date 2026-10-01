"""Orchestrator: Switch, not blend: while BTC is in trend (team_trend_2's state) hold the momentum rotation (team_rot_ew) in
full; otherwise hold the long/short trend model (pol_trend_ls), which can short the falling alts.

The state rule is team_trend_2's, untuned, fixed before this model was scored. Shared logic in
src/models/pol/_combo.py; sleeves and the switch in config.yaml under `models: pol_switch_rt:`.
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._combo import Combo


class SwitchRT(Combo):
    spec = ModelSpec(name="pol_switch_rt", method="selector", author="pol", rebalance_hours=24, band=0.03, uses_shorts=True,
                     description="BTC in trend: momentum rotation; out of trend: long/short trend")


MODEL = SwitchRT()
