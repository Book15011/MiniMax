"""Independent numeric and causal checks for the Book conditional evaluator."""
import numpy as np
import pandas as pd
import pytest

from research.book.regime_eval.metrics import (
    continuation_returns,
    eligible_pool,
    grouped_bootstrap_delta,
    mix_weights,
    normalized_weights,
    weighted_crps,
    weighted_quantile,
)


@pytest.mark.parametrize("weights", [
    [],
    [0.0, 0.0],
    [-1.0, 2.0],
    [np.nan, 1.0],
    [np.inf, 1.0],
])
def test_weights_reject_invalid_probability_mass(weights):
    with pytest.raises(ValueError):
        normalized_weights(weights)


def test_weights_allow_zero_mass_rows_and_are_scale_invariant():
    actual = normalized_weights([0.0, 2.0, 6.0])
    np.testing.assert_allclose(actual, [0.0, 0.25, 0.75])
    np.testing.assert_allclose(actual, normalized_weights([0.0, 20.0, 60.0]))


def test_remaining_return_keeps_accrued_losses_and_only_closes_terminal_inventory():
    equity = np.array([[1.0, 0.8, 0.88], [1.0, 1.2, 1.08]])
    gross = np.array([[0.0, 0.7, 0.5], [0.0, 0.4, 1.2]])
    actual = continuation_returns(equity, gross, prefix_hours=1, close_fee=0.001)
    expected = np.array([0.88 * (1 - 0.001 * 0.5) / 0.8 - 1,
                         1.08 * (1 - 0.001 * 1.2) / 1.2 - 1])
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-14)
    # A larger cash account does not change percentage continuation returns.
    np.testing.assert_allclose(
        continuation_returns(equity * 100_000, gross, 1, 0.001), expected,
        rtol=0, atol=1e-14,
    )
    # Recompose with the original prefix, rather than erasing the initial loss.
    recomposed = (equity[:, 1] / equity[:, 0]) * (1 + actual) - 1
    expected_round = equity[:, -1] * (1 - 0.001 * gross[:, -1]) / equity[:, 0] - 1
    np.testing.assert_allclose(recomposed, expected_round, rtol=0, atol=1e-14)


def test_cash_continuation_does_not_invent_a_liquidation_fee():
    equity = np.ones((2, 5))
    np.testing.assert_array_equal(
        continuation_returns(equity, np.zeros_like(equity), 2, 0.001), [0.0, 0.0]
    )


@pytest.mark.parametrize("prefix", [-1, 3, 4])
def test_prefix_requires_a_real_remaining_horizon(prefix):
    with pytest.raises(ValueError):
        continuation_returns(np.ones((2, 4)), np.zeros((2, 4)), prefix, 0.001)


@pytest.mark.parametrize("equity,gross", [
    (np.ones(4), np.zeros(4)),
    (np.ones((2, 4)), np.zeros((1, 4))),
    (np.array([[1.0, 0.0, 1.0]]), np.zeros((1, 3))),
    (np.array([[1.0, -0.5, 1.0]]), np.zeros((1, 3))),
    (np.array([[1.0, np.nan, 1.0]]), np.zeros((1, 3))),
    (np.ones((1, 3)), np.array([[0.0, -0.5, 0.0]])),
    (np.ones((1, 3)), np.array([[0.0, np.inf, 0.0]])),
])
def test_continuation_rejects_corrupt_or_misaligned_accounts(equity, gross):
    with pytest.raises(ValueError):
        continuation_returns(equity, gross, 1, 0.001)


@pytest.mark.parametrize("fee", [-0.001, np.nan, np.inf])
def test_continuation_rejects_invalid_cost_parameters(fee):
    with pytest.raises(ValueError):
        continuation_returns(np.ones((1, 3)), np.zeros((1, 3)), 1, fee)


@pytest.mark.parametrize("q,expected", [
    (0.0, -3.0), (0.2, -3.0), (0.20001, 1.0), (0.5, 1.0), (1.0, 5.0),
])
def test_weighted_quantile_is_inverse_cdf_without_interpolation(q, expected):
    assert weighted_quantile([5.0, -3.0, 1.0], [5.0, 2.0, 3.0], q) == expected


