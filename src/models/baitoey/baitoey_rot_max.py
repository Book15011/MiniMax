"""Return-first momentum rotation: the team ROT_EW rotation, fully invested.

Score of a coin = mean over 3, 7 and 14 days of its return over the span divided by its volatility over the span;
hold the top k, keep a holding while it ranks in the top 12, equal weights. Unlike ROT_EW the book is never scaled
down for volatility (gross 1.0), and k can be smaller, so more of the book rides the strongest coins. Optional light
gate: all cash when BTC closed below its 20-day average at the decision hour on two days in a row.
"""
from __future__ import annotations

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baselines.team_rot_ew import rotation_targets

BTC = "BTCUSDT"


def btc_below_average(close: pd.Series, days: int, confirm: int) -> bool:
    """True when BTC closed below its `days`-day average at each of the last `confirm` decision hours. Daily closes
    are the closes 24 h apart ending at the last row; each average includes that day. Missing data: False."""
    need = (days + confirm - 1) * 24 + 1
    s = close.iloc[-need:]
    if len(s) < need:
        return False
    daily = s.iloc[::-24].iloc[::-1]
    below = daily < daily.rolling(days, min_periods=days).mean()
    return bool(below.iloc[-confirm:].all())


class ReturnFirstRotation:
    spec = ModelSpec(name="baitoey_rot_max", method="momentum", author="baitoey", rebalance_hours=24, band=0.05,
                     description="ROT_EW rotation fully invested (no vol cap), top k equal weights; "
                                 "optional BTC 20-day-average gate")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        if p["btc_gate"] and BTC in view.close.columns and btc_below_average(
                view.close[BTC], p["gate_days"], p["gate_confirm_days"]):
            return pd.Series(dtype=float)
        return rotation_targets(view, p)


MODEL = ReturnFirstRotation()
