"""Research only (research/baitoey/prereg/20261009-overlays.md): baitoey_vt_dual with alt basket 10-day return below BTC -> alt longs to cash."""
from __future__ import annotations

from src.models.baitoey.baitoey_vt_dual import MODEL as BASE
from src.models.baitoey._overlays import AltBtc, make

MODEL = make(AltBtc, BASE, "baitoey_ovl_altbtc_b_dual", "dual", "research only: baitoey_vt_dual with alt basket 10-day return below BTC -> alt longs to cash", TO="cash")