def test_zero_weight_extremes_do_not_change_quantiles():
    assert weighted_quantile([-999.0, 2.0, 999.0], [0.0, 1.0, 0.0], 0.0) == 2.0
    assert weighted_quantile([-999.0, 2.0, 999.0], [0.0, 1.0, 0.0], 1.0) == 2.0


def test_crps_uses_the_full_weighted_predictive_distribution():
    # E|X-y| - 0.5 E|X-X'|: X=-1/+1 with mass 0.5 each, y=0.
    assert weighted_crps([-1.0, 1.0], [1.0, 1.0], 0.0) == pytest.approx(0.5)
    # Nonuniform mass 0.25/0.75: 1 - (0.25*0.75*2) = 0.625.
    assert weighted_crps([-1.0, 1.0], [1.0, 3.0], 0.0) == pytest.approx(0.625)
    assert weighted_crps([7.0], [1.0], 7.0) == pytest.approx(0.0)
    assert weighted_crps([7.0], [1.0], 5.0) == pytest.approx(2.0)


def test_crps_is_translation_and_weight_scale_invariant():
    a = weighted_crps([-1.0, 1.0], [1.0, 3.0], 0.0)
    b = weighted_crps([99.0, 101.0], [10.0, 30.0], 100.0)
    assert a == pytest.approx(b)


def test_training_pool_requires_completed_outcomes_and_embargo():
    starts = pd.to_datetime([
        "2026-01-01 00:00Z",
        "2026-01-01 01:00Z",
        "2026-01-02 00:00Z",
    ], utc=True)
    query = pd.Timestamp("2026-01-03 00:00Z")
    # With a 24h label and 24h embargo, only the exact-boundary first label has matured.
    actual = eligible_pool(starts, query, horizon_hours=24, embargo_hours=24)
    np.testing.assert_array_equal(np.asarray(actual), [True, False, False])
    # An otherwise nearly matching future state cannot join the historical pool.
    later = starts.append(pd.DatetimeIndex([pd.Timestamp("2026-01-04 00:00Z")]))
    actual_later = eligible_pool(later, query, horizon_hours=24, embargo_hours=24)
    np.testing.assert_array_equal(np.asarray(actual_later), [True, False, False, False])


def test_uniform_shrinkage_preserves_support_and_known_mass():
    weights = mix_weights(5, picked=[0, 4], alpha=0.6)
    np.testing.assert_allclose(weights, [0.38, 0.08, 0.08, 0.08, 0.38])
    assert sum(weights) == pytest.approx(1.0)
    np.testing.assert_allclose(mix_weights(5, [0, 4], 0.0), np.full(5, 0.2))


@pytest.mark.parametrize("n,picked,alpha", [
    (0, [0], 0.5), (5, [5], 0.5), (5, [-1], 0.5),
    (5, [0, 0], 0.5), (5, [0], -0.1), (5, [0], 1.1),
])
def test_shrinkage_rejects_invalid_indices_or_mixture(n, picked, alpha):
    with pytest.raises(ValueError):
        mix_weights(n, picked, alpha)


def test_paired_bootstrap_is_deterministic_and_identical_models_cancel():
    starts = pd.date_range("2025-01-01", periods=120, freq="D", tz="UTC")
    delta = np.sin(np.arange(120)) / 100.0
    weights = np.arange(1, 121, dtype=float)
    a = grouped_bootstrap_delta(starts, delta, weights, reps=400, seed=17, level=0.9)
    b = grouped_bootstrap_delta(starts, delta, weights, reps=400, seed=17, level=0.9)
    assert a == b
    assert a["mean"] == pytest.approx(np.dot(delta, weights / weights.sum()))
    zero = grouped_bootstrap_delta(starts, np.zeros(120), weights, reps=400, seed=17, level=0.9)
    assert zero["mean"] == pytest.approx(0.0)
    assert zero["lower"] == pytest.approx(0.0)
    assert zero["upper"] == pytest.approx(0.0)


