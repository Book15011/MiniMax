"""book_orch: a daily base strategy, with an ML weight adjustment, a BTC shock rule and a breadth-gated short sleeve.

Pre-registered in reports/review/20261003-prereg-orch.md. Every number lives in config.yaml under `book_orch:`;
each layer has an `enabled` switch, and with every layer off the model is its base.

- Base (default baitoey_vt_mom, unchanged): called only at its own decision hour (16:00 UTC), or when the book is
  empty (a window's first hour, as the live bot's first decision). It is given this model's current holdings as its
  previous holdings; vt_mom reads only which coins are held long, so no layer may change that set.
- Between decisions the model holds: it returns its holdings drifted by the last hour's returns, with the engine's
  own drift formula w (1 + r) / (1 + sum w r), so the engine does not trade them back to stale targets.
- T, ML adjustment (16:00 only): pooled walk-forward forecasts of each held coin's 1-day and 3-day return
  (src/models/book/_orch_ml.py) scale its weight between 0.5 and 1.5 times the base's; a coin moves only if
  |mu3| >= 2 round-trip costs, and the gross never exceeds the base's.
- X, short sleeve (16:00 only, while breadth < 0.3): up to 5 liquid coins the base does not hold, with mu3 below
  -2 short round-trip costs (or, without ML, coins in no up-trend at all), weights proportional to -1/sigma, the sleeve
  at most min(25%, 1 - long gross). It never reduces the base's longs.
- S, shock (hourly): Pol's trigger, imported (pol_abl_shock.ShockOverride.shocked: BTC 4-hour return of -5% or worse
  at any hour of the last 24 h). While it is active the longs are held at 50%; shorts unchanged. `response: cash`
  is Pol's own response (report-only).
- P, partial moves (report-only): at 16:00, coins the base keeps or adds move half-way; dropped coins exit fully.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey.baitoey_vt_mom import MODEL as VT_MOM
from src.models.book import _orch_features as F
from src.models.book._trend import hourly_vol, liquid_universe, trend_scores
from src.models.book._trend import breadth as trend_breadth
from src.models.pol.pol_abl_shock import ShockOverride

HOUR = pd.Timedelta(hours=1)
CARRY_ROWS = 48                                   # as the engine and the live store: carry a price at most 48 hours
_BASES = {VT_MOM.spec.name: VT_MOM}


def _clean(w: pd.Series) -> pd.Series:
    w = w.astype(float)
    return w[w != 0.0]


def base_model(name: str):
    if name not in _BASES:
        from src.models import get                # deferred: src.models imports every model module
        _BASES[name] = get(name)
    return _BASES[name]


def drift(prev: pd.Series, view: MarketView) -> pd.Series:
    """The holdings after the last hour's price move: w (1 + r) / (1 + sum w r), r = the last close over the previous
    one (last known price carried, 0 if none), exactly the engine's update (backtest/engine.py)."""
    if prev.empty:
        return prev
    c = view.close.reindex(columns=list(prev.index)).iloc[-(CARRY_ROWS + 2):].ffill()
    if len(c) < 2:
        return prev
    r = (c.iloc[-1] / c.iloc[-2] - 1.0).fillna(0.0)
    pr = float((prev * r).sum())
    return prev * (1.0 + r) / (1.0 + pr)


def cap_gross(w: pd.Series, longs_only: bool = False) -> pd.Series:
    g = float(w.abs().sum())
    if g <= 1.0:
        return w
    if not longs_only:
        return w / g
    shorts = float(-w[w < 0].sum())
    room = max(0.0, 1.0 - shorts)
    out = w.copy()
    out[w > 0] = w[w > 0] * room / float(w[w > 0].sum())
    return out


def shock_view_at(view: MarketView, t: pd.Timestamp) -> MarketView:
    """BTC's closes as the view at time t (one hour earlier) had them: rows up to t, padded to t with the last price
    carried if t has no bar, as the harness's view_frames does. Enough for ShockOverride.shocked."""
    btc = view.close[["BTCUSDT"]].loc[:t] if "BTCUSDT" in view.close.columns else view.close.iloc[:0, :0]
    if len(btc) and btc.index[-1] < t:
        extra = pd.date_range(btc.index[-1] + HOUR, t, freq="h")
        last = btc.iloc[-CARRY_ROWS:].ffill().iloc[-1]
        btc = pd.concat([btc, pd.DataFrame([last.to_numpy()] * len(extra), index=extra, columns=btc.columns)])
    return replace(view, t=t, close=btc)


def shocked(view: MarketView, s: dict) -> bool:
    return ShockOverride.shocked(view, {"shock_4h": s["shock_4h"], "cooldown_hours": s["cooldown_hours"]})


def partial(prev: pd.Series, b: pd.Series, alpha: float) -> pd.Series:
    """Coins the base keeps or adds move alpha of the way from the held weight; dropped coins exit fully."""
    held = prev.reindex(b.index).fillna(0.0)
    return held + alpha * (b - held)


