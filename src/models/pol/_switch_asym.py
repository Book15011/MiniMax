"""Asymmetric BTC switch for the pol_switch_vt_tl_e20v45_d* variants (reports/review/20261009-prereg-e20v45-band.md,
addendum 1): BTC turns 'down' below EMA x (1 - down_hysteresis) and back 'up' above EMA x (1 + hysteresis), and keeps
its state in between. _combo.btc_state with separate down and up bars; _combo.py itself is unchanged."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.contracts import MarketView
from src.models.baselines import team_trend_2
from src.models.pol._combo import Combo


def in_trend(price: pd.Series, ema: pd.Series, up: float, down: float) -> bool:
    """State at the last point: the side of the last close outside the band; out of trend if there is none."""
    ratio = (price / ema).to_numpy()
    decisive = np.flatnonzero((ratio > 1 + up) | (ratio < 1 - down))
    return bool(decisive.size) and bool(ratio[decisive[-1]] > 1 + up)


def btc_state(view: MarketView, p: dict, coin: str = "BTCUSDT") -> str:
    """_combo.btc_state with the down bar at p['down_hysteresis'] and the up bar at p['hysteresis']."""
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
    return "up" if in_trend(px[pts], ema[pts], float(p["hysteresis"]), float(p["down_hysteresis"])) else "down"


class AsymSwitch(Combo):
    """A Combo whose switch uses btc_state above; no calm state."""

    @staticmethod
    def state(view: MarketView, p: dict) -> str | None:
        if not p.get("switch"):
            return None
        if p.get("calm"):
            raise ValueError("the asymmetric switch has no calm state")
        return btc_state(view, p["switch"])
