"""Concentration: baitoey_vt_mom holding 4 coins instead of 6, everything else unchanged.

vt_mom's own parameter `k` sets how many coins it holds. This model is vt_mom itself (its targets(), taken from the
registry) under its own config block, which is vt_mom's block (YAML merge of the anchor) with k: 4. The lever: more
of the book in the strongest coins, so more upside in rallies (and larger losses when they turn).
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.contracts import MarketView
from src.models.baitoey.baitoey_vt_mom import MODEL as VT_MOM


class VtTop4:
    spec = replace(VT_MOM.spec, name="book_vt_top4", author="book",
                   description="baitoey_vt_mom holding its top 4 coins instead of 6 (its own k parameter)")

    def targets(self, view: MarketView) -> pd.Series:
        return VT_MOM.targets(view)


MODEL = VtTop4()
