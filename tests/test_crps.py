import math

import numpy as np
import pytest

from src.validation.crps import GridKernelCRPS, abs_normal_mean, crps_fair, crps_standard, to_grid


def unweighted_fair(x, y):
    """mean|x - y| - sum_{i,j}|x_i - x_j| / (2 n (n - 1))  (the unweighted fair CRPS, Ferro 2014)."""
    x = np.asarray(x, float)
    n = len(x)
    return np.mean(np.abs(x - y)) - np.abs(x[:, None] - x[None, :]).sum() / (2 * n * (n - 1))


def weighted_fair_bruteforce(x, w, y):
    x, w = np.asarray(x, float), np.asarray(w, float) / np.sum(w)
    pair = sum(w[i] * w[j] * abs(x[i] - x[j]) for i in range(len(x)) for j in range(len(x)) if i != j)
    return float(np.sum(w * np.abs(x - y)) - 0.5 * pair / (1 - np.sum(w * w)))


def test_equal_weights_equal_the_unweighted_fair_crps():
    rng = np.random.default_rng(0)
    for n in (2, 3, 25, 200):
        x, y = rng.normal(size=n), rng.normal()
        assert crps_fair(x, y) == pytest.approx(unweighted_fair(x, y), rel=1e-12, abs=1e-14)
        assert crps_fair(x, y, np.ones(n)) == pytest.approx(unweighted_fair(x, y), rel=1e-12, abs=1e-14)
        assert crps_fair(x, y, np.full(n, 7.3)) == pytest.approx(unweighted_fair(x, y), rel=1e-12, abs=1e-14)


def test_weighted_matches_bruteforce():
    rng = np.random.default_rng(1)
    for _ in range(20):
        n = int(rng.integers(2, 30))
        x, w, y = rng.normal(size=n), rng.uniform(0, 1, n), rng.normal()
        assert crps_fair(x, y, w) == pytest.approx(weighted_fair_bruteforce(x, w, y), rel=1e-12, abs=1e-14)


def test_hand_computed_small_case():
    # x = (0, 2), w = (0.25, 0.75), y = 1:
    #   sum w|x - y| = 0.25*1 + 0.75*1 = 1
    #   sum_{i!=j} w_i w_j |x_i - x_j| = 2 * 0.25*0.75*2 = 0.75 ;  1 - sum w^2 = 1 - (0.0625 + 0.5625) = 0.375
    #   CRPS = 1 - 0.5 * 0.75 / 0.375 = 0
    assert crps_fair([0.0, 2.0], 1.0, [0.25, 0.75]) == pytest.approx(0.0, abs=1e-15)
    # single member: |x - y|
    assert crps_fair([3.0], 1.0) == pytest.approx(2.0)
    assert crps_fair([3.0, 5.0], 1.0, [1.0, 0.0]) == pytest.approx(2.0)


def test_standard_crps_unchanged():
    rng = np.random.default_rng(2)
    x, y = rng.normal(size=37), 0.3
    brute = np.mean(np.abs(x - y)) - 0.5 * np.mean(np.abs(x[:, None] - x[None, :]))
    assert crps_standard(x, y) == pytest.approx(brute, rel=1e-12)


def test_abs_normal_mean():
    s = 0.3
    assert abs_normal_mean(0.0, s) == pytest.approx(s * math.sqrt(2 / math.pi), rel=1e-15)
    assert abs_normal_mean(5.0, 1e-6) == pytest.approx(5.0, rel=1e-12)
    assert abs_normal_mean(-5.0, 1e-6) == pytest.approx(5.0, rel=1e-12)


def kernel_bruteforce(u, w, v, b):
    u, w = np.asarray(u, float), np.asarray(w, float) / np.sum(w)
    t1 = sum(w[i] * abs_normal_mean(u[i] - v, b) for i in range(len(u)))
    pair = sum(w[i] * w[j] * abs_normal_mean(u[i] - u[j], math.sqrt(2) * b)
               for i in range(len(u)) for j in range(len(u)) if i != j)
    return float(t1 - 0.5 * pair / (1 - np.sum(w * w)))


def test_grid_kernel_matches_bruteforce_and_limits():
    rng = np.random.default_rng(3)
    n = 40                                   # a pool of 40 -> grid 1/80
    pos = rng.integers(0, 2 * n + 1, 15)
    w = rng.uniform(0, 1, 15)
    obs = 33
    for b in (0.05, 0.10, 0.20):
        k = GridKernelCRPS(2 * n, b)
        assert k(pos, w, obs) == pytest.approx(kernel_bruteforce(pos / (2 * n), w, obs / (2 * n), b), rel=1e-10)
    tiny = GridKernelCRPS(2 * n, 1e-9)
    assert tiny(pos, w, obs) == pytest.approx(crps_fair(pos / (2 * n), obs / (2 * n), w), rel=1e-7, abs=1e-12)


def test_to_grid_rejects_off_grid_values():
    assert to_grid(np.array([0.0125, 0.5]), 40).tolist() == [1, 40]
    with pytest.raises(ValueError):
        to_grid(np.array([0.013]), 40)
