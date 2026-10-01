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
"""
from __future__ import annotations

import dataclasses

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baselines import team_btc_hold, team_ew_daily, team_rot_ew, team_rot_iv, team_trend_2
from src.models.pol import pol_mom_ss, pol_trend_ls

SLEEVES = {m.MODEL.spec.name: m.MODEL for m in (team_btc_hold, team_ew_daily, team_rot_ew, team_rot_iv, team_trend_2,
                                                 pol_mom_ss, pol_trend_ls)}


def _clean(w: pd.Series) -> pd.Series:
    w = w.astype(float)
    return w[w != 0.0]


def cut(view: MarketView, hours_back: int, params: dict, prev: pd.Series) -> MarketView:
    """The view as it stood `hours_back` hours earlier (same universe), with the sleeve's parameters."""
    t = view.t - pd.Timedelta(hours=hours_back)
    close, qv = view.close.loc[:t], view.quote_volume.loc[:t]
    return dataclasses.replace(view, t=close.index[-1], close=close, quote_volume=qv, params=params, prev_targets=prev)


class Combo:
    spec: ModelSpec                    # set by each pol_combo_* subclass

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
        book = pd.Series(dtype=float)
        for name, s in p["sleeves"].items():
            w = self.sleeve(name, view, s.get("params") or {}, int(p.get("replay_steps", 1)))
            book = book.add(float(s["weight"]) * w, fill_value=0.0)
        book = book[book.abs() > 1e-12]
        gross = float(book.abs().sum())
        return book / gross if gross > 1.0 else book
