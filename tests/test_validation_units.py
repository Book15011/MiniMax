import numpy as np
import pandas as pd
import pytest

from src.validation.selection import PickRules, greedy_pick, jaccard, mid_rank_pct, recent_nonoverlapping
from src.validation.walkforward import choose_variant, crps, skill


def test_crps_single_member_is_absolute_error():
    assert crps([2.0], 5.0) == pytest.approx(3.0)


def test_crps_matches_bruteforce():
    rng = np.random.default_rng(0)
    x, y = rng.normal(size=37), 0.3
    brute = np.mean(np.abs(x - y)) - 0.5 * np.mean(np.abs(x[:, None] - x[None, :]))
    assert crps(x, y) == pytest.approx(brute, rel=1e-12)


def test_mid_rank_percentiles_with_ties():
    ref = np.array([[1.0], [2.0], [2.0], [3.0]])
    p = mid_rank_pct(ref, np.array([[2.0], [0.0], [9.0]]))[:, 0]
    assert p.tolist() == [0.5, 0.0, 1.0]
    assert mid_rank_pct(ref, ref)[:, 0].tolist() == [0.125, 0.5, 0.5, 0.875]


def test_greedy_spacing_rules():
    days = pd.date_range("2021-01-01 16:00", periods=400, freq="D", tz="UTC")
    rng = np.random.default_rng(1)
    picked = greedy_pick(days[rng.permutation(len(days))], PickRules(k=25))
    ts = sorted(picked)
    gaps = np.diff([t.value for t in ts]) / 86_400e9
    assert (gaps >= 14).all()
    for i in range(len(ts) - 3):
        assert (ts[i + 3] - ts[i]).days >= 90


def test_greedy_respects_order_preference():
    days = pd.date_range("2021-01-01 16:00", periods=200, freq="D", tz="UTC")
    order = pd.DatetimeIndex([days[100], days[101], days[120]] + list(days[:100]))
    picked = greedy_pick(order, PickRules(k=3))
    assert days[100] in picked and days[101] not in picked and days[120] in picked


def test_recent_nonoverlapping():
    days = pd.date_range("2021-01-01 16:00", periods=200, freq="D", tz="UTC")
    out = recent_nonoverlapping(days, PickRules(k=5, horizon_days=14))
    assert out[-1] == days[-1] and all((b - a).days == 14 for a, b in zip(out, out[1:]))


def test_choice_rule():
    s = {"CORE": 0.01, "CORE+MACRO": 0.05, "ALL": 0.02}
    assert choose_variant(s, {"CORE": 0.02, "CORE+MACRO": 0.03})["chosen"] == "CORE+MACRO"
    assert choose_variant(s, {"CORE": 0.04, "CORE+MACRO": 0.03})["chosen"] == "CORE"
    r = choose_variant(s, {"CORE": -0.01, "CORE+MACRO": -0.005})
    assert r["chosen"] == "CORE" and r["core_not_predictive"]
    assert choose_variant({"CORE": 0.05, "ALL": 0.01}, {"CORE": -0.1})["chosen"] == "CORE"


def test_skill_point_estimate():
    D = pd.date_range("2022-07-01 16:00", periods=8, freq="7D", tz="UTC")
    rows = [("CORE", d, y, 1.0, 2.0, 2.0, 2.0) for d in D for y in [f"Y{i}" for i in range(1, 9)]]
    df = pd.DataFrame(rows, columns=["variant", "D", "Y", "lookalike", "all", "recent", "random"])
    s = skill(df, "CORE", "all", D[0], D[-1], n_boot=200, block=4, seed=0)
    assert s.loc["MEAN", "skill"] == pytest.approx(0.5) and s.loc["MEAN", "lo"] == pytest.approx(0.5)


def test_jaccard():
    assert jaccard([1, 2, 3], [2, 3, 4]) == pytest.approx(0.5)
