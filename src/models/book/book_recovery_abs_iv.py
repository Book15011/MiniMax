"""Fixed selection/sizing research candidate; never the live model."""
from src.contracts import ModelSpec
from src.models.book._recovery_selection import Selection
class Candidate(Selection):
    ABS=True
    IV=True
    spec=ModelSpec(name="book_recovery_abs_iv",method="selector",author="book",rebalance_hours=24,band=.03,uses_shorts=True,
                   description="research: current brk-cash with abs_iv selection/sizing")
MODEL=Candidate()
