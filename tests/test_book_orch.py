"""book_orch v2 (reports/review/20261003-prereg-orch-v2.md, section 6): layers off = the base held between decisions,
the layers on hand-built cases, no look-ahead (features, model, stored forecasts), the purge, labels, and
deterministic training. A hand-built forecast store stands in for the trained one; only the training tests need
scikit-learn (they skip without it), and the stored-vs-live check also needs the trained artifacts."""
from __future__ import annotations

import copy
import hashlib
import json
import pickle
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from backtest.data import Market, universe_at, universe_from_panel
from backtest.engine import view_frames
from src.config import load_config, resolve
from src.contracts import MarketView, check_targets
from src.models.baitoey.baitoey_vt_mom import MODEL as VT_MOM
from src.models.book import _orch_ml, book_orch
from src.models.book._orch_features import FEATURES, feature_frame, features_at
from src.models.book._trend import hourly_vol, trend_scores
from src.models.book.book_orch import MODEL, f_full, fs_layer, run_base
from tests.synth import make_market

CFG = load_config()
P = CFG["models"]["book_orch"]
H = pd.Timedelta(hours=1)
T0 = pd.Timestamp("2021-03-01 16:00", tz="UTC")          # a 16:00 UTC base decision


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


def chain(model, market, p, start, hours, prev=None):
    """Hourly decisions, each given the previous one (as the engine's compute_targets does); checked by contract."""
    out, prev = [], pd.Series(dtype=float) if prev is None else prev
    for k in range(hours):
        t = start + k * H
        v = view(market, t, p, prev)
        w = check_targets(model.targets(v), v, model.spec)
        out.append((t, prev, w))
        prev = w
    return out


def fake_store(rows: list[dict], key: str) -> dict:
    """A forecast store from hand-built rows (t, coin, pf, pr and optionally e8, pbar_fall, pbar_rise); the same
    probabilities at every horizon. Returns the forecasts parameters that point the model at it."""
    out = []
    for r in rows:
        d = {"t": r["t"], "coin": r["coin"], "retrain": r["t"], "pbar_fall": r.get("pbar_fall", 0.3),
             "pbar_rise": r.get("pbar_rise", 0.3), "e8": r.get("e8", 0.0), "sigma8": 0.02}
        for h in (2, 4, 8):
            d[f"pf{h}"], d[f"pr{h}"], d[f"pn{h}"] = r["pf"], r["pr"], 1.0 - r["pf"] - r["pr"]
        out.append(d)
    df = _orch_ml.add_signals(pd.DataFrame(out).sort_values(["t", "coin"]).reset_index(drop=True))
    st = _orch_ml.Store(key, df, df.t.to_numpy(dtype="datetime64[ns]").astype(np.int64), {}, 0.0005, df.t.min())
    _orch_ml._CACHE[(key, key)] = st
    return {"manifest": key, "manifest_sha256": key}


NEUTRAL = {"pf": 0.3, "pr": 0.3}
FALL = {"pf": 0.6, "pr": 0.1}                         # fall margin 0.30: confident and strong
CLEAR = {"pf": 0.2, "pr": 0.4}                        # q = +0.2, no confident fall


# ------------------------------------------------------------- every layer off -----------------------------------------

def test_every_layer_off_is_the_base_held_between_decisions(market):
    p = params()
    start = pd.Timestamp("2021-03-01 12:00", tz="UTC")              # a window's first hour, as the scoring tool
    for t, prev, w in chain(MODEL, market, p, start, 52):
        longs = prev[prev > 0]
        if t.hour == 16 or longs.empty:
            b = VT_MOM.targets(view(market, t, p["base_params"], longs))
            assert np.allclose(w.reindex(b.index).to_numpy(), b.to_numpy(), atol=1e-15) and set(w.index) == set(b.index)
        else:
            assert w.equals(prev)


# ------------------------------------------------------------- R, E ---------------------------------------------------

def test_R_weights_are_inverse_vol_at_the_base_gross(market):
    p = params(size={"enabled": True})
    v = view(market, T0, p)
    B = run_base(v, pd.Series(dtype=float), p)
    w = MODEL.targets(v)
    sig = hourly_vol(v.close, T0, list(B.index), 30)
    assert set(w.index) == set(B.index) and abs(w.sum() - B.sum()) < 1e-12
    x = (w * sig.reindex(w.index)).to_numpy()
    assert np.allclose(x, x[0], rtol=1e-12)


