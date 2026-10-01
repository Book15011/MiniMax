"""Orchestrator (switch): pol_switch_vt_tl with a faster trend switch (BTC 20-day EMA instead of 40) and a higher
volatility cap on the momentum sleeve (4.5%/day instead of 3%).

Found in the pre-registered sensitivity check of the launch pick (reports/review/20261002-prereg-sensitivity.md), so
it was chosen after looking: evidence and caveats in reports/review/20261002-recheck.md. Sleeves and the changed
numbers sit under `models: pol_switch_vt_tl_e20v45:` (overrides on the shared anchors; Baitoey's block is unchanged).
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._combo import Combo


class SwitchVtTlE20V45(Combo):
    spec = ModelSpec(name="pol_switch_vt_tl_e20v45", method="selector", author="pol", rebalance_hours=24, band=0.03,
                     uses_shorts=True,
                     description="pol_switch_vt_tl with a 20-day BTC trend switch and a 4.5%/day momentum vol cap")


MODEL = SwitchVtTlE20V45()
