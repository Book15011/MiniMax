"""Research only (research/baitoey/prereg/20261009-btc-short-fast.md): BTC short or cash, variant A2 (fast trend short)."""
from __future__ import annotations

from src.models.baitoey._btc_short import BtcShort, make

MODEL = make(BtcShort, "baitoey_btc_short_a2", "research only: BTC short or cash, never long; variant A2 (fast trend short)")
