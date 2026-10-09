"""Research only (research/baitoey/prereg/20261009-btc-short.md): BTC short or cash, variant B (breakdown short)."""
from __future__ import annotations

from src.models.baitoey._btc_short import BtcShort, make

MODEL = make(BtcShort, "baitoey_btc_short_b", "research only: BTC short or cash, never long; variant B (breakdown short)")
