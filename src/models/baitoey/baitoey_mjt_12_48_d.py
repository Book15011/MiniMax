"""Research only (research/baitoey/prereg/20261010-majors-trend.md): majors trend long/short, EMA 12/48 hours, decided daily."""
from __future__ import annotations

from src.models.baitoey._majors_trend import make

MODEL = make("baitoey_mjt_12_48_d", 24, "research only: trend long/short on the five majors, EMA 12/48 hours, decided daily")
