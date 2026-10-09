"""pol_switch_vt_tl_e20v45 with the dual-momentum filter in its up-state sleeve: baitoey_vt_dual (vt_mom where a coin
holds a slot only while its own momentum is positive; empty slots stay cash) instead of baitoey_vt_mom, same 4.5%/day
vol cap. The 20-day BTC EMA switch and the down-state pol_trend_ls sleeve are unchanged.
Pre-registration: reports/review/20261009-prereg-e20v45-dual.md (written before this code).
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._combo import Combo


class SwitchVtdTlE20V45(Combo):
    spec = ModelSpec(name="pol_switch_vtd_tl_e20v45", method="selector", author="pol", rebalance_hours=24, band=0.03,
                     uses_shorts=True,
                     description="e20v45 with the dual-momentum filter (baitoey_vt_dual) in its up-state sleeve")


MODEL = SwitchVtdTlE20V45()
