"""pol_switch_vt_tl_e20v45 with the switch into the long/short trend mode at BTC 20-day EMA x 0.99 instead of x 0.97; back to
momentum above EMA x 1.03, as live. Pre-registration: reports/review/20261009-prereg-e20v45-band.md, addendum 1."""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._switch_asym import AsymSwitch


class SwitchE20V45D1(AsymSwitch):
    spec = ModelSpec(name="pol_switch_vt_tl_e20v45_d1", method="selector", author="pol", rebalance_hours=24, band=0.03,
                     uses_shorts=True, description="e20v45, down below EMA x 0.99 (0.97 live), up above x 1.03 as live")


MODEL = SwitchE20V45D1()