def test_month_clusters_do_not_treat_overlapping_daily_rows_as_independent():
    # Thirty-one correlated positive rows are ONE January cluster, versus ONE negative February cluster.
    starts = pd.date_range("2025-01-01", periods=32, freq="D", tz="UTC")
    delta = np.r_[np.full(31, 0.1), -0.1]
    result = grouped_bootstrap_delta(starts, delta, np.ones(32), reps=1000, seed=11, level=0.9)
    assert result["mean"] == pytest.approx(30 * 0.1 / 32)
    assert result["lower"] == pytest.approx(-0.1)
    assert result["upper"] == pytest.approx(0.1)


def _short_events(episode_ids):
    signal = pd.Timestamp("2026-10-08 00:00:00Z")
    rows = []
    for episode in episode_ids:
        rows.append({
            "episode_id": episode,
            "signal_time": signal,
            "entry_time": signal + pd.Timedelta(seconds=6),
            "cover_signal_time": signal + pd.Timedelta(minutes=5),
            "cover_time": signal + pd.Timedelta(minutes=5, seconds=6),
            "entry_bid": 100.0,
            "cover_ask": 98.0,
            "entry_lag_seconds": 6.0,
            "cover_lag_seconds": 6.0,
        })
    return pd.DataFrame(rows)


def test_short_net_profit_charges_both_actual_traded_notionals():
    events = _short_events(["one", "two"])
    events.loc[1, "cover_ask"] = 101.0
    # Profit per original short notional: (100-cover)/100 - fee*(1+cover/100).
    expected = ((0.02 - 0.001 * 1.98) + (-0.01 - 0.001 * 2.01)) / 2
    assert result["mean_net"] == pytest.approx(expected)
    assert result["n_events"] == 2
    assert result["n_episodes"] == 2
    assert result["eligible"] is True


def test_short_evidence_counts_independent_episodes_not_correlated_trades():
    assert result["n_events"] == 3
    assert result["n_episodes"] == 1
    assert result["eligible"] is False


def test_cover_cannot_fill_at_the_same_close_that_reveals_the_signal():
    events = _short_events(["one"])
    events.loc[0, "cover_time"] = events.loc[0, "cover_signal_time"]
    with pytest.raises(ValueError):


def test_entry_cannot_precede_observable_signal_plus_latency():
    events = _short_events(["one"])
    events.loc[0, "entry_time"] = events.loc[0, "signal_time"] + pd.Timedelta(seconds=5)
    with pytest.raises(ValueError):


@pytest.mark.parametrize("field,bad_price", [
    ("entry_bid", 0.0), ("entry_bid", -100.0), ("cover_ask", 0.0),
    ("cover_ask", -1.0), ("entry_bid", np.nan), ("cover_ask", np.inf),
])
def test_short_metrics_reject_non_executable_prices(field, bad_price):
    events = _short_events(["one"])
    events.loc[0, field] = bad_price
    with pytest.raises(ValueError):


def test_match_uses_only_allowlisted_market_state_and_ignores_future_outcomes():
    from research.book.regime_eval.features import match_windows
    from src.validation.selection import PickRules

    at = pd.date_range("2024-01-01 12:00", periods=6, freq="30D", tz="UTC")
    pool = pd.DataFrame({
        "btc_ret24": [0.12, -0.30, 0.08, 0.20, 0.00, 0.90],
        "future_return": [0.5, -0.1, -0.4, 0.8, 0.9, -0.7],
        "R_liq": [-0.9, 0.8, 0.7, -0.6, 0.5, 0.4],
    }, index=at)
    groups = {"FAST": ["btc_ret24"]}
    rules = PickRules(k=3, min_separation_days=14, span_days=90, max_per_span=3)
    query = pd.Series({"btc_ret24": 0.10})
    reference = match_windows(pool, query, groups, rules)
    assert len(reference) == 3
    assert {"t0", "distance"}.issubset(reference.columns)
    changed = pool.copy()
    changed["future_return"] = [np.nan, 9e9, -9e9, np.nan, 8e9, -8e9]
    changed["R_liq"] = pool["R_liq"].iloc[::-1].to_numpy()
    query_with_outcomes = pd.Series({
        "btc_ret24": 0.10, "future_return": -1e12, "R_liq": np.nan,
    })
    actual = match_windows(changed, query_with_outcomes, groups, rules)
    pd.testing.assert_frame_equal(
        reference[["t0", "distance"]].reset_index(drop=True),
        actual[["t0", "distance"]].reset_index(drop=True),
    )


