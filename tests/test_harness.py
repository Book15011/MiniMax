"""Harness tests: metrics against hand-computed values, engine accounting, contracts, registry."""
from __future__ import annotations

import math
import statistics

import numpy as np
import pandas as pd
import pytest

from backtest.data import Market, universe_from_panel
from backtest.engine import Costs, Simulator, compute_targets, decision_times, fit_gross
from backtest.evaluate import lookahead_check
from backtest.metrics import max_drawdown, sharpe, sortino, window_metrics
from src.config import load_config
from src.contracts import MarketView, ModelSpec, check_targets
from src.models import discover
from tests.synth import make_market

HOURS = 14 * 24


# ---------------- metrics ----------------

def test_sharpe_sortino_mdd_by_hand():
    r = np.array([0.01, -0.02, 0.03])
    exp_sharpe = statistics.mean(r) / statistics.stdev(r) * math.sqrt(365)
    exp_sortino = statistics.mean(r) / math.sqrt((0 + 0.02 ** 2 + 0) / 3) * math.sqrt(365)
    assert sharpe(r, 365) == pytest.approx(exp_sharpe)
    assert sortino(r, 365) == pytest.approx(exp_sortino)
    assert max_drawdown(np.array([1.0, 1.1, 0.99, 1.2])) == pytest.approx(0.99 / 1.1 - 1)


def test_window_metrics_composites():
    day_ret = [0.01, -0.02, 0.03, 0.0, 0.005, -0.01, 0.02, 0.01, -0.005, 0.0, 0.01, -0.02, 0.015, 0.005]
    eq = [1.0]
    for r in day_ret:                                  # flat inside each day, jump on the day's last hour
        eq += [eq[-1]] * 23 + [eq[-1] * (1 + r)]
    eq = np.array(eq)
    m = window_metrics(eq, 14)
    ret = eq[-1] - 1
    mdd = max_drawdown(eq)
    assert m["ret"] == pytest.approx(ret)
    assert m["mdd"] == pytest.approx(mdd)
    assert m["sharpe_d"] == pytest.approx(statistics.mean(day_ret) / statistics.stdev(day_ret) * math.sqrt(365))
    assert m["calmar_raw"] == pytest.approx(ret / abs(mdd))
    assert m["calmar_ann"] == pytest.approx(((1 + ret) ** (365 / 14) - 1) / abs(mdd))
    assert m["comp_a"] == pytest.approx(0.4 * m["sortino_d"] + 0.3 * m["sharpe_d"] + 0.3 * m["calmar_ann"])
    assert m["comp_b"] == pytest.approx(0.4 * m["sortino_h"] + 0.3 * m["sharpe_h"] + 0.3 * m["calmar_raw"])


def test_flat_window_scores_zero():
    m = window_metrics(np.ones(HOURS + 1))
    assert m["ret"] == 0 and m["mdd"] == 0 and m["comp_a"] == 0 and m["comp_b"] == 0


# ---------------- engine ----------------

def market_from(prices: dict[str, list[float]], start: str = "2024-01-01 00:00") -> Market:
    n = len(next(iter(prices.values())))
    idx = pd.date_range(start, periods=n, freq="h", tz="UTC")
    close = pd.DataFrame({k: np.asarray(v, float) for k, v in prices.items()}, index=idx)
    qv = pd.DataFrame(1e6, index=idx, columns=close.columns)
    uni = pd.Series({t: tuple(close.columns) for t in idx[idx.hour == 16]})
    return Market(close, qv, uni, pd.Series(0.0, index=close.columns), {})


class Const:
    def __init__(self, w: dict, shorts: bool = False, band: float = 0.0):
        self.w = w
        self.spec = ModelSpec(name="pol_const", method="momentum", author="pol", band=band, uses_shorts=shorts)

    def targets(self, view: MarketView) -> pd.Series:
        return pd.Series(self.w, dtype=float)


def run_const(prices: dict, w: dict, shorts=False, band=0.0, taker=0.001):
    mk = market_from(prices)
    i0 = 16                                             # 2024-01-01 16:00 UTC = 00:00 HKT
    times = decision_times(mk.close.index, 24, 16, mk.close.index[i0], mk.close.index[i0 + HOURS])
    model = Const(w, shorts, band)
    tg = compute_targets(model, mk, times, {})
    sim = Simulator(mk, tg, band, Costs(taker, taker), lag_hours=1, anchor_hour=16, guard_offset_hours=20)
    return sim.run(i0, HOURS)


N = 16 + HOURS + 30


def test_entry_fee_then_gain():
    a = [100.0] * 18 + [110.0] * (N - 18)               # entry fills at bar 17 (price 100); +10% at bar 18
    res = run_const({"A": a}, {"A": 1.0})
    assert res.equity[1] == pytest.approx(1 - 0.001)
    assert res.equity[-1] == pytest.approx((1 - 0.001) * 1.10)


def test_one_bar_lag_misses_the_jump():
    a = [100.0] * 17 + [120.0] * (N - 17)               # jump lands on bar 17, the entry bar itself
    res = run_const({"A": a}, {"A": 1.0})
    assert res.equity[-1] == pytest.approx(1 - 0.001)


