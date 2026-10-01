import numpy as np
import pandas as pd
import pytest

from src.config import load_config
from src.contracts import MarketView, check_targets
from src.models.baitoey._volume_signals import breakdown_blocked, chase_blocked, volume_ratio
from src.models.baitoey.baitoey_breakout import MODEL as BREAKOUT
from src.models.baitoey.baitoey_vt_mom import MODEL as VT_MOM
from src.models.baselines.team_rot_ew import rotation_targets

MODELS = load_config()["models"]
COINS = ["BTCUSDT", "ETHUSDT"] + [f"C{i}USDT" for i in range(8)]
N = 40 * 24


def market(seed: int = 3):
    idx = pd.date_range("2024-01-01 01:00", periods=N, freq="h", tz="UTC")
    k = np.arange(N)
    close = pd.DataFrame({c: 100 * (1 + 0.004 * np.sin(k / (5 + j)) + 0.0002 * j * k / N)
                          for j, c in enumerate(COINS)}, index=idx)
    qv = pd.DataFrame(1e6, index=idx, columns=COINS)
    return close, qv


def view(close, qv, params, prev=None):
    return MarketView(t=close.index[-1], close=close, quote_volume=qv, universe=tuple(COINS), params=params,
                      prev_targets=pd.Series(prev or {}, dtype=float))


def test_volume_ratio_counts_the_last_day_against_the_week():
    _, qv = market()
    qv.iloc[-24:] *= 2.0
    r = volume_ratio(qv, 24, 7).iloc[-1]
    assert r["BTCUSDT"] == pytest.approx(48 / ((144 + 48) * 24 / 168))
    qv.iloc[-5, 0] = np.nan
    assert np.isnan(volume_ratio(qv, 24, 7).iloc[-1]["BTCUSDT"])


def breakout_case(volume_mult):
    close, qv = market()
    c = "C3USDT"
    close.iloc[-1, close.columns.get_loc(c)] = close[c].iloc[-73:-1].max() * 1.05
    qv.iloc[-24:, qv.columns.get_loc(c)] *= volume_mult
    return close, qv, c


def test_breakout_enters_only_with_volume():
    close, qv, c = breakout_case(3.0)
    w = check_targets(BREAKOUT.targets(view(close, qv, MODELS["baitoey_breakout"])), view(close, qv, {}), BREAKOUT.spec)
    assert list(w.index) == [c] and w[c] <= 1 / MODELS["baitoey_breakout"]["k"] + 1e-12
    close, qv, c = breakout_case(1.0)
    assert BREAKOUT.targets(view(close, qv, MODELS["baitoey_breakout"])).empty


def test_breakout_ignores_missing_volume():
    close, qv, c = breakout_case(3.0)
    qv.iloc[-3, qv.columns.get_loc(c)] = np.nan
    assert BREAKOUT.targets(view(close, qv, MODELS["baitoey_breakout"])).empty


def test_breakout_holds_until_a_24h_low():
    close, qv = market()
    c = "C5USDT"
    close.iloc[-1, close.columns.get_loc(c)] = close[c].iloc[-73:-1].max()
    w = BREAKOUT.targets(view(close, qv, MODELS["baitoey_breakout"], {c: 0.1}))
    assert c in w.index
    close.iloc[-1, close.columns.get_loc(c)] = close[c].iloc[-25:-1].min() * 0.99
    assert c not in BREAKOUT.targets(view(close, qv, MODELS["baitoey_breakout"], {c: 0.1})).index


@pytest.mark.parametrize("hours_ago, mult, blocked", [(10, 5.0, True), (30, 5.0, False), (10, 1.0, False)])
def test_breakdown_blocks_for_the_cooldown_only_on_volume(hours_ago, mult, blocked):
    close, qv = market()
    c = "C2USDT"
    j = close.columns.get_loc(c)
    close.iloc[-hours_ago:, j] = close[c].iloc[-hours_ago - 24:-hours_ago].min() * 0.9
    qv.iloc[-hours_ago - 23:-hours_ago + 1, j] *= mult
    assert (c in breakdown_blocked(close, qv, MODELS["baitoey_vt_mom"])) is blocked


@pytest.mark.parametrize("now_price, spike_ago, blocked", [(120.0, 40, True), (113.0, 40, False), (120.0, 100, False)])
def test_chase_blocks_until_a_pullback(now_price, spike_ago, blocked):
    close, qv = market()
    c = "C6USDT"
    j = close.columns.get_loc(c)
    close.iloc[:, j] = 100.0
    close.iloc[-spike_ago:, j] = 120.0
    close.iloc[-1, j] = now_price
    qv.iloc[-spike_ago - 23:-spike_ago + 1, j] *= 10.0
    assert (c in chase_blocked(close, qv, MODELS["baitoey_vt_mom"])) is blocked


def test_vt_mom_without_filters_is_the_rotation_core():
    close, qv = market()
    p = {**MODELS["baitoey_vt_mom"], "early_exit": False, "no_chase": False}
    v = view(close, qv, p)
    pd.testing.assert_series_equal(VT_MOM.targets(v), rotation_targets(v, p))


def test_vt_mom_never_holds_a_blocked_coin_and_keeps_the_contract():
    close, qv = market()
    p = {**MODELS["baitoey_vt_mom"], "early_exit": True, "no_chase": True}
    top = rotation_targets(view(close, qv, p), p).index[0]
    j = close.columns.get_loc(top)
    close.iloc[-10:, j] = close[top].iloc[-34:-10].min() * 0.9
    qv.iloc[-33:-9, j] *= 5.0
    v = view(close, qv, p, {top: 0.2})
    w = check_targets(VT_MOM.targets(v), v, VT_MOM.spec)
    assert top not in w.index and w.abs().sum() <= 1 + 1e-12 and (w >= 0).all()
    pd.testing.assert_series_equal(VT_MOM.targets(v), VT_MOM.targets(v))
