"""Dual momentum: baitoey_vt_mom's choices, each held only while the coin is in its own up-trend.

Relative momentum picks the coins: baitoey_vt_mom, unchanged, taken from the registry. Absolute momentum decides
whether each one is held: the shared trend signal of src/models/book/_trend.py (s_i = the share of the 5, 10, 20,
30 and 60-day returns that are positive; up-trend = s_i >= 0.6). The lever: in falling markets most coins lose
their up-trend, so the book moves to cash and loses less.

vt_mom's previous holdings are the coins this model kept: its own previous targets, passed as they are. Dropped
coins are forgotten, so vt_mom may refill their slots with its next choices. Every choice is then filtered by the
up-trend rule, and a slot without an up-trending coin stays in cash. A window start and "everything was dropped"
both give vt_mom an empty previous book, and it starts fresh in both cases. (This is a pre-registered DEVIATION from
giving vt_mom its own unfiltered previous targets, which a pure model cannot rebuild:
reports/review/20261003-prereg-batch4.md.)
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey.baitoey_vt_mom import MODEL as VT_MOM
from src.models.book._trend import trend_scores


class VtDual:
    spec = ModelSpec(name="book_vt_dual", method="momentum", author="book", rebalance_hours=24,
                     band=VT_MOM.spec.band,
                     description="baitoey_vt_mom's choices, each held only while in its own up-trend (>= 3 of its "
                                 "5/10/20/30/60-day returns positive); otherwise cash")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        w = VT_MOM.targets(replace(view, params=p["vt"]))          # previous holdings = the coins this model kept
        if w.empty:
            return w
        s = trend_scores(view.close, view.t, w.index, p["trend"])
        return w[s >= p["trend"]["up_threshold"]]


MODEL = VtDual()
