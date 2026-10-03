"""Research only (not a registered model): pol_switch_vt_tl_e20v45 with a per-coin stop-loss checked every hour.

The daily model decides at 16:00 UTC as usual (params under "vt", as in pol_abl_shock). At every other hour the book
is the latest daily decision, except that a coin held long that has fallen at least `stop` since the 16:00 UTC bar
(a short: risen at least `stop`) is closed to cash and stays out until the next daily decision. If the book is
empty between decisions (the first hour of a round, or every coin stopped), the daily model decides afresh and the
coins past the stop are left out. Pre-registration: research/baitoey/prereg/20261003-stop-loss.md.
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.pol.pol_switch_vt_tl_e20v45 import MODEL as E20V45

GRID_HOUR = 16


class StopLoss:
    INNER = E20V45
    spec = ModelSpec(name="baitoey_stop_e20v45", method="momentum", author="baitoey", rebalance_hours=1,
                     band=E20V45.spec.band, uses_shorts=True,
                     description="research only: pol_switch_vt_tl_e20v45 with an hourly per-coin stop-loss")

    @staticmethod
    def stopped(book: pd.Series, view: MarketView, stop: float) -> pd.Series:
        """True for each coin in book that moved against the position by at least stop since the last 16:00 UTC bar."""
        grid = view.close.index[view.close.index.hour == GRID_HOUR]
        if len(grid) == 0 or book.empty:
            return pd.Series(False, index=book.index)
        r = view.close.iloc[-1].reindex(book.index) / view.close.loc[grid[-1]].reindex(book.index) - 1.0
        return (((book > 0) & (r <= -stop)) | ((book < 0) & (r >= stop))).fillna(False)

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        if view.t.hour == GRID_HOUR:
            return self.INNER.targets(replace(view, params=p["vt"]))
        prev = view.prev_targets[view.prev_targets != 0]
        book = self.INNER.targets(replace(view, params=p["vt"])) if prev.empty else prev[prev.index.isin(list(view.universe))]
        book = book[book != 0]
        return book[~self.stopped(book, view, float(p["stop"]))]


MODEL = StopLoss()
