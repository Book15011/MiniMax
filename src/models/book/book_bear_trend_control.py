"""Frozen selective-short research; metadata comes from config.yaml."""
from src.config import load_config
from ._bear_selective import BearSelective
_p=load_config()["models"]["book_bear_trend_control"]
MODEL=BearSelective("book_bear_trend_control","trend_control",_p["rebalance_hours"],_p["band"])
del _p
