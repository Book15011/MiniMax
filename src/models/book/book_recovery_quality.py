"""Frozen positive-momentum path-quality selection; research only."""
from src.contracts import ModelSpec
from src.models.book._quality_recovery import QualityRecovery

class Model(QualityRecovery):
    BLEND=False
    spec=ModelSpec(name="book_recovery_quality",method="selector",author="book",rebalance_hours=24,band=0.03,
                   uses_shorts=True,description="Positive parent momentum pool with daily path quality"+(" / equal rank blend" if False else ""))

MODEL=Model()
