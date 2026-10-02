import numpy as np
import pandas as pd
import pytest

from src.config import load_config
from src.contracts import check_targets
from src.models.baitoey._bar_signals import bollinger, rsi, sample_bars
from src.models.baitoey.baitoey_mr_bbrsi import MODEL as MR
from src.models.baitoey.baitoey_rot_dip import MODEL as DIP
from src.models.baselines.team_rot_ew import rotation_targets
from tests.test_baitoey_volume_timing import market, view

M = load_config()["models"]
C = "C4USDT"


def test_rsi_and_bands_on_known_series():
    up = pd.DataFrame({"x": np.arange(1.0, 30.0)})
    down = pd.DataFrame({"x": np.arange(30.0, 1.0, -1)})
    zig = pd.DataFrame({"x": [10.0, 11.0] * 15})
    assert rsi(up, 14).iloc[-1, 0] == pytest.approx(100.0)
    assert rsi(down, 14).iloc[-1, 0] == pytest.approx(0.0)
    assert rsi(zig, 14).iloc[-1, 0] == pytest.approx(50.0, abs=4.0)
    mid, lower = bollinger(zig, 20, 2.0)
    assert mid.iloc[-1, 0] == pytest.approx(10.5) and lower.iloc[-1, 0] == pytest.approx(10.5 - 2 * 0.5)


def test_sample_bars_ends_at_the_decision_and_steps_back():
    close, _ = market()
    b = sample_bars(close, 24, 5)
    assert b.index[-1] == close.index[-1] and (np.diff(b.index.asi8) == 24 * 3600 * 10**9).all()


def flat_coin(close):
    close[C] = 100.0
    return close


def test_buys_an_oversold_coin_below_the_lower_band():
    close, qv = market()
    flat_coin(close).iloc[-1, close.columns.get_loc(C)] = 85.0
    v = view(close, qv, M["baitoey_mr_bbrsi"])
    w = check_targets(MR.targets(v), v, MR.spec)
    assert C in w.index and w[C] <= 1 / M["baitoey_mr_bbrsi"]["k"] + 1e-12


@pytest.mark.parametrize("drop_bars_ago, kept", [(2, True), (5, False)])
def test_time_stop_after_max_hold(drop_bars_ago, kept):
    close, qv = market()
    flat_coin(close)
    j = close.columns.get_loc(C)
    close.iloc[-(drop_bars_ago * 24):, j] = 96.0
    close.iloc[-(drop_bars_ago * 24 + 1), j] = 85.0
    w = MR.targets(view(close, qv, M["baitoey_mr_bbrsi"], {C: 0.1}))
    assert (C in w.index) is kept


def test_sells_back_at_the_mean():
    close, qv = market()
    flat_coin(close)
    close.iloc[-25, close.columns.get_loc(C)] = 85.0
    close.iloc[-1, close.columns.get_loc(C)] = 101.0
    assert C not in MR.targets(view(close, qv, M["baitoey_mr_bbrsi"], {C: 0.1})).index


def test_dip_filter_blocks_a_new_leader_that_just_ran_up_but_keeps_holdings():
    close, qv = market()
    close[C] = np.linspace(100.0, 160.0, len(close))
    p = M["baitoey_rot_dip"]
    off = {**p, "dip_filter": False}
    assert C in rotation_targets(view(close, qv, off), off).index
    v = view(close, qv, p)
    w = check_targets(DIP.targets(v), v, DIP.spec)
    assert C not in w.index and w.abs().sum() <= 1 + 1e-12
    assert C in DIP.targets(view(close, qv, p, {C: 0.15})).index


def test_dip_filter_off_is_the_rotation_core():
    close, qv = market()
    p = {**M["baitoey_rot_dip"], "dip_filter": False}
    v = view(close, qv, p)
    pd.testing.assert_series_equal(DIP.targets(v), rotation_targets(v, p))
