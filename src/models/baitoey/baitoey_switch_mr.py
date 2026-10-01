"""Calm/trend switch: mean reversion when the market is calm, momentum rotation otherwise.

Calm means BTC's 30-day realized volatility (from hourly returns) is below the `calm_quantile` of its daily values
over the past 365 days, measured at the decision. In calm markets the book follows baitoey_mr_bbrsi (Bollinger +
RSI mean reversion on 4 h bars), which earns from swings around a flat price; otherwise it follows the team ROT_EW
rotation, which earns from trends. Each sleeve runs with its own parameters, under `sleeves:` in config.yaml.
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey.baitoey_mr_bbrsi import MODEL as MEAN_REVERSION
from src.models.baselines.team_rot_ew import MODEL as ROTATION

BTC = "BTCUSDT"


def btc_calm(close: pd.Series, vol_days: int, regime_days: int, q: float) -> bool:
    """True when BTC's latest 30-day volatility is below quantile q of its values at the decision hour on each of
    the last regime_days days. Too little history or a missing latest value: not calm."""
    need = (regime_days + vol_days) * 24 + 1
    s = close.iloc[-need:]
    if len(s) < need:
        return False
    vol = s.pct_change(fill_method=None).rolling(vol_days * 24, min_periods=vol_days * 12).std()
    if pd.isna(vol.iloc[-1]):
        return False
    daily = vol.iloc[::-24].iloc[:regime_days].dropna()
    return bool(vol.iloc[-1] < daily.quantile(q))


class CalmSwitch:
    spec = ModelSpec(name="baitoey_switch_mr", method="selector", author="baitoey", rebalance_hours=4, band=0.05,
                     description="Mean reversion when BTC volatility is below its 1-year median, ROT_EW rotation "
                                 "otherwise")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        calm = BTC in view.close.columns and btc_calm(view.close[BTC], p["vol_days"], p["regime_days"],
                                                      p["calm_quantile"])
        sleeve, params = (MEAN_REVERSION, p["sleeves"]["calm"]) if calm else (ROTATION, p["sleeves"]["trend"])
        return sleeve.targets(replace(view, params=params))


MODEL = CalmSwitch()
