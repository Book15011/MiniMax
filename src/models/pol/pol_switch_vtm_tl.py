"""Orchestrator (switch): pol_switch_vt_tl with the market-volume-gated momentum sleeve (pol_vt_mvr) in the up state;
pol_trend_ls out of trend. Exploratory (reports/review/20261002-volume.md). Sleeves under `models: pol_switch_vtm_tl:`.
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._combo import Combo


class SwitchVtmTl(Combo):
    spec = ModelSpec(name="pol_switch_vtm_tl", method="selector", author="pol", rebalance_hours=24, band=0.03, uses_shorts=True,
                     description="BTC in trend: volume-timed momentum gated by market volume; out of trend: long/short trend")


MODEL = SwitchVtmTl()
