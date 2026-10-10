"""Frozen research strategy; metadata is loaded from config.yaml."""
from src.config import load_config
from ._bear_exit import BearExit
_p=load_config()["models"]["book_bear_cost_guard"]
MODEL=BearExit("book_bear_cost_guard","cost_guard",_p["rebalance_hours"],_p["band"])
del _p
