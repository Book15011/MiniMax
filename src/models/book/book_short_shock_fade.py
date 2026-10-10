"""Fixed exhaustion-short research hypothesis; parameters in config.yaml."""
from src.config import load_config
from ._short_exhaustion import ShortExhaustion
_p=load_config()["models"]["book_short_shock_fade"]
MODEL=ShortExhaustion("book_short_shock_fade","shock",_p["rebalance_hours"],_p["band"])
del _p
