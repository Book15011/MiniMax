"""Research only (not a registered model): pol_switch_vt_tl_e20v45 deciding once a day at `decision_hour` (UTC).

Checked every hour like pol_abl_shock: at `decision_hour` the daily model decides (params under "vt"); at every
other hour the book is the latest decision, unchanged. If the book is empty (the first hour of a round), the daily
model decides at once, as the live bot does. The guard, day boundaries and everything else stay on the harness clock
(16:00 UTC days). Pre-registration: research/baitoey/prereg/20261003-decision-hour.md.
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.pol.pol_switch_vt_tl_e20v45 import MODEL as E20V45


class DecisionHour:
    INNER = E20V45
    spec = ModelSpec(name="baitoey_hour_e20v45", method="momentum", author="baitoey", rebalance_hours=1,
                     band=E20V45.spec.band, uses_shorts=True,
                     description="research only: pol_switch_vt_tl_e20v45 deciding once a day at a chosen UTC hour")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        prev = view.prev_targets[view.prev_targets != 0]
        if view.t.hour == int(p["decision_hour"]) or prev.empty:
            return self.INNER.targets(replace(view, params=p["vt"]))
        return prev[prev.index.isin(list(view.universe))]


MODEL = DecisionHour()
