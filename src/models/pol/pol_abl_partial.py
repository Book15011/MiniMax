"""Ablation C of Book's hierarchical-orchestrator plan: the daily strategy (baitoey_vt_mom, unchanged) but each
decision moves only `alpha` of the way from the previous book to the new target.

Research only (reports/review/20261002-orchestrator-ablation.md), not a launch candidate. vt_mom is given this model's
previous coins as its previous holdings (its keep-while-ranked rule reads only which coins are held), so a coin that
is being phased out still counts as held while it decays; coins below `min_weight` are dropped.
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey.baitoey_vt_mom import MODEL as VT_MOM


class PartialMove:
    spec = ModelSpec(name="pol_abl_partial", method="momentum", author="pol", rebalance_hours=24, band=VT_MOM.spec.band,
                     description="ablation C: baitoey_vt_mom, moving only alpha of the way to each new target")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        prev = view.prev_targets[view.prev_targets > 0]
        new = VT_MOM.targets(replace(view, params=p["vt"]))
        if prev.empty:
            return new                                       # first decision: straight to target, as live
        idx = new.index.union(prev.index)
        w = prev.reindex(idx, fill_value=0.0) + float(p["alpha"]) * (new.reindex(idx, fill_value=0.0) - prev.reindex(idx, fill_value=0.0))
        w = w[(w >= float(p["min_weight"])) & w.index.isin(list(view.universe))]
        return w


MODEL = PartialMove()
