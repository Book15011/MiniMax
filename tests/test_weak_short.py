"""Focused money-math and causality tests for hourly short diagnostics."""
import numpy as np
import pandas as pd
import pytest

from backtest.scoring.weak_short import short_diagnostics

T0 = pd.Timestamp("2026-01-01 12:00", tz="UTC")
CFG = {"fee_rate": .001, "half_spread": .0005, "horizons_hours": [1, 3, 6],
       "take_profit": .004, "stop_loss": .004, "barrier_max_hours": 6,
       "tolerance": 1e-12, "minimum_episodes": 30}
COLS = ["window_start", "hour", "time_utc", "kind", "series", "w_before", "w_after",
        "notional_usd", "fee_usd", "spread_usd"]


def ledger(rows):
    return pd.DataFrame([(T0, h, T0 + pd.Timedelta(hours=h), kind, "BTCUSDT",
                          before, after, 1000., 1., .5)
                         for h, kind, before, after in rows], columns=COLS)


def prices(values):
    return pd.DataFrame({"BTCUSDT": values},
                        index=pd.date_range(T0, periods=len(values), freq="h"))


def run(rows, values, hours=8, cfg=None):
    return short_diagnostics(ledger(rows), prices(values), pd.DatetimeIndex([T0]),
                             hours, CFG if cfg is None else cfg)


def test_two_sided_short_fee_uses_cover_notional_and_spread():
    result = run([(1, "entry", 0., -.3), (7, "decision", -.3, 0.)],
                 [100., 100., 99., 99., 99., 99., 99., 99., 99.])
    e = result["episodes"].iloc[0]
    ratio = (99. * 1.0005) / (100. * .9995)
    expected = 1. - ratio - .001 * (1. + ratio)
    assert e["proxy_net_1h"] == pytest.approx(expected)
    assert e["proxy_net_1h"] != pytest.approx(1. - ratio - .002)
    assert result["windows"].iloc[0]["correct_1h"] == 1


def test_price_fall_smaller_than_cost_is_false_after_cost():
    result = run([(1, "entry", 0., -.3)], [100., 100., 99.9, 99.9, 99.9, 99.9, 99.9, 99.9, 99.9])
    row = result["windows"].iloc[0]
    assert row["correct_1h"] == 0
    assert row["loss_1h"] == 1
    assert row["wrong_direction_1h"] == 0
    assert row["cost_only_loss_1h"] == 1


def test_additions_and_partial_covers_do_not_count_extra_triggers():
    result = run([(1, "entry", 0., -.2), (3, "decision", -.2, -.4),
                  (5, "decision", -.4, -.1), (7, "decision", -.1, 0.)],
                 [100., 100., 99., 98., 97., 96., 95., 96., 96.])
    row = result["windows"].iloc[0]
    assert row["onsets"] == 1
    assert row["closed_episodes"] == 1
    assert len(result["episodes"]) == 1
    e = result["episodes"].iloc[0]
    assert e["reweighted"] is True or bool(e["reweighted"])
    assert e["cover_hour"] == 7
    assert e["duration_hours"] == 6
    assert e["account_short_pnl_available"] is False or not bool(e["account_short_pnl_available"])


def test_guard_onset_is_separately_counted_and_excluded_from_precision():
    result = run([(1, "guard", 0., -.2), (7, "decision", -.2, 0.)],
                 [100., 100., 99., 98., 97., 96., 95., 96., 96.])
    row = result["windows"].iloc[0]
    assert row["onsets"] == 0
    assert row["guard_onsets"] == 1
    assert row["valid_1h"] == 0
    assert len(result["episodes"]) == 1


def test_missing_hourly_price_is_unresolved_and_not_forward_filled():
    result = run([(1, "entry", 0., -.2)],
                 [100., 100., np.nan, 98., 97., 96., 95., 96., 96.])
    row = result["windows"].iloc[0]
    assert row["valid_1h"] == 0
    assert row["unresolved_1h"] == 1
    assert result["episodes"].iloc[0]["status_1h"] == "MISSING_PRICE"


def test_tail_labels_censored_without_using_price_after_window():
    result = run([(7, "decision", 0., -.2)],
                 [100., 100., 99., 98., 97., 96., 95., 96., 95., 80., 60., 40.])
    e = result["episodes"].iloc[0]
    assert e["status_1h"] == "VALID"
    assert e["status_3h"] == "CENSORED"
    assert e["status_6h"] == "CENSORED"
    assert e["terminal_censored"]
    changed = run([(7, "decision", 0., -.2)],
                  [100., 100., 99., 98., 97., 96., 95., 96., 95., 1000., 2000., 3000.])
    pd.testing.assert_frame_equal(result["windows"], changed["windows"])
    pd.testing.assert_frame_equal(result["episodes"], changed["episodes"])


def test_rebound_loss_reports_profit_given_back():
    result = run([(1, "entry", 0., -.2)],
                 [100., 100., 99., 98., 99., 101., 101., 102., 102.])
    row = result["windows"].iloc[0]
    assert row["rebound_losses_6h"] == 1
    assert row["wrong_direction_6h"] == 1
    e = result["episodes"].iloc[0]
    assert e["barrier_label"] == "TAKE_PROFIT_SAMPLED"
    assert e["barrier_intrahour_order_unverified"]
    assert row["barrier_intrahour_ambiguous"] == 1


