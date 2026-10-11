"""Predeclared research-only BTC-adjusted long selection."""
from src.contracts import ModelSpec
from src.models.book._residual_recovery import ResidualRecovery
class Candidate(ResidualRecovery):
    BLEND=True
    spec=ModelSpec(name="book_recovery_resid_blend",method="selector",author="book",rebalance_hours=24,
                   band=.03,uses_shorts=True,description="research: BTC-adjusted long selection on brk-cash")
MODEL=Candidate()