def short_sleeve(view: MarketView, longs: pd.Series, exclude, p: dict, bundle, market: dict | None) -> pd.Series:
    """Layer X at a 16:00 decision. Empty unless breadth < breadth_max."""
    s, trend = p["short"], p["trend"]
    if (market["breadth"] if market else trend_breadth(view, trend)) >= float(s["breadth_max"]):
        return pd.Series(dtype=float)
    cand = [c for c in liquid_universe(view, trend) if c not in set(exclude)]
    if not cand:
        return pd.Series(dtype=float)
    if s["candidates"] == "ml":
        X = F.coin_features(view, cand, pd.Series(dtype=float), trend, market).dropna()
        pred = bundle.predict(view.t, X)
        if pred is None:
            return pd.Series(dtype=float)
        cost = pd.Series({c: float(s["fee_open"]) + float(s["fee_close"]) + 2.0 * bundle.spread(c) for c in pred.index})
        ok = pred.mu3 <= -float(s["filter_mult"]) * cost
        ranked = pred.mu3[ok].sort_values(kind="mergesort")
        picks = list(ranked.index[: int(s["max_coins"])])
    elif s["candidates"] == "trend":
        sc = trend_scores(view.close, view.t, cand, trend)
        zero = [c for c in cand if sc.get(c, 1.0) == 0.0]
        stale = pd.Timedelta(hours=float(trend["max_stale_hours"]))
        r30 = F._returns(view.close, view.t, zero, (30,), stale)["ret_30d"].dropna() if zero else pd.Series(dtype=float)
        picks = list(sorted(r30.index, key=lambda c: (r30[c], c))[: int(s["max_coins"])])
    else:
        raise ValueError(f"book_orch: short.candidates must be 'ml' or 'trend', not {s['candidates']!r}")
    if not picks:
        return pd.Series(dtype=float)
    sigma = hourly_vol(view.close, view.t, picks, float(s["vol_days"]))
    inv = (1.0 / sigma).replace([np.inf, -np.inf], np.nan).dropna()
    inv = inv[inv > 0]
    total = min(float(s["max_gross"]), 1.0 - float(longs[longs > 0].sum()))
    if inv.empty or total <= 0:
        return pd.Series(dtype=float)
    return -total * inv / float(inv.sum())


class BookOrch:
    spec = ModelSpec(name="book_orch", method="momentum", author="book", rebalance_hours=1, band=VT_MOM.spec.band,
                     uses_shorts=True,
                     description="baitoey_vt_mom daily, its weights tilted by a cost-filtered ML forecast, longs held "
                                 "at 50% after a BTC crash, a small short sleeve when few coins trend up")

    def decide(self, view: MarketView, prev: pd.Series, p: dict) -> pd.Series:
        base = base_model(p["base"])
        b = _clean(base.targets(replace(view, params=p["base_params"], prev_targets=prev)))
        if p["partial"]["enabled"] and not prev.empty:
            b = _clean(partial(prev[prev > 0], b, float(p["partial"]["alpha"])))
        longs, others = b[b > 0], b[b < 0]
        at_grid = view.t.hour == int(p["decision_hour_utc"])
        ml, x = p["ml"], p["short"]
        bundle = market = None
        if at_grid and (ml["enabled"] or (x["enabled"] and x["candidates"] == "ml")):
            from src.models.book import _orch_ml
            bundle = _orch_ml.load(ml["manifest"], ml["manifest_sha256"])
            market = F.market_features(view, p["trend"])
        if ml["enabled"] and at_grid and not longs.empty:
            X = F.coin_features(view, longs.index, longs, p["trend"], market).dropna()
            pred = bundle.predict(view.t, X)
            if pred is not None:
                from src.models.book import _orch_ml
                longs, _ = _orch_ml.adjust(longs, pred, bundle.spread, ml)
        sleeve = pd.Series(dtype=float)
        if x["enabled"] and at_grid:
            sleeve = short_sleeve(view, longs, b.index, p, bundle, market)
        return pd.concat([longs, others, sleeve])

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        prev = _clean(view.prev_targets)
        s = p["shock"]
        now = bool(s["enabled"]) and shocked(view, s)
        if now and s["response"] == "cash":
            return pd.Series(dtype=float)
        if view.t.hour == int(p["decision_hour_utc"]) or prev.empty:
            w = self.decide(view, prev, p)
            if now:
                w[w > 0] = w[w > 0] * float(s["scale"])
            return _clean(w)
        w = drift(prev, view)
        w = w[w.index.isin(list(view.universe))]
        if s["enabled"] and s["response"] == "half":
            before = shocked(shock_view_at(view, view.t - HOUR), s)
            if now and not before:
                w[w > 0] = w[w > 0] * float(s["scale"])
            elif before and not now:
                w[w > 0] = w[w > 0] / float(s["scale"])
                w = cap_gross(w, longs_only=True)
        return _clean(cap_gross(w))


MODEL = BookOrch()
