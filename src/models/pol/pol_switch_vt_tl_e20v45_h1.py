"""pol_switch_vt_tl_e20v45 with a switch band of 0.01 instead of 0.03 (BTC 20-day EMA x (1 -/+ 0.01)): a lower bar to
switch into the long/short trend mode. Pre-registration: reports/review/20261009-prereg-e20v45-band.md."""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._combo import Combo


class SwitchE20V45H1(Combo):
    spec = ModelSpec(name="pol_switch_vt_tl_e20v45_h1", method="selector", author="pol", rebalance_hours=24, band=0.03,
                     uses_shorts=True, description="e20v45 with a 0.01 switch band (0.03 live)")


MODEL = SwitchE20V45H1()
