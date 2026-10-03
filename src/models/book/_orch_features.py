"""Features of book_orch's forecasts (not a model: the registry skips modules starting with "_").

Pure functions of a MarketView, shared by the model (src/models/book/book_orch.py) and by its walk-forward training
(backtest/orch_train.py), so both compute exactly the same numbers. Everything is looked up by timestamp: a coin's
close at time x is its last close at or before x, at most `max_stale_hours` old (src/models/book/_trend.py).

Per coin i at decision time t (columns COIN_FEATURES):
- ret_{1,3,7,14,30}d: close(t) / close(t - L days) - 1
- vol_{1,7,30}d: sample std of hourly returns over (t - L days, t] on the clock grid (_trend.hourly_vol); vol_ratio = 7d / 30d
- dist_high30: close(t) / the highest close over (t - 30 days, t] - 1
- qv_ratio: quote volume over (t - 24 h, t] / (quote volume over (t - 30 days, t] / 30)
- base_w: the base's weight in the coin (0 if not held)
Market-wide (MARKET_FEATURES, the same for every coin at t):
- btc_ret_{1,7,30}d; btc_vol7_pct: mid-rank percentile of BTC's 7-day volatility at t among its values at
  t - 24 h * k, k = 0..364
- breadth: _trend.breadth; dispersion: cross-sectional std (ddof 1) of the 7-day returns of _trend.liquid_universe
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.contracts import MarketView
from src.models.book._trend import _last_close, breadth, hourly_vol, liquid_universe

DAY = pd.Timedelta(days=1)
HOUR = pd.Timedelta(hours=1)
RET_DAYS = (1, 3, 7, 14, 30)
VOL_DAYS = (1, 7, 30)
COIN_FEATURES = ([f"ret_{d}d" for d in RET_DAYS] + [f"vol_{d}d" for d in VOL_DAYS]
                 + ["vol_ratio", "dist_high30", "qv_ratio", "base_w"])
MARKET_FEATURES = ["btc_ret_1d", "btc_ret_7d", "btc_ret_30d", "btc_vol7_pct", "breadth", "dispersion"]
FEATURES = COIN_FEATURES + MARKET_FEATURES
BTC = "BTCUSDT"


def _returns(close: pd.DataFrame, t: pd.Timestamp, cols: list[str], days, stale: pd.Timedelta) -> pd.DataFrame:
    sub = close.loc[t - max(days) * DAY - stale: t, cols]
    now = _last_close(sub, t, stale)
    return pd.DataFrame({f"ret_{d}d": now / _last_close(sub, t - d * DAY, stale) - 1.0 for d in days})


def btc_vol_percentile(close: pd.DataFrame, t: pd.Timestamp) -> float:
    """Mid-rank percentile of BTC's 7-day hourly-return volatility at t among its values at t - 24 h * k, k = 0..364."""
    if BTC not in close.columns:
        return np.nan
    grid = pd.date_range(t - 372 * DAY, t, freq="h")
    r = close[BTC].loc[grid[0]: t].reindex(grid).pct_change(fill_method=None)
    vol = r.rolling(168, min_periods=2).std(ddof=1)
    pts = vol.reindex(t - DAY * np.arange(365)).to_numpy()
    pts = pts[np.isfinite(pts)]
    if len(pts) == 0 or not np.isfinite(vol.iloc[-1]):
        return np.nan
    x = vol.iloc[-1]
    return float(((pts < x).sum() + 0.5 * (pts == x).sum()) / len(pts))


def market_features(view: MarketView, trend: dict) -> dict:
    t = view.t
    stale = pd.Timedelta(hours=float(trend["max_stale_hours"]))
    out = {}
    if BTC in view.close.columns:
        b = _returns(view.close, t, [BTC], (1, 7, 30), stale).iloc[0]
        out.update({"btc_ret_1d": b["ret_1d"], "btc_ret_7d": b["ret_7d"], "btc_ret_30d": b["ret_30d"]})
    else:
        out.update({"btc_ret_1d": np.nan, "btc_ret_7d": np.nan, "btc_ret_30d": np.nan})
    out["btc_vol7_pct"] = btc_vol_percentile(view.close, t)
    out["breadth"] = breadth(view, trend)
    liquid = liquid_universe(view, trend)
    r7 = _returns(view.close, t, liquid, (7,), stale)["ret_7d"].dropna() if liquid else pd.Series(dtype=float)
    out["dispersion"] = float(r7.std(ddof=1)) if len(r7) > 1 else np.nan
    return out


def coin_features(view: MarketView, coins, base_w: pd.Series, trend: dict, market: dict | None = None) -> pd.DataFrame:
    """One row per coin (index = series id), columns FEATURES, from data at or before view.t only."""
    t = view.t
    cols = [c for c in coins if c in view.close.columns]
    if not cols:
        return pd.DataFrame(columns=FEATURES, dtype=float)
    stale = pd.Timedelta(hours=float(trend["max_stale_hours"]))
    f = _returns(view.close, t, cols, RET_DAYS, stale)
    for d in VOL_DAYS:
        f[f"vol_{d}d"] = hourly_vol(view.close, t, cols, d)
    f["vol_ratio"] = f["vol_7d"] / f["vol_30d"]
    win = view.close.loc[t - 30 * DAY: t, cols]
    win = win[win.index > t - 30 * DAY]
    f["dist_high30"] = _last_close(view.close.loc[t - stale: t, cols], t, stale) / win.max() - 1.0
    qv = view.quote_volume.loc[t - 30 * DAY: t, cols]
    qv = qv[qv.index > t - 30 * DAY]
    q30 = qv.sum() / 30.0
    f["qv_ratio"] = (qv[qv.index > t - DAY].sum() / q30).where(q30 > 0)
    f["base_w"] = base_w.reindex(cols).fillna(0.0).astype(float)
    m = market if market is not None else market_features(view, trend)
    for k in MARKET_FEATURES:
        f[k] = m[k]
    return f[FEATURES].replace([np.inf, -np.inf], np.nan)
