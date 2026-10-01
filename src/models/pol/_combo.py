"""Combinations: existing models (sleeves) mixed into one book. Shared code of the pol_combo_* models.

- Each sleeve is a registered model, run on the same view with its own parameters. Those parameters sit inside
  the combination's config block (`sleeves: {<model>: {weight: w, params: *anchor}}`); the YAML anchor points at
  the sleeve's own block, so there is one copy of every number.
- A sleeve's previous decision (its keep-while-ranked rules need it) is rebuilt by replaying the sleeve from an
  empty book `replay_steps` decisions back, on the view cut at each of those times. The combination stays
  view-only and deterministic, and each sleeve behaves close to how it does alone.
- Book = sum over sleeves of weight x sleeve targets, netted per coin, then scaled down if gross > 1.
- Sleeves keep their own vol targets and filters; mixing methods that win in different markets (cross-sectional
  momentum, time-series trend, a BTC core) is what smooths the book.
- A sleeve may set `override:` (e.g. a 4-hour bar for mean reversion); the anchored `params:` stay one copy.
- `prev: own` (switches): the active sleeve gets the combination's own previous targets. With one sleeve at a time the
  book is that sleeve's position, so this is exact; sleeves keep or drop those holdings by their own rules.
- Three states (optional `calm:` block, Baitoey's rule): a calm market is `when: calm` before any trend reading.
- Switch (optional `switch:` block): a sleeve with `when: up` or `when: down` runs only in that BTC trend state,
  the state team_trend_2 uses (40-day EMA of hourly closes, +-3% hysteresis, replayed every 6 h over
  `state_days`; out of trend when undecided). Holding one method fully instead of a blend: the competition's
  return gate pays nothing below the bar, and a blend dilutes each method's winning windows.
"""
from __future__ import annotations

import dataclasses

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey import baitoey_mr_bbrsi, baitoey_rot_max, baitoey_vt_mom
from src.models.baitoey.baitoey_switch_mr import btc_calm
from src.models.baselines import team_btc_hold, team_ew_daily, team_rot_ew, team_rot_iv, team_trend_2
from src.models.pol import pol_mom_ss, pol_trend_ls

SLEEVES = {m.MODEL.spec.name: m.MODEL for m in (team_btc_hold, team_ew_daily, team_rot_ew, team_rot_iv, team_trend_2,
                                                 pol_mom_ss, pol_trend_ls, baitoey_rot_max, baitoey_mr_bbrsi,
                                                 baitoey_vt_mom)}


def _clean(w: pd.Series) -> pd.Series:
    w = w.astype(float)
    return w[w != 0.0]


def btc_state(view: MarketView, p: dict, coin: str = "BTCUSDT") -> str:
    """'up' or 'down': team_trend_2's trend state of `coin` at view.t (p = team_trend_2's parameters)."""
    span = int(p["ema_days"]) * 24
    close, _ = view.tail((int(p["state_days"]) + 3 * int(p["ema_days"])) * 24 + 1)
    if coin not in close:
        return "down"
    px = close[coin].dropna()
    if len(px) < span:
        return "down"
    ema = px.ewm(span=span, adjust=False).mean()
    step = (px.index.hour - px.index[-1].hour) % team_trend_2.MODEL.spec.rebalance_hours == 0
    pts = (px.index > px.index[-1] - pd.Timedelta(days=int(p["state_days"]))) & step
    return "up" if team_trend_2.in_trend(px[pts], ema[pts], p["hysteresis"]) else "down"


def cut(view: MarketView, hours_back: int, params: dict, prev: pd.Series) -> MarketView:
    """The view as it stood `hours_back` hours earlier (same universe), with the sleeve's parameters."""
    t = view.t - pd.Timedelta(hours=hours_back)
    close, qv = view.close.loc[:t], view.quote_volume.loc[:t]
    return dataclasses.replace(view, t=close.index[-1], close=close, quote_volume=qv, params=params, prev_targets=prev)


class Combo:
    spec: ModelSpec                    # set by each pol_combo_* subclass

    @staticmethod
    def state(view: MarketView, p: dict) -> str | None:
        """None without a switch. With `calm:` (Baitoey's rule: BTC's 30-day volatility below its 1-year median at the
        decision hour) a calm market is 'calm' whatever the trend; otherwise 'up' or 'down' by btc_state."""
        if not p.get("switch"):
            return None
        c = p.get("calm")
        if c and "BTCUSDT" in view.close.columns and btc_calm(view.close["BTCUSDT"], int(c["vol_days"]),
                                                              int(c["regime_days"]), float(c["calm_quantile"])):
            return "calm"
        return btc_state(view, p["switch"])

    def sleeve(self, name: str, view: MarketView, params: dict, steps: int) -> pd.Series:
        model = SLEEVES[name]
        step = self.spec.rebalance_hours
        prev = pd.Series(dtype=float)
        for k in range(steps, 0, -1):
            prev = _clean(model.targets(cut(view, k * step, params, prev)))
        return _clean(model.targets(dataclasses.replace(view, params=params, prev_targets=prev)))

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        unknown = set(p["sleeves"]) - set(SLEEVES)
        if unknown:
            raise ValueError(f"{self.spec.name}: unknown sleeves {sorted(unknown)}; known: {sorted(SLEEVES)}")
        state = self.state(view, p)
        book = pd.Series(dtype=float)
        for name, s in p["sleeves"].items():
            if state is not None and s.get("when", state) != state:
                continue
            params = {**(s.get("params") or {}), **(s.get("override") or {})}
            if p.get("prev") == "own":
                w = _clean(SLEEVES[name].targets(dataclasses.replace(view, params=params)))
            else:
                w = self.sleeve(name, view, params, int(p.get("replay_steps", 1)))
            book = book.add(float(s.get("weight", 1.0)) * w, fill_value=0.0)
        book = book[book.abs() > 1e-12]
        gross = float(book.abs().sum())
        return book / gross if gross > 1.0 else book
