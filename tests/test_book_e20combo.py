"""Tests for the e20v45 + overlay + cash-short combos (feature/e20-shortguard)."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.config import load_config
from src.contracts import MarketView
from src.models import discover
from src.models.book import _e20combo

NAMES = ["book_e20combo_alt_cash", "book_e20combo_alt_cash_pb", "book_e20combo_alt_trim", "book_e20combo_brk_cash"]
COINS = ["BTCUSDT", "AUSDT", "BUSDT", "CUSDT", "DUSDT"]


def view(name="book_e20combo_alt_cash", prev=None):
    idx = pd.date_range(end="2026-10-01 16:00", periods=200, freq="h", tz="UTC")
    close = pd.DataFrame({c: 100 + np.arange(200) * 0.1 for c in COINS}, index=idx)
    return MarketView(t=idx[-1], close=close, quote_volume=close * 0 + 1e6, universe=tuple(COINS),
                      params=load_config()["models"][name],
                      prev_targets=prev if prev is not None else pd.Series(dtype=float))


def patch(monkeypatch, base, shorts):
    seen = []
    monkeypatch.setitem(_e20combo.BASES, "alt", SimpleNamespace(
        targets=lambda v: seen.append(v) or pd.Series(base, dtype=float)))
    calls = []

    def sw(v, held, p, pullback):
        calls.append((held.to_dict(), pullback))
        return pd.Series(shorts, dtype=float)
    monkeypatch.setattr(_e20combo._cashshort, "short_weights", sw)
    return seen, calls


def test_registered_with_config():
    models, cfg = discover(), load_config()["models"]
    for n in NAMES:
        assert n in models and models[n].spec.uses_shorts and models[n].spec.rebalance_hours == 24
        assert cfg[n]["base"]["vt"] == cfg["pol_switch_vt_tl_e20v45"] and cfg[n]["volume_fill_hours"] == 12
        assert cfg[n]["short_gross_cap"] == 0.25


def test_base_gets_its_own_params_and_long_prev(monkeypatch):
    seen, _ = patch(monkeypatch, {"AUSDT": 1.0}, {})
    _e20combo.targets(view(prev=pd.Series({"AUSDT": 0.6, "CUSDT": -0.2})), base="alt", pullback=False, funding="cash")
    assert seen[0].params == load_config()["models"]["book_e20combo_alt_cash"]["base"]
    assert list(seen[0].prev_targets.index) == ["AUSDT"]


def test_cash_funding_never_trims_the_base(monkeypatch):
    _, calls = patch(monkeypatch, {"AUSDT": 0.3}, {"CUSDT": -0.2})
    out = _e20combo.targets(view(), base="alt", pullback=False, funding="cash")
    assert calls == [({"AUSDT": 0.3}, False)]                    # budget = min(cap, unused cash)
    assert out["AUSDT"] == pytest.approx(0.3) and out["CUSDT"] == pytest.approx(-0.2)


def test_trim_funding_scales_the_base(monkeypatch):
    _, calls = patch(monkeypatch, {"AUSDT": 0.5, "BUSDT": 0.5}, {"CUSDT": -0.25})
    out = _e20combo.targets(view("book_e20combo_alt_trim"), base="alt", pullback=True, funding="trim")
    assert calls == [({"AUSDT": 0.0, "BUSDT": 0.0}, True)]
    assert out["AUSDT"] == pytest.approx(0.375) and out.abs().sum() <= 1 + 1e-12


def test_no_regime_or_own_shorts_pass_through(monkeypatch):
    patch(monkeypatch, {"AUSDT": 0.4}, {})
    out = _e20combo.targets(view(), base="alt", pullback=False, funding="cash")
    pd.testing.assert_series_equal(out, pd.Series({"AUSDT": 0.4}, dtype=float))
    _, calls = patch(monkeypatch, {"AUSDT": 0.4, "DUSDT": -0.3}, {"CUSDT": -0.2})
    out = _e20combo.targets(view(), base="alt", pullback=False, funding="cash")
    assert calls == [] and out["DUSDT"] == pytest.approx(-0.3) and "CUSDT" not in out