def test_E_stages_new_coins_and_tops_them_up_at_midnight_unless_broken(market, monkeypatch):
    p = params(stage={"enabled": True})
    v = view(market, T0, p)
    B = run_base(v, pd.Series(dtype=float), p)
    s = trend_scores(v.close, T0, list(B.index), p["trend"])
    sig = hourly_vol(v.close, T0, list(B.index), 30)
    full = [c for c in B.index if s[c] == 1.0 and sig[c] < sig.median()]
    half = [c for c in B.index if c not in full]
    assert half, "the synthetic case needs at least one staged coin"
    w = MODEL.targets(v)
    for c in B.index:
        assert w[c] == pytest.approx(B[c] * (1.0 if c in full else 0.5), rel=1e-12)
    monkeypatch.setattr(book_orch, "breakdown_blocked", lambda close, qv, vp: {half[0]})
    out = chain(MODEL, market, p, T0 + H, 8, prev=w)                 # 17:00 ... 00:00 UTC
    for t, prev, x in out[:-1]:
        assert x.equals(prev)                                        # nothing moves before 00:00
    t, _, x = out[-1]
    assert t.hour == 0
    for c in B.index:
        exp = B[c] if c in full or (c in half and c != half[0]) else 0.5 * B[c]
        assert x[c] == pytest.approx(exp, rel=1e-12), c
    # a held coin is not staged again at the next decision: it goes to the base's weight
    nxt = chain(MODEL, market, p, T0 + 24 * H, 1, prev=x)[0][2]
    b2 = VT_MOM.targets(view(market, T0 + 24 * H, p["base_params"], x))
    for c in set(b2.index) & set(x.index):
        assert nxt[c] == pytest.approx(b2[c], rel=1e-12)


# ------------------------------------------------------------- F ------------------------------------------------------

def test_F_multiplier_filter_and_rescale_by_hand():
    p = params(forecast_longs={"enabled": True})
    L = pd.Series({"A": 0.2, "B": 0.2, "C": 0.2, "D": 0.1})
    t = pd.Timestamp("2021-03-01 16:00", tz="UTC")
    rows = [{"t": t, "coin": "A", "pf": 0.1, "pr": 0.6, "e8": 0.05},      # q = +0.5, gain clears -> 1.5
            {"t": t, "coin": "B", "pf": 0.15, "pr": 0.55, "e8": 0.05},    # q = +0.4 -> 1.4
            {"t": t, "coin": "C", "pf": 0.4, "pr": 0.2, "e8": -0.05},     # q = -0.2, loss clears -> 0.8
            {"t": t, "coin": "D", "pf": 0.1, "pr": 0.6, "e8": 0.001}]     # q = +0.5, but 0.1% < 2 round trips -> 1
    fake_store(rows, "fhand")
    fc = _orch_ml._CACHE[("fhand", "fhand")].at(t)
    full, out, m = f_full(L, fc, p, lambda c: 0.0005)
    assert out == set() and m.to_dict() == pytest.approx({"A": 1.5, "B": 1.4, "C": 0.8, "D": 1.0})
    assert full.sum() == pytest.approx(L.sum())                          # 0.30 + 0.28 + 0.16 + 0.10 > 0.70: rescaled
    assert full["C"] == pytest.approx(0.16) and full["D"] == pytest.approx(0.10)   # m <= 1 untouched
    assert full["A"] / full["B"] == pytest.approx(1.5 / 1.4)


