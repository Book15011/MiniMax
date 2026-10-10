"""e20v45 unchanged, plus the cash-short study's conditional short leg, funded by trimming e20v45's longs.

EXPERIMENTAL (feature/e20-shortguard), research only. Research hypothesis, not a validated forecast.

At each daily decision (16:00 UTC, e20v45's own grid):
- e20v45 decides exactly as the live model does. It reads only which coins it held long before (team_rot_ew's
  keep rule), so it gets the positive part of the previous book and its decision is unchanged by the short leg.
- If e20v45 is in its own long/short mode (any negative target), its book is returned unchanged.
- Otherwise the short leg of src/models/book/_cashshort.py runs with the full `short_gross_cap` as budget:
  active only when BTC is below its 20-day EMA, BTC's 7-day return is negative and at most 40% of the 30 most liquid
  coins rose over 48 h; it shorts up to `short_k` coins with negative momentum (pullback: whose 4-hour bounce just
  failed), never a coin e20v45 holds long, inverse-vol sized with per-coin and volatility caps.
- With shorts of gross g, e20v45's longs are scaled by (1 - g): gross stays <= 1. With no shorts, the book is
  exactly e20v45's.
- Optional `volume_fill_hours` (the "_r" variants, added after the live check of 2026-10-10): the short leg's view
  carries each coin's hourly quote volume forward over gaps of at most that many hours. The cash-short breadth rule
  drops any coin with a single missing volume hour; an 8-hour gap in the live store (Oct 4 01-08 UTC, 75 of 90
  coins) left 14 of 29 coins and disabled the rule for the whole round. On complete data the variants are
  identical. e20v45 always gets the unfilled view.
No I/O or mutable state.
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.contracts import MarketView
from src.models.book import _cashshort
from src.models.pol.pol_switch_vt_tl_e20v45 import MODEL as E20


def targets(view: MarketView, *, pullback: bool) -> pd.Series:
    view = _cashshort._causal(view)
    p = view.params
    prev = view.prev_targets[view.prev_targets > 0]
    base = E20.targets(replace(view, params=p["e20"], prev_targets=prev)).astype(float)
    base = base[base.abs() > 1e-12]
    if (base < 0).any():
        return base
    held = pd.Series(0.0, index=base.index)        # full budget; held coins are never shorted
    if p.get("volume_fill_hours"):
        view = replace(view, quote_volume=view.quote_volume.ffill(limit=int(p["volume_fill_hours"])))
    shorts = _cashshort.short_weights(view, held, p, pullback)
    if shorts.empty:
        return base
    return pd.concat([base * (1.0 + float(shorts.sum())), shorts])
