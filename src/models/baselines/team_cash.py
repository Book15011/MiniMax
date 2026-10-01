"""Reference: all cash. The model never trades; the engine's keep-alive trade (0.2% BTC, reversed the next day) still
makes every day active, as the live bot would, and costs about 0.004% a window. Scores about 0."""
from __future__ import annotations

import pandas as pd

from src.contracts import MarketView, ModelSpec


class Cash:
    spec = ModelSpec(name="team_cash", method="reference", author="team", rebalance_hours=24, band=0.0,
                     description="Hold USD only (the keep-alive trade keeps it active). The floor of the scoring: scores about 0")

    def targets(self, view: MarketView) -> pd.Series:
        return pd.Series(dtype=float)


MODEL = Cash()