def test_F_exits_on_a_confident_fall_and_reenters_when_clear(market, monkeypatch):
    calls = []

    class Rec:
        spec = VT_MOM.spec

        def targets(self, v):
            calls.append((v.t, tuple(sorted(v.prev_targets[v.prev_targets > 0].index))))
            return VT_MOM.targets(v)

    monkeypatch.setitem(book_orch._BASES, "baitoey_vt_mom", Rec())
    book_orch._B_CACHE.clear()
    p0 = params()
    B = run_base(view(market, T0, p0), pd.Series(dtype=float), p0)
    a, b = sorted(B.index)[:2]
    rows = []
    for k in range(0, 25):
        t = T0 + k * H
        for c in B.index:
            r = NEUTRAL
            if c == a and t == T0:
                r = FALL                                                  # new coin with a confident fall: waits
            if c == b and T0 + 3 * H <= t < T0 + 6 * H:
                r = FALL                                                  # held coin: exits at +3 h
            if c == b and t == T0 + 6 * H:
                r = {"pf": 0.35, "pr": 0.32}                             # no confident fall, but q < 0: still out
            if c == b and t >= T0 + 7 * H:
                r = CLEAR
            rows.append({"t": t, "coin": c, **r})
    p = params(forecast_longs={"enabled": True}, forecasts=fake_store(rows, "fchain"))
    out = {t: w for t, _, w in chain(MODEL, market, p, T0, 25)}
    assert a not in out[T0] and b in out[T0]
    assert a in out[T0 + H]                                               # q = 0 and no confident fall: enters
    assert b in out[T0 + 2 * H] and b not in out[T0 + 3 * H] and b not in out[T0 + 6 * H]
    assert out[T0 + 7 * H][b] == pytest.approx(B[b], rel=1e-12)           # back at the base's weight
    assert sum(out[T0 + 7 * H].values) <= B.sum() + 1e-12
    held_at_next = [x for x in calls if x[0] == T0 + 24 * H]
    assert held_at_next and held_at_next[0][1] == tuple(sorted(out[T0 + 23 * H].index))   # option 2


# ------------------------------------------------------------- FS -----------------------------------------------------

def _fs_fc(t, rows):
    key = f"fs{len(rows)}{rows[0]['coin']}{t.value}"
    st = _orch_ml._CACHE[tuple([fake_store(rows, key)["manifest"]] * 2)]
    return st.at(t)


def test_FS_sizes_ranking_limits_and_room():
    p = params(forecast_shorts={"enabled": True})
    t = pd.Timestamp("2021-03-01 05:00", tz="UTC")
    rows = [{"t": t, "coin": c, "pf": pf, "pr": 0.1, "e8": e8} for c, pf, e8 in
            [("B", 0.60, -0.05), ("C", 0.56, -0.05), ("D", 0.48, -0.05), ("E", 0.46, -0.05), ("F", 0.47, -0.05),
             ("G", 0.70, -0.001), ("A", 0.70, -0.05)]]
    fc = _fs_fc(t, rows)
    v = MarketView(t=t, close=pd.DataFrame(), quote_volume=pd.DataFrame(), universe=tuple("ABCDEFG"), params=p)
    longs = pd.Series({"A": 0.5})
    tr = book_orch.Trace()
    S = fs_layer(v, longs, pd.Series(dtype=float), fc, p, lambda c: 0.0005, 0.015, tr)
    # A is long; G's expected drop is too small; ranked B (0.30) and C (0.26), both strong, then D, F (E is fifth)
    assert S.to_dict() == pytest.approx({"B": -0.05, "C": -0.05, "D": -0.02, "F": -0.02})
    assert tr.rows["G"]["decision"] == "no_short" and tr.rows["E"]["decision"] == "no_short"
    S2 = fs_layer(v, pd.Series({"A": 0.9}), pd.Series(dtype=float), fc, p, lambda c: 0.0005, 0.015, book_orch.Trace())
    assert S2.to_dict() == pytest.approx({"B": -0.05, "C": -0.05})       # room 0.10; then 0 left
    S3 = fs_layer(v, pd.Series({"A": 0.92}), pd.Series(dtype=float), fc, p, lambda c: 0.0005, 0.015, book_orch.Trace())
    assert S3.to_dict() == pytest.approx({"B": -0.05, "C": -0.03})       # the second cut to the room left (> band)


