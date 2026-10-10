"""Research only (research/baitoey/prereg/20261010-majors-trend.md): majors trend long/short, EMA 6/24 hours, decided daily."""
from __future__ import annotations

from src.models.baitoey._majors_trend import make

MODEL = make("baitoey_mjt_06_24_d", 24, "research only: trend long/short on the five majors, EMA 6/24 hours, decided daily")
