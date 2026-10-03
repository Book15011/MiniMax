"""Research only (not registered models): the volume-confirmed exit of baitoey_vt_mom checked every hour.

The daily model decides at 16:00 UTC as usual (params under "vt"). At every other hour the book is the latest daily
decision, except that a coin held long whose close falls below its lowest close of the previous `exit_low_hours`
hours while its volume ratio is above `exit_volume_ratio` (the daily model's own exit, params under "exit") is sold
to cash and stays out until the next daily decision, where the daily model's 24-hour block applies as usual. Shorts
are untouched. With `hourly_exit: false` the wrapper only holds the book (the control). The band is 5%, as in
pol_abl_shock, so the hourly checks do not rebalance small drifts. Pre-registration:
research/baitoey/prereg/20261003-hourly-exit.md.
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey._volume_signals import prior_low, volume_ratio
from src.models.baitoey.baitoey_vt_mom import MODEL as VT_MOM
from src.models.pol.pol_switch_vt_tl_e20v45 import MODEL as E20V45

GRID_HOUR = 16


def broke_down(view: MarketView, coins: list[str], q: dict) -> set[str]:
    """Coins whose last close is below the previous exit_low_hours low on a volume ratio above exit_volume_ratio."""
    if not coins:
        return set()
    need = int(q["volume_long_days"]) * 24 + int(q["exit_low_hours"]) + 2
    close, qv = view.close[coins].iloc[-need:], view.quote_volume[coins].iloc[-need:]
    ratio = volume_ratio(qv, int(q["volume_short_hours"]), int(q["volume_long_days"])).iloc[-1]
    hit = (close.iloc[-1] < prior_low(close, int(q["exit_low_hours"])).iloc[-1]) & (ratio > float(q["exit_volume_ratio"]))
    return set(hit[hit.fillna(False)].index)


class HourlyExit:
    INNER = E20V45
    spec = ModelSpec(name="baitoey_vexit_e20v45", method="momentum", author="baitoey", rebalance_hours=1, band=0.05,
                     uses_shorts=True, description="research only: e20v45 with its volume-confirmed exit checked hourly")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        prev = view.prev_targets[view.prev_targets != 0]
        if view.t.hour == GRID_HOUR or prev.empty:
            return self.INNER.targets(replace(view, params=p["vt"]))
        book = prev[prev.index.isin(list(view.universe))]
        if not p.get("hourly_exit", True):
            return book
        out = broke_down(view, [c for c in book.index if book[c] > 0], p["exit"])
        return book.drop(list(out))


class HourlyExitVt(HourlyExit):
    INNER = VT_MOM
    spec = replace(HourlyExit.spec, name="baitoey_vexit_vt", uses_shorts=False,
                   description="research only: vt_mom with its volume-confirmed exit checked hourly")
