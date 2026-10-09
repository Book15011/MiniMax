"""Research only (research/baitoey/prereg/20261009-overlays.md): pol_switch_vt_tl_e20v45 with alt basket 10-day return below BTC -> alt longs to BTC."""
from __future__ import annotations

from src.models.pol.pol_switch_vt_tl_e20v45 import MODEL as BASE
from src.models.baitoey._overlays import AltBtc, make

MODEL = make(AltBtc, BASE, "baitoey_ovl_altbtc_a_e20", "e20", "research only: pol_switch_vt_tl_e20v45 with alt basket 10-day return below BTC -> alt longs to BTC", TO="btc")
