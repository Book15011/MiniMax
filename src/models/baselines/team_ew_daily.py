"""Reference (EW_DAILY): equal weights across the day's universe, rebalanced every day at 16:00 UTC."""
from __future__ import annotations

import pandas as pd

from src.contracts import MarketView, ModelSpec


class EqualWeightDaily:
    spec = ModelSpec(name="team_ew_daily", method="reference", author="team", rebalance_hours=24, band=0.0,
                     description="Equal weights across the point-in-time universe, rebalanced daily (scoring field)")

    def targets(self, view: MarketView) -> pd.Series:
        last = view.close.iloc[-1].reindex(list(view.universe))
        held = sorted(last.dropna().index)                 # coins with a price at t
        if not held:
            return pd.Series(dtype=float)
        return pd.Series(1.0 / len(held), index=held)


MODEL = EqualWeightDaily()
