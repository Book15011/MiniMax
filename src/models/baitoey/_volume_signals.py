"""Volume-confirmed timing signals for baitoey models, from hourly closes and quote volumes only.

The view carries no OHLC, so highs, lows and true ranges are taken from hourly closes. Every function reads rows up
to the last one (the decision time) and nothing later. A missing quote volume makes the volume ratio missing, and a
condition that needs it is then false: no breakout entry, no volume-confirmed exit, no chase block.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def volume_ratio(qv: pd.DataFrame, short_h: int, long_days: int) -> pd.DataFrame:
    """Quote volume of the last short_h hours over its average for the same length across the last long_days."""
    long_h = long_days * 24
    short = qv.rolling(short_h, min_periods=short_h).sum()
    base = qv.rolling(long_h, min_periods=long_h).sum() * short_h / long_h
    return short / base.where(base > 0)


def prior_high(close: pd.DataFrame, hours: int) -> pd.DataFrame:
    """Highest close of the previous `hours` hours, excluding the current one."""
    return close.shift(1).rolling(hours, min_periods=hours).max()


def prior_low(close: pd.DataFrame, hours: int) -> pd.DataFrame:
    """Lowest close of the previous `hours` hours, excluding the current one."""
    return close.shift(1).rolling(hours, min_periods=hours).min()


def momentum_score(close: pd.DataFrame, lookback_days: list[int]) -> pd.Series:
    """The ROT_EW score: mean over the lookbacks of the lookback return over the volatility of that span."""
    rets = close.pct_change(fill_method=None)
    last = close.iloc[-1]
    terms = [(last / close.iloc[-1 - d * 24] - 1) / (rets.iloc[-d * 24:].std() * np.sqrt(d * 24))
             for d in lookback_days]
    return (sum(terms) / len(terms)).replace([np.inf, -np.inf], np.nan).dropna()


def daily_atr(close: pd.DataFrame, days: int) -> pd.Series:
    """Mean true range of the last `days` 24-hour blocks ending at the last row. A block spans its hourly closes,
    widened to the last close of the block before it. Needs days * 24 + 1 rows; a gap makes the result NaN."""
    c = close.iloc[-(days * 24 + 1):].to_numpy(dtype=float)
    prev = c[0:-1:24]
    blocks = c[1:].reshape(days, 24, -1)
    hi = np.maximum(blocks.max(axis=1), prev)
    lo = np.minimum(blocks.min(axis=1), prev)
    return pd.Series((hi - lo).mean(axis=0), index=close.columns)


def chandelier_exit(close: pd.DataFrame, trail_h: int, atr_days: int, mult: float) -> pd.Series:
    """True where the last close is below the highest close of the last trail_h hours minus mult daily ATRs."""
    peak = close.iloc[-trail_h:].max()
    return close.iloc[-1] < peak - mult * daily_atr(close.ffill(), atr_days)


def breakdown_blocked(close: pd.DataFrame, qv: pd.DataFrame, p: dict) -> set[str]:
    """Coins that, within the last exit_cooldown_hours, closed below their previous exit_low_hours low while the
    volume ratio was above exit_volume_ratio."""
    ratio = volume_ratio(qv, p["volume_short_hours"], p["volume_long_days"])
    hit = (close < prior_low(close, p["exit_low_hours"])) & (ratio > p["exit_volume_ratio"])
    recent = hit.iloc[-p["exit_cooldown_hours"]:].any()
    return set(recent[recent].index)


def chase_blocked(close: pd.DataFrame, qv: pd.DataFrame, p: dict) -> set[str]:
    """Coins that spiked (chase_return_hours return above chase_return on a volume ratio above chase_volume_ratio)
    within the last chase_window_hours and have not yet pulled back chase_pullback from their highest close since
    the latest spike."""
    ratio = volume_ratio(qv, p["volume_short_hours"], p["volume_long_days"])
    h = p["chase_return_hours"]
    spike = (close / close.shift(h) - 1 > p["chase_return"]) & (ratio > p["chase_volume_ratio"])
    win, cw = spike.iloc[-p["chase_window_hours"]:], close.iloc[-p["chase_window_hours"]:]
    out = set()
    for c in win.columns[win.any().to_numpy()]:
        latest = win.index[win[c].to_numpy()][-1]
        peak = cw[c].loc[latest:].max()
        if close[c].iloc[-1] > peak * (1 - p["chase_pullback"]):
            out.add(c)
    return out


def scale_to_daily_vol(w: pd.Series, close: pd.DataFrame, vol_days: int, target: float) -> pd.Series:
    """Scale the book down so its estimated daily volatility (vol_days of hourly covariance, times 24) is at most
    target, as the ROT_EW benchmark does."""
    rets = close[w.index].pct_change(fill_method=None).iloc[-vol_days * 24:]
    cov = rets.cov().to_numpy() * 24.0
    book = float(np.sqrt(max(w.to_numpy() @ cov @ w.to_numpy(), 0.0)))
    scale = min(1.0, target / book) if book > 0 else 1.0
    w = (w * scale).replace([np.inf, -np.inf], np.nan).dropna()
    return w[w > 0]
