"""src/models/baitoey/_fast_down.py: the asymmetric BTC switch (research/baitoey/prereg/20261009-faster-down-switch.md)."""
import pandas as pd

from src.config import load_config
from src.models.baitoey._fast_down import in_trend_asym
from src.models.baselines.team_trend_2 import in_trend


def test_a_close_between_the_two_down_triggers_flips_only_the_fast_variant():
    ema = pd.Series([100.0] * 3)
    price = pd.Series([104.0, 99.5, 98.9])                     # up, then -0.5%, then -1.1%
    assert in_trend_asym(price, ema, 0.03, 0.01) is False      # -1.1% < -1%: down
    assert in_trend_asym(price, ema, 0.03, 0.015) is True      # -1.1% is inside the -1.5% band: still up
    assert in_trend_asym(price, ema, 0.03, 0.03) == in_trend(price, ema, 0.03)


def test_the_up_trigger_is_unchanged():
    ema = pd.Series([100.0] * 3)
    assert in_trend_asym(pd.Series([98.0, 102.0, 102.9]), ema, 0.03, 0.01) is False   # +2.9%: not yet up
    assert in_trend_asym(pd.Series([98.0, 103.1]), ema[:2], 0.03, 0.01) is True


def test_the_variants_are_e20v45_except_the_down_trigger():
    m = load_config()["models"]
    base = m["pol_switch_vt_tl_e20v45"]
    for name, down in (("baitoey_e20_out10", 0.01), ("baitoey_e20_out15", 0.015)):
        v = m[name]
        assert {k: x for k, x in v.items() if k != "switch"} == {k: x for k, x in base.items() if k != "switch"}
        assert {k: x for k, x in v["switch"].items() if k != "hysteresis_down"} == base["switch"]
        assert v["switch"]["hysteresis_down"] == down
