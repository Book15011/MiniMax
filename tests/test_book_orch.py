"""book_orch (reports/review/20261003-prereg-orch.md, section 4.2): the base stays exact, the layers keep their bounds,
no look-ahead, the purge, and deterministic training. A fake forecaster stands in for the fitted models, so only the
training tests need scikit-learn (they skip without it)."""
from __future__ import annotations

import copy
import hashlib
import pickle
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from backtest.data import Market, universe_at, universe_from_panel
from backtest.engine import decision_times, view_frames
from src.config import load_config
from src.contracts import MarketView, check_targets
from src.models.book import _orch_ml, book_orch
from src.models.book._orch_features import FEATURES, coin_features, market_features
from src.models.book.book_orch import MODEL, short_sleeve
from tests.synth import make_market

CFG = load_config()
P = CFG["models"]["book_orch"]
H = pd.Timedelta(hours=1)


class Lin:
    """A stand-in forecaster: a fixed multiple of a feature (or a constant)."""

    def __init__(self, k: float, feature: str = "ret_7d", const: float | None = None):
        self.k, self.j, self.const = k, FEATURES.index(feature), const

    def predict(self, A):
        return np.full(len(A), self.const) if self.const is not None else self.k * A[:, self.j]


def fake_bundle(mu1, mu3, q=0.02, key="fake") -> dict:
    b = _orch_ml.Bundle(key, list(FEATURES), [_orch_ml.Forecaster(pd.Timestamp("2019-01-01", tz="UTC"), mu1, mu3, q)],
                        pd.DatetimeIndex([pd.Timestamp("2019-01-01", tz="UTC")]), {}, 0.0005)
    _orch_ml._CACHE[(key, key)] = b
    return {"manifest": key, "manifest_sha256": key}


def params(**layers) -> dict:
    p = copy.deepcopy(P)
    for k, v in layers.items():
        p[k] = {**p[k], **v}
    return p


@pytest.fixture(scope="module")
def market() -> Market:
    md = make_market()
    uni = universe_from_panel(md.close, md.quote_volume, top_n=10, min_history_days=45)
    return Market(md.close, md.quote_volume, uni, pd.Series(0.0005, index=md.close.columns), {"synthetic": True})


def view(market: Market, t, p, prev=None) -> MarketView:
    c, q = view_frames(market.close, market.quote_volume, t)
    return MarketView(t=t, close=c, quote_volume=q, universe=universe_at(market, t), params=p,
                      prev_targets=pd.Series(dtype=float) if prev is None else prev)


def chain(model, market, p, start, hours):
    """Hourly decisions from an empty book, each given the previous one (as the engine's compute_targets does)."""
    out, prev = [], pd.Series(dtype=float)
    for k in range(hours):
        t = start + k * H
        w = check_targets(model.targets(view(market, t, p, prev)), view(market, t, p, prev), model.spec)
        out.append((t, w))
        prev = w
    return out


class Recorder:
    """Wraps the base and records every call (time, previous long coins, output)."""

    def __init__(self, inner):
        self.inner, self.spec, self.calls = inner, inner.spec, []

    def targets(self, v):
        w = self.inner.targets(v)
        self.calls.append((v.t, tuple(sorted(v.prev_targets[v.prev_targets > 0].index)), w))
        return w


START = pd.Timestamp("2021-03-01 12:00", tz="UTC")


def test_every_layer_off_gives_the_base_at_every_base_decision(market):
    base = book_orch.base_model("baitoey_vt_mom")
    ours = chain(MODEL, market, P, START, 24 * 8)
    times = decision_times(market.close.index, 24, 16, START, START + 8 * pd.Timedelta(days=1))
    prev, bt = pd.Series(dtype=float), {}
    for t in [START] + list(times):                                  # the base alone: first decision at the start
        w = base.targets(view(market, t, P["base_params"], prev))
        bt[t], prev = w[w != 0], w[w != 0]
    got = dict(ours)
    for t, w in bt.items():
        if t in got:
            assert got[t].sort_index().equals(w.astype(float).sort_index()), t
    # between decisions the last decision's targets are returned unchanged
    for (t0, a), (t1, b) in zip(ours, ours[1:]):
        if t1.hour != 16:
            assert b.equals(a)


