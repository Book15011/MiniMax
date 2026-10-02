"""Reference: 100% BTC. Every competing model must have a better worst fortnight than this."""
from __future__ import annotations

import pandas as pd

from src.contracts import MarketView, ModelSpec


class BtcHold:
    spec = ModelSpec(name="team_btc_hold", method="reference", author="team", rebalance_hours=24, band=0.0,
                     description="Hold 100% BTC. Reference for the worst-fortnight check; active daily only through the keep-alive trade")

    def targets(self, view: MarketView) -> pd.Series:
        return pd.Series({"BTCUSDT": 1.0}) if "BTCUSDT" in view.universe else pd.Series(dtype=float)


MODEL = BtcHold()
