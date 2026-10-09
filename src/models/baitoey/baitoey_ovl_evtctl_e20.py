"""Research only (research/baitoey/prereg/20261009-overlays.md): pol_switch_vt_tl_e20v45 with control: the hourly event wrapper with factor 1."""
from __future__ import annotations

from src.models.pol.pol_switch_vt_tl_e20v45 import MODEL as BASE
from src.models.baitoey._overlays import EventDerisk, make

MODEL = make(EventDerisk, BASE, "baitoey_ovl_evtctl_e20", "e20", "research only: pol_switch_vt_tl_e20v45 with control: the hourly event wrapper with factor 1", hourly=True)
