"""Research only (research/baitoey/prereg/20261009-faster-down-switch.md): pol_switch_vt_tl_e20v45 with its own BTC
trend switch made asymmetric. Up after a 6-hourly close above EMA x (1 + hysteresis), down after one below
EMA x (1 - hysteresis_down); between the two the state is kept (team_trend_2's rule, with the down side apart)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.contracts import MarketView
from src.models.baselines import team_trend_2
from src.models.pol.pol_switch_vt_tl_e20v45 import SwitchVtTlE20V45


def in_trend_asym(price: pd.Series, ema: pd.Series, up: float, down: float) -> bool:
    """State at the last point: the side of the last close outside the band [1 - down, 1 + up]; out if none."""
    ratio = (price / ema).to_numpy()
    decisive = np.flatnonzero((ratio > 1 + up) | (ratio < 1 - down))
    return bool(decisive.size) and bool(ratio[decisive[-1]] > 1 + up)


def btc_state_asym(view: MarketView, p: dict, coin: str = "BTCUSDT") -> str:
    """'up' or 'down' as src.models.pol._combo.btc_state, with the down trigger at p['hysteresis_down']."""
    span = int(p["ema_days"]) * 24
    close, _ = view.tail((int(p["state_days"]) + 3 * int(p["ema_days"])) * 24 + 1)
    if coin not in close:
        return "down"
    px = close[coin].dropna()
    if len(px) < span:
        return "down"
    ema = px.ewm(span=span, adjust=False).mean()
    step = (px.index.hour - px.index[-1].hour) % team_trend_2.MODEL.spec.rebalance_hours == 0
    pts = (px.index > px.index[-1] - pd.Timedelta(days=int(p["state_days"]))) & step
    return "up" if in_trend_asym(px[pts], ema[pts], float(p["hysteresis"]), float(p["hysteresis_down"])) else "down"


class FastDown(SwitchVtTlE20V45):
    @staticmethod
    def state(view: MarketView, p: dict) -> str | None:
        if not p.get("switch"):
            return None
        if p.get("calm"):
            raise ValueError("FastDown does not support the calm switch")
        return btc_state_asym(view, p["switch"])