def test_hold_returns_the_last_decision_unchanged(market):
    t = pd.Timestamp("2021-03-02 03:00", tz="UTC")
    v = view(market, t, P)
    prev = pd.Series({c: w for c, w in zip(list(v.universe)[:3], (0.4, -0.2, 0.3))})
    assert MODEL.targets(view(market, t, P, prev)).equals(prev.astype(float))


def test_held_long_set_equals_the_base_and_the_sleeve_never_moves_it(market):
    ml = fake_bundle(Lin(0.3), Lin(1.0), q=0.02)
    rec_on, rec_off = Recorder(book_orch.base_model("baitoey_vt_mom")), Recorder(book_orch.base_model("baitoey_vt_mom"))
    book_orch._BASES["rec_on"], book_orch._BASES["rec_off"] = rec_on, rec_off
    on = params(ml={"enabled": True, **ml}, shock={"enabled": True},
                short={"enabled": True, "candidates": "ml", "breadth_max": 1.01})   # sleeve always allowed
    off = params(ml={"enabled": True, **ml}, shock={"enabled": True})
    on["base"], off["base"] = "rec_on", "rec_off"
    a = chain(MODEL, market, on, START, 24 * 6)
    chain(MODEL, market, off, START, 24 * 6)
    assert len(rec_on.calls) == len(rec_off.calls) > 3
    for (t1, prev1, w1), (t2, prev2, w2) in zip(rec_on.calls, rec_off.calls):
        assert t1 == t2 and prev1 == prev2 and w1.equals(w2)              # with X on, the base decides identically
    base_at = {t: set(w[w > 0].index) for t, _, w in rec_on.calls}
    longs = None
    shorts_seen = False
    for t, w in a:
        if t in base_at:
            longs = base_at[t]
        assert set(w[w > 0].index) == longs, t                           # the long set is always the base's
        shorts_seen |= bool((w < 0).any())
        assert not (set(w[w < 0].index) & longs)                          # shorts only in coins not held long
    assert shorts_seen


def test_adjustment_bounds_and_gross():
    rng = np.random.default_rng(1)
    for _ in range(200):
        n = rng.integers(1, 8)
        idx = [f"C{i}USDT" for i in range(n)]
        b = pd.Series(rng.uniform(0.01, 1.0 / n, n), index=idx)
        pred = pd.DataFrame({"mu1": rng.normal(0, 0.02, n), "mu3": rng.normal(0, 0.05, n), "q": 0.03}, index=idx)
        out, info = _orch_ml.adjust(b, pred, lambda c: 0.0005, P["ml"])
        assert ((out >= 0.5 * b - 1e-12) & (out <= 1.5 * b + 1e-12)).all()
        assert out.sum() <= b.sum() + 1e-12 and (out > 0).all()
        assert (out[~info.passed] == b[~info.passed]).all()               # filtered coins stay exactly at the base


def test_cost_filter_by_hand():
    b = pd.Series({"AUSDT": 0.2, "BUSDT": 0.2, "CUSDT": 0.2})
    spread = {"AUSDT": 0.0005, "BUSDT": 0.0, "CUSDT": 0.0}.get
    # round trip A = 2 (0.001 + 0.0005) = 0.003 -> needs |mu3| >= 0.006; B and C: 0.002 -> 0.004
    pred = pd.DataFrame({"mu1": [0.01, 0.01, 0.01], "mu3": [0.005, 0.005, -0.008], "q": 0.01}, index=b.index)
    out, info = _orch_ml.adjust(b, pred, spread, P["ml"])
    assert info.passed.tolist() == [False, True, True]
    # B: adj = clip(0.5 x 0.5, -0.5, 0.5) = 0.25 -> 0.25 · C: mu1 > 0 but mu3 < 0: signs differ -> adj 0 -> stays 0.2
    assert out["AUSDT"] == 0.2 and out["CUSDT"] == pytest.approx(0.2)
    # only B moved up: the moved coins may not exceed their base total, so B is scaled back to 0.2
    assert out["BUSDT"] == pytest.approx(0.2)
    pred2 = pd.DataFrame({"mu1": [0.01, 0.01, -0.01], "mu3": [0.005, 0.005, -0.008], "q": 0.01}, index=b.index)
    out2, _ = _orch_ml.adjust(b, pred2, spread, P["ml"])
    # B +0.25 -> 0.25, C adj = clip(0.5 x -0.8) = -0.4 -> 0.12; moved total 0.37 <= 0.4: no rescale
    assert out2["BUSDT"] == pytest.approx(0.25) and out2["CUSDT"] == pytest.approx(0.12) and out2["AUSDT"] == 0.2


