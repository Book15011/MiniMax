"""Asymmetric switch (src/models/pol/_switch_asym.py): separate down and up bars; equal bars give _combo.btc_state."""
from __future__ import annotations

import pandas as pd

from src.config import load_config
from src.models.pol import _switch_asym
from src.models.pol._combo import btc_state
from tests.test_combo import market, view_at  # noqa: F401  (fixture)

CFG = load_config()


def test_in_trend_uses_the_down_bar_to_leave_and_the_up_bar_to_return():
    ema = pd.Series(1.0, index=range(4))
    f = _switch_asym.in_trend
    assert f(pd.Series([1.04, 1.02, 0.985, 1.0]), ema, 0.03, 0.02) is True      # 0.985 is above the 0.98 bar: still up
    assert f(pd.Series([1.04, 1.02, 0.975, 1.0]), ema, 0.03, 0.02) is False     # below 0.98: down
    assert f(pd.Series([1.04, 0.975, 1.025, 1.0]), ema, 0.03, 0.02) is False    # 1.025 is under the 1.03 bar: stays down
    assert f(pd.Series([1.04, 0.975, 1.035, 1.0]), ema, 0.03, 0.02) is True     # above 1.03: up again
    assert f(pd.Series([1.0, 1.01, 0.995, 1.0]), ema, 0.03, 0.02) is False      # never decisive: out of trend


def test_equal_bars_give_the_combo_state(market):  # noqa: F811
    trend = dict(CFG["models"]["team_trend_2"])
    for t in pd.date_range("2021-02-01 16:00", "2021-04-01 16:00", freq="3D", tz="UTC"):
        v = view_at(market, str(t), {})
        for h in (0.0, 0.01, 0.03):
            p = {**trend, "hysteresis": h, "down_hysteresis": h}
            assert _switch_asym.btc_state(v, p) == btc_state(v, p)


def test_live_config_blocks_move_only_the_down_bar():
    for d, h in (("d2", 0.02), ("d1", 0.01), ("d0", 0.0)):
        p = CFG["models"][f"pol_switch_vt_tl_e20v45_{d}"]
        live = CFG["models"]["pol_switch_vt_tl_e20v45"]
        assert p["switch"]["hysteresis"] == live["switch"]["hysteresis"] == 0.03
        assert p["switch"]["down_hysteresis"] == h
        assert {k: v for k, v in p["switch"].items() if k != "down_hysteresis"} == live["switch"]
        assert p["sleeves"] == live["sleeves"]