def test_FS_closes_on_base_rate_long_target_and_room():
    p = params(forecast_shorts={"enabled": True})
    t = pd.Timestamp("2021-03-01 05:00", tz="UTC")
    rows = [{"t": t, "coin": "B", "pf": 0.29, "pr": 0.3}, {"t": t, "coin": "C", "pf": 0.5, "pr": 0.1},
            {"t": t, "coin": "D", "pf": 0.46, "pr": 0.1}, {"t": t, "coin": "E", "pf": 0.6, "pr": 0.1}]
    fc = _fs_fc(t, rows)
    v = MarketView(t=t, close=pd.DataFrame(), quote_volume=pd.DataFrame(), universe=tuple("ABCDEF"), params=p)
    prev = pd.Series({"B": -0.02, "C": -0.05, "D": -0.02, "E": -0.05, "F": -0.02})
    tr = book_orch.Trace()
    S = fs_layer(v, pd.Series({"E": 0.3}), prev, fc, p, lambda c: 0.0005, 0.015, tr)
    # B: below its base rate; E: in the long target; F: no forecast; C and D held at their sizes
    assert S.to_dict() == pytest.approx({"C": -0.05, "D": -0.02})
    assert {c: tr.rows[c]["decision"] for c in "BEF"} == {"B": "close_short", "E": "close_short", "F": "close_short"}
    S2 = fs_layer(v, pd.Series({"A": 0.94}), prev.drop(["B", "E", "F"]), fc, p, lambda c: 0.0005, 0.015, book_orch.Trace())
    assert S2.to_dict() == pytest.approx({"C": -0.05})                   # room 0.06: the weakest (D) closes first


def test_all_layers_on_keep_the_contract_and_gross(market):
    rows = [{"t": T0 + k * H, "coin": c, **(FALL if (k + j) % 5 == 0 else CLEAR if (k + j) % 3 == 0 else NEUTRAL),
             "e8": -0.05 if (k + j) % 5 == 0 else 0.03}
            for k in range(30) for j, c in enumerate(market.close.columns)]
    p = params(size={"enabled": True}, stage={"enabled": True}, forecast_longs={"enabled": True},
               forecast_shorts={"enabled": True}, forecasts=fake_store(rows, "allon"))
    out = chain(MODEL, market, p, T0, 30)
    assert all(w.abs().sum() <= 1.0 + 1e-12 for _, _, w in out)
    assert any((w < 0).any() for _, _, w in out) and all((w > 0).any() for _, _, w in out)
    v5 = view(market, T0 + 5 * H, p, out[4][2])
    w, rec = MODEL.explain(v5)
    assert w.equals(out[5][2]) and rec and all({"decision", "reason"} <= set(r) for r in rec.values())
    log = book_orch.coin_log(v5, w, rec, _orch_ml._CACHE[("allon", "allon")].at(v5.t), p)
    assert {r["coin"] for r in log} >= set(w.index) | set(rec)
    for r in log:
        assert set(r) == {"coin", "hour", "signals", "probabilities", "decision", "reason", "size"}
        assert r["size"] == pytest.approx(float(w.get(r["coin"], 0.0)))
        json.dumps(r)                                                    # one JSON line per record


# ------------------------------------------------------------- no look-ahead ------------------------------------------

def test_no_look_ahead_when_later_bars_change_or_vanish(market):
    rows = [{"t": T0 + k * H, "coin": c, **(FALL if (k + j) % 4 == 0 else CLEAR), "e8": -0.05 if (k + j) % 4 == 0 else 0.03}
            for k in range(30) for j, c in enumerate(market.close.columns)]
    p = params(size={"enabled": True}, stage={"enabled": True}, forecast_longs={"enabled": True},
               forecast_shorts={"enabled": True}, forecasts=fake_store(rows, "la"))
    out = chain(MODEL, market, p, T0, 12)
    for t, prev, w in (out[0], out[3], out[8]):
        cut = replace(market, close=market.close.loc[:t], quote_volume=market.quote_volume.loc[:t])
        noisy = market.close.copy()
        later = noisy.index > t
        noisy.loc[later] *= np.exp(np.random.default_rng(0).normal(0, 0.05, noisy.loc[later].shape))
        for mk in (cut, replace(market, close=noisy)):
            book_orch._B_CACHE.clear()
            assert MODEL.targets(view(mk, t, p, prev)).equals(w)


