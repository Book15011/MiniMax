"""Fixed selection/sizing research candidate; never the live model."""
from src.contracts import ModelSpec
from src.models.book._recovery_selection import Selection
class Candidate(Selection):
    ABS=True
    IV=False
    spec=ModelSpec(name="book_recovery_abs",method="selector",author="book",rebalance_hours=24,band=.03,uses_shorts=True,
                   description="research: current brk-cash with abs selection/sizing")
MODEL=Candidate()