def _two_coin_feature_fixture(min_breadth_coins=2):
    from copy import deepcopy
    from src.config import load_config

    cfg = deepcopy(load_config())
    validation_cfg = deepcopy(cfg["validation"])
    validation_cfg["grid_hour_utc"] = 12
    validation_cfg["universe"]["min_history_days"] = 1
    validation_cfg["universe"]["top_n"] = 2
    cfg["book_regime_eval"]["state_grid_hour_utc"] = 12
    cfg["book_regime_eval"]["min_breadth_coins"] = min_breadth_coins
    at = pd.date_range("2024-01-01 00:00", periods=420 * 24 + 1, freq="h", tz="UTC")
    h = np.arange(len(at), dtype=float)
    close = pd.DataFrame({
        "BTCUSDT": 30_000 * np.exp(0.000025 * h + 0.003 * np.sin(h / 13)),
        "ETHUSDT": 2_000 * np.exp(0.000020 * h + 0.004 * np.sin(h / 17)),
    }, index=at)
    qv = pd.DataFrame({
        "BTCUSDT": 1_000_000 + 50_000 * np.sin(h / 31),
        "ETHUSDT": 800_000 + 40_000 * np.sin(h / 23),
    }, index=at)
    states = pd.DatetimeIndex([at[400 * 24 + 12]])
    return close, qv, states, validation_cfg, cfg


def test_features_at_anchor_are_unchanged_by_future_price_and_volume_mutations():
    from research.book.regime_eval.features import build_features

    close, qv, states, validation_cfg, cfg = _two_coin_feature_fixture()
    anchor = states[0]
    reference = build_features(close, qv, states, validation_cfg, cfg)
    assert reference.index.equals(states)
    selected = [feature for group in cfg["book_regime_eval"]["features"].values() for feature in group]
    assert set(selected).issubset(reference.columns)
    assert np.isfinite(reference[selected].to_numpy()).all()
    future_close, future_qv = close.copy(), qv.copy()
    after = close.index > anchor
    future_close.loc[after, "BTCUSDT"] *= 0.01
    future_close.loc[after, "ETHUSDT"] *= 100.0
    future_qv.loc[after, "BTCUSDT"] *= 1e-8
    future_qv.loc[after, "ETHUSDT"] *= 1e8
    actual = build_features(future_close, future_qv, states, validation_cfg, cfg)
    pd.testing.assert_frame_equal(reference, actual)


def test_breadth_quality_guard_marks_too_small_universe_unusable_and_exports_counts():
    from research.book.regime_eval.features import build_features

    close, qv, states, validation_cfg, cfg = _two_coin_feature_fixture(min_breadth_coins=20)
    result = build_features(close, qv, states, validation_cfg, cfg)
    anchor = states[0]
    assert pd.isna(result.loc[anchor, "breadth48"])
    assert pd.isna(result.loc[anchor, "alt_minus_btc48"])
    assert result.loc[anchor, "universe_n"] == 2
    assert result.loc[anchor, "breadth_valid_n"] == 2


