"""Section 2 metrics: golden values computed by hand (arithmetic in the comments) and an independent re-implementation."""
from __future__ import annotations

import math

import numpy as np
import pytest

from backtest.scoring.metrics import max_drawdown, window_metrics
from src.config import load_config
from tests.scoring_reference import metrics as reference_metrics

SC = load_config()["scoring"]
E0 = 100_000.0


def hourly_from_daily(D: list[float]) -> np.ndarray:
    """Hourly equity that is flat inside each day and moves on the day's last hour: E_k = D_floor(k/24)."""
    return np.array([D[k // 24] for k in range(14 * 24 + 1)], dtype=float)


def equity(daily_returns: list[float]) -> list[float]:
    D = [E0]
    for r in daily_returns:
        D.append(D[-1] * (1 + r))
    return D


def one(E, gross_end=0.0) -> dict:
    return window_metrics(E, [gross_end], SC).iloc[0].to_dict()


# ---------------- 5.1 golden: a 15-point equity series, every metric, 4 variants, 2 conventions ----------------

R14 = [0.02, -0.01, 0.01, 0.00, 0.03, -0.02, 0.01, 0.00, 0.02, -0.01, 0.01, 0.00, 0.02, -0.01]
D15 = equity(R14)        # 15 points: 100000, 102000, 100980, 101989.8, ..., 107086.2032...


def test_golden_daily_series_all_variants_both_conventions():
    m = one(hourly_from_daily(D15), gross_end=0.5)
    # sum r = .02-.01+.01+0+.03-.02+.01+0+.02-.01+.01+0+.02-.01 = 0.07  ->  m = 0.07 / 14 = 0.005
    # r - m = .015 -.015 .005 -.005 .025 -.025 .005 -.005 .015 -.015 .005 -.005 .015 -.015
    # squares (x1e-6): 6 x 225 + 6 x 25 + 2 x 625 = 1350 + 150 + 1250 = 2750  ->  sum = 0.00275, s^2 = 0.00275 / 13
    # losses: -.01, -.02, -.01, -.01 -> squares .0001 + .0004 + .0001 + .0001 = .0007 -> dd^2 = .0007 / 14 = .00005
    m_d, s_d, dd_d = 0.005, math.sqrt(0.00275 / 13), math.sqrt(0.00005)
    # equity: 100000 -> 102000 -> 100980 (-1% from the 102000 peak) ... 105049.494 -> 102948.50412 (-2%: deepest)
    mdd = 0.02
    R = math.prod(1 + r for r in R14) - 1                       # 0.0708620323278695
    assert m["R"] == pytest.approx(R, rel=1e-12) and R == pytest.approx(0.0708620323278695, rel=1e-12)
    assert m["R_liq"] == pytest.approx((1 + R) * (1 - 0.001 * 0.5) - 1, rel=1e-12)   # 0.1% of 50% gross left open
    assert m["MDD"] == pytest.approx(mdd, rel=1e-12)
    assert (m["m_daily"], m["s_daily"], m["dd_daily"]) == pytest.approx((m_d, s_d, dd_d), rel=1e-12)
    sharpe1 = m_d / s_d                                         # = sqrt(0.005^2 * 13 / 0.00275) = sqrt(13 / 110) = 0.3437758
    sortino1 = m_d / dd_d                                       # = 0.005 / (0.005 * sqrt 2) = 1 / sqrt 2 = 0.7071068
    assert sharpe1 == pytest.approx(math.sqrt(13 / 110), rel=1e-12)
    assert sortino1 == pytest.approx(1 / math.sqrt(2), rel=1e-12)
    # hourly: 336 returns, 14 of them equal to the daily ones, 322 zeros
    m_h = 0.07 / 336                                            # = 1 / 4800
    s_h = math.sqrt((0.0031 - 336 * m_h ** 2) / 335)             # sum h^2 = sum r^2 = (4+1+1+0+9+4+1+0+4+1+1+0+4+1)e-4 = 0.0031
    dd_h = math.sqrt(0.0007 / 336)                              # same losses, over 336 hours
    assert (m["m_hourly"], m["s_hourly"], m["dd_hourly"]) == pytest.approx((m_h, s_h, dd_h), rel=1e-12)
    expected = {
        "V1": (sharpe1, sortino1, m_d / mdd),                                # Calmar = 0.005 / 0.02 = 0.25
        "V2": (sharpe1 * math.sqrt(365), sortino1 * math.sqrt(365), m_d * 365 / mdd),   # Calmar = 1.825 / 0.02 = 91.25
        "V3": (m_h / s_h * math.sqrt(8760), m_h / dd_h * math.sqrt(8760), m_h * 8760 / mdd),  # Calmar 91.25 too
        "V4": (sharpe1, sortino1, R / mdd),                                  # Calmar = 0.07086203 / 0.02 = 3.5431016
    }
    assert expected["V1"][2] == pytest.approx(0.25) and expected["V2"][2] == pytest.approx(91.25)
    assert expected["V3"][2] == pytest.approx(91.25) and expected["V4"][2] == pytest.approx(3.543101616393475)
    for conv in ("FLOORED", "POL"):                             # no denominator is below any floor here
        for v, (sh, so, ca) in expected.items():
            assert m[f"{conv}.{v}.sharpe"] == pytest.approx(sh, rel=1e-12)
            assert m[f"{conv}.{v}.sortino"] == pytest.approx(so, rel=1e-12)
            assert m[f"{conv}.{v}.calmar"] == pytest.approx(ca, rel=1e-12)
            assert m[f"{conv}.{v}.composite"] == pytest.approx(0.4 * so + 0.3 * sh + 0.3 * ca, rel=1e-12)
        assert not any(m[f"{conv}.hit.{f}"] for f in ("s_daily", "dd_daily", "s_hourly", "dd_hourly", "mdd"))
    # V1 composite = 0.4 * 0.70710678 + 0.3 * 0.34377584 + 0.3 * 0.25 = 0.28284271 + 0.10313275 + 0.075 = 0.46097546
    assert m["FLOORED.V1.composite"] == pytest.approx(0.46097546, abs=1e-8)


def test_all_zero_returns_give_zero_ratios():
    m = one(np.full(337, E0))
    assert m["R"] == 0 and m["MDD"] == 0
    for conv in ("FLOORED", "POL"):
        for v in ("V1", "V2", "V3", "V4"):
            for r in ("sharpe", "sortino", "calmar", "composite"):
                assert m[f"{conv}.{v}.{r}"] == 0.0


def test_no_losses_sortino_uses_the_floor_or_pol_rule():
    r = [0.01] * 7 + [0.0] * 7                                  # m = 0.07 / 14 = 0.005, no losing day, no drawdown
    m = one(hourly_from_daily(equity(r)))
    assert m["dd_daily"] == 0 and m["dd_hourly"] == 0 and m["MDD"] == 0
    # s^2 = sum (r - m)^2 / 13 = 14 * 0.005^2 / 13  ->  Sharpe = 0.005 / sqrt(0.00035 / 13) = sqrt(13 / 14)
    assert m["FLOORED.V1.sharpe"] == pytest.approx(math.sqrt(13 / 14), rel=1e-12)
    assert m["POL.V1.sharpe"] == pytest.approx(math.sqrt(13 / 14), rel=1e-12)
    # FLOORED: dd floored at 0.001 -> Sortino = 0.005 / 0.001 = 5; MDD floored at 0.002 -> Calmar = 0.005 / 0.002 = 2.5
    assert m["FLOORED.V1.sortino"] == pytest.approx(5.0, rel=1e-12)
    assert m["FLOORED.V1.calmar"] == pytest.approx(2.5, rel=1e-12)
    assert m["FLOORED.V4.calmar"] == pytest.approx((1.01 ** 7 - 1) / 0.002, rel=1e-12)   # R = 1.01^7 - 1
    # hourly floor 0.001 / sqrt(24): Sortino = (1/4800) / (0.001 / sqrt 24) * sqrt 8760
    assert m["FLOORED.V3.sortino"] == pytest.approx((1 / 4800) / (0.001 / math.sqrt(24)) * math.sqrt(8760), rel=1e-12)
    # POL (backtest/metrics.py): a zero downside deviation gives Sortino 0; MDD floored at 1e-4 -> Calmar = 0.005 / 1e-4 = 50
    assert m["POL.V1.sortino"] == 0.0 and m["POL.V3.sortino"] == 0.0
    assert m["POL.V1.calmar"] == pytest.approx(50.0, rel=1e-12)
    assert m["FLOORED.hit.dd_daily"] and m["FLOORED.hit.dd_hourly"] and m["FLOORED.hit.mdd"]
    assert not m["FLOORED.hit.s_daily"]
    assert m["POL.hit.dd_daily"] and m["POL.hit.mdd"] and not m["POL.hit.s_daily"]


def test_mdd_when_the_peak_is_e0():
    assert max_drawdown(np.array([100.0, 98.0, 99.0, 97.0, 99.5]))[0] == pytest.approx(0.03)   # 1 - 97/100
    assert max_drawdown(np.array([100.0, 99.0, 98.0]))[0] == pytest.approx(0.02)              # from E_0, not E_1
    assert max_drawdown(np.array([100.0, 101.0, 102.0]))[0] == 0.0


def test_hourly_floor_is_the_daily_floor_over_sqrt_24():
    for k in ("s_hourly", "dd_hourly"):
        assert SC["conventions"]["FLOORED"][k] == pytest.approx(0.001 / math.sqrt(24), rel=1e-14)
    assert SC["primary"] == {"variant": "V1", "convention": "FLOORED"}


# ---------------- 5.2: independent implementation, 1,000 random equity series, match to 1e-12 ----------------

def random_series(rng: np.random.Generator, k: int) -> np.ndarray:
    kind = k % 5
    if kind == 0:
        h = rng.normal(0.0, rng.uniform(1e-4, 2e-2), 336)                  # ordinary
    elif kind == 1:
        h = np.abs(rng.normal(0.0, rng.uniform(1e-5, 1e-3), 336))         # no losses
        h[rng.random(336) < 0.5] = 0.0
    elif kind == 2:
        h = np.zeros(336)                                                 # flat, a few jumps
        h[rng.choice(336, 5, replace=False)] = rng.normal(0.0, 0.01, 5)
    elif kind == 3:
        h = rng.standard_t(3, 336) * rng.uniform(1e-4, 5e-3)              # fat tails
    else:
        h = np.zeros(336)                                                 # cash
    return E0 * np.concatenate([[1.0], np.cumprod(1.0 + h)])


def test_independent_implementation_matches_on_1000_random_series():
    rng = np.random.default_rng(20261003)
    E = np.stack([random_series(rng, k) for k in range(1000)])
    gross = rng.uniform(0, 1, 1000)
    got = window_metrics(E, gross, SC)
    worst = 0.0
    for k in range(1000):
        ref = reference_metrics(E[k].tolist(), float(gross[k]), SC)
        for col, v in ref.items():
            g = float(got[col].iloc[k])
            assert math.isclose(g, v, rel_tol=1e-12, abs_tol=1e-12), (k, col, g, v)
            worst = max(worst, abs(g - v) / max(abs(v), 1e-12))
    assert worst < 1e-12