def shock_market(market: Market, at: pd.Timestamp) -> Market:
    """BTC flat for 48 hours, then -6% in the hour ending at `at`, then flat: Pol's trigger (-5% over 4 hours) fires
    at at, at + 1h, at + 2h and at + 3h, so it is active from at through at + 26h."""
    close = market.close.copy()
    p0 = close.loc[at - 48 * H, "BTCUSDT"]
    close.loc[at - 48 * H: at - H, "BTCUSDT"] = p0
    close.loc[at:, "BTCUSDT"] = 0.94 * p0
    return replace(market, close=close)


def test_shock_trigger_and_response_by_hand(market):
    at = pd.Timestamp("2021-03-03 05:00", tz="UTC")
    mk = shock_market(market, at)
    s = P["shock"]
    assert not book_orch.shocked(view(mk, at - H, P), s) and book_orch.shocked(view(mk, at, P), s)
    assert book_orch.shocked(view(mk, at + 26 * H, P), s) and not book_orch.shocked(view(mk, at + 27 * H, P), s)
    p = params(shock={"enabled": True})
    prev = pd.Series({"ETHUSDT": 0.3, "AAAUSDT": 0.2, "BBBUSDT": -0.1})
    w = MODEL.targets(view(mk, at, p, prev))                             # turns on: longs x 0.5, shorts unchanged
    assert np.allclose(w[["ETHUSDT", "AAAUSDT"]], 0.5 * prev[["ETHUSDT", "AAAUSDT"]]) and w["BBBUSDT"] == prev["BBBUSDT"]
    w2 = MODEL.targets(view(mk, at + H, p, w))                            # still on: just held
    assert w2.equals(w)
    prev_at = w2
    off = at + 27 * H                                                     # 08:00: not a decision hour
    held = w2
    for k in range(2, 27):                                                # through the shock, incl. a 16:00 decision,
        tk = at + k * H                                                   # whose new longs are halved as well
        held = MODEL.targets(view(mk, tk, p, held))
        if tk.hour == 16:
            base = book_orch.base_model("baitoey_vt_mom").targets(replace(view(mk, tk, p["base_params"], prev=None),
                                                                           prev_targets=prev_at))
            assert np.allclose(held.sort_index(), 0.5 * base[base != 0].sort_index())
        prev_at = held
    w3 = MODEL.targets(view(mk, off, p, held))
    assert set(w3.index) == set(held.index)                               # the coins never change
    assert np.allclose(w3[w3 > 0], 2.0 * held[held > 0])                  # longs back to full
    cash = params(shock={"enabled": True, "response": "cash"})
    assert MODEL.targets(view(mk, at, cash, prev)).empty                  # Pol's response: cash while active
    assert not MODEL.targets(view(mk, off, cash, pd.Series(dtype=float))).empty   # then the base decides afresh


def test_short_sleeve_size_gate_and_candidates(market):
    t = pd.Timestamp("2021-03-05 16:00", tz="UTC")
    ml = fake_bundle(Lin(0, const=-0.05), Lin(0, const=-0.05), key="neg")
    p = params(short={"enabled": True, "candidates": "ml"}, ml=ml)
    v = view(market, t, p)
    bundle = _orch_ml.load("neg", "neg")
    longs = pd.Series({"BTCUSDT": 0.6, "ETHUSDT": 0.3})
    m = market_features(v, P["trend"])
    s = short_sleeve(v, longs, longs.index, p, bundle, {**m, "breadth": 0.1})
    assert 0 < len(s) <= 5 and (s < 0).all() and not (set(s.index) & set(longs.index))
    assert -s.sum() == pytest.approx(min(0.25, 1 - 0.9))                  # sleeve = min(25%, 1 - long gross)
    sig = book_orch.hourly_vol(v.close, t, list(s.index), 30)
    assert np.allclose(s / s.sum(), (1 / sig) / (1 / sig).sum())          # proportional to 1 / sigma
    assert short_sleeve(v, longs, longs.index, p, bundle, {**m, "breadth": 0.5}).empty   # gate off: closed
    small = pd.Series({"BTCUSDT": 0.1})
    assert -short_sleeve(v, small, small.index, p, bundle, {**m, "breadth": 0.1}).sum() == pytest.approx(0.25)
    ml2 = fake_bundle(Lin(0, const=-0.0001), Lin(0, const=-0.0001), key="tiny")   # too small to pay the costs
    assert short_sleeve(v, longs, longs.index, params(short={"enabled": True, "candidates": "ml"}, ml=ml2),
                        _orch_ml.load("tiny", "tiny"), {**m, "breadth": 0.1}).empty
    # without ML (the gate failed): coins in no up-trend at all (s_i = 0), the most negative 30-day return first
    pt = params(short={"enabled": True, "candidates": "trend"})
    st = short_sleeve(v, longs, longs.index, pt, None, {**m, "breadth": 0.1})
    cand = [c for c in book_orch.liquid_universe(v, P["trend"]) if c not in longs.index]
    sc = book_orch.trend_scores(v.close, t, cand, P["trend"])
    assert set(st.index) <= {c for c in cand if sc[c] == 0.0} and (st < 0).all()