def test_features_use_only_data_up_to_t_and_match_the_live_path(market):
    trend = P["trend"]
    times = pd.DatetimeIndex([pd.Timestamp("2021-03-05 16:00", tz="UTC"), pd.Timestamp("2021-04-02 03:00", tz="UTC")])
    full = feature_frame(market.close, market.quote_volume, times, lambda t: universe_at(market, t), trend)
    assert list(full.columns) == ["t", "coin"] + FEATURES and len(FEATURES) == 37
    for t in times:
        a = full[full.t == t].set_index("coin")[FEATURES]
        cut = feature_frame(market.close.loc[:t], market.quote_volume.loc[:t], [t], lambda x: universe_at(market, x),
                            trend).set_index("coin")[FEATURES]
        noisy = market.close.copy()
        noisy.loc[noisy.index > t] *= 3.0
        b = feature_frame(noisy, market.quote_volume, [t], lambda x: universe_at(market, x), trend).set_index("coin")[FEATURES]
        live = features_at(view(market, t, P), trend)
        for other in (cut, b, live):
            assert list(other.index) == list(a.index)
            assert np.allclose(other.to_numpy(), a.to_numpy(), rtol=1e-9, atol=1e-12, equal_nan=True)


# ------------------------------------------------------------- labels, purge, training ---------------------------------

