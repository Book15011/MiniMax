"""Bar indicators (Bollinger Bands, RSI) on bars of `bar_hours`, sampled from hourly closes.

A bar is the hourly close every bar_hours hours, ending at the last row (the decision time), so a 24 h bar series
holds the closes at the daily decision hour. RSI uses simple averages of the last n bar changes (no Wilder
smoothing, so the value depends only on the window). Missing data gives NaN, and every condition on NaN is false.
"""
from __future__ import annotations

import pandas as pd


def sample_bars(close: pd.DataFrame, bar_hours: int, n_bars: int) -> pd.DataFrame:
    rows = close.iloc[-((n_bars - 1) * bar_hours + 1):]
    return rows.iloc[::-bar_hours].iloc[::-1]


def bollinger(bars: pd.DataFrame, n: int, k: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Middle band (n-bar mean) and lower band (mean minus k population standard deviations)."""
    mid = bars.rolling(n, min_periods=n).mean()
    sd = bars.rolling(n, min_periods=n).std(ddof=0)
    return mid, mid - k * sd


def rsi(bars: pd.DataFrame, n: int) -> pd.DataFrame:
    d = bars.diff()
    gain = d.clip(lower=0).rolling(n, min_periods=n).mean()
    loss = (-d.clip(upper=0)).rolling(n, min_periods=n).mean()
    return 100 - 100 / (1 + gain / loss)
