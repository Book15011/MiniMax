"""Two sleeves: a long-only trend sleeve plus a cross-sectional momentum sleeve (Baitoey, spec of 2026-10-04).

- Universe: the view's universe cut to coins with at least `min_history_hours` of hourly history, ranked by quote
  volume over the last `universe_volume_days`.
- Trend sleeve (the `trend.top_n` most liquid): for each lookback L in `trend.lookback_days`, the t-statistic
  log(P_t / P_t-L) / (hourly volatility over L x sqrt(L in hours)), clipped to +-`trend.clip`; the score is their
  mean. Coins with a positive score are held, weights proportional to score / hourly volatility over
  `trend.vol_days`, scaled so the sleeve's estimated volatility (hourly covariance, annualised) is
  `trend.target_vol_annual`.
- Momentum sleeve (the `momentum.top_n` most liquid): each coin's `momentum.lookback_days` return minus the mean of
  those coins; the top `momentum.k` long with inverse-volatility weights summing to `momentum.long_gross`, and the
  bottom k short summing to `momentum.short_gross` (variant B only, research only, never live).
- The sleeves are added, each coin capped at +-`cap`, and the book scaled down to at most `max_gross`.
Decides daily at 16:00 UTC with a 2% band (ModelSpec band; `band` in config.yaml records it). The research variants
A-D are under `variants` in config.yaml (pre-registration research/baitoey/prereg/20261004-two-sleeve.md).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.contracts import MarketView, ModelSpec

HOURS_PER_YEAR = 24 * 365
EMPTY = pd.Series(dtype=float)


def liquid(view: MarketView, p: dict, n: int) -> list[str]:
    """The n most liquid coins (quote volume over universe_volume_days) with min_history_hours of history."""
    hist, vh = int(p["min_history_hours"]), int(p["universe_volume_days"]) * 24
    close, qv = view.tail(max(hist, vh))
    ok = [c for c in close.columns if close[c].iloc[-hist:].notna().sum() >= hist]
    vol = qv[ok].iloc[-vh:].sum()
    return list(vol.sort_values(ascending=False, kind="stable").index[:n])


def hourly_vol(close: pd.DataFrame, hours: int) -> pd.Series:
    return np.log(close).diff().iloc[-hours:].std()


def annual_vol(w: pd.Series, close: pd.DataFrame, vol_days: int) -> float:
    """Estimated annualised volatility of weights w from the hourly covariance over the last vol_days."""
    r = np.log(close[list(w.index)]).diff().iloc[-vol_days * 24:]
    cov = r.cov().to_numpy() * HOURS_PER_YEAR
    x = w.to_numpy()
    return float(np.sqrt(max(x @ cov @ x, 0.0)))


def trend_scores(view: MarketView, p: dict, coins: list[str]) -> pd.Series:
    t = p["trend"]
    lbs, clip = [int(d) for d in t["lookback_days"]], float(t["clip"])
    close, _ = view.tail(max(lbs) * 24 + 1)
    logc = np.log(close[coins])
    terms = []
    for d in lbs:
        h = d * 24
        ret = logc.iloc[-1] - logc.iloc[-1 - h]
        sd = logc.diff().iloc[-h:].std()
        terms.append((ret / (sd * np.sqrt(h))).clip(-clip, clip))
    return (sum(terms) / len(terms)).replace([np.inf, -np.inf], np.nan).dropna()


def trend_sleeve(view: MarketView, p: dict) -> pd.Series:
    t = p["trend"]
    coins = liquid(view, p, int(t["top_n"]))
    if not coins:
        return EMPTY
    s = trend_scores(view, p, coins)
    s = s[s > 0]
    if s.empty:
        return EMPTY
    vd = int(t["vol_days"])
    close, _ = view.tail(vd * 24 + 1)
    raw = (s / hourly_vol(close[list(s.index)], vd * 24)).replace([np.inf, -np.inf], np.nan).dropna()
    raw = raw[raw > 0]
    if raw.empty:
        return EMPTY
    w = raw / raw.sum()
    v = annual_vol(w, close, vd)
    return w * float(t["target_vol_annual"]) / v if v > 0 else EMPTY


def momentum_sleeve(view: MarketView, p: dict) -> pd.Series:
    m = p["momentum"]
    long_g, short_g, k = float(m["long_gross"]), float(m["short_gross"]), int(m["k"])
    if long_g <= 0 and short_g <= 0:
        return EMPTY
    coins = liquid(view, p, int(m["top_n"]))
    if len(coins) < 2 * k if short_g > 0 else len(coins) < k:
        return EMPTY
    lh, vh = int(m["lookback_days"]) * 24, int(m["vol_days"]) * 24
    close, _ = view.tail(max(lh, vh) + 1)
    r = (close[coins].iloc[-1] / close[coins].iloc[-1 - lh] - 1).dropna()
    order = (r - r.mean()).sort_values(ascending=False, kind="stable")
    vol = hourly_vol(close[coins], vh)

    def inverse_vol(names, gross: float) -> pd.Series:
        x = 1.0 / vol[list(names)]
        return x / x.sum() * gross

    parts = []
    if long_g > 0:
        parts.append(inverse_vol(order.index[:k], long_g))
    if short_g > 0:
        parts.append(-inverse_vol(order.index[-k:], short_g))
    return pd.concat(parts).groupby(level=0).sum()


def combine(trend: pd.Series, momentum: pd.Series, p: dict) -> pd.Series:
    w = trend.add(momentum, fill_value=0.0) if not momentum.empty else trend.copy()
    if w.empty:
        return EMPTY
    w = w.clip(-float(p["cap"]), float(p["cap"]))
    gross = float(w.abs().sum())
    if gross > float(p["max_gross"]):
        w = w * float(p["max_gross"]) / gross
    return w[w.abs() > 1e-12]


class TwoSleeve:
    spec = ModelSpec(name="baitoey_two_sleeve", method="momentum", author="baitoey", rebalance_hours=24, band=0.02,
                     description="long-only trend sleeve (t-stat score, 25% vol target) + top-5 momentum sleeve")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        return combine(trend_sleeve(view, p), momentum_sleeve(view, p), p)


MODEL = TwoSleeve()
