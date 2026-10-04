"""Research only (not registered models): variants B and D of baitoey_two_sleeve.

- TwoSleeveLS (variant B): the same model allowed to short, for the momentum sleeve's bottom 5. Research only: the
  competition allows directional strategies only, so it never runs live.
- TwoSleeveStaggered (variant D): variant C in len(`stagger_hours`) equal tranches, one rebalanced at each of the
  hours (00:00, 08:00, 16:00 UTC): at each of those hours the book is the mean of the tranches' targets, each computed
  from data up to its own latest rebalance hour.
Pre-registration: research/baitoey/prereg/20261004-two-sleeve.md.
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.contracts import MarketView
from src.models.baitoey.baitoey_two_sleeve import TwoSleeve


class TwoSleeveLS(TwoSleeve):
    spec = replace(TwoSleeve.spec, name="baitoey_two_sleeve_ls", uses_shorts=True,
                   description="research only: two sleeves with momentum shorts (variant B), never live")


class TwoSleeveStaggered:
    INNER = TwoSleeve()
    spec = replace(TwoSleeve.spec, name="baitoey_two_sleeve_stag", rebalance_hours=8,
                   description="research only: two sleeves in three tranches rebalanced at 00, 08 and 16 UTC (variant D)")

    def targets(self, view: MarketView) -> pd.Series:
        n = len(view.params["stagger_hours"])
        step = 24 // n
        parts = []
        for k in range(n):
            t = view.t - pd.Timedelta(hours=step * k)
            close, qv = view.close.loc[:t], view.quote_volume.loc[:t]
            parts.append(self.INNER.targets(replace(view, t=close.index[-1], close=close, quote_volume=qv)))
        book = pd.concat(parts, axis=1).fillna(0.0).mean(axis=1)
        return book[book.abs() > 1e-12]
