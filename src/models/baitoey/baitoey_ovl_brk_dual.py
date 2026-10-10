"""Research only (research/baitoey/prereg/20261009-overlays.md): baitoey_vt_dual with exit a long below its 20-day low, back only above its 20-day mean."""
from __future__ import annotations

from src.models.baitoey.baitoey_vt_dual import MODEL as BASE
from src.models.baitoey._overlays import Breakdown, make

MODEL = make(Breakdown, BASE, "baitoey_ovl_brk_dual", "dual", "research only: baitoey_vt_dual with exit a long below its 20-day low, back only above its 20-day mean")
