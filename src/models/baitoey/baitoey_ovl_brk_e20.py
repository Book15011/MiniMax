"""Research only (research/baitoey/prereg/20261009-overlays.md): pol_switch_vt_tl_e20v45 with exit a long below its 20-day low, back only above its 20-day mean."""
from __future__ import annotations

from src.models.pol.pol_switch_vt_tl_e20v45 import MODEL as BASE
from src.models.baitoey._overlays import Breakdown, make

MODEL = make(Breakdown, BASE, "baitoey_ovl_brk_e20", "e20", "research only: pol_switch_vt_tl_e20v45 with exit a long below its 20-day low, back only above its 20-day mean")
