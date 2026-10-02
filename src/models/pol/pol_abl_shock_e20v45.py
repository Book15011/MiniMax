"""Ablation F on the switch candidate: pol_switch_vt_tl_e20v45 (unchanged, deciding at 16:00 UTC) plus the hourly
BTC shock override of pol_abl_shock (cash for 24 h after BTC falls 5% within 4 hours). Research only."""
from __future__ import annotations

from dataclasses import replace

from src.models.pol.pol_abl_shock import ShockOverride
from src.models.pol.pol_switch_vt_tl_e20v45 import MODEL as E20V45


class ShockE20V45(ShockOverride):
    INNER = E20V45
    spec = replace(ShockOverride.spec, name="pol_abl_shock_e20v45", uses_shorts=True,
                   description="ablation F on pol_switch_vt_tl_e20v45: cash for 24 h after a BTC 4-hour crash")


MODEL = ShockE20V45()