def test_reopen_creates_distinct_episode():
    result = run([(1, "entry", 0., -.2), (3, "decision", -.2, 0.),
                  (5, "decision", 0., -.2), (8, "decision", -.2, 0.)],
                 [100., 100., 99., 98., 99., 100., 99., 98., 97.])
    assert result["windows"].iloc[0]["onsets"] == 2
    assert len(result["episodes"]) == 2


def test_long_to_short_flip_counts_one_short_onset():
    result = run([(1, "entry", 0., .2), (3, "decision", .2, -.2)],
                 [100., 100., 99., 98., 97., 96., 95., 96., 96.])
    assert result["windows"].iloc[0]["onsets"] == 1


def test_no_shorts_has_zero_counts_and_no_precision_claim():
    result = run([(1, "entry", 0., .2), (7, "decision", .2, 0.)],
                 [100.] * 9)
    assert result["windows"].iloc[0]["onsets"] == 0
    assert result["summary"]["precision_1h"] is None
    assert result["summary"]["fine_resolution_supported"] is False
    assert result["summary"]["account_short_pnl_available"] is False


def test_naive_timestamps_rejected():
    tr = ledger([(1, "entry", 0., -.2)])
    tr["time_utc"] = tr["time_utc"].dt.tz_localize(None)
    with pytest.raises(ValueError, match="timezone"):
        short_diagnostics(tr, prices([100.] * 9), pd.DatetimeIndex([T0]), 8, CFG)


def test_wrong_timestamp_hour_rejected():
    tr = ledger([(1, "entry", 0., -.2)])
    tr.loc[0, "time_utc"] = T0 + pd.Timedelta(hours=2)
    with pytest.raises(ValueError, match="hour"):
        short_diagnostics(tr, prices([100.] * 9), pd.DatetimeIndex([T0]), 8, CFG)


def test_unknown_kind_rejected():
    with pytest.raises(ValueError, match="kind"):
        run([(1, "strategy", 0., -.2)], [100.] * 9)


def test_unknown_schema_rejected():
    tr = ledger([(1, "entry", 0., -.2)]).drop(columns=["spread_usd"])
    with pytest.raises(ValueError, match="schema"):
        short_diagnostics(tr, prices([100.] * 9), pd.DatetimeIndex([T0]), 8, CFG)


def test_unsorted_and_duplicate_hourly_prices_rejected():
    x = prices([100.] * 9)
    for bad in (x.iloc[::-1], pd.concat([x, x.iloc[-1:]])):
        with pytest.raises(ValueError, match="monotonic|unique"):
            short_diagnostics(ledger([(1, "entry", 0., -.2)]), bad, pd.DatetimeIndex([T0]), 8, CFG)


def test_short_before_any_onset_rejected_as_inherited_state():
    with pytest.raises(ValueError, match="cash-start"):
        run([(1, "entry", -.2, 0.)], [100.] * 9)


def test_repeated_onset_without_cover_rejected():
    with pytest.raises(ValueError, match="ledger"):
        run([(1, "entry", 0., -.2), (3, "decision", 0., -.2)], [100.] * 9)


def test_proxy_configuration_must_be_predeclared_and_valid():
    for key, value in (("half_spread", -.1), ("fee_rate", 1.), ("horizons_hours", [1, 1]),
                       ("take_profit", 0), ("stop_loss", 0), ("minimum_episodes", 0)):
        bad = dict(CFG, **{key: value})
        with pytest.raises(ValueError):
            run([(1, "entry", 0., -.2)], [100.] * 9, cfg=bad)


def test_boundary_cover_is_completed_but_tail_horizon_censored():
    result = run([(7, "decision", 0., -.2), (8, "decision", -.2, 0.)],
                 [100., 100., 99., 98., 97., 96., 95., 96., 95.])
    e = result["episodes"].iloc[0]
    assert not e["terminal_censored"]
    assert e["cover_hour"] == 8
    assert e["cover_proxy_net"] > 0
    assert e["status_3h"] == "CENSORED"



def test_no_short_episode_export_still_has_auditable_schema():
    result = run([(1, "entry", 0., .2)], [100.] * 9)
    assert result["episodes"].empty
    assert {"window_start", "entry_time", "proxy_net_1h", "status_6h"}.issubset(result["episodes"].columns)


def test_fixed_labels_are_directional_probes_even_if_model_already_covered():
    result = run([(1, "entry", 0., -.2), (2, "decision", -.2, 0.)],
                 [100., 100., 99., 100., 101., 102., 103., 104., 105.])
    episode = result["episodes"].iloc[0]
    assert episode["cover_proxy_net"] > 0
    assert episode["proxy_net_6h"] < 0
    assert result["windows"].iloc[0]["cover_proxy_wins"] == 1
    assert result["windows"].iloc[0]["loss_6h"] == 1