def test_no_look_ahead_when_later_bars_change_or_vanish(market):
    ml = fake_bundle(Lin(0.3), Lin(1.0), q=0.02, key="la")
    p = params(ml={"enabled": True, **ml}, shock={"enabled": True},
               short={"enabled": True, "candidates": "ml", "breadth_max": 1.01})
    prev = pd.Series({"ETHUSDT": 0.3, "AAAUSDT": 0.2})
    for t in (pd.Timestamp("2021-03-05 16:00", tz="UTC"), pd.Timestamp("2021-03-06 03:00", tz="UTC")):
        w = MODEL.targets(view(market, t, p, prev))
        cut = replace(market, close=market.close.loc[:t], quote_volume=market.quote_volume.loc[:t])
        noisy = market.close.copy()
        noisy.loc[noisy.index > t] *= np.exp(np.random.default_rng(0).normal(0, 0.05, noisy.loc[noisy.index > t].shape))
        for mk in (cut, replace(market, close=noisy)):
            assert MODEL.targets(view(mk, t, p, prev)).equals(w)


def test_purge_no_label_ends_after_the_retrain_time():
    from backtest.orch_train import HOUR, LAG_HOURS, training_rows
    t = pd.date_range("2021-01-01 16:00", "2021-03-31 16:00", freq="D", tz="UTC")
    df = pd.DataFrame({"t": t, "y_mu1": 0.01, "y_mu3": 0.02, **{f: 1.0 for f in FEATURES}})
    complete = df[FEATURES].notna().all(axis=1)
    R = pd.Timestamp("2021-03-01 00:00", tz="UTC")
    for name, h in (("mu1", 24), ("mu3", 72)):
        tr = training_rows(df, complete, R, name)
        assert (tr.t + (LAG_HOURS + h) * HOUR <= R).all()
        nxt = df.t[df.t > tr.t.max()].min()                               # the next row would end after R
        assert nxt + (LAG_HOURS + h) * HOUR > R
    assert training_rows(df, complete, R, "mu1").t.max() == pd.Timestamp("2021-02-27 16:00", tz="UTC")
    assert training_rows(df, complete, R, "mu3").t.max() == pd.Timestamp("2021-02-25 16:00", tz="UTC")


def test_training_is_deterministic_and_the_manifest_hash_keys_the_run(market):
    pytest.importorskip("sklearn")
    from backtest.orch_train import fit
    from backtest.scoring.evaluate import run_key
    rng = np.random.default_rng(0)
    X, y = rng.normal(size=(3000, len(FEATURES))), rng.normal(size=3000)
    h = [hashlib.sha256(pickle.dumps(fit(X, y), protocol=4)).hexdigest() for _ in range(2)]
    assert h[0] == h[1]
    starts = pd.DatetimeIndex([pd.Timestamp("2021-03-01 12:00", tz="UTC")])
    a = params(ml={"manifest_sha256": "a" * 64})
    b = params(ml={"manifest_sha256": "b" * 64})
    assert run_key(MODEL, a, False, starts, CFG, market) != run_key(MODEL, b, False, starts, CFG, market)


def test_features_use_only_data_up_to_t(market):
    t = pd.Timestamp("2021-03-05 16:00", tz="UTC")
    v = view(market, t, P)
    f = coin_features(v, list(v.universe)[:5], pd.Series(dtype=float), P["trend"])
    cut = replace(market, close=market.close.loc[:t], quote_volume=market.quote_volume.loc[:t])
    g = coin_features(view(cut, t, P), list(v.universe)[:5], pd.Series(dtype=float), P["trend"])
    assert f.equals(g) and list(f.columns) == FEATURES
