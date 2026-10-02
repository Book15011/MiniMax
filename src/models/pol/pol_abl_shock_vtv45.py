"""Ablation F on vt_mom with a 4.5%/day vol cap: baitoey_vt_mom (cap raised from 3%) plus the hourly BTC shock
override of pol_abl_shock. Research only."""
from __future__ import annotations

from dataclasses import replace

from src.models.pol.pol_abl_shock import ShockOverride


class ShockVtv45(ShockOverride):
    spec = replace(ShockOverride.spec, name="pol_abl_shock_vtv45",
                   description="ablation F on baitoey_vt_mom with a 4.5%/day vol cap")


MODEL = ShockVtv45()
