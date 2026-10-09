"""Remaining-horizon net equity, competition CS, and clock-boundary checks."""
import copy
import numpy as np
import pandas as pd
import pytest
from backtest.scoring.weak_risk import remainder_risk


@pytest.fixture
def scoring():
    return {
        "hours_per_day": 24, "liquidation_cost": .001,
        "composite": {"sortino": .4, "sharpe": .3, "calmar": .3},
        "variants": {"V1": {"returns": "daily", "annualize": 1, "calmar": "mean"}},
        "conventions": {"FLOORED": {"s_daily": .001, "dd_daily": .001,
            "s_hourly": .000204124145231931, "dd_hourly": .000204124145231931,
            "mdd": .002}},
    }


def arrays(n=1):
    e = np.ones((n, 337), dtype=float) * 100.
    g = np.zeros_like(e)
    starts = pd.date_range("2024-01-01 12:00", periods=n, freq="D", tz="UTC")
    return e, g, starts


def reference_cs(curve, offsets):
    daily = curve[offsets[1:]] / curve[offsets[:-1]] - 1.
    m = daily.mean()
    s = daily.std(ddof=1)
    dd = np.sqrt(np.mean(np.minimum(daily, 0.) ** 2))
    mdd = (1. - curve / np.maximum.accumulate(curve)).max()
    sharpe, sortino, calmar = m / max(s, .001), m / max(dd, .001), m / max(mdd, .002)
    return .4 * sortino + .3 * sharpe + .3 * calmar, sharpe, sortino, calmar, mdd


def test_net_terminal_return_charged_once_and_input_unchanged(scoring):
    e, g, starts = arrays(2)
    e[0] = np.linspace(100., 140., 337)
    e[1] = np.linspace(100., 80., 337)
    g[:, 240] = [.75, 1.2]
    old_e, old_g, old_sc = e.copy(), g.copy(), copy.deepcopy(scoring)
    out = remainder_risk(e, g, starts, 96, 144, scoring)
    expected = e[:, 240] * (1. - .001 * g[:, 240]) / e[:, 96] - 1.
    np.testing.assert_allclose(out["return"], expected, rtol=0., atol=1e-14)
    np.testing.assert_array_equal(e, old_e)
    np.testing.assert_array_equal(g, old_g)
    assert scoring == old_sc
    assert all(v.shape == (2,) and np.isfinite(v).all() for v in out.values())


def test_cs_daily_clock_and_remaining_prefix_not_full_window_clock(scoring):
    e, g, starts = arrays()
    # Remaining starts at 18:00 UTC, hence HKT buckets are 22h/24h/24h/2h.
    prefix, hours = 6, 72
    curve = np.interp(np.arange(hours + 1), [0, 6, 22, 30, 46, 54, 70, 72],
                      [1., 1.02, .98, 1.01, 1.03, 1., 1.01, 1.04])
    e[0, prefix:prefix + hours + 1] = curve * 120.
    g[0, prefix + hours] = .5
    out = remainder_risk(e, g, starts, prefix, hours, scoring)
    net = curve.copy(); net[-1] *= 1. - .001 * .5
    hkt = reference_cs(net, np.array([0, 22, 46, 70, 72]))
    utc = reference_cs(net, np.array([0, 6, 30, 54, 72]))
    for key, value in zip(["CS", "Sharpe", "Sortino", "Calmar", "mdd"], hkt):
        assert out[key][0] == pytest.approx(value, abs=1e-13)
    assert out["CS_UTC"][0] == pytest.approx(utc[0], abs=1e-13)
    assert out["CS"][0] != pytest.approx(out["CS_UTC"][0])


