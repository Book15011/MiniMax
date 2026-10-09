"""Research only (research/baitoey/prereg/20261009-overlays.md): pol_switch_vt_tl_e20v45 with gross halved from 12 h before to 6 h after each CPI / FOMC minutes."""
from __future__ import annotations

from src.models.pol.pol_switch_vt_tl_e20v45 import MODEL as BASE
from src.models.baitoey._overlays import EventDerisk, make

MODEL = make(EventDerisk, BASE, "baitoey_ovl_evt_e20", "e20", "research only: pol_switch_vt_tl_e20v45 with gross halved from 12 h before to 6 h after each CPI / FOMC minutes", hourly=True)
