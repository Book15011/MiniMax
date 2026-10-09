"""Independent review of one-sided bound direction and causal selection."""
import numpy as np
import pandas as pd
import pytest
from backtest.scoring import weak_stats


def test_asymmetric_lower_bound_uses_upper_estimation_error_tail():
    # Cash incumbent is exact zero; the candidate has returns [0, 0, 10%].
    # Six resamples omit the gain; four over-represent it. Its upper bootstrap
    # estimation error is 10%-3.333%, so the centered one-sided lower bound is
    # 3.333%-(10%-3.333%)=-3.333%. Reversing the error's sign wrongly gives zero.
    x = np.array([[[0.], [0.], [0.]], [[0.], [0.], [.1]]])
    d = np.zeros((100, 3))
    d[:60, 0] = 1.; d[60:, 2] = 1.
    out = weak_stats.simultaneous_bounds(x, 0, d, .9)
    assert out["cash_family_lower"][1, 0] == pytest.approx(-1/30., abs=1e-14)
    assert out["delta_family_lower"][1, 0] == pytest.approx(-1/30., abs=1e-14)
    assert out["family_lower"][0, 0] == 0.


def test_exact_paired_identical_contrast_stays_zero():
    starts = pd.date_range("2020-01-01", periods=16, freq="90D", tz="UTC")
    d, _ = weak_stats.clustered_draws(starts, 1000, 23)
    vector = np.linspace(-.04, .08, len(starts))
    x = np.stack([vector, vector])[:, :, None]
    out = weak_stats.simultaneous_bounds(x, 0, d, .9)
    np.testing.assert_array_equal(out["delta"], np.zeros((2, 1)))
    np.testing.assert_array_equal(out["delta_family_lower"], np.zeros((2, 1)))


def test_one_joint_penalty_includes_all_contexts():
    starts = pd.date_range("2020-01-01", periods=16, freq="90D", tz="UTC")
    d, _ = weak_stats.clustered_draws(starts, 1000, 29)
    a = np.linspace(-.1, .2, len(starts))
    x = np.stack([np.zeros_like(a), a])[:, :, None]
    original = weak_stats.simultaneous_bounds(x, 0, d, .9)
    extra = np.concatenate([x, x[:, ::-1, :]], axis=2)
    joint = weak_stats.simultaneous_bounds(extra, 0, d, .9)
    assert joint["family_quantile"] >= original["family_quantile"]
    assert joint["cash_family_lower"][1, 0] <= original["cash_family_lower"][1, 0]


@pytest.mark.parametrize("change", ["negative", "nan", "inf", "empty", "one", "zero"])
def test_invalid_resampling_mass_fails_closed(change):
    x = np.array([[[0.], [0.], [0.]], [[0.], [0.], [.1]]])
    d = np.full((100, 3), 1/3.)
    if change == "negative": d[0] = [1.1, -.1, 0.]
    elif change == "nan": d[0, 0] = np.nan
    elif change == "inf": d[0, 0] = np.inf
    elif change == "empty": d = d[:0]
    elif change == "one": d = d[:1]
    elif change == "zero": d[0] = 0.
    with pytest.raises(ValueError):
        weak_stats.simultaneous_bounds(x, 0, d, .9)


@pytest.mark.parametrize("incumbent", [-1, 2, .5, True])
def test_invalid_incumbent_index_fails_closed(incumbent):
    x = np.zeros((2, 3, 1))
    d = np.full((100, 3), 1/3.)
    with pytest.raises(ValueError):
        weak_stats.simultaneous_bounds(x, incumbent, d, .9)


def test_quarter_draws_do_not_accept_missing_timestamp():
    starts = pd.DatetimeIndex(["2020-01-01 00:00Z", "2020-04-01 00:00Z", pd.NaT])
    with pytest.raises(ValueError):
        weak_stats.clustered_draws(starts, 1000, 29)


def scenario_fixture():
    starts = pd.date_range("2023-01-01 12:00", periods=8, freq="30D", tz="UTC")
    features = pd.DataFrame({
        "btc_ret48": [-.01, -.02, .03, -.3, -.01, -.02, -.03, -.04],
        "btc_ret24": [0., 0., 0., 0., .03, 0., 0., 0.],
        "breadth48": [.2, .3, .2, .2, .2, .5, .2, .2],
    }, index=starts)
    cfg = {"features": {"FAST": ["btc_ret48", "btc_ret24"], "BREADTH": ["breadth48"]},
           "embargo_hours": 48, "weak": {"ret48_min": -.1, "ret48_max": 0.,
                  "ret24_max": .01, "breadth_max": .4},
           "positive": {"ret48_min": 0., "ret48_max": .1, "breadth_min": .6},
           "lookalikes": {"k": 2, "min_separation_days": 14,
                         "max_per_span": 3, "span_days": 90}}
    return features, features.iloc[0], starts[6] + pd.Timedelta(hours=287), cfg


def test_selection_uses_mature_past_states_and_never_future_outcomes(monkeypatch):
    f, query, asof, cfg = scenario_fixture()
    seen = []
    def matcher(pool, query, groups, rules):
        seen.append(pool.index.copy())
        return pd.DataFrame({"t0": pool.index[:rules.k], "distance": [.1, .2]})
    monkeypatch.setattr(weak_stats, "match_windows", matcher)
    first = weak_stats.select_cases(f, query, asof, 240, cfg)
    # Any realized future returns, labels or candidate returns must be inert.
    augmented = f.assign(future_btc_return=[.99, -.99, .99, -.99, .99, -.99, .99, -.99],
                         future_candidate_return=np.arange(8) * 100.,
                         future_rebound=True)
    second = weak_stats.select_cases(augmented, query, asof, 240, cfg)
    pd.testing.assert_frame_equal(first, second)
    assert list(seen[0]) == list(f.index[:2])
    # Row6 remains immature by one hour at the explicit 48h embargo;
    # row7 is in the future. Other rows fail the observed-state definition.
    assert f.index[6] not in seen[0] and f.index[7] not in seen[0]


