"""Research only (research/baitoey/prereg/20261009-overlays.md): baitoey_vt_dual with gross halved from 12 h before to 6 h after each CPI / FOMC minutes."""
from __future__ import annotations

from src.models.baitoey.baitoey_vt_dual import MODEL as BASE
from src.models.baitoey._overlays import EventDerisk, make

MODEL = make(EventDerisk, BASE, "baitoey_ovl_evt_dual", "dual", "research only: baitoey_vt_dual with gross halved from 12 h before to 6 h after each CPI / FOMC minutes", hourly=True)
