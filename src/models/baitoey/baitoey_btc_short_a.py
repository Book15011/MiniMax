"""Research only (research/baitoey/prereg/20261009-btc-short.md): BTC short or cash, variant A (trend short)."""
from __future__ import annotations

from src.models.baitoey._btc_short import BtcShort, make

MODEL = make(BtcShort, "baitoey_btc_short_a", "research only: BTC short or cash, never long; variant A (trend short)")
