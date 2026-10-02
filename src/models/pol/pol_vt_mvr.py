"""Volume-timed momentum (baitoey_vt_mom) with a market-volume gate: when the whole universe trades less than usual,
hold a smaller book.

Exploratory (reports/review/20261002-volume.md): across 2021-2026, days after the universe's 24-hour quote volume was
below 0.85 times its 30-day daily average returned less for the momentum basket (Sharpe 1.44 -> 1.73 when sitting
those days out), but the effect is not stable by year (2026 inverted for the market). Same holdings as
baitoey_vt_mom; only the book size changes. Parameters: baitoey_vt_mom's plus mvr_* under `models: pol_vt_mvr:`.
"""
from __future__ import annotations

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey.baitoey_vt_mom import MODEL as VT_MOM
from src.models.pol._volume import market_volume_ratio


class VolumeGatedMomentum:
    spec = ModelSpec(name="pol_vt_mvr", method="momentum", author="pol", rebalance_hours=24, band=0.05,
                     description="baitoey_vt_mom; book scaled down while the market's 24 h volume is below its 30-day normal")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        w = VT_MOM.targets(view)
        r = market_volume_ratio(view, int(p["mvr_short_hours"]), int(p["mvr_long_days"]), int(p["mvr_min_coins"]))
        return w * float(p["mvr_low_scale"]) if r is not None and r < p["mvr_threshold"] else w


MODEL = VolumeGatedMomentum()
