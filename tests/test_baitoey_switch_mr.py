import numpy as np
import pandas as pd
import pytest
from dataclasses import replace

from src.config import load_config
from src.contracts import MarketView, check_targets
from src.models.baitoey.baitoey_mr_bbrsi import MODEL as MR
from src.models.baitoey.baitoey_switch_mr import MODEL as SWITCH, btc_calm
from src.models.baselines.team_rot_ew import MODEL as ROT

M = load_config()["models"]
P = M["baitoey_switch_mr"]
N = 400 * 24
COINS = ["BTCUSDT", "ETHUSDT"] + [f"C{i}USDT" for i in range(8)]


def btc(sigma_old, sigma_new, seed=1):
    rng = np.random.default_rng(seed)
    r = np.r_[rng.normal(0, sigma_old, N - 30 * 24), rng.normal(0, sigma_new, 30 * 24)]
    return 100 * np.exp(np.cumsum(r))


def frames(btc_path):
    idx = pd.date_range("2025-01-01 01:00", periods=N, freq="h", tz="UTC")
    k = np.arange(N)
    close = pd.DataFrame({c: 100 * (1 + 0.004 * np.sin(k / (5 + j)) + 0.0002 * j * k / N) for j, c in enumerate(COINS)},
                         index=idx)
    close["BTCUSDT"] = btc_path
    close.iloc[-1, close.columns.get_loc("C4USDT")] *= 0.85        # one oversold coin for the MR sleeve
    return close, pd.DataFrame(1e6, index=idx, columns=COINS)


def test_sleeves_follow_their_own_blocks():
    assert P["sleeves"]["calm"] == {**M["baitoey_mr_bbrsi"], "bar_hours": 4}
    assert P["sleeves"]["trend"] == M["team_rot_ew"]


@pytest.mark.parametrize("old, new, calm", [(0.01, 0.002, True), (0.002, 0.02, False)])
def test_calm_means_volatility_below_its_one_year_median(old, new, calm):
    assert btc_calm(pd.Series(btc(old, new)), 30, 365, 0.5) is calm


def test_short_history_is_not_calm():
    assert btc_calm(pd.Series(btc(0.01, 0.002))[-5000:], 30, 365, 0.5) is False


@pytest.mark.parametrize("old, new, sleeve, key", [(0.01, 0.002, MR, "calm"), (0.002, 0.02, ROT, "trend")])
def test_switch_hands_the_decision_to_one_sleeve(old, new, sleeve, key):
    close, qv = frames(btc(old, new))
    v = MarketView(t=close.index[-1], close=close, quote_volume=qv, universe=tuple(COINS), params=P)
    w = check_targets(SWITCH.targets(v), v, SWITCH.spec)
    pd.testing.assert_series_equal(w, sleeve.targets(replace(v, params=P["sleeves"][key])).astype(float))
    assert not w.empty and (w >= 0).all()
