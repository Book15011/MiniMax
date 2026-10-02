"""Orchestrator (switch): three states, each held by the best model of the method that wins there on the field-best bar: calm BTC (30-day
volatility below its 1-year median, Baitoey's rule) → MR_4h; otherwise BTC in trend (team_trend_2's rule) →
baitoey_vt_mom; otherwise → pol_trend_ls (can short). Decisions every 4 hours.

Pre-registered in reports/review/20261001-prereg-realtest.md before it was scored. State rules untuned. Shared logic
in src/models/pol/_combo.py; sleeves in config.yaml under `models: pol_switch3:`.
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.pol._combo import Combo


class Switch3(Combo):
    spec = ModelSpec(name="pol_switch3", method="selector", author="pol", rebalance_hours=4, band=0.03, uses_shorts=True,
                     description="Calm: 4-hour mean reversion; trending up: volume-timed momentum; trending down: long/short trend")


MODEL = Switch3()
