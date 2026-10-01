"""CRPS estimators for ensemble forecasts.

The standard sample CRPS divides the spread term by n^2, which is biased for small ensembles; the
fair CRPS (Ferro 2014) excludes i = j pairs. For weights w (sum 1):

    CRPS_fair(x, w; y) = sum_i w_i |x_i - y| - 1/2 * sum_{i!=j} w_i w_j |x_i - x_j| / (1 - sum_i w_i^2)

With equal weights this is mean|x - y| - sum_{i,j}|x_i - x_j| / (2 n (n - 1)).
The kernel version replaces each member by N(x_i, b^2): |.| becomes A(mu, s^2) = E|mu + s Z|.
"""
from __future__ import annotations

import math

import numpy as np


def _normalise(w) -> np.ndarray:
    w = np.asarray(w, dtype=float)
    if (w < 0).any() or not np.isfinite(w).all() or w.sum() <= 0:
        raise ValueError("weights must be finite, non-negative and not all zero")
    return w / w.sum()


def crps_fair(x, y: float, w=None) -> float:
    """Weighted fair CRPS in O(n log n). w=None means equal weights."""
    x = np.asarray(x, dtype=float)
    w = np.full(len(x), 1.0 / len(x)) if w is None else _normalise(w)
    t1 = float(np.sum(w * np.abs(x - y)))
    s2 = float(np.sum(w * w))
    if s2 >= 1.0 - 1e-15:
        return t1
    o = np.argsort(x, kind="stable")
    xs, ws = x[o], w[o]
    w_before = np.cumsum(ws) - ws
    s_before = np.cumsum(ws * xs) - ws * xs
    pair = 2.0 * float(np.sum(ws * (xs * w_before - s_before)))  # sum_{i!=j} w_i w_j |x_i - x_j|
    return t1 - 0.5 * pair / (1.0 - s2)


def crps_standard(x, y: float) -> float:
    """Standard sample CRPS: mean|x - y| - 0.5 * mean_{i,j}|x_i - x_j| (as used by the v1 rule)."""
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    i = np.arange(n)
    return float(np.mean(np.abs(x - y)) - 0.5 * 2.0 * np.sum((2 * i - n + 1) * x) / n**2)


def abs_normal_mean(mu, s: float):
    """A(mu, s^2) = E|mu + s Z| = 2 s phi(mu/s) + mu (2 Phi(mu/s) - 1); exact (math.erf)."""
    mu = np.asarray(mu, dtype=float)
    z = mu / s
    phi = np.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)
    erf = np.vectorize(math.erf, otypes=[float])(z / math.sqrt(2.0))
    return 2.0 * s * phi + mu * erf


class GridKernelCRPS:
    """Kernel fair CRPS for members and observations that lie on the grid k / m (k = 0..m).

    Mid-rank percentiles within a pool of n are multiples of 1/(2n), so with m = 2n every difference
    is a multiple of 1/m and A() is needed only on 2m + 1 points.
    """

    def __init__(self, m: int, b: float):
        self.m, self.b = m, b
        lags = np.arange(-m, m + 1) / m
        self.a1 = abs_normal_mean(lags, b)                 # member vs observation: variance b^2
        self.a2 = abs_normal_mean(lags, math.sqrt(2) * b)  # member vs member: variance 2 b^2

    def __call__(self, pos: np.ndarray, w, obs_pos: int) -> float:
        pos = np.asarray(pos, dtype=int)
        w = _normalise(w)
        m = self.m
        t1 = float(np.sum(w * self.a1[pos - obs_pos + m]))
        s2 = float(np.sum(w * w))
        if s2 >= 1.0 - 1e-15:
            return t1
        h = np.bincount(pos, weights=w, minlength=m + 1)
        c = np.convolve(h, self.a2)               # c[p + m] = sum_q h_q A2(p - q)
        full = float(np.dot(h, c[m: 2 * m + 1]))  # sum_{i,j} incl. i = j
        pair = full - s2 * float(self.a2[m])       # remove i = j terms, A2(0)
        return t1 - 0.5 * pair / (1.0 - s2)


def to_grid(pct: np.ndarray, n: int) -> np.ndarray:
    """Mid-rank percentiles (multiples of 1/(2n)) -> integer grid positions 0..2n."""
    pos = np.rint(np.asarray(pct, dtype=float) * 2 * n).astype(int)
    if np.abs(pos / (2 * n) - pct).max() > 1e-9:
        raise ValueError("percentiles are not on the 1/(2n) grid")
    return pos