def test_grouped_mixed_start_clocks_and_scale_invariance(scoring):
    e, g, starts = arrays(3)
    e[:] = np.linspace(100., 110., 337)
    e[1] *= 7.; e[2] *= .01
    g[:] = .25
    starts = pd.DatetimeIndex(["2024-01-01 12:00Z", "2024-01-02 12:00Z", "2024-01-03 16:00Z"])
    out = remainder_risk(e, g, starts, 96, 216, scoring)
    for value in out.values():
        assert value[0] == pytest.approx(value[1], abs=1e-12)
    scalar = remainder_risk(e[2:3], g[2:3], starts[2:3], 96, 216, scoring)
    for name in out:
        assert out[name][2] == pytest.approx(scalar[name][0], abs=1e-13)


def test_cash_has_zero_net_return_and_cs(scoring):
    out = remainder_risk(*arrays(), 96, 240, scoring)
    assert all(v[0] == 0. for v in out.values())


def test_terminal_liquidation_loss_is_part_of_drawdown_and_cs(scoring):
    e, g, starts = arrays(); g[0, 336] = 1.
    out = remainder_risk(e, g, starts, 96, 240, scoring)
    assert out["return"][0] == pytest.approx(-.001)
    assert out["mdd"][0] == pytest.approx(.001)
    assert out["CS"][0] < 0. and out["CS_UTC"][0] < 0.


def test_no_lookahead_after_remainder_end(scoring):
    e, g, starts = arrays()
    before = remainder_risk(e, g, starts, 72, 216, scoring)
    e[:, 289:] = 500.; g[:, 289:] = 3.
    after = remainder_risk(e, g, starts, 72, 216, scoring)
    for name in before:
        np.testing.assert_array_equal(before[name], after[name])


@pytest.mark.parametrize("change", [
    "equity_1d", "gross_1d", "different_shape", "zero_rows", "nan_equity",
    "inf_gross", "zero_equity", "negative_equity", "negative_gross",
    "short_starts", "bad_starts", "nonhour_starts",
])
def test_invalid_paths_fail_closed(scoring, change):
    e, g, starts = arrays()
    if change == "equity_1d": e = e[0]
    elif change == "gross_1d": g = g[0]
    elif change == "different_shape": g = g[:, :-1]
    elif change == "zero_rows": e, g, starts = e[:0], g[:0], starts[:0]
    elif change == "nan_equity": e[0, 200] = np.nan
    elif change == "inf_gross": g[0, 200] = np.inf
    elif change == "zero_equity": e[0, 200] = 0.
    elif change == "negative_equity": e[0, -1] = -1.
    elif change == "negative_gross": g[0, 200] = -.1
    elif change == "short_starts": starts = starts[:0]
    elif change == "bad_starts": starts = ["bad timestamp"]
    elif change == "nonhour_starts": starts = starts + pd.Timedelta(minutes=1)
    with pytest.raises(ValueError):
        remainder_risk(e, g, starts, 96, 240, scoring)


@pytest.mark.parametrize("prefix,hours", [
    (-1, 240), (96, 241), (337, 48), (96.0, 240), (True, 240),
    (96, 0), (96, -1), (96, 240.0), (96, True), (0, 1), (4, 24),
])
def test_invalid_horizons_fail_closed(scoring, prefix, hours):
    with pytest.raises(ValueError):
        remainder_risk(*arrays(), prefix, hours, scoring)


@pytest.mark.parametrize("fee", [-.001, np.nan, np.inf])
def test_invalid_fee_fails_closed(scoring, fee):
    scoring["liquidation_cost"] = fee
    with pytest.raises(ValueError):
        remainder_risk(*arrays(), 96, 240, scoring)


def test_negative_terminal_equity_after_liquidation_rejected(scoring):
    e, g, starts = arrays(); g[0, 336] = 1001.
    with pytest.raises(ValueError, match="terminal"):
        remainder_risk(e, g, starts, 96, 240, scoring)


def test_zero_terminal_equity_after_liquidation_records_total_loss(scoring):
    e, g, starts = arrays(); g[0, 336] = 1000.
    out = remainder_risk(e, g, starts, 96, 240, scoring)
    assert out["return"][0] == -1.
    assert out["mdd"][0] == 1.
    assert all(np.isfinite(v).all() for v in out.values())
