"""Research only (research/baitoey/prereg/20261009-overlays.md): baitoey_vt_dual with control: the hourly event wrapper with factor 1."""
from __future__ import annotations

from src.models.baitoey.baitoey_vt_dual import MODEL as BASE
from src.models.baitoey._overlays import EventDerisk, make

MODEL = make(EventDerisk, BASE, "baitoey_ovl_evtctl_dual", "dual", "research only: baitoey_vt_dual with control: the hourly event wrapper with factor 1", hourly=True)