def test_short_loses_when_price_rises():
    a = [100.0] * 18 + [110.0] * (N - 18)
    res = run_const({"A": a}, {"A": -0.5}, shorts=True)
    assert res.equity[2] == pytest.approx((1 - 0.5 * 0.001) * (1 - 0.5 * 0.10))   # right after the move
    assert res.equity[-1] < res.equity[2]          # the daily rebalance trims the grown short and pays a fee


def test_guard_makes_every_day_active_even_when_band_blocks():
    rng = np.random.default_rng(1)
    a = list(100 * np.exp(np.cumsum(rng.normal(0, 0.002, N))))
    res = run_const({"A": a, "B": [100.0] * N}, {"A": 0.5}, band=0.4)   # band too wide to ever trade
    assert res.active_days == 14


def test_all_cash_is_inactive_and_flat():
    res = run_const({"A": [100.0] * N}, {})
    assert res.active_days == 0 and res.turnover == 0 and np.allclose(res.equity, 1.0)


def test_fit_gross_keeps_reductions_and_scales_increases():
    w = np.array([0.55, 0.45, 0.0, -0.1])
    new = np.array([0.55, 0.0, 0.5, -0.2])       # A drifted but within band; B exits; C new; short D grows
    out = fit_gross(w, new)
    assert np.abs(out).sum() == pytest.approx(1.0)
    assert out[0] == 0.55 and out[1] == 0.0       # kept holding and exit untouched
    assert out[2] / 0.5 == pytest.approx((out[3] + 0.1) / -0.1)   # both increases scaled by one factor
    assert np.array_equal(fit_gross(w, np.array([0.5, 0.4, 0.0, -0.1])), [0.5, 0.4, 0.0, -0.1])  # fits: unchanged
    flip = fit_gross(np.array([0.6, 0.4]), np.array([-0.7, 0.4]))  # closing leg in full, opening leg scaled
    assert flip[1] == 0.4 and flip[0] == pytest.approx(-0.6)


def test_band_limited_rotation_never_exceeds_full_gross():
    """A rallies 10% inside the band while the model rotates B -> C: C is bought only with the free cash."""
    a = [100.0] * 18 + [110.0] * (N - 18)
    mk = market_from({"A": a, "B": [100.0] * N, "C": [100.0] * N})
    i0 = 16
    times = decision_times(mk.close.index, 24, 16, mk.close.index[i0], mk.close.index[i0 + HOURS])
    tg = pd.DataFrame(0.0, index=times, columns=mk.close.columns)
    tg.loc[times[0], ["A", "B"]] = 0.5
    tg.loc[times[1]:, ["A", "C"]] = 0.5
    sim = Simulator(mk, tg, 0.05, Costs(0.001, 0.001), lag_hours=1, anchor_hour=16, guard_offset_hours=20)
    res = sim.run(i0, HOURS, trace=True)
    assert res.max_gross <= 1.0 + 1e-12
    assert res.trace["gross"].max() <= 1.0 + 1e-12


# ---------------- contracts ----------------

def test_check_targets_rejects_contract_breaks():
    mk = market_from({"A": [1.0] * 40, "B": [1.0] * 40})
    t = mk.close.index[16]
    view = MarketView(t=t, close=mk.close.iloc[:17], quote_volume=mk.quote_volume.iloc[:17], universe=("A",))
    long_only = ModelSpec(name="pol_x", method="momentum", author="pol")
    with pytest.raises(ValueError, match="outside the universe"):
        check_targets(pd.Series({"B": 0.5}), view, long_only)
    with pytest.raises(ValueError, match="gross exposure"):
        check_targets(pd.Series({"A": 1.2}), view, long_only)
    with pytest.raises(ValueError, match="negative weights"):
        check_targets(pd.Series({"A": -0.2}), view, long_only)


def test_registry_specs_are_valid_and_named_by_author():
    models = discover()
    assert {"team_btc_hold", "pol_mom_ss", "pol_trend_ls"} <= set(models)
    for name, m in models.items():
        m.spec.validate()
        assert m.spec.name == name


@pytest.mark.parametrize("name", ["pol_mom_ss", "pol_trend_ls", "team_btc_hold"])
def test_registered_models_keep_the_contract_on_synthetic_data(name):
    md = make_market()
    uni = universe_from_panel(md.close, md.quote_volume, top_n=10, min_history_days=45)
    mk = Market(md.close, md.quote_volume, uni, pd.Series(0.0005, index=md.close.columns), {})
    model = discover()[name]
    params = (load_config().get("models") or {}).get(name, {})
    idx = mk.close.index
    times = decision_times(idx, model.spec.rebalance_hours, 16, idx[0] + pd.Timedelta(days=120),
                           idx[0] + pd.Timedelta(days=150))
    tg = compute_targets(model, mk, times, params)        # raises on any contract break
    assert (tg.abs().sum(axis=1) <= 1 + 1e-9).all()
    assert lookahead_check(model, mk, tg, params, n=4) == []