def test_circular_block_bootstrap_is_deterministic_and_zero_differences_cancel():
    from research.book.regime_eval.metrics import block_bootstrap_interval

    values = np.array([0.01, 0.02, -0.01, 0.0, -0.03, 0.02, 0.01, -0.02])
    a = block_bootstrap_interval(values, block=4, reps=400, seed=19, level=0.9)
    b = block_bootstrap_interval(values, block=4, reps=400, seed=19, level=0.9)
    assert a == b
    assert a["mean"] == pytest.approx(values.mean())
    zeros = block_bootstrap_interval(np.zeros(20), block=4, reps=400, seed=19, level=0.9)
    assert zeros["mean"] == pytest.approx(0.0)
    assert zeros["lower"] == pytest.approx(0.0)
    assert zeros["upper"] == pytest.approx(0.0)


@pytest.mark.parametrize("values,block", [
    ([], 4),
    ([0.0, np.nan], 4),
    ([0.0, np.inf], 4),
    ([0.0, 1.0], 0),
    ([0.0, 1.0], -1),
])
def test_circular_block_bootstrap_rejects_invalid_observations_or_block(values, block):
    from research.book.regime_eval.metrics import block_bootstrap_interval

    with pytest.raises(ValueError):
        block_bootstrap_interval(values, block=block, reps=400, seed=19, level=0.9)


def test_market_outcome_drawdown_measures_peak_to_trough_even_after_round_trip():
    from research.book.regime_eval.features import market_outcomes

    at = pd.date_range("2026-01-01 12:00", periods=3, freq="h", tz="UTC")
    close = pd.DataFrame({"BTCUSDT": [100.0, 120.0, 100.0]}, index=at)
    cfg = {"minimum_hour_coverage": 0.98, "annual_hours": 8760}
    result = market_outcomes(
        close, pd.DatetimeIndex([at[0]]), prefix_hours=0, horizon_hours=2, cfg=cfg,
    )
    assert result.loc[at[0], "future_return"] == pytest.approx(0.0)
    # Finishing at the starting price still includes a 120 -> 100 drawdown.
    assert result.loc[at[0], "future_drawdown"] == pytest.approx(1.0 / 6.0)


def test_matching_rejects_outcomes_disguised_under_an_unapproved_alias():
    from research.book.regime_eval.features import match_windows
    from src.validation.selection import PickRules

    at = pd.date_range("2024-01-01 12:00", periods=3, freq="30D", tz="UTC")
    pool = pd.DataFrame({
        "btc_ret24": [0.12, -0.30, 0.08],
        "foo_outcome": [0.5, -0.1, -0.4],
    }, index=at)
    query = pd.Series({"btc_ret24": 0.10, "foo_outcome": 0.9})
    with pytest.raises(ValueError):
        match_windows(
            pool, query, {"FAST": ["btc_ret24", "foo_outcome"]},
            PickRules(k=1),
        )


def test_walkforward_validation_counts_query_column_and_checks_prior_only_pool():
    from research.book.regime_eval.validation import validate_matching

    starts = pd.date_range("2010-01-01 12:00", periods=160, freq="14D", tz="UTC")
    x = np.arange(len(starts), dtype=float)
    features = pd.DataFrame({"btc_ret24": np.sin(x / 7) / 10}, index=starts)
    outcomes = pd.DataFrame({
        "future_return": np.sin(x / 11) / 5,
        "future_drawdown": 0.02 + np.abs(np.sin(x / 13)) / 10,
        "future_vol": 0.20 + np.abs(np.cos(x / 17)) / 5,
    }, index=starts)
    queries = pd.to_datetime(["2020-01-01 12:00Z", "2021-01-01 12:00Z"], utc=True)
    states = pd.DataFrame({"btc_ret24": [0.03, -0.04]}, index=queries)
    observations = pd.DataFrame({
        "future_return": [0.04, -0.03],
        "future_drawdown": [0.06, 0.09],
        "future_vol": [0.25, 0.33],
    }, index=queries)
    cfg = {
        "lookalikes": {"k": 3, "min_separation_days": 14, "span_days": 90, "max_per_span": 3},
        "horizon_hours": 336,
        "embargo_hours": 24,
        "features": {"FAST": ["btc_ret24"]},
        "alpha_candidates": [0.0, 0.25],
        "walkforward": {
            "min_pool": 50, "min_queries": 1,
            "screen_end": "2020-06-30 23:59:59+00:00",
            "bootstrap_block_queries": 1,
        },
        "bootstrap": {"reps": 50, "seed": 23, "level": 0.9},
        "gates": {"min_confirm_skill_lower": 0.0, "max_brier_degradation": 0.0},
    }
    frame, summary = validate_matching(
        features, states, outcomes, observations, queries, cfg,
    )
    assert {"query", "phase", "alpha"}.issubset(frame.columns)
    assert len(frame) == 4
    assert set(frame["query"]) == set(queries)
    assert set(frame["alpha"]) == {0.0, 0.25}
    assert summary["queries"] == {"SCREEN": 1, "CONFIRM": 1}
    assert summary["statistical_gates"]["prior_only"] is True
    assert (
        frame["pool_max_end"] <= frame["query"] - pd.Timedelta(hours=24)
    ).all()


