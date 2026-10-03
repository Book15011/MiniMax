"""Shared trend signal of the book_* models (not a model: the registry skips modules starting with "_").

For coin i at decision time t, from hourly closes up to t only, looked up by timestamp (never by bar count):
- close(x) = the coin's last close at or before x, if it is at most `max_stale_hours` old; otherwise missing.
- ret_L = close(t) / close(t - L days) - 1, for each L in `lookback_days` (5, 10, 20, 30, 60).
- s_i = the share of the available lookbacks with ret_L > 0. Lookback L is available when close(t - L days)
  exists, so a coin with less than 60 days of history uses only the lookbacks it has, and a coin with less than
  5 days (or no close(t)) has s_i = 0. With all five lookbacks, s_i is one of 0, 0.2, ..., 1.
- Up-trend: s_i >= `up_threshold` (0.6).
- Liquid universe at t: the `liquid_n` (20) coins of view.universe with the highest quote volume over
  (t - `volume_days`, t]; ties by name. view.universe is the validation build's point-in-time top-30, which
  already leaves out stablecoins (validation.universe.stablecoins), PAXG and every tokenized stock (not in the
  pair list).
- breadth_t = the share of the liquid universe in an up-trend.
- sigma_i = the sample standard deviation of the coin's hourly returns over (t - vol_days, t], on the clock-hour
  grid (a return across a missing hour is missing).
Every number comes from the calling model's block in config.yaml.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.contracts import MarketView

HOUR = pd.Timedelta(hours=1)
DAY = pd.Timedelta(days=1)


def _last_close(close: pd.DataFrame, at: pd.Timestamp, stale: pd.Timedelta) -> pd.Series:
    """Per column, the last non-missing close in [at - stale, at]; NaN if there is none."""
    win = close.loc[at - stale: at]
    if win.empty:
        return pd.Series(np.nan, index=close.columns)
    return win.ffill().iloc[-1]


def trend_scores(close: pd.DataFrame, t: pd.Timestamp, coins, p: dict) -> pd.Series:
    """s_i in [0, 1] for each coin, from closes at or before t (rows after t are ignored)."""
    cols = [c for c in coins if c in close.columns]
    if not cols:
        return pd.Series(dtype=float)
    lbs = [int(L) for L in p["lookback_days"]]
    stale = pd.Timedelta(hours=float(p["max_stale_hours"]))
    sub = close.loc[t - max(lbs) * DAY - stale: t, cols]
    now = _last_close(sub, t, stale)
    hits = pd.Series(0.0, index=cols)
    avail = pd.Series(0.0, index=cols)
    for L in lbs:
        past = _last_close(sub, t - L * DAY, stale)
        ok = now.notna() & past.notna()
        avail += ok
        hits += ok & (now / past - 1.0 > 0.0)
    return (hits / avail).where(avail > 0, 0.0)


def liquid_universe(view: MarketView, p: dict) -> list[str]:
    """The `liquid_n` coins of view.universe with the highest quote volume over (t - volume_days, t]."""
    t, start = view.t, view.t - float(p["volume_days"]) * DAY
    qv = view.quote_volume.loc[start: t, [c for c in view.universe if c in view.quote_volume.columns]]
    vol = qv[qv.index > start].sum()                     # missing hours count as 0
    vol = vol.sort_index().sort_values(ascending=False, kind="mergesort")   # ties by name
    return list(vol.index[: int(p["liquid_n"])])


def breadth(view: MarketView, p: dict) -> float:
    """Share of the liquid universe in an up-trend (0 if the universe is empty)."""
    liquid = liquid_universe(view, p)
    if not liquid:
        return 0.0
    s = trend_scores(view.close, view.t, liquid, p)
    return float((s >= p["up_threshold"]).mean())


def hourly_vol(close: pd.DataFrame, t: pd.Timestamp, coins, days: float) -> pd.Series:
    """Sample std (ddof 1) of hourly returns over (t - days, t] on the clock grid; NaN with fewer than 2 returns."""
    cols = [c for c in coins if c in close.columns]
    grid = pd.date_range(t - float(days) * DAY, t, freq="h")
    c = close.loc[grid[0]: t, cols].reindex(grid)
    return c.pct_change(fill_method=None).iloc[1:].std(ddof=1)


def exposure(b: float, p: dict) -> float:
    """clip(b / full_breadth, min_exposure, 1), rounded half up to the nearest exposure_step."""
    e = min(max(b / float(p["full_breadth"]), float(p["min_exposure"])), 1.0)
    step = float(p["exposure_step"])
    return math.floor(e / step + 0.5 + 1e-9) * step
