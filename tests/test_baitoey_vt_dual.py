import numpy as np
import pandas as pd
import pytest

from src.config import load_config
from src.contracts import MarketView, check_targets
from src.models.baitoey.baitoey_vt_dual import MODEL as DUAL
from src.models.baitoey.baitoey_vt_mom import MODEL as VT_MOM

MODELS = load_config()["models"]
N = 40 * 24


def market(drifts: list[float]):
    """Hourly closes: a per-coin drift per hour plus a small wiggle (so volatility is never zero); flat volume."""
    coins = [f"C{i}USDT" for i in range(len(drifts))]
    idx = pd.date_range("2024-01-01 01:00", periods=N, freq="h", tz="UTC")
    k = np.arange(N)
    close = pd.DataFrame({c: 100 * np.exp(d * k) * (1 + 0.004 * np.sin(k / (5 + j)))
                          for j, (c, d) in enumerate(zip(coins, drifts))}, index=idx)
    return close, pd.DataFrame(1e6, index=idx, columns=coins)


def view(close, qv, params, prev=None):
    return MarketView(t=close.index[-1], close=close, quote_volume=qv, universe=tuple(close.columns), params=params,
                      prev_targets=pd.Series(prev or {}, dtype=float))


def test_registered_with_vt_mom_parameters_plus_the_threshold():
    p = MODELS["baitoey_vt_dual"]
    assert p["min_score"] == 0.0
    assert {k: v for k, v in p.items() if k != "min_score"} == MODELS["baitoey_vt_mom"]
    assert DUAL.spec.rebalance_hours == VT_MOM.spec.rebalance_hours and DUAL.spec.band == VT_MOM.spec.band


def test_equals_vt_mom_when_every_coin_is_eligible():
    close, qv = market([0.0004 * (1 + j / 10) for j in range(10)])
    p = {**MODELS["baitoey_vt_dual"], "min_score": -np.inf}
    for prev in (None, {"C0USDT": 0.1, "C9USDT": 0.1}):
        a = DUAL.targets(view(close, qv, p, prev)).sort_index()
        b = VT_MOM.targets(view(close, qv, MODELS["baitoey_vt_mom"], prev)).sort_index()
        assert len(b) == 6
        pd.testing.assert_series_equal(a, b, check_names=False, rtol=1e-12)


def test_falling_coins_never_hold_a_slot_and_empty_slots_stay_cash():
    close, qv = market([0.0005, 0.0006, 0.0007] + [-0.0005] * 7)
    p = MODELS["baitoey_vt_dual"]
    w = check_targets(DUAL.targets(view(close, qv, p)), view(close, qv, {}), DUAL.spec)
    assert set(w.index) == {"C0USDT", "C1USDT", "C2USDT"}
    assert (w <= 1 / p["k"] + 1e-12).all() and w.sum() <= 3 / p["k"] + 1e-12   # three slots of six; the rest is cash
    assert len(VT_MOM.targets(view(close, qv, MODELS["baitoey_vt_mom"]))) == 6  # vt_mom fills all six


def test_a_held_coin_is_sold_once_its_own_trend_turns_negative():
    close, qv = market([0.0005, 0.0006, 0.0007, -0.0005] + [-0.0006] * 6)
    p = MODELS["baitoey_vt_dual"]
    w = DUAL.targets(view(close, qv, p, {"C3USDT": 0.15}))           # held, still in the top 12 by rank
    assert "C3USDT" not in w.index
    assert "C3USDT" in VT_MOM.targets(view(close, qv, MODELS["baitoey_vt_mom"], {"C3USDT": 0.15})).index


def test_all_coins_falling_means_all_cash():
    close, qv = market([-0.0004 * (1 + j / 10) for j in range(10)])
    assert DUAL.targets(view(close, qv, MODELS["baitoey_vt_dual"])).empty
