"""Finite pre-registered research candidate; no live configuration change."""
from src.contracts import ModelSpec
from src.models.book._recovery import Recovery
class Candidate(Recovery):
    VOL=True
    SHORT=True
    spec=ModelSpec(name="book_recovery_both",method="selector",author="book",rebalance_hours=24,band=.03,uses_shorts=True,
                   description="research: current brk-cash with both risk control")
MODEL=Candidate()
