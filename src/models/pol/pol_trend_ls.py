"""Per-coin trend, long and short.

For each liquid coin, measure its trend as a t-statistic: the lookback log return divided by the
volatility expected over that horizon. Go long clear up-trends and short clear down-trends, weight by
inverse volatility, and scale the whole book to a portfolio volatility target estimated from the
recent covariance of hourly returns (never above 100% gross).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.contracts import MarketView, ModelSpec

HOURS_PER_YEAR = 24 * 365


class TrendLongShort:
    spec = ModelSpec(name="pol_trend_ls", method="trend", author="pol", rebalance_hours=24, band=0.03,
                     uses_shorts=True,
                     description="Long coins in clear up-trends, short clear down-trends, inverse-vol weights, portfolio vol target")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        hours = (max(p["lookback_days"], p["vol_days"]) + 1) * 24
        close, qv = view.tail(hours)
        ok = close.notna().sum() >= p["min_history_days"] * 24
        close, qv = close.loc[:, ok], qv.loc[:, ok]
        if close.shape[1] < p["min_coins"]:
            return pd.Series(dtype=float)
        liquid = qv.iloc[-p["vol_days"] * 24:].sum().sort_values(ascending=False).index[: p["top_n"]]
        close = close[liquid]
        rets = close.pct_change(fill_method=None).iloc[-p["vol_days"] * 24:]
        vol = rets.std() * np.sqrt(HOURS_PER_YEAR)
        lb = p["lookback_days"]
        trend = np.log(close.iloc[-1] / close.iloc[-1 - lb * 24]) / (vol / np.sqrt(365) * np.sqrt(lb))
        trend = trend.replace([np.inf, -np.inf], np.nan).dropna()
        longs = trend[trend > p["threshold"]].index
        shorts = trend[trend < -p["threshold"]].index

        w = pd.Series(0.0, index=trend.index)
        for names, sign in ((longs, 1.0), (shorts, -1.0)):
            if len(names):
                iv = 1.0 / vol[names]
                w[names] = sign * (iv / iv.sum()) * 0.5
        w = w[w != 0.0]
        if w.empty:
            return w
        cov = rets[w.index].fillna(0.0).cov().to_numpy() * HOURS_PER_YEAR
        port_vol = float(np.sqrt(max(w.to_numpy() @ cov @ w.to_numpy(), 1e-12)))
        scale = min(p["target_vol"] / port_vol, 1.0 / float(w.abs().sum()))
        return w * scale


MODEL = TrendLongShort()
