"""Orchestrator (three states): pol_switch3 with capitulation-volume mean reversion (pol_mr_cap) in the calm state;
volume-timed momentum up, long/short trend down. Exploratory (reports/review/20261002-volume.md).
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._combo import Combo


class Switch3Cap(Combo):
    spec = ModelSpec(name="pol_switch3_cap", method="selector", author="pol", rebalance_hours=4, band=0.03, uses_shorts=True,
                     description="Calm: MR_4h on capitulation volume; trending up: volume-timed momentum; down: long/short trend")


MODEL = Switch3Cap()
