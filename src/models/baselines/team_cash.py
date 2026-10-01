"""Reference: all cash. Every score is 0 and it never trades, so it fails the activity gate (G1)."""
from __future__ import annotations

import pandas as pd

from src.contracts import MarketView, ModelSpec


class Cash:
    spec = ModelSpec(name="team_cash", method="reference", author="team", rebalance_hours=24, band=0.0,
                     description="Hold USD only. The floor of the scoring: scores 0 everywhere and fails G1")

    def targets(self, view: MarketView) -> pd.Series:
        return pd.Series(dtype=float)


MODEL = Cash()
