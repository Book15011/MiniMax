"""Frozen historical-state forecast; parameters are in config.yaml."""
from src.config import load_config
from ._short_forecast import ShortForecast
_p=load_config()["models"]["book_short_analogue6"]
MODEL=ShortForecast("book_short_analogue6","analogue",_p["rebalance_hours"],_p["band"])
del _p