def test_unknown_selection_mode_fails_closed(monkeypatch):
    f, query, asof, cfg = scenario_fixture()
    with pytest.raises(ValueError, match="mode"):
        weak_stats.select_cases(f, query, asof, 240, cfg, mode="typo")


def test_tail_mean_fractional_boundary_includes_partial_observation():
    assert weak_stats.tail_mean([-.1, -.05, .02], .5) == pytest.approx(-1/12.)


def test_overlapping_cross_quarter_replays_share_merged_cluster():
    starts = pd.DatetimeIndex(["2020-03-30 12:00Z", "2020-04-02 12:00Z",
                               "2020-07-01 12:00Z", "2020-10-01 12:00Z"])
    d, n = weak_stats.clustered_draws(starts, 1000, 29, hours=240)
    assert n == 3  # Q1/Q2 joined, Q3 and Q4 remain separate.
    np.testing.assert_array_equal(d[:, 0], d[:, 1])
    np.testing.assert_allclose(d.sum(axis=1), 1.)


def test_cluster_merging_is_independent_of_input_order():
    starts = pd.DatetimeIndex(["2020-03-30 12:00Z", "2020-04-02 12:00Z",
                               "2020-07-01 12:00Z", "2020-10-01 12:00Z"])
    permutation = np.array([3, 1, 0, 2])
    original, n = weak_stats.clustered_draws(starts, 1000, 29)
    shuffled, n2 = weak_stats.clustered_draws(starts[permutation], 1000, 29)
    assert n == n2
    np.testing.assert_array_equal(shuffled, original[:, permutation])


def test_overlaps_can_remove_bootstrap_support_and_fail_closed():
    starts = pd.DatetimeIndex(["2020-03-30 12:00Z", "2020-04-02 12:00Z"])
    with pytest.raises(ValueError, match="two"):
        weak_stats.clustered_draws(starts, 1000, 29)


@pytest.mark.parametrize("hours", [0, -1, 240.5, True])
def test_invalid_replay_hours_rejected(hours):
    starts = pd.DatetimeIndex(["2020-01-01 12:00Z", "2020-04-01 12:00Z"])
    with pytest.raises(ValueError):
        weak_stats.clustered_draws(starts, 1000, 29, hours=hours)


def test_nonconstant_returns_cannot_claim_exact_zero_bootstrap_error():
    x = np.array([[[0.], [0.], [0.]], [[0.], [.1], [0.]]])
    d = np.full((100, 3), 1/3.)
    with pytest.raises(ValueError, match="degenerate"):
        weak_stats.simultaneous_bounds(x, 0, d, .9)


@pytest.mark.parametrize("groups", [{}, {"UNKNOWN": ["btc_ret48"]},
                                    {"FAST": ["future_return"]},
                                    {"FAST": []}])
def test_unknown_or_empty_feature_groups_fail_closed(groups):
    f, query, asof, cfg = scenario_fixture()
    with pytest.raises(ValueError, match="group"):
        weak_stats.select_cases(f, query, asof, 240, cfg, groups=groups)


def test_predeclared_group_subset_is_allowed_and_missing_query_breadth_stays_missing(monkeypatch):
    f, query, asof, cfg = scenario_fixture()
    query = query.copy(); query["breadth48"] = np.nan
    def matcher(pool, query, groups, rules):
        return pd.DataFrame({"t0": pool.index[:rules.k], "distance": [.1, .2]})
    monkeypatch.setattr(weak_stats, "match_windows", matcher)
    result = weak_stats.select_cases(f, query, asof, 240, cfg,
                                    groups={"FAST": cfg["features"]["FAST"]})
    assert "breadth48" not in result.columns
    assert pd.isna(query["breadth48"])


@pytest.mark.parametrize("shape", [(0, 3, 1), (2, 0, 1), (2, 3, 0)])
def test_empty_model_window_or_context_axis_rejected(shape):
    with pytest.raises(ValueError):
        weak_stats.simultaneous_bounds(np.empty(shape), 0,
                                       np.ones((100, shape[1])), .9)


def test_constant_weighted_support_remains_exact_despite_irrelevant_values():
    x = np.array([[[0.], [0.], [99.]], [[.1], [.1], [-99.]]])
    d = np.zeros((100, 3)); d[:50, 0] = 1.; d[50:, 1] = 1.
    weights = np.array([[.5], [.5], [0.]])
    out = weak_stats.simultaneous_bounds(x, 0, d, .9, weights=weights)
    assert out["cash_family_lower"][1, 0] == pytest.approx(.1)
    assert out["delta_family_lower"][1, 0] == pytest.approx(.1)


@pytest.mark.parametrize("k", [0, -1, 2.5, True])
def test_invalid_case_count_cannot_fall_back_to_default(k):
    f, query, asof, cfg = scenario_fixture()
    with pytest.raises(ValueError, match="case count"):
        weak_stats.select_cases(f, query, asof, 240, cfg, k=k)
