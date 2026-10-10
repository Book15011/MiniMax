"""Tests for the e20v45 short guard (feature/e20-shortguard): e20v45 is never changed except for the trim."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.config import load_config
from src.contracts import MarketView
from src.models import discover
from src.models.book import _e20guard

NAMES = ["book_e20guard_pullback", "book_e20guard_confirm", "book_e20guard_pullback40", "book_e20guard_confirm40",
         "book_e20guard_pullback_r", "book_e20guard_confirm_r"]
COINS = ["BTCUSDT", "AUSDT", "BUSDT", "CUSDT", "DUSDT"]


def view(prev=None, name="book_e20guard_pullback"):
    idx = pd.date_range(end="2026-10-01 16:00", periods=200, freq="h", tz="UTC")
    close = pd.DataFrame({c: 100 + np.arange(200) * 0.1 for c in COINS}, index=idx)
    return MarketView(t=idx[-1], close=close, quote_volume=close * 0 + 1e6, universe=tuple(COINS),
                      params=load_config()["models"][name],
                      prev_targets=prev if prev is not None else pd.Series(dtype=float))


def patch(monkeypatch, base, shorts, seen=None):
    def e20(v):
        if seen is not None:
            seen.append(v.prev_targets.copy())
        return pd.Series(base, dtype=float)
    monkeypatch.setattr(_e20guard, "E20", SimpleNamespace(targets=e20))
    calls = []

    def sw(v, held, p, pullback):
        calls.append((list(held.index), float(held.sum()), pullback))
        return pd.Series(shorts, dtype=float)
    monkeypatch.setattr(_e20guard._cashshort, "short_weights", sw)
    return calls


def test_registered_with_config():
    models = discover()
    cfg = load_config()["models"]
    for n in NAMES:
        assert n in models and models[n].spec.uses_shorts and models[n].spec.rebalance_hours == 24
        assert "e20" in cfg[n] and cfg[n]["short_gross_cap"] in (0.25, 0.4)
    assert cfg["book_e20guard_pullback"]["e20"] == cfg["pol_switch_vt_tl_e20v45"]


def test_no_regime_returns_e20v45_exactly(monkeypatch):
    base = {"AUSDT": 0.5, "BUSDT": 0.5}
    patch(monkeypatch, base, {})
    out = _e20guard.targets(view(), pullback=True)
    pd.testing.assert_series_equal(out.sort_index(), pd.Series(base, dtype=float).sort_index())


def test_shorts_trim_longs_and_keep_gross(monkeypatch):
    calls = patch(monkeypatch, {"AUSDT": 0.5, "BUSDT": 0.5}, {"CUSDT": -0.15, "DUSDT": -0.10})
    out = _e20guard.targets(view(), pullback=False)
    assert calls == [(["AUSDT", "BUSDT"], 0.0, False)]          # full budget, held coins excluded
    assert out["AUSDT"] == pytest.approx(0.375) and out["BUSDT"] == pytest.approx(0.375)
    assert out["CUSDT"] == pytest.approx(-0.15) and out["DUSDT"] == pytest.approx(-0.10)
    assert out.abs().sum() <= 1 + 1e-12


def test_e20v45_long_short_mode_is_left_alone(monkeypatch):
    base = {"AUSDT": 0.3, "CUSDT": -0.2}
    calls = patch(monkeypatch, base, {"DUSDT": -0.1})
    out = _e20guard.targets(view(), pullback=True)
    assert calls == []
    pd.testing.assert_series_equal(out.sort_index(), pd.Series(base, dtype=float).sort_index())


def test_e20v45_sees_only_its_long_holdings(monkeypatch):
    seen = []
    patch(monkeypatch, {"AUSDT": 1.0}, {}, seen)
    _e20guard.targets(view(prev=pd.Series({"AUSDT": 0.75, "CUSDT": -0.25})), pullback=True)
    assert list(seen[0].index) == ["AUSDT"] and (seen[0] > 0).all()


def test_volume_fill_only_reaches_the_short_leg(monkeypatch):
    seen_e20, seen_short = [], []
    monkeypatch.setattr(_e20guard, "E20", SimpleNamespace(targets=lambda v: seen_e20.append(v.quote_volume.copy()) or pd.Series({"AUSDT": 1.0})))
    monkeypatch.setattr(_e20guard._cashshort, "short_weights",
                        lambda v, held, p, pullback: seen_short.append(v.quote_volume.copy()) or pd.Series(dtype=float))
    v = view(name="book_e20guard_pullback_r")
    qv = v.quote_volume.copy()
    qv.iloc[-20:-12, 1] = np.nan                    # an 8-hour gap
    qv.iloc[-60:-40, 2] = np.nan                    # a 20-hour gap: longer than the 12 h fill
    from dataclasses import replace
    _e20guard.targets(replace(v, quote_volume=qv), pullback=True)
    assert seen_e20[0].isna().sum().sum() == 28                  # e20v45 sees the raw gaps
    assert seen_short[0].iloc[:, 1].isna().sum() == 0             # the 8-hour gap is filled for the short leg
    assert seen_short[0].iloc[:, 2].isna().sum() == 8             # only 12 of the 20 hours are filled
