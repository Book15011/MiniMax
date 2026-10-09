"""Tests written before implementation for the frozen cash-only short study."""
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.config import load_config
from src.contracts import MarketView, check_targets
from src.models.book import _cashshort
from src.models.book.book_cashshort_confirm import MODEL as CONFIRM
from src.models.book.book_cashshort_pullback import MODEL as PULLBACK

COINS = ["BTCUSDT"] + [f"C{i:02d}USDT" for i in range(34)]


def params():
    return load_config()["models"]["book_cashshort_confirm"]


def market(n=1501):
    idx = pd.date_range(end="2024-05-01 16:00", periods=n, freq="h", tz="UTC")
    x = np.arange(n)
    close = pd.DataFrame({
        c: 200 * np.exp((-0.00023 - i * 0.000002) * x + 0.002 * np.sin(x / (5 + i)))
        for i, c in enumerate(COINS)
    }, index=idx)
    qv = pd.DataFrame({c: np.full(n, 1e6 - i * 1000) for i, c in enumerate(COINS)}, index=idx)
    return MarketView(t=idx[-1], close=close, quote_volume=qv, universe=tuple(COINS), params=params())


def fixed_base(monkeypatch, weights):
    def targets(v):
        assert (v.prev_targets >= 0).all()
        return pd.Series(weights, dtype=float)
    monkeypatch.setattr(_cashshort, "BASE", SimpleNamespace(targets=targets))


def test_specs_and_dependency_identity():
    from backtest.evaluate import model_modules
    assert CONFIRM.spec.uses_shorts and PULLBACK.spec.uses_shorts
    assert CONFIRM.spec.rebalance_hours == PULLBACK.spec.rebalance_hours == 24
    assert CONFIRM.spec.band == PULLBACK.spec.band == 0.05
    for model in (CONFIRM, PULLBACK):
        modules = model_modules(model)
        assert "src.models.book._cashshort" in modules
        assert "src.models.baitoey.baitoey_ovl_brk_dual" in modules
        assert "src.models.baitoey.baitoey_vt_dual" in modules
        assert "src.models.baitoey.baitoey_vt_mom" in modules
        assert "src.models.baitoey._volume_signals" in modules
        assert "src.models.baselines.team_rot_ew" in modules
    assert type(CONFIRM).__module__ != type(PULLBACK).__module__


def test_confirm_enters_only_unused_cash_and_preserves_longs(monkeypatch):
    v = market()
    fixed_base(monkeypatch, {"C31USDT": .70, "C32USDT": .20})
    w = check_targets(CONFIRM.targets(v), v, CONFIRM.spec)
    assert w["C31USDT"] == .70 and w["C32USDT"] == .20
    short = w[w < 0]
    assert len(short) <= 3 and len(short) > 0
    assert short.abs().sum() <= .10 + 1e-12
    assert short.abs().max() <= .10 + 1e-12
    assert w.abs().sum() <= 1 + 1e-12
    rets = v.close[short.index].pct_change(fill_method=None).iloc[-720:]
    bound = (short.abs() * rets.std() * np.sqrt(24)).sum()
    assert bound <= .01 + 1e-12


def test_full_long_book_opens_no_short(monkeypatch):
    fixed_base(monkeypatch, {"C31USDT": 1.0})
    assert CONFIRM.targets(market()).to_dict() == {"C31USDT": 1.0}


@pytest.mark.parametrize("change", ["btc_up", "breadth_up", "too_few_liquid", "missing_endpoint", "missing_btc"])
def test_failed_regime_keeps_base_and_exits_old_shorts(monkeypatch, change):
    fixed_base(monkeypatch, {"C31USDT": .40})
    v = market()
    v = replace(v, prev_targets=pd.Series({"C31USDT": .40, "C02USDT": -.08}))
    if change == "btc_up":
        v.close.loc[v.close.index[-169:], "BTCUSDT"] = np.linspace(130, 230, 169)
    elif change == "breadth_up":
        v.close.iloc[-1, :] = v.close.iloc[-49, :].to_numpy() * 1.03
        v.close.loc[v.t, "BTCUSDT"] = v.close.iloc[-49]["BTCUSDT"] * .98
    elif change == "too_few_liquid":
        v = replace(v, universe=tuple(COINS[:19] + ["C31USDT"]))
        v.quote_volume.loc[v.t, "C31USDT"] = np.nan
    elif change == "missing_endpoint":
        v.close.loc[v.t - pd.Timedelta(hours=48), "C02USDT"] = np.nan
    else:
        v.close.loc[v.t - pd.Timedelta(hours=1000), "BTCUSDT"] = np.nan
    assert CONFIRM.targets(v).to_dict() == {"C31USDT": .40}


def test_missing_selected_endpoint_never_replaced_by_lower_liquidity_coin(monkeypatch):
    fixed_base(monkeypatch, {})
    v = market()
    v.close.loc[v.t, "C28USDT"] = np.nan
    assert CONFIRM.targets(v).empty


def test_unselected_missing_endpoint_does_not_change_declared_breadth(monkeypatch):
    fixed_base(monkeypatch, {})
    v = market()
    old = CONFIRM.targets(v)
    v.close.loc[v.t, "C33USDT"] = np.nan
    pd.testing.assert_series_equal(CONFIRM.targets(v), old)


def test_short_history_gap_disqualifies_coin_without_rewriting_breadth(monkeypatch):
    fixed_base(monkeypatch, {})
    v = market()
    before = CONFIRM.targets(v)
    c = before.index[0]
    v.close.loc[v.t - pd.Timedelta(hours=400), c] = np.nan
    assert c not in CONFIRM.targets(v).index


