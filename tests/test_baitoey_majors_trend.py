"""src/models/baitoey/_majors_trend.py (research/baitoey/prereg/20261010-majors-trend.md)."""
import numpy as np
import pandas as pd

from src.contracts import MarketView
from src.models.baitoey import _majors_trend as mt

P = {"fast": 6, "slow": 24, "dead_band": 0.0025, "vol_days": 30, "cap": 0.30, "target_daily_vol": 0.03}


def view(paths: dict, extra=()):
    n = len(next(iter(paths.values())))
    idx = pd.date_range("2026-01-01", periods=n, freq="h", tz="UTC")
    close = pd.DataFrame(paths, index=idx)
    return MarketView(t=idx[-1], close=close, quote_volume=close * 0 + 1e6, universe=tuple(paths) + tuple(extra), params=P)


def wiggle(n, drift, amp, seed=None):
    """A clear trend (drift per hour) times a fixed up-down wiggle of size amp (its volatility)."""
    t = np.arange(n)
    return 100 * np.exp(drift * t) * (1 + amp * (-1.0) ** t)


def test_rising_coins_are_long_falling_ones_short_and_flat_ones_held_at_nothing():
    n = 31 * 24 + 1
    v = view({"BTCUSDT": wiggle(n, 0.002, 0.001), "ETHUSDT": wiggle(n, -0.002, 0.001), "BNBUSDT": wiggle(n, 0.0, 0.001)})
    w = mt.make("t", 24, "t").targets(v)
    assert w["BTCUSDT"] > 0 and w["ETHUSDT"] < 0 and "BNBUSDT" not in w


def test_weights_are_inverse_volatility_capped_and_within_gross_one_and_only_majors():
    n = 31 * 24 + 1
    v = view({"BTCUSDT": wiggle(n, 0.002, 0.001), "SOLUSDT": wiggle(n, 0.002, 0.004), "PEPEUSDT": wiggle(n, 0.002, 0.002)})
    w = mt.make("t", 24, "t").targets(v)
    assert "PEPEUSDT" not in w and w.abs().max() <= 0.30 + 1e-12 and w.abs().sum() <= 1.0 + 1e-12
    assert w["BTCUSDT"] >= w["SOLUSDT"]                              # the calmer coin gets at least as much


def test_the_volatility_target_scales_a_wild_book_down():
    n = 31 * 24 + 1
    calm = mt.make("t", 24, "t").targets(view({"BTCUSDT": wiggle(n, 0.002, 0.001)}))
    wild = mt.make("t", 24, "t").targets(view({"BTCUSDT": wiggle(n, 0.002, 0.05)}))   # about 49%/day: capped to 3%
    assert not wild.empty and wild.abs().sum() < calm.abs().sum()
