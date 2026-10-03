"""Features of book_orch's per-coin forecasts, v2 (not a model: the registry skips modules starting with "_").

Pre-registered in reports/review/20261003-prereg-orch-v2.md, section 2.3. feature_frame computes the 37 features of
the liquid coins at the requested hours from hourly closes and quote volumes. Training runs it once on the whole
panel (backtest/orch_train.py); the live path runs it on a view (features_at), so both compute the same numbers.
A value at t uses bars stamped at or before t only: every window ends at t.

On the clock-hour grid:
- px(x) = the last close at or before x, at most `max_stale_hours` (24) old; ret_L = px(t) / px(t - L) - 1;
- hourly returns are close-to-close, missing across a missing hour; vol_L = their sample std over (t - L, t], at
  least 2 returns (as _trend.hourly_vol); vol_ratio = vol_24h / vol_30d;
- dist_hi24 / dist_lo24 / dist_hi7d = px(t) / the highest (lowest) close in (t - L, t] - 1;
- qv_ratio_1h = qv(t) / (quote volume over (t - 24 h, t] / 24); qv_ratio_24h = quote volume over (t - 24 h, t] /
  (quote volume over (t - 30 d, t] / 30); missing volume counts as 0;
- beta_30d = cov / var of the coin's and BTC's hourly returns over (t - 30 d, t], pairwise complete, >= 48 pairs;
- rel_btc_L = ret_L - BTC's ret_L; rel_univ_L = ret_L - the mean ret_L of the liquid universe (coins that have it);
  vol_rel_btc = vol_7d / BTC's vol_7d; qv24_rel = 24-hour quote volume / its median over the liquid universe;
- btc_vol7_pct = mid-rank percentile of BTC's vol_7d at t among its values at t - 24 h * k, k = 0..364 (as v1);
- breadth = share of the liquid universe with trend score >= up_threshold (as _trend.breadth); dispersion =
  cross-sectional std (ddof 1) of ret_7d over the liquid universe (as v1).
The liquid universe at t is _trend.liquid_universe (top 20 of the point-in-time universe by 30-day quote volume).
Cross-sectional numbers are computed per hour from that hour's coins only, so an hour's rows do not depend on which
other hours are requested.
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from src.contracts import MarketView
from src.models.book._trend import liquid_universe

BTC = "BTCUSDT"
RET_HOURS = {"1h": 1, "2h": 2, "4h": 4, "8h": 8, "24h": 24, "3d": 72, "7d": 168, "14d": 336}
VOL_HOURS = {"24h": 24, "7d": 168, "30d": 720}
REL = ("1h", "4h", "24h", "7d")
COIN_FEATURES = ([f"ret_{k}" for k in RET_HOURS] + [f"vol_{k}" for k in VOL_HOURS]
                 + ["vol_ratio", "dist_hi24", "dist_lo24", "dist_hi7d", "qv_ratio_1h", "qv_ratio_24h", "hour", "dow",
                    "beta_30d"])
RELATIVE_FEATURES = [f"rel_btc_{k}" for k in REL] + [f"rel_univ_{k}" for k in REL] + ["vol_rel_btc", "qv24_rel"]
MARKET_FEATURES = [f"btc_ret_{k}" for k in REL] + ["btc_vol7_pct", "breadth", "dispersion"]
FEATURES = COIN_FEATURES + RELATIVE_FEATURES + MARKET_FEATURES
LOOKBACK = pd.Timedelta(days=400)       # history features_at needs: the 365-day BTC volatility percentile + 7 days
BETA_HOURS, BETA_MIN_PAIRS = 720, 48


def liquid_sets(close: pd.DataFrame, qv: pd.DataFrame, times, universe_of: Callable, trend: dict) -> dict:
    """{t: the liquid universe at t}, from _trend.liquid_universe itself (it reads quote volume in (t - 30 d, t])."""
    out = {}
    for t in times:
        out[t] = liquid_universe(MarketView(t=t, close=close, quote_volume=qv, universe=tuple(universe_of(t))), trend)
    return out


def vol_percentile(v: pd.Series) -> pd.Series:
    """On an hourly grid: mid-rank percentile of v(t) among the finite v(t - 24 h k), k = 0..364 (v(t) included)."""
    a = v.to_numpy(dtype=float)
    out = np.full(len(a), np.nan)
    for h0 in range(24):
        idx = np.arange(h0, len(a), 24)
        s = a[idx]
        if len(s) == 0:
            continue
        W = np.lib.stride_tricks.sliding_window_view(np.concatenate([np.full(364, np.nan), s]), 365)
        fin = np.isfinite(W)
        x = s[:, None]
        cnt = fin.sum(axis=1)
        res = ((W < x) & fin).sum(axis=1) + 0.5 * ((W == x) & fin).sum(axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[idx] = np.where(np.isfinite(s) & (cnt > 0), res / np.maximum(cnt, 1), np.nan)
    return pd.Series(out, index=v.index)


def trend_score_panel(px: pd.DataFrame, trend: dict) -> pd.DataFrame:
    """_trend.trend_scores on the whole grid: the share of available lookbacks with a positive return (0 if none)."""
    hits = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    avail = hits.copy()
    for L in trend["lookback_days"]:
        past = px.shift(24 * int(L))
        ok = px.notna() & past.notna()
        avail += ok
        hits += ok & (px / past - 1.0 > 0.0)
    return (hits / avail).where(avail > 0, 0.0)


def _group(values: np.ndarray, g: np.ndarray, n: int, how: str) -> np.ndarray:
    """Per-group statistic over finite values (rows of one group are in a fixed order), as an array of length n."""
    fin = np.isfinite(values)
    x = np.where(fin, values, 0.0)
    cnt = np.bincount(g, weights=fin.astype(float), minlength=n)
    s1 = np.bincount(g, weights=x, minlength=n)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = np.where(cnt > 0, s1 / cnt, np.nan)
        if how == "mean":
            return mean
        dev = np.where(fin, values - mean[g], 0.0)
        ss = np.bincount(g, weights=dev * dev, minlength=n)
        return np.where(cnt > 1, np.sqrt(ss / (cnt - 1)), np.nan)


def feature_frame(close: pd.DataFrame, qv: pd.DataFrame, times, universe_of: Callable, trend: dict) -> pd.DataFrame:
    """One row per (t, liquid coin at t), columns t, coin and FEATURES; rows sorted by t, then coin name.
    close and qv are hourly frames indexed by bar time; every requested time must be <= their last row."""
    times = pd.DatetimeIndex(times)
    liquid = liquid_sets(close, qv, times, universe_of, trend)
    coins = sorted({c for v in liquid.values() for c in v} | ({BTC} if BTC in close.columns else set()))
    if not coins or len(times) == 0:
        return pd.DataFrame(columns=["t", "coin"] + FEATURES)
    grid = pd.date_range(close.index[0], close.index[-1], freq="h")
    C = close[coins].reindex(grid)
    Q = qv[coins].reindex(grid).fillna(0.0)
    px = C.ffill(limit=int(trend["max_stale_hours"]))
    r1 = C.pct_change(fill_method=None)
    panel = {f"ret_{k}": px / px.shift(L) - 1.0 for k, L in RET_HOURS.items()}
    for k, L in VOL_HOURS.items():
        panel[f"vol_{k}"] = r1.rolling(L, min_periods=2).std(ddof=1)
    panel["vol_ratio"] = panel["vol_24h"] / panel["vol_30d"]
    panel["dist_hi24"] = px / C.rolling(24, min_periods=1).max() - 1.0
    panel["dist_lo24"] = px / C.rolling(24, min_periods=1).min() - 1.0
    panel["dist_hi7d"] = px / C.rolling(168, min_periods=1).max() - 1.0
    s24 = Q.rolling(24, min_periods=1).sum()
    s720 = Q.rolling(720, min_periods=1).sum()
    panel["qv_ratio_1h"] = Q / (s24 / 24.0).where(s24 > 0)
    panel["qv_ratio_24h"] = s24 / (s720 / 30.0).where(s720 > 0)
    panel["s24"] = s24
    if BTC in coins:
        rb = r1[BTC]
        pair = r1.notna() & rb.notna().to_numpy()[:, None]
        X, Y = r1.where(pair), pair.mul(rb.fillna(0.0), axis=0).where(pair)
        n = pair.rolling(BETA_HOURS, min_periods=1).sum()
        sx, sy = X.rolling(BETA_HOURS, min_periods=1).sum(), Y.rolling(BETA_HOURS, min_periods=1).sum()
        sxy, syy = (X * Y).rolling(BETA_HOURS, min_periods=1).sum(), (Y * Y).rolling(BETA_HOURS, min_periods=1).sum()
        var = syy - sy * sy / n
        panel["beta_30d"] = ((sxy - sx * sy / n) / var.where(var > 0)).where(n >= BETA_MIN_PAIRS)
        btc_vol7 = panel["vol_7d"][BTC]
        btc_pct = vol_percentile(btc_vol7)
    s = trend_score_panel(px, trend)

    tpos = grid.get_indexer(times)
    if (tpos < 0).any():
        raise ValueError("feature_frame: every requested time must be an hour inside the frames")
    cpos = {c: j for j, c in enumerate(coins)}
    rows_t, rows_c, g = [], [], []
    for k, t in enumerate(times):
        for c in sorted(liquid[t]):
            rows_t.append(tpos[k])
            rows_c.append(cpos[c])
            g.append(k)
    ti, ci, g = np.asarray(rows_t, dtype=int), np.asarray(rows_c, dtype=int), np.asarray(g, dtype=int)
    if len(ti) == 0:
        return pd.DataFrame(columns=["t", "coin"] + FEATURES)
    n = len(times)
    out = {"t": times[g], "coin": np.asarray(coins, dtype=object)[ci]}
    vals = {k: v.to_numpy(dtype=float)[ti, ci] for k, v in panel.items()}
    for k in COIN_FEATURES:
        if k in vals:
            out[k] = vals[k]
    out["hour"] = times.hour.to_numpy()[g].astype(float)
    out["dow"] = times.dayofweek.to_numpy()[g].astype(float)
    if BTC not in coins:
        out["beta_30d"] = np.full(len(ti), np.nan)
    bt = tpos[g]
    bj = cpos.get(BTC)
    for k in REL:
        b = panel[f"ret_{k}"].to_numpy(dtype=float)[bt, bj] if bj is not None else np.full(len(ti), np.nan)
        out[f"rel_btc_{k}"] = vals[f"ret_{k}"] - b
        out[f"rel_univ_{k}"] = vals[f"ret_{k}"] - _group(vals[f"ret_{k}"], g, n, "mean")[g]
        out[f"btc_ret_{k}"] = b
    if bj is not None:
        out["vol_rel_btc"] = vals["vol_7d"] / panel["vol_7d"].to_numpy(dtype=float)[bt, bj]
        out["btc_vol7_pct"] = btc_pct.to_numpy()[bt]
    else:
        out["vol_rel_btc"] = out["btc_vol7_pct"] = np.full(len(ti), np.nan)
    med = pd.Series(vals["s24"]).groupby(g).transform("median").to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        out["qv24_rel"] = np.where(med > 0, vals["s24"] / np.where(med > 0, med, 1.0), np.nan)
    up = (s.to_numpy(dtype=float)[ti, ci] >= float(trend["up_threshold"])).astype(float)
    out["breadth"] = _group(up, g, n, "mean")[g]
    out["dispersion"] = _group(vals["ret_7d"], g, n, "std")[g]
    df = pd.DataFrame(out)
    df[FEATURES] = df[FEATURES].astype(float).replace([np.inf, -np.inf], np.nan)
    return df[["t", "coin"] + FEATURES].reset_index(drop=True)


def features_at(view: MarketView, trend: dict) -> pd.DataFrame:
    """The live path: features of the liquid coins at view.t (index = coin), from the view's last 400 days."""
    lo = view.t - LOOKBACK
    f = feature_frame(view.close.loc[lo:], view.quote_volume.loc[lo:], [view.t], lambda t: view.universe, trend)
    return f.set_index("coin")[FEATURES]