def test_negative_momentum_required(monkeypatch):
    fixed_base(monkeypatch, {})
    v = market()
    v.close.iloc[-1, 1] = v.close.iloc[-337, 1] * 1.2
    assert "C00USDT" not in CONFIRM.targets(v).index


def test_pullback_uses_only_ordered_closed_bar_returns(monkeypatch):
    fixed_base(monkeypatch, {})
    v = market()
    assert PULLBACK.targets(v).empty
    c = "C02USDT"
    px = v.close[c].copy()
    anchor = float(px.iloc[-25])
    px.iloc[-24:-4] = np.linspace(anchor * 1.001, anchor * 1.02, 20)
    px.iloc[-4:] = np.linspace(anchor * 1.015, anchor * 1.005, 4)
    v.close[c] = px
    w = PULLBACK.targets(v)
    assert list(w.index) == [c] and w[c] < 0
    v.close.loc[v.t, c] = float(v.close.loc[v.t - pd.Timedelta(hours=4), c]) * 1.01
    assert PULLBACK.targets(v).empty


@pytest.mark.parametrize("model", [CONFIRM, PULLBACK])
def test_future_rows_and_short_prev_cannot_change_long_or_short_targets(monkeypatch, model):
    fixed_base(monkeypatch, {"C31USDT": .40})
    v = market()
    expected = model.targets(v)
    future_idx = pd.date_range(v.t + pd.Timedelta(hours=1), periods=10, freq="h")
    future_c = pd.DataFrame(1e9, index=future_idx, columns=COINS)
    future_q = pd.DataFrame(1e15, index=future_idx, columns=COINS)
    altered = replace(v, close=pd.concat([v.close, future_c]),
                      quote_volume=pd.concat([v.quote_volume, future_q]),
                      prev_targets=pd.Series({"C02USDT": -.10}))
    pd.testing.assert_series_equal(model.targets(altered), expected)


@pytest.mark.parametrize("hour", [12, 16])
def test_real_base_targets_exactly_preserved_at_bootstrap_and_daily_decisions(hour):
    v = market(3601)
    x = np.arange(len(v.close))
    for c in ["C31USDT", "C32USDT"]:
        v.close[c] = 100 * np.exp(.0003 * x + .002 * np.sin(x / 7))
    t = v.t.normalize() + pd.Timedelta(hours=hour)
    v = replace(v, t=t, close=v.close.loc[:t], quote_volume=v.quote_volume.loc[:t],
                prev_targets=pd.Series({"C31USDT": .08, "C02USDT": -.06}))
    positive = v.prev_targets[v.prev_targets > 0]
    baseline = _cashshort.BASE.targets(replace(v, params=v.params["long_base"], prev_targets=positive))
    got = CONFIRM.targets(v)
    assert len(baseline) > 0
    pd.testing.assert_series_equal(got[got > 0].sort_index(), baseline[baseline > 0].sort_index())


def test_conservative_risk_cap_can_only_scale_down(monkeypatch):
    fixed_base(monkeypatch, {})
    v = market()
    v.params["short_daily_vol"] = .000001
    w = CONFIRM.targets(v)
    sigma = v.close[w.index].pct_change(fill_method=None).iloc[-720:].std() * np.sqrt(24)
    assert np.isclose((w.abs() * sigma).sum(), .000001)
    assert w.abs().sum() < .25


def test_long_base_params_are_exact_pinned_snapshot():
    from pathlib import Path
    import json
    p = Path("results/scoring/score2/603da2948b68ee0f5c8a/baitoey_ovl_brk_dual/"
             "f30fa79cde92399a-dd87f9f0d65673f9/score.json")
    if not p.exists():
        pytest.skip("Shared immutable score source unavailable")
    record = json.loads(p.read_text())
    assert params()["long_base"] == record["model"]["params"]


def test_exactly_twenty_liquid_coins_are_sufficient(monkeypatch):
    fixed_base(monkeypatch, {})
    v = market()
    v = replace(v, universe=tuple(COINS[:20]))
    assert not CONFIRM.targets(v).empty


@pytest.mark.parametrize("positive_count, expect_short", [(12, True), (13, False)])
def test_breadth_includes_zero_returns_as_nonpositive(monkeypatch, positive_count, expect_short):
    fixed_base(monkeypatch, {})
    v = market()
    # Selected universe has exactly30coins. Exclude BTC from the flipped names.
    names = COINS[1:positive_count + 1]
    v.close.loc[v.t, names] = v.close.loc[v.t - pd.Timedelta(hours=48), names] * 1.001
    got = CONFIRM.targets(v)
    assert (not got.empty) == expect_short


def test_equal_zero_momentum_never_becomes_short(monkeypatch):
    fixed_base(monkeypatch, {})
    v = market()
    c = "C00USDT"
    px = float(v.close.loc[v.t, c])
    for h in [7 * 24, 14 * 24]:
        v.close.loc[v.t - pd.Timedelta(hours=h), c] = px
    assert c not in CONFIRM.targets(v).index


def test_no_short_long_overlap_even_when_mocked_long_has_negative_momentum(monkeypatch):
    v = market()
    initial = CONFIRM.targets(v)
    c = initial[initial < 0].index[0]
    fixed_base(monkeypatch, {c: .20})
    w = CONFIRM.targets(v)
    assert w[c] == .20 and not w.index.duplicated().any()


def test_illiquid_coin_is_never_shortable(monkeypatch):
    fixed_base(monkeypatch, {})
    v = market()
    c = "C33USDT"
    v.close[c] = v.close[c] * np.exp(-np.arange(len(v.close)) * .001)
    assert c not in CONFIRM.targets(v).index
