"""Combinations (src/models/pol/_combo.py): sleeves mixed by weight, gross capped, view-only, keyed on every sleeve."""
from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import pytest

from backtest.data import Market, universe_at, universe_from_panel
from backtest.engine import compute_targets, decision_times
from backtest.evaluate import model_modules
from backtest.scoring.leakage import leakage_gate
from src.config import load_config
from src.contracts import MarketView, ModelSpec
from src.models import discover
from src.models.pol._combo import SLEEVES, Combo, btc_state
from tests.synth import make_market

CFG = load_config()
COMBOS = sorted(n for n in discover() if n.startswith(("pol_combo_", "pol_switch_")))


@pytest.fixture(scope="module")
def market() -> Market:
    md = make_market()
    uni = universe_from_panel(md.close, md.quote_volume, top_n=10, min_history_days=45)
    return Market(md.close, md.quote_volume, uni, pd.Series(0.0005, index=md.close.columns), {"synthetic": True})


def view_at(market: Market, t: str, params: dict) -> MarketView:
    t = pd.Timestamp(t, tz="UTC")
    i = market.close.index.get_loc(t)
    return MarketView(t=t, close=market.close.iloc[: i + 1], quote_volume=market.quote_volume.iloc[: i + 1],
                      universe=universe_at(market, t), params=params)


class Mix(Combo):
    spec = ModelSpec(name="pol_mix", method="selector", author="pol", uses_shorts=True)


def test_one_sleeve_at_weight_one_is_that_sleeve(market):
    v = view_at(market, "2021-03-01 16:00", {"sleeves": {"team_ew_daily": {"weight": 1.0}}})
    want = SLEEVES["team_ew_daily"].targets(dataclasses.replace(v, params={}))
    pd.testing.assert_series_equal(Mix().targets(v).sort_index(), want.sort_index(), check_names=False)


def test_weights_scale_net_and_cap_gross(market):
    rot = CFG["models"]["team_rot_ew"]
    v = view_at(market, "2021-03-01 16:00", {"sleeves": {"team_btc_hold": {"weight": 1.0},
                                                         "team_rot_ew": {"weight": 1.0, "params": rot}}})
    w = Mix().targets(v)
    assert w.abs().sum() == pytest.approx(1.0)                 # 1.0 + up to 1.0 of rotation: scaled back to 100%
    half = Mix().targets(dataclasses.replace(v, params={"sleeves": {"team_btc_hold": {"weight": 0.5}}}))
    assert half.to_dict() == {"BTCUSDT": 0.5}
    with pytest.raises(ValueError, match="unknown sleeves"):
        Mix().targets(dataclasses.replace(v, params={"sleeves": {"nope": {"weight": 1.0}}}))


@pytest.mark.parametrize("name", COMBOS)
def test_combos_keep_the_contract_and_reach_every_sleeve(name, market):
    model = discover()[name]
    p = CFG["models"][name]
    for s, block in p["sleeves"].items():                      # anchors: one copy of every sleeve number
        assert (block.get("params") or {}) == (CFG["models"].get(s) or {}), f"{name}: {s} params drifted"
        assert f"{type(SLEEVES[s]).__module__}" in model_modules(model)
    if not model.spec.uses_shorts:
        assert not any(SLEEVES[s].spec.uses_shorts for s in p["sleeves"])
    idx = market.close.index
    times = decision_times(idx, 24, 16, pd.Timestamp("2021-02-01 16:00", tz="UTC"), pd.Timestamp("2021-03-10 16:00", tz="UTC"))
    tg = compute_targets(model, market, times, p)               # raises on any contract break
    assert (tg.abs().sum(axis=1) <= 1 + 1e-9).all()
    if "switch" not in p:                                       # a switch to cash may sit out a short sample
        assert (tg.abs().sum(axis=1) > 0).mean() > 0.5


def test_combo_is_view_only_and_deterministic(market):
    model = discover()["pol_combo_rt"]
    p = CFG["models"]["pol_combo_rt"]
    idx = market.close.index
    times = decision_times(idx, 24, 16, pd.Timestamp("2021-02-01 16:00", tz="UTC"), pd.Timestamp("2021-03-15 16:00", tz="UTC"))
    out = leakage_gate(model, market, compute_targets(model, market, times, p), p,
                       {"decisions": 8, "seed": 1, "noise_sigma": 0.01})
    assert out["pass"], out
    assert np.isfinite(compute_targets(model, market, times[:3], p).to_numpy()).all()


def test_switch_runs_only_the_sleeve_of_the_current_state(market):
    trend = CFG["models"]["team_trend_2"]
    rot = CFG["models"]["team_rot_ew"]
    seen = set()
    for t in pd.date_range("2021-02-01 16:00", "2021-04-01 16:00", freq="7D", tz="UTC"):
        v = view_at(market, str(t), {"switch": trend, "sleeves": {"team_rot_ew": {"when": "up", "params": rot},
                                                                   "team_btc_hold": {"when": "down"}}})
        state = btc_state(v, trend)
        seen.add(state)
        w = Mix().targets(v)
        if state == "down":
            assert w.to_dict() == {"BTCUSDT": 1.0}
        else:
            want = Mix().targets(dataclasses.replace(v, params={"sleeves": {"team_rot_ew": {"weight": 1.0, "params": rot}}}))
            pd.testing.assert_series_equal(w.sort_index(), want.sort_index())
    assert seen                                                 # the synthetic sample visits at least one state


def test_own_prev_reaches_the_active_sleeve_and_replay_does_not(market, monkeypatch):
    from src.models.pol import _combo

    class Echo:                                                 # returns whatever it held before
        spec = ModelSpec(name="echo", method="momentum", author="pol")

        def targets(self, view):
            return view.prev_targets.copy()
    monkeypatch.setitem(_combo.SLEEVES, "echo", Echo())
    prev = pd.Series({"BTCUSDT": 0.4})
    v = dataclasses.replace(view_at(market, "2021-03-01 16:00", {"prev": "own", "sleeves": {"echo": {}}}), prev_targets=prev)
    assert Mix().targets(v).to_dict() == {"BTCUSDT": 0.4}
    v = dataclasses.replace(v, params={"sleeves": {"echo": {}}})
    assert Mix().targets(v).empty                               # replay rebuilds the sleeve's own history: empty
