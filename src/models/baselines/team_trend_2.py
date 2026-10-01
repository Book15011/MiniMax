"""Reference (TREND_2): slow BTC and ETH trend, sized by volatility.

For each coin: a 40-day EMA of hourly closes. The coin is in trend once its price closes above EMA * 1.03 and
out of trend once it closes below EMA * 0.97; between the two it keeps its state. The state is replayed at
every 6-hour decision point of the last `state_days` days, starting out of trend, so it depends only on the
view. Weight = 0.25 / the coin's 30-day annualized volatility, cut to 15% of that when out of trend; the book
is scaled down if the two weights add up to more than 1. Decisions every 6 h; trades only on > 5 points of
drift (spec.band).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.contracts import MarketView, ModelSpec

HOURS_PER_YEAR = 24 * 365


def in_trend(price: pd.Series, ema: pd.Series, hysteresis: float) -> bool:
    """State at the last point: the side of the last close outside the band; out of trend if there is none."""
    ratio = (price / ema).to_numpy()
    decisive = np.flatnonzero((ratio > 1 + hysteresis) | (ratio < 1 - hysteresis))
    return bool(decisive.size) and bool(ratio[decisive[-1]] > 1 + hysteresis)


class Trend2:
    spec = ModelSpec(name="team_trend_2", method="reference", author="team", rebalance_hours=6, band=0.05,
                     description="BTC and ETH 40-day EMA trend with 3% hysteresis, 0.25/vol sizing (scoring field)")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        coins = [c for c in p["coins"] if c in view.universe]
        span = int(p["ema_days"]) * 24
        close, _ = view.tail((int(p["state_days"]) + 3 * int(p["ema_days"])) * 24 + 1)
        w = {}
        for c in coins:
            px = close[c].dropna()
            if len(px) < span or px.index[-1] != view.t:
                continue
            ema = px.ewm(span=span, adjust=False).mean()
            window = px.index[-1] - pd.Timedelta(days=int(p["state_days"]))
            step = (px.index.hour - px.index[-1].hour) % self.spec.rebalance_hours == 0
            pts = (px.index > window) & step
            vol = px.pct_change(fill_method=None).iloc[-int(p["vol_days"]) * 24:].std() * np.sqrt(HOURS_PER_YEAR)
            if not np.isfinite(vol) or vol <= 0:
                continue
            full = p["risk_budget"] / vol
            w[c] = full if in_trend(px[pts], ema[pts], p["hysteresis"]) else full * p["out_of_trend_scale"]
        out = pd.Series(w, dtype=float)
        gross = float(out.abs().sum())
        return out / gross if gross > 1.0 else out


MODEL = Trend2()
