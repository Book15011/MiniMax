"""Research only (not a registered model): pol_switch_vt_tl_e20v45 acting at once when its BTC up/down state flips.

Checked every hour. At 16:00 UTC the model decides as usual (params under "vt"). At any other hour, if BTC's state
(btc_state, the rule e20v45 uses) differs from the state at the last 16:00 UTC bar and did not differ an hour earlier
(a new flip), the model decides at once; otherwise the book is held. `fast: up_and_down` acts on both flips, `down`
only on flips to down, `never` holds (the control). The band is 5%, so the hourly checks do not rebalance small
drifts. States are cached by bar time (they depend only on BTC up to that bar and the switch parameters).
`grid: decision` (v2) checks only at the 6-hour points of the 16:00 UTC decision (22:00, 04:00, 10:00 UTC), where
btc_state samples the same points as the daily decision, and compares with the point 6 hours earlier: it acts only on
real flips. The default `grid: hourly` (v1) checks every hour, where the 6-hour sampling shifts with the hour and the
state flickers (932 triggers against 112 real flips, 2020-2026).
Pre-registration: research/baitoey/prereg/20261004-fast-switch.md.
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.pol._combo import btc_state
from src.models.pol.pol_switch_vt_tl_e20v45 import MODEL as E20V45

GRID_HOUR = 16
_STATE: dict = {}


def state_at(view: MarketView, t: pd.Timestamp, sw: dict) -> str:
    key = (t, int(sw["ema_days"]), float(sw["hysteresis"]), int(sw["state_days"]))
    if key not in _STATE:
        close, qv = view.close.loc[:t], view.quote_volume.loc[:t]
        _STATE[key] = btc_state(replace(view, t=close.index[-1], close=close, quote_volume=qv), sw)
    return _STATE[key]


class FastSwitch:
    INNER = E20V45
    spec = ModelSpec(name="baitoey_fastswitch_e20v45", method="selector", author="baitoey", rebalance_hours=1, band=0.05,
                     uses_shorts=True, description="research only: e20v45 deciding at once when its BTC state flips")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        prev = view.prev_targets[view.prev_targets != 0]
        decide = lambda: self.INNER.targets(replace(view, params=p["vt"]))
        if view.t.hour == GRID_HOUR or prev.empty or p.get("fast", "up_and_down") == "never":
            return decide() if (view.t.hour == GRID_HOUR or prev.empty) else prev[prev.index.isin(list(view.universe))]
        idx = view.close.index
        grid = idx[idx.hour == GRID_HOUR]
        if len(grid) == 0 or len(idx) < 7:
            return prev[prev.index.isin(list(view.universe))]
        sw = p["vt"]["switch"]
        if p.get("grid", "hourly") == "decision":
            if (view.t.hour - GRID_HOUR) % 6 != 0:
                return prev[prev.index.isin(list(view.universe))]
            then, now, before = state_at(view, grid[-1], sw), state_at(view, idx[-1], sw), state_at(view, idx[-7], sw)
        else:
            then, now, before = state_at(view, grid[-1], sw), state_at(view, idx[-1], sw), state_at(view, idx[-2], sw)
        new_flip = now != then and before == then
        if new_flip and (p.get("fast", "up_and_down") == "up_and_down" or now == "down"):
            return decide()
        return prev[prev.index.isin(list(view.universe))]


MODEL = FastSwitch()
