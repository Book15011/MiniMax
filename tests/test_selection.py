"""Selection ladder helpers and the fair-CRPS side check."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest.selection import blend_targets, block_boot_ci, completed, pick_best, recent_starts
from src.validation.fair_crps import crps_fair
from src.validation.walkforward import crps


def test_fair_and_standard_crps_by_hand():
    # sample {1, 2, 4}, outcome 3: mean|x-y| = 4/3; sum over ordered pairs |xi-xj| = 12
    assert crps_fair([1, 2, 4], 3) == pytest.approx(4 / 3 - 12 / (2 * 3 * 2))   # = 1/3
    assert crps([1, 2, 4], 3) == pytest.approx(4 / 3 - 12 / (2 * 3 * 3))        # = 2/3 (n^2 denominator)
    assert crps_fair([5.0], 2.0) == pytest.approx(3.0)


def test_block_bootstrap_of_a_constant_is_the_constant():
    lo, hi = block_boot_ci(np.full(40, 0.25))
    assert lo == pytest.approx(0.25) and hi == pytest.approx(0.25)


def _w(values: dict[str, list[float]]):
    idx = pd.date_range("2024-01-01 16:00", periods=len(next(iter(values.values()))), freq="D", tz="UTC")
    return {m: pd.DataFrame({"comp_a": v}, index=idx) for m, v in values.items()}, idx


def test_pick_best_uses_the_median_and_breaks_ties_alphabetically():
    W, idx = _w({"b_model": [1, 1, 9], "a_model": [2, 2, 0]})
    assert pick_best(W, idx) == "a_model"                 # medians 2 vs 1
    W, idx = _w({"b_model": [1, 1], "a_model": [1, 1]})
    assert pick_best(W, idx) == "a_model"
    assert pick_best(W, []) is None


def test_completed_and_recent_windows_never_look_past_D():
    idx = pd.date_range("2024-01-01 16:00", periods=60, freq="D", tz="UTC")
    D = idx[40]
    done = completed(idx, D, 14)
    assert (done + pd.Timedelta(days=14) <= D).all() and done[-1] == idx[26]
    rec = recent_starts(done, 14, 3)
    assert rec == [idx[26], idx[12]]            # idx[0] would overlap the window starting at idx[12]
    assert all(a - b >= pd.Timedelta(days=14) for a, b in zip(rec, rec[1:]))


def test_blend_is_the_average_of_the_decisions():
    t = pd.date_range("2024-01-01 16:00", periods=2, freq="D", tz="UTC")

    class E:
        def __init__(self, df):
            self.targets = df
    a = E(pd.DataFrame({"X": [1.0, 1.0]}, index=t))
    b = E(pd.DataFrame({"Y": [-0.5, 0.0]}, index=t))
    out = blend_targets({"a": a, "b": b})
    assert out.loc[t[0], "X"] == pytest.approx(0.5) and out.loc[t[0], "Y"] == pytest.approx(-0.25)
    assert (out.abs().sum(axis=1) <= 1 + 1e-12).all()
