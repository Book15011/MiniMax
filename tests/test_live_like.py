import math

import numpy as np
import pandas as pd
import pytest

from src.validation.live_like import (
    direction_normalise, ensemble_weights, kde_density, mixture_quantiles, p_up_for, pct_to_value, recency_weights,
    trend_state,
)
from src.validation.sets import greedy_spaced, stress_sets

T = pd.Timestamp("2026-10-03 16:00", tz="UTC")
H14 = pd.Timedelta(days=14)


def test_recency_weight_halves_at_half_life():
    ends = pd.DatetimeIndex([T, T - pd.Timedelta(days=120), T - pd.Timedelta(days=240)])
    w = recency_weights(ends, T, 120)
    assert w.sum() == pytest.approx(1.0)
    assert w[1] / w[0] == pytest.approx(0.5, rel=1e-15)
    assert w[2] / w[0] == pytest.approx(0.25, rel=1e-15)
    assert np.allclose(recency_weights(ends, T, math.inf), 1 / 3)


def test_mix_is_half_lookalikes_half_recency():
    pool = pd.date_range("2024-01-01 16:00", periods=100, freq="D", tz="UTC")
    look = pool[[3, 40, 77]]
    m = ensemble_weights("MIX", pool, look, T, H14, hl_star=180)
    rec = recency_weights(pool + H14, T, 180)
    assert m.sum() == pytest.approx(1.0)
    assert m[3] == pytest.approx(0.5 / 3 + 0.5 * rec[3])
    assert m[5] == pytest.approx(0.5 * rec[5])


def test_direction_normalisation_gives_exact_up_share():
    rng = np.random.default_rng(0)
    base = rng.uniform(0.1, 5, 500)
    up = rng.uniform(size=500) > 0.4
    for p in (0.2, 0.537, 0.9):
        w = direction_normalise(base, up, p)
        assert w[up].sum() == pytest.approx(p, abs=1e-14)
        assert w.sum() == pytest.approx(1.0, abs=1e-14)
        # proportions inside each group are unchanged
        assert w[up][0] / w[up][1] == pytest.approx(base[up][0] / base[up][1])


def test_kde_density_single_member():
    b = 0.1
    pts = np.array([[0.5, 0.5, 0.5], [0.6, 0.5, 0.5]])
    f = kde_density(pts, np.array([[0.5, 0.5, 0.5]]), np.array([1.0]), b)
    peak = 1 / (b * math.sqrt(2 * math.pi)) ** 3
    assert f[0] == pytest.approx(peak)
    assert f[1] == pytest.approx(peak * math.exp(-0.5))  # one sd away in one dimension


def test_mixture_quantiles_single_gaussian():
    q10, q50, q90 = mixture_quantiles(np.array([0.4]), np.array([1.0]), 0.1)
    assert q50 == pytest.approx(0.4, abs=1e-12)
    assert q10 == pytest.approx(0.4 - 1.2815515655446004 * 0.1, abs=1e-9)
    assert q90 == pytest.approx(0.4 + 1.2815515655446004 * 0.1, abs=1e-9)


def test_pct_to_value():
    vals = np.array([10.0, 20.0, 30.0, 40.0])        # plotting positions 0.125, 0.375, 0.625, 0.875
    assert pct_to_value(0.5, vals) == pytest.approx(25.0)
    assert pct_to_value(0.0, vals) == pytest.approx(10.0)
    assert pct_to_value(1.3, vals) == pytest.approx(40.0)


def test_trend_state_and_fallback():
    cuts = np.array([-0.1, 0.1])
    assert trend_state(0.02, 0.2, cuts) == (3, True)
    assert trend_state(-0.02, -0.5, cuts) == (1, False)
    t2 = np.array([0.2] * 40 + [-0.5] * 10)
    t1 = np.array([0.1] * 40 + [-0.1] * 10)
    up = np.array([True] * 30 + [False] * 10 + [True] * 2 + [False] * 8)
    p, n, fb, _ = p_up_for((3, True), t1, t2, up, cuts)
    assert (p, n, fb) == (0.75, 40, False)
    p, n, fb, _ = p_up_for((1, False), t1, t2, up, cuts)   # only 10 windows -> tercile-only fallback
    assert (n, fb) == (10, True) and p == pytest.approx(0.2)


def test_greedy_spacing_and_stress_rule():
    days = pd.date_range("2022-01-01 16:00", periods=120, freq="D", tz="UTC")
    y1 = pd.Series(np.linspace(-0.3, 0.3, 120), index=days)
    y1.iloc[60] = -0.5                                          # the single worst window
    assert greedy_spaced(days[[0, 5, 14, 20, 30]], 10, 14) == list(days[[0, 14, 30]])
    price = pd.Series(100.0, index=days)
    price.iloc[50:] = 70.0                                     # 30% below the 90-day high from day 50 on
    s = stress_sets(days, y1, price, k=3)
    assert s["drops"][0]["start"] == str(days[60])
    starts = [pd.Timestamp(r["start"]) for r in s["drops"]]
    assert all(abs(a - b) >= pd.Timedelta(days=14) for i, a in enumerate(starts) for b in starts[i + 1:])
    assert all(pd.Timestamp(r["start"]) >= days[50] for r in s["rebounds"])   # needs >= 20% below the high
    assert s["rebounds"][0]["start"] == str(days[-1])
