"""Frozen all-parent short protection; research only."""
from src.contracts import ModelSpec
from src.models.book._rebound_recovery import ReboundRecovery
class Model(ReboundRecovery):
    MARKET=False
    spec=ModelSpec(name="book_recovery_allshort24",method="selector",author="book",rebalance_hours=24,band=0.03,
                   uses_shorts=True,description="Parent with "+("broad rebound short protection" if False else "all-short 24h direction confirmation"))
MODEL=Model()
