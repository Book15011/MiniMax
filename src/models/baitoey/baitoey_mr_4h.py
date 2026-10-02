"""MR_4h: Baitoey's Bollinger + RSI mean reversion (baitoey_mr_bbrsi) on 4-hour bars, deciding every 4 hours.

The run her mean-reversion study chose (research/baitoey/prereg/20261001-mean-reversion.md) and the top model
under the field-best bar (reports/review/20261001-final-selection.md). Registered so the live bot can run it.
Same code; parameters under `models: baitoey_mr_4h:` (her block with bar_hours: 4).
"""
from __future__ import annotations

from src.contracts import ModelSpec
from src.models.baitoey.baitoey_mr_bbrsi import BollingerRsiReversion


class MeanReversion4h(BollingerRsiReversion):
    spec = ModelSpec(name="baitoey_mr_4h", method="trend", author="baitoey", rebalance_hours=4, band=0.05,
                     description="baitoey_mr_bbrsi on 4-hour bars, decisions every 4 h (MR_4h of her study)")


MODEL = MeanReversion4h()
