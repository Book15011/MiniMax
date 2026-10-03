"""Breadth-scaled exposure: baitoey_vt_mom's book times e_t = clip(breadth_t / 0.6, 0.25, 1), rounded to 0.25.

breadth_t is the share of the 20 most traded coins that are in an up-trend (the shared signal of
src/models/book/_trend.py: at least 3 of a coin's 5, 10, 20, 30 and 60-day returns positive). The book is fully
exposed when at least 60% of liquid coins trend up and never below 25%, in steps of 25% (rounded half up). It is
a gradual, daily replacement for the 40-day BTC switch of the pol_switch_* models.

vt_mom (baitoey_vt_mom, unchanged, from the registry) gets its own previous holdings. It reads only which coins it
held (team_rot_ew.rotation_targets keeps a holding with w > 0 while it ranks in the top keep_rank), and scaling by
e_t >= 0.25 never changes that set. So this model's previous targets, which hold exactly vt_mom's previous coins,
are passed as they are; a test checks that vt_mom's decision does not change when its previous weights are scaled.
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey.baitoey_vt_mom import MODEL as VT_MOM
from src.models.book._trend import breadth, exposure


class VtBreadth:
    spec = ModelSpec(name="book_vt_breadth", method="momentum", author="book", rebalance_hours=24,
                     band=VT_MOM.spec.band,
                     description="baitoey_vt_mom scaled by the share of liquid coins in up-trends: full at >= 60%, "
                                 "never below 25%, in 25% steps")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        w = VT_MOM.targets(replace(view, params=p["vt"]))
        if w.empty:
            return w
        return w * exposure(breadth(view, p["trend"]), p)


MODEL = VtBreadth()