@pytest.mark.parametrize("missing,confirmed,statistical,stable,expected", [
    (False,True,True,True,0.5),
    (True,True,True,True,0.0),
    (False,False,True,True,0.0),
    (False,True,False,True,0.0),
    (False,True,True,False,0.0),
])
def test_adaptive_activation_keeps_failed_coverage_archive_and_forecast_gates(
        missing,confirmed,statistical,stable,expected):
    from research.book.regime_eval.validation import activation_decision
    d=pd.Timestamp("2026-10-08 12:00Z")
    q=pd.Series({"btc_ret24":-.02,"breadth48":np.nan if missing else 0.0,
                 "universe_n":30,"breadth_valid_n":29 if missing else 30})
    result=activation_decision(
        {"statistical_pass":statistical,"chosen_on_screen":.5},
        q,{"FAST":["btc_ret24"],"BREADTH":["breadth48"]},
        d,d if confirmed else d-pd.Timedelta(hours=12),stable)
    assert result["active_alpha"]==expected
    assert result["current_query_coverage"] is (not missing)
    assert result["adaptive_pass"] is (expected>0)
    if missing: assert result["current_missing_features"]==["breadth48"]

def test_unavailable_current_match_can_use_baseline_without_fake_selected_windows():
    np.testing.assert_allclose(mix_weights(4,[],0.0),np.full(4,.25))


def test_registry_snapshot_keeps_checkpoint_models_and_rejects_score_tampering(tmp_path,monkeypatch):
    import hashlib,json
    from pathlib import Path
    from research.book.regime_eval import run

    monkeypatch.setattr(run,"safe_path",lambda value:Path(value))
    out=tmp_path/"out";out.mkdir()
    cache=tmp_path/"cache";cache.mkdir()
    score=tmp_path/"score.json"
    score.write_text(json.dumps({"per_window":{"start":["2020-01-01T12:00:00Z"]},
                                "data":{"version":"same"},"inputs_sha256":{}}))
    entry={"ts":"2026-10-01T00:00:00Z","full":True,"tool_version":"v1",
           "model":"incumbent","candidate":True,"eligible":True,"run_key":"original",
           "score_json":str(score),"score_sha256":hashlib.sha256(score.read_bytes()).hexdigest(),
           "gates":{"coverage":True}}
    registry=tmp_path/"registry.jsonl";registry.write_text(json.dumps(entry)+"\n")
    c={"registry":str(registry),"cache_dir":str(cache),"incumbent":"incumbent","tool_version":"v1"}
    first=run.frozen_registered(c,out)
    run.dump(out/"model_inventory.json",{"registered":first[3]})
    newer={**entry,"ts":"2026-10-02T00:00:00Z","run_key":"new-publication"}
    registry.write_text(json.dumps(entry)+"\n"+json.dumps(newer)+"\n")
    assert run.frozen_registered(c,out)[0]["incumbent"]["run_key"]=="original"
    score.write_text(score.read_text()+" ")
    with pytest.raises(ValueError,match="score hash mismatch"):
        run.frozen_registered(c,out)
