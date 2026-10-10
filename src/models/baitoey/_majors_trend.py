"""Research only (research/baitoey/prereg/20261010-majors-trend.md): a fast trend long/short on the five majors.

Signal per coin s = EMA_fast / EMA_slow - 1 of hourly closes (spans in hours); |s| under the dead band holds
nothing. Weights sign(s) / daily volatility, normalised to gross 1, capped per coin, then scaled down so the book's
covariance daily volatility is at most the target. A generic public method; no other team's constants are used.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from src.contracts import MarketView, ModelSpec

MAJORS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT")


def trend_signals(close: pd.DataFrame, fast: int, slow: int) -> pd.Series:
    ef = close.ewm(span=fast, adjust=False).mean().iloc[-1]
    es = close.ewm(span=slow, adjust=False).mean().iloc[-1]
    return (ef / es - 1.0).replace([np.inf, -np.inf], np.nan).dropna()


def scale_signed(w: pd.Series, close: pd.DataFrame, vol_days: int, target: float) -> pd.Series:
    """Scale a signed book down so its daily volatility (vol_days of hourly covariance x 24) is at most target."""
    rets = close[w.index].pct_change(fill_method=None).iloc[-vol_days * 24:]
    cov = rets.cov().to_numpy() * 24.0
    v = float(np.sqrt(max(w.to_numpy() @ cov @ w.to_numpy(), 0.0)))
    return w * (min(1.0, target / v) if v > 0 else 1.0)


class MajorsTrend:
    spec = ModelSpec(name="baitoey_mjt", method="trend", author="baitoey", rebalance_hours=24, band=0.05,
                     uses_shorts=True, description="research only: fast trend long/short on the five majors")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        fast, slow, vol_days = int(p["fast"]), int(p["slow"]), int(p["vol_days"])
        coins = [c for c in MAJORS if c in view.universe and c in view.close.columns]
        if not coins:
            return pd.Series(dtype=float)
        close = view.close[coins].iloc[-(max(4 * slow, vol_days * 24) + 1):]
        close = close.loc[:, close.iloc[-1].notna() & (close.notna().sum() >= vol_days * 24)]
        if close.empty:
            return pd.Series(dtype=float)
        s = trend_signals(close, fast, slow)
        s = s[s.abs() >= float(p["dead_band"])]
        if s.empty:
            return pd.Series(dtype=float)
        vol = close[s.index].pct_change(fill_method=None).iloc[-vol_days * 24:].std() * np.sqrt(24.0)
        raw = (np.sign(s) / vol).replace([np.inf, -np.inf], np.nan).dropna()
        if raw.empty or raw.abs().sum() <= 0:
            return pd.Series(dtype=float)
        w = (raw / raw.abs().sum()).clip(-float(p["cap"]), float(p["cap"]))
        w = scale_signed(w, close, vol_days, float(p["target_daily_vol"]))
        return w[w.abs() > 1e-12]


def make(name: str, hours: int, description: str):
    cls = type(name, (MajorsTrend,), {})
    cls.spec = replace(MajorsTrend.spec, name=name, rebalance_hours=hours, description=description)
    return cls()
