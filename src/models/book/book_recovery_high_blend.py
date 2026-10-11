"""Frozen near-high long selection; research only."""
from src.contracts import ModelSpec
from src.models.book._high_recovery import HighRecovery

class Model(HighRecovery):
    BLEND=True
    spec=ModelSpec(name="book_recovery_high_blend",method="selector",author="book",rebalance_hours=24,band=0.03,
                   uses_shorts=True,description="Parent brk cash shorts with near-high long selection"+(" / equal momentum blend" if True else ""))

MODEL=Model()