def test_labels_by_hand():
    from backtest.orch_train import add_labels
    idx = pd.date_range("2021-01-01 00:00", periods=20, freq="h", tz="UTC")
    close = pd.DataFrame({"X": 100.0 * np.ones(20)}, index=idx)
    close.iloc[1:, 0] = [100, 100.3, 100.6, 101, 99, 100, 100, 100, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
    close.iloc[6, 0] = np.nan                                             # a gap at 06:00
    df = pd.DataFrame({"t": idx[:5], "coin": "X"})
    out = add_labels(df, close, pd.Series({"X": 0.0005}))
    assert out.c.iloc[0] == pytest.approx(0.003)
    # t = 00:00: entry 01:00 (100), exits 03:00 (100.6, +0.6% > 0.3%: rise), 05:00 (99: fall), 09:00 (100: flat)
    assert out.r2.iloc[0] == pytest.approx(0.006) and out.y2.iloc[0] == 2
    assert out.y4.iloc[0] == 0 and out.y8.iloc[0] == 1
    # t = 01:00: the 4-hour exit is at 06:00, a gap: dropped
    assert out.y4.iloc[1] == -1 and np.isnan(out.r4.iloc[1])
    # t = 05:00 is not a row; t = 04:00: entry 05:00 (99), 2-hour exit 07:00 (100): +1.01% rise
    assert out.y2.iloc[4] == 2


def _toy_rows(n_hours=24 * 70, coins=("A", "B", "C", "D")):
    rng = np.random.default_rng(1)
    t = pd.date_range("2021-01-01 00:00", periods=n_hours, freq="h", tz="UTC")
    df = pd.DataFrame({"t": np.repeat(t, len(coins)), "coin": np.tile(coins, n_hours)})
    X = rng.normal(size=(len(df), len(FEATURES)))
    df[FEATURES] = X
    for h in (2, 4, 8):
        r = 0.01 * X[:, 0] + rng.normal(0, 0.01, len(df))
        df[f"r{h}"] = r
        df[f"y{h}"] = np.where(r > 0.003, 2, np.where(r < -0.003, 0, 1)).astype(np.int8)
    df.loc[df.index % 97 == 0, "y8"] = -1
    df["c"] = 0.003
    df["sigma8"] = 0.02
    return df


def test_purge_S_window_and_L_weights():
    from backtest import orch_train as O
    df = _toy_rows()
    Ts = pd.DatetimeIndex([pd.Timestamp("2021-02-22 16:00", tz="UTC"), pd.Timestamp("2021-03-01 16:00", tz="UTC")])
    O._init_globals(df, "real", Ts, "unused", False)
    for k in range(len(Ts)):
        T = int(Ts.asi8[k])
        for h in (2, 4, 8):
            iL, iS = O.training_index(T, h)
            t = O.G["t"]
            assert (t[iL] + (1 + h) * int(H.value) < T).all()               # every label known before T
            nxt = t[(t > t[iL].max()) & O.G["train"] & (O.G["lab"][f"y{h}"] >= 0)].min()
            assert nxt + (1 + h) * int(H.value) >= T                        # the next training row would not be
            assert set(pd.DatetimeIndex(t[iL], tz="UTC").hour) <= set(O.TRAIN_HOURS)
            assert (O.G["lab"][f"y{h}"][iL] >= 0).all()
            assert (t[iS] > T - 180 * int(pd.Timedelta(days=1).value)).all()
            assert set(iS) <= set(iL)
    assert O.retrain_times(pd.Timestamp("2020-06-01 16:00", tz="UTC"), pd.Timestamp("2021-07-01", tz="UTC"))[0] == \
        pd.Timestamp("2021-06-07 16:00", tz="UTC")


def test_shuffles_keep_the_labels_and_move_them():
    from backtest import orch_train as O
    df = _toy_rows(24 * 10)
    train = np.isin(df.t.dt.hour.to_numpy(), O.TRAIN_HOURS)
    real = O.shuffled_labels(df, "real", train)
    for kind in ("shuffled", "shuffled_hour"):
        s = O.shuffled_labels(df, kind, train)
        assert (s["y8"][~train] == real["y8"][~train]).all()
        assert sorted(s["y8"][train]) == sorted(real["y8"][train]) and (s["y8"] != real["y8"]).any()
        assert (s["r8"] != real["r8"]).any()
    sh = O.shuffled_labels(df, "shuffled_hour", train)
    for _, g in df[train].groupby("t"):
        assert sorted(sh["r8"][g.index]) == sorted(df.r8.to_numpy()[g.index])


def test_training_is_deterministic_and_the_manifest_hash_keys_the_run(market, tmp_path):
    pytest.importorskip("sklearn")
    from backtest import orch_train as O
    from backtest.scoring.evaluate import run_key
    df = _toy_rows()
    Ts = pd.DatetimeIndex([pd.Timestamp("2021-03-01 16:00", tz="UTC")])
    res = []
    for k in range(2):
        O._init_globals(df, "real", Ts, tmp_path / f"run{k}", True)
        res.append(O.fit_task((0, 8)))
    a, b = res
    assert np.array_equal(a["PL"], b["PL"]) and np.array_equal(a["PS"], b["PS"])
    assert {n: f["sha256"] for n, f in a["files"].items()} == {n: f["sha256"] for n, f in b["files"].items()}
    starts = pd.DatetimeIndex([pd.Timestamp("2021-03-01 12:00", tz="UTC")])
    pa = params(forecasts={"manifest_sha256": "a" * 64})
    pb = params(forecasts={"manifest_sha256": "b" * 64})
    assert run_key(MODEL, pa, False, starts, CFG, market) != run_key(MODEL, pb, False, starts, CFG, market)


def test_stored_forecasts_equal_the_live_path_on_real_data():
    pytest.importorskip("sklearn")
    path = resolve(P["forecasts"]["manifest"])
    if not path.exists() or P["forecasts"]["manifest_sha256"] == "PENDING":
        pytest.skip("the trained forecaster is not available")
    raw = path.read_bytes()
    m = json.loads(raw)
    if not resolve(m["forecasts"]["path"]).exists():
        pytest.skip("the stored forecasts are not available")
    from backtest.data import load_market
    sha = hashlib.sha256(raw).hexdigest()
    mk = load_market(CFG)
    st = _orch_ml.load(P["forecasts"]["manifest"], sha)
    rng = np.random.default_rng(0)
    hours = st.df.t.drop_duplicates().to_numpy()
    for t in pd.DatetimeIndex(rng.choice(hours, 6, replace=False)):
        c, q = view_frames(mk.close, mk.quote_volume, t)
        v = MarketView(t=t, close=c, quote_volume=q, universe=universe_at(mk, t))
        a, b = st.at(t), _orch_ml.live(v, P["forecasts"]["manifest"], sha, P["trend"])
        cols = _orch_ml.PROB_COLS + ["e8", "pbar_fall", "pbar_rise"]
        assert list(a.index) == list(b.index)
        assert np.allclose(a[cols].to_numpy(dtype=float), b[cols].to_numpy(dtype=float), atol=1e-12, equal_nan=True)
