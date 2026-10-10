"""e20v45 with one of Baitoey's de-risking overlays, plus the cash-short study's conditional short leg.

EXPERIMENTAL (feature/e20-shortguard), research only. Research hypotheses, not validated forecasts.

At each daily decision (16:00 UTC):
1. The base: e20v45 through one overlay from src/models/baitoey/_overlays.py, imported unchanged
   - alt: when the equal-weight alt basket's 10-day return is below BTC's, e20v45's alt longs go to cash
     (baitoey_ovl_altbtc_b_e20);
   - brk: a long whose daily close broke its 20-day low is held in cash until it closes above its 20-day mean
     (baitoey_ovl_brk_e20).
   It gets the positive part of the previous book, as in _e20guard.py.
2. If the base holds any short (e20v45's own long/short mode), it is returned unchanged.
3. The short leg of src/models/book/_cashshort.py (weak-BTC regime: BTC below its 20-day EMA, 7-day return
   negative, at most 40% of the 30 most liquid coins up over 48 h; negative-momentum coins, pullback filter optional,
   inverse-vol, per-coin and volatility caps; never a coin the base holds long), on a view whose hourly volume is
   carried forward over gaps of at most `volume_fill_hours` (see _e20guard.py).
   - cash: budget = min(cap, the base's unused cash); the base is never trimmed.
   - trim: budget = cap; the base's longs are scaled by (1 - short gross).
No I/O or mutable state.
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.contracts import MarketView
from src.models.baitoey.baitoey_ovl_altbtc_b_e20 import MODEL as ALT_CASH
from src.models.baitoey.baitoey_ovl_brk_e20 import MODEL as BREAKDOWN
from src.models.book import _cashshort

BASES = {"alt": ALT_CASH, "brk": BREAKDOWN}


def targets(view: MarketView, *, base: str, pullback: bool, funding: str) -> pd.Series:
    view = _cashshort._causal(view)
    p = view.params
    prev = view.prev_targets[view.prev_targets > 0]
    w = BASES[base].targets(replace(view, params=p["base"], prev_targets=prev)).astype(float)
    w = w[w.abs() > 1e-12]
    if (w < 0).any():
        return w
    held = w[w > 0] if funding == "cash" else pd.Series(0.0, index=w.index)
    sv = view
    if p.get("volume_fill_hours"):
        sv = replace(view, quote_volume=view.quote_volume.ffill(limit=int(p["volume_fill_hours"])))
    shorts = _cashshort.short_weights(sv, held, p, pullback)
    if shorts.empty:
        return w
    if funding == "cash":
        return pd.concat([w, shorts])
    return pd.concat([w * (1.0 + float(shorts.sum())), shorts])
