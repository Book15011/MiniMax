"""Cash-only conditional shorts on the pinned dual-momentum long book.

Research hypotheses, not validated market forecasts. Every call (including the
scorer's 12 UTC cash bootstrap) recomputes the exact positive-only long backbone.
Regular calls follow ModelSpec's daily 16 UTC grid. No I/O or mutable state.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from src.contracts import MarketView
# Explicit global module dependencies close the dynamic baseline wrapper's source
# identity gap without changing the shared framework or the baseline.
from src.models.baitoey import _overlays as overlay_source
from src.models.baitoey import _volume_signals as signal_source
from src.models.baitoey import baitoey_ovl_brk_dual as base_source
from src.models.baitoey import baitoey_vt_dual as dual_source
from src.models.baitoey import baitoey_vt_mom as timing_source
from src.models.baselines import team_rot_ew as rotation_source
from src.models.baitoey.baitoey_ovl_brk_dual import MODEL as BASE


def _causal(view: MarketView) -> MarketView:
    """Honor view.t even if a caller accidentally supplies future rows."""
    return replace(view, close=view.close.loc[:view.t], quote_volume=view.quote_volume.loc[:view.t])


def _grid(view: MarketView, hours: int) -> pd.DatetimeIndex:
    return pd.date_range(end=view.t, periods=hours, freq="h")


def _valid_prices(frame: pd.DataFrame | pd.Series) -> bool:
    x = frame.to_numpy(dtype=float)
    return bool(np.isfinite(x).all() and (x > 0).all())


def liquid_breadth(view: MarketView, p: dict) -> tuple[list[str], float | None]:
    """Select by complete past volume FIRST; never drop selected bad prices.

    This model input is separate from the frozen score2 broad-universe query,
    which still fails at 29/30 endpoints because BCH has no competition data.
    """
    h = int(p["liquidity_hours"])
    coins = sorted(set(view.universe).intersection(view.quote_volume.columns))
    if not coins:
        return [], None
    q = view.quote_volume.reindex(index=_grid(view, h), columns=coins)
    eligible = np.isfinite(q).all() & (q >= 0).all() & (q.sum() > 0)
    volume = q.sum()[eligible].sort_index().sort_values(ascending=False, kind="mergesort")
    chosen = volume.head(int(p["breadth_top_n"])).index.tolist()
    if len(chosen) < int(p["breadth_min_coins"]):
        return chosen, None
    endpoints = pd.DatetimeIndex([view.t - pd.Timedelta(hours=int(p["breadth_hours"])), view.t])
    px = view.close.reindex(index=endpoints, columns=chosen)
    if not _valid_prices(px):
        return chosen, None
    positive = px.iloc[-1] / px.iloc[0] - 1 > 0
    return chosen, float(positive.mean())


def regime_ok(view: MarketView, p: dict) -> tuple[bool, list[str]]:
    """Slow BTC weakness AND weak point-in-time liquid breadth."""
    chosen, breadth = liquid_breadth(view, p)
    if breadth is None or breadth > float(p["breadth_max_positive"]):
        return False, chosen
    btc = p["btc_symbol"]
    if btc not in view.close:
        return False, chosen
    span = int(p["btc_ema_days"]) * 24
    warm = span * int(p["btc_ema_warmup_spans"]) + 1
    btc_px = view.close[btc].reindex(_grid(view, warm))
    if not _valid_prices(btc_px):
        return False, chosen
    then = view.t - pd.Timedelta(hours=int(p["btc_return_hours"]))
    if then not in btc_px.index:
        return False, chosen
    ema = btc_px.ewm(span=span, adjust=False).mean().iloc[-1]
    falling = float(btc_px.iloc[-1] / btc_px.loc[then] - 1) < 0
    return bool(btc_px.iloc[-1] < ema and falling), chosen


def short_weights(view: MarketView, longs: pd.Series, p: dict, pullback: bool) -> pd.Series:
    """Negative absolute momentum, inverse-vol sizing, downward-only caps."""
    empty = pd.Series(dtype=float)
    budget = min(float(p["short_gross_cap"]), max(0.0, 1.0 - float(longs.sum())))
    if budget <= 0:
        return empty
    active, liquid = regime_ok(view, p)
    if not active:
        return empty
    coins = sorted(set(liquid) - set(longs.index))
    if not coins:
        return empty
    vol_h = int(p["short_vol_days"]) * 24
    lookbacks = [int(d) for d in p["short_lookback_days"]]
    need = max(vol_h, max(lookbacks) * 24) + 1
    close = view.close.reindex(index=_grid(view, need), columns=coins)
    ok = np.isfinite(close).all() & (close > 0).all()
    close = close.loc[:, ok]
    if close.empty:
        return empty
    score = signal_source.momentum_score(close, lookbacks)
    score = score[score < float(p["short_min_score"])]
    if pullback and len(score):
        now = view.t
        recent = now - pd.Timedelta(hours=int(p["pullback_recent_hours"]))
        prior = now - pd.Timedelta(hours=int(p["pullback_prior_hours"]))
        px = close.reindex(index=[prior, recent, now], columns=score.index)
        rebound = px.iloc[1] / px.iloc[0] - 1 > 0
        failure = px.iloc[2] / px.iloc[1] - 1 < 0
        score = score[rebound & failure]
    if score.empty:
        return empty
    picked = score.sort_index().sort_values(kind="mergesort").head(int(p["short_k"])).index
    sigma = close[picked].pct_change(fill_method=None).iloc[-vol_h:].std() * np.sqrt(24.0)
    sigma = sigma[np.isfinite(sigma) & (sigma > 0)]
    if sigma.empty:
        return empty
    inv = 1.0 / sigma
    w = (inv / inv.sum() * budget).clip(upper=float(p["short_coin_cap"]))
    # Triangle-inequality bound on standalone short daily volatility. It ignores
    # correlations and possible long hedging benefits, so never spends the long
    # book's risk allowance. It is not a total-book risk guarantee.
    bound = float((w * sigma).sum())
    if bound > float(p["short_daily_vol"]):
        w *= float(p["short_daily_vol"]) / bound
    return -w[w > 0]


def targets(view: MarketView, *, pullback: bool) -> pd.Series:
    view = _causal(view)
    p = view.params
    positive_prev = view.prev_targets[view.prev_targets > 0]
    base_view = replace(view, params=p["long_base"], prev_targets=positive_prev)
    longs = BASE.targets(base_view).astype(float)
    longs = longs[longs > 0]
    shorts = short_weights(view, longs, p, pullback)
    return pd.concat([longs, shorts])
