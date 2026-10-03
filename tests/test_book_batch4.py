"""Batch 4 (reports/review/20261003-prereg-batch4.md): the shared trend signal and the four book_* models."""
from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import pytest

from backtest.data import Market, universe_at, universe_from_panel
from backtest.engine import compute_targets, decision_times
from backtest.evaluate import lookahead_check
from backtest.scoring.leakage import leakage_gate
from src.config import REPO_ROOT, load_config
from src.contracts import MarketView
from src.models import discover
from src.models.baitoey.baitoey_vt_mom import MODEL as VT_MOM
from src.models.book import book_coin_trend, book_vt_dual
from src.models.book._trend import breadth, exposure, hourly_vol, liquid_universe, trend_scores
from tests.synth import make_market

CFG = load_config()
M = CFG["models"]
BOOK = ["book_coin_trend", "book_vt_breadth", "book_vt_dual", "book_vt_top4"]
TREND = M["book_coin_trend"]["trend"]
UTC = "UTC"


@pytest.fixture(scope="module")
def market() -> Market:
    md = make_market()
    uni = universe_from_panel(md.close, md.quote_volume, top_n=10, min_history_days=45)
    return Market(md.close, md.quote_volume, uni, pd.Series(0.0005, index=md.close.columns), {"synthetic": True})


def view_at(mk: Market, t: str, params: dict, prev: dict | None = None) -> MarketView:
    t = pd.Timestamp(t, tz=UTC)
    i = mk.close.index.get_loc(t)
    return MarketView(t=t, close=mk.close.iloc[: i + 1], quote_volume=mk.quote_volume.iloc[: i + 1],
                      universe=universe_at(mk, t), params=params, prev_targets=pd.Series(prev or {}, dtype=float))


def times(mk: Market, a: str, b: str) -> pd.DatetimeIndex:
    return decision_times(mk.close.index, 24, 16, pd.Timestamp(a, tz=UTC), pd.Timestamp(b, tz=UTC))


# ---------------------------------------------------------------- settings

def test_settings_are_the_preregistered_defaults_and_come_from_config():
    vt = M["baitoey_vt_mom"]
    assert M["book_vt_top4"] == {**vt, "k": 4}                              # vt_mom's own block, k changed only
    assert M["book_vt_dual"]["vt"] == vt and M["book_vt_breadth"]["vt"] == vt
    assert M["book_vt_dual"]["trend"] == TREND == M["book_vt_breadth"]["trend"]
    assert TREND == {"lookback_days": [5, 10, 20, 30, 60], "up_threshold": 0.6, "max_stale_hours": 24,
                     "liquid_n": 20, "volume_days": 30}
    ct = {k: v for k, v in M["book_coin_trend"].items() if k != "trend"}
    assert ct == {"vol_days": 30, "max_weight": 0.25, "shorts": False, "short_breadth": 0.3, "short_scale": 0.5}
    assert {k: v for k, v in M["book_vt_breadth"].items() if k not in ("vt", "trend")} == \
        {"full_breadth": 0.6, "min_exposure": 0.25, "exposure_step": 0.25}
    assert set(M["book_vt_dual"]) == {"vt", "trend"}
    models = discover()
    for n in BOOK:
        s = models[n].spec
        assert s.author == "book" and s.rebalance_hours == 24 and not s.uses_shorts


def test_models_read_their_settings_from_the_view(market):
    t = "2021-03-01 16:00"
    four = discover()["book_vt_top4"].targets(view_at(market, t, M["book_vt_top4"]))
    two = discover()["book_vt_top4"].targets(view_at(market, t, {**M["book_vt_top4"], "k": 2}))
    assert len(two) == 2 and len(four) == 4
    p = M["book_coin_trend"]
    w = discover()["book_coin_trend"].targets(view_at(market, t, {**p, "max_weight": 0.01}))
    assert (w <= 0.01 + 1e-12).all()


# ---------------------------------------------------------------- the shared trend signal

def hand_panel() -> pd.DataFrame:
    """A: rises 0.1 an hour from Jan 1, flat from Feb 25 00:00. B: peaks at Feb 15 00:00 (200 - 0.1 x hours from
    the peak). C: listed Mar 10 00:00, rises. Hourly closes, close-time index."""
    idx = pd.date_range("2024-01-01 00:00", "2024-03-31 00:00", freq="h", tz=UTC)
    h = (idx - idx[0]) / pd.Timedelta(hours=1)
    flat = (pd.Timestamp("2024-02-25 00:00", tz=UTC) - idx[0]) / pd.Timedelta(hours=1)
    peak = (pd.Timestamp("2024-02-15 00:00", tz=UTC) - idx[0]) / pd.Timedelta(hours=1)
    listed = idx >= pd.Timestamp("2024-03-10 00:00", tz=UTC)
    return pd.DataFrame({"AUSDT": 100 + 0.1 * np.minimum(h, flat),
                         "BUSDT": 200 - 0.1 * np.abs(h - peak),
                         "CUSDT": np.where(listed, 50 + 0.1 * h, np.nan)}, index=idx)


# By hand (lookbacks 5, 10, 20, 30, 60 days; a lookback point before a coin's first close is unavailable):
# Feb 20 16:00: A rising at every point, t-60d = Dec 22 before Jan 1 -> 4/4 = 1.0.
#               B: 5.67 days after the peak; ret_L > 0 iff t - L is further from the peak, i.e. L > 2 x 5.67 = 11.3
#               -> L = 20, 30 of the 4 available -> 0.5.  C: not listed -> 0.
# Mar 1 16:00:  A: t-5d = Feb 25 16:00 is flat like t -> ret 0, not > 0; 10/20/30/60 rising (t-60d = Jan 1 16:00
#               exists) -> 4/5 = 0.8.  B: 15.67 days after -> L > 31.3 -> only 60 -> 0.2.  C: 0.
# Mar 20 16:00: A: t-5/10/20d (Mar 15, Mar 10, Feb 29) flat -> 0; 30 (Feb 19) and 60 rising -> 2/5 = 0.4.
#               B: 34.67 days after -> L > 69.3 -> none -> 0.0.  C: 10.67 days of history: 5 and 10 available
#               (t-10d = Mar 10 16:00), both rising; 20/30/60 before the listing -> 2/2 = 1.0.
HAND = {"2024-02-20 16:00": (1.0, 0.5, 0.0), "2024-03-01 16:00": (0.8, 0.2, 0.0), "2024-03-20 16:00": (0.4, 0.0, 1.0)}


@pytest.mark.parametrize("t, want", list(HAND.items()))
def test_trend_scores_by_hand(t, want):
    s = trend_scores(hand_panel(), pd.Timestamp(t, tz=UTC), ["AUSDT", "BUSDT", "CUSDT"], TREND)
    assert tuple(s.round(12)) == want


def test_trend_scores_less_than_five_days_or_no_close_is_zero():
    close = hand_panel()
    assert trend_scores(close, pd.Timestamp("2024-03-14 16:00", tz=UTC), ["CUSDT"], TREND)["CUSDT"] == 0.0
    stale = close.copy()
    stale.loc[stale.index > pd.Timestamp("2024-03-18 00:00", tz=UTC), "AUSDT"] = np.nan    # no close for 64 h
    assert trend_scores(stale, pd.Timestamp("2024-03-20 16:00", tz=UTC), ["AUSDT"], TREND)["AUSDT"] == 0.0


def test_trend_scores_look_up_by_timestamp_not_bar_count():
    close = hand_panel()
    t = pd.Timestamp("2024-03-01 16:00", tz=UTC)
    want = trend_scores(close, t, close.columns, TREND)
    # delete whole bars between the lookback points: a bar-count lookup would shift, a timestamp lookup does not
    drop = close.index[(close.index > pd.Timestamp("2024-02-02", tz=UTC)) & (close.index < pd.Timestamp("2024-02-03", tz=UTC))]
    pd.testing.assert_series_equal(trend_scores(close.drop(drop), t, close.columns, TREND), want)
    # a 17-hour gap ending at a lookback point uses the last close before it: A at t - 5d (Feb 25 16:00) falls
    # back to Feb 24 23:00, still rising and below the flat level, so ret_5 turns positive and s_A = 5/5
    gap = close.copy()
    gap.loc[pd.Timestamp("2024-02-25 00:00", tz=UTC): pd.Timestamp("2024-02-25 16:00", tz=UTC), "AUSDT"] = np.nan
    assert trend_scores(gap, t, ["AUSDT"], TREND)["AUSDT"] == 1.0
    # no close in the 24 h up to a lookback point: that lookback is unavailable. At Mar 1 00:00, t - 30d = Jan 31
    # 00:00 falls in a gap from Jan 29 12:00. Left: 5 (Feb 25 00:00, flat: 0), 10, 20 and 60 (t - 60d = Jan 1 00:00,
    # A's first close; 2024 is a leap year), all rising -> 3/4
    long_gap = close.copy()
    long_gap.loc[pd.Timestamp("2024-01-29 12:00", tz=UTC): pd.Timestamp("2024-01-31 00:00", tz=UTC), "AUSDT"] = np.nan
    assert trend_scores(long_gap, pd.Timestamp("2024-03-01 00:00", tz=UTC), ["AUSDT"], TREND)["AUSDT"] == 0.75
    assert trend_scores(close, pd.Timestamp("2024-03-01 00:00", tz=UTC), ["AUSDT"], TREND)["AUSDT"] == 0.8   # 4/5


def test_signal_ignores_bars_after_t(market):
    t = pd.Timestamp("2021-01-15 16:00", tz=UTC)
    v = view_at(market, "2021-01-15 16:00", {})
    rng = np.random.default_rng(1)
    after = market.close.index > t
    close_x, qv_x = market.close.copy(), market.quote_volume.copy()
    close_x.loc[after] *= rng.uniform(0.5, 2.0, close_x.loc[after].shape)
    qv_x.loc[after] *= rng.uniform(0.1, 10.0, qv_x.loc[after].shape)
    altered = dataclasses.replace(v, close=close_x, quote_volume=qv_x)      # future rows present and altered
    keep = ~after | (np.arange(len(after)) % 3 == 0)                        # two in three future rows deleted
    deleted = dataclasses.replace(v, close=close_x[keep], quote_volume=qv_x[keep])
    for w in (altered, deleted):
        pd.testing.assert_series_equal(trend_scores(w.close, t, v.universe, TREND), trend_scores(v.close, t, v.universe, TREND))
        assert breadth(w, TREND) == breadth(v, TREND)
        assert liquid_universe(w, TREND) == liquid_universe(v, TREND)
        pd.testing.assert_series_equal(hourly_vol(w.close, t, v.universe, 30), hourly_vol(v.close, t, v.universe, 30))


def test_liquid_universe_is_the_top_n_by_30_day_volume(market):
    v = view_at(market, "2021-01-15 16:00", {})
    p = {**TREND, "liquid_n": 3}
    got = liquid_universe(v, p)
    vol = v.quote_volume.loc[v.t - pd.Timedelta(days=30) + pd.Timedelta(hours=1): v.t, list(v.universe)].sum()
    assert got == list(vol.sort_values(ascending=False).index[:3]) and set(got) <= set(v.universe)
    assert len(liquid_universe(v, TREND)) == min(20, len(v.universe))


@pytest.mark.skipif(not (REPO_ROOT / "data/validation/universe.parquet").exists(), reason="no validation build here")
def test_real_universe_never_holds_a_stablecoin_or_excluded_coin():
    members = set(pd.read_parquet(REPO_ROOT / "data/validation/universe.parquet")["series"])
    u = CFG["validation"]["universe"]
    assert members and not members & (set(u["stablecoins"]) | set(u["exclude"]))


@pytest.mark.parametrize("b, e", [(0.0, 0.25), (0.1, 0.25), (0.3, 0.5), (0.35, 0.5), (0.375, 0.75), (0.4, 0.75),
                                  (0.45, 0.75), (0.5, 0.75), (0.55, 1.0), (0.6, 1.0), (1.0, 1.0)])
def test_exposure_is_clipped_and_rounded_half_up_to_quarters(b, e):
    assert exposure(b, M["book_vt_breadth"]) == e


# ---------------------------------------------------------------- the models

@pytest.mark.parametrize("name", BOOK)
def test_models_keep_the_contract_and_reproduce(name, market):
    model = discover()[name]
    p = M[name]
    tg = compute_targets(model, market, times(market, "2021-01-01 16:00", "2021-02-15 16:00"), p)   # raises on a break
    assert (tg.abs().sum(axis=1) <= 1 + 1e-9).all() and (tg >= 0).all().all()
    assert (tg.abs().sum(axis=1) > 0).any()
    assert lookahead_check(model, market, tg, p, n=4) == []


@pytest.mark.parametrize("name", BOOK)
def test_models_have_no_lookahead_and_no_io(name, market):
    model = discover()[name]
    p = M[name]
    tg = compute_targets(model, market, times(market, "2021-01-01 16:00", "2021-02-10 16:00"), p)
    out = leakage_gate(model, market, tg, p, {"decisions": 6, "seed": 3, "noise_sigma": 0.01})
    assert out["pass"], out


def same_frames(a: pd.DataFrame, b: pd.DataFrame):
    pd.testing.assert_frame_equal(a, b, check_exact=True)


def test_vt_dual_with_every_s_one_is_vt_mom(market, monkeypatch):
    monkeypatch.setattr(book_vt_dual, "trend_scores", lambda close, t, coins, p: pd.Series(1.0, index=list(coins)))
    ts = times(market, "2021-01-01 16:00", "2021-03-01 16:00")
    same_frames(compute_targets(discover()["book_vt_dual"], market, ts, M["book_vt_dual"]),
                compute_targets(VT_MOM, market, ts, M["baitoey_vt_mom"]))


def test_vt_breadth_with_exposure_one_is_vt_mom(market):
    ts = times(market, "2021-01-01 16:00", "2021-03-01 16:00")
    same_frames(compute_targets(discover()["book_vt_breadth"], market, ts, {**M["book_vt_breadth"], "min_exposure": 1.0}),
                compute_targets(VT_MOM, market, ts, M["baitoey_vt_mom"]))


def test_vt_top4_with_six_coins_is_vt_mom(market):
    ts = times(market, "2021-01-01 16:00", "2021-03-01 16:00")
    same_frames(compute_targets(discover()["book_vt_top4"], market, ts, {**M["book_vt_top4"], "k": 6}),
                compute_targets(VT_MOM, market, ts, M["baitoey_vt_mom"]))


def test_vt_mom_reads_only_which_coins_it_held(market):
    """Why book_vt_breadth may pass its scaled previous targets: vt_mom's decision is the same for any positive scale."""
    v = view_at(market, "2021-02-01 16:00", M["baitoey_vt_mom"])
    held = VT_MOM.targets(view_at(market, "2021-01-31 16:00", M["baitoey_vt_mom"]))
    base = VT_MOM.targets(dataclasses.replace(v, prev_targets=held))
    for scale in (0.25, 0.5, 0.75, 3.0):
        pd.testing.assert_series_equal(VT_MOM.targets(dataclasses.replace(v, prev_targets=held * scale)), base)


def filtered_vt(v: MarketView, kept: pd.Series) -> pd.Series:
    """vt_mom with the kept coins as its previous holdings, then the up-trend filter (the pre-registered rule)."""
    w = VT_MOM.targets(dataclasses.replace(v, params=M["baitoey_vt_mom"], prev_targets=kept))
    return w[trend_scores(v.close, v.t, w.index, TREND) >= TREND["up_threshold"]]


def test_vt_dual_after_a_drop_gives_vt_mom_only_the_kept_coins(market):
    model, p = discover()["book_vt_dual"], M["book_vt_dual"]
    ts = times(market, "2020-11-01 16:00", "2021-06-15 16:00")
    tg = compute_targets(model, market, ts, p)
    checked = 0
    for t0, t1 in zip(ts[:-1], ts[1:]):
        v0 = view_at(market, str(t0.tz_convert(None)), M["baitoey_vt_mom"])
        prev0 = tg.loc[ts[ts.get_loc(t0) - 1]] if ts.get_loc(t0) else pd.Series(dtype=float)
        prev0 = prev0[prev0 != 0]
        chosen = VT_MOM.targets(dataclasses.replace(v0, prev_targets=prev0))
        kept = tg.loc[t0][tg.loc[t0] != 0]
        if not set(chosen.index) - set(kept.index):
            continue                                                        # nothing dropped at t0
        v1 = view_at(market, str(t1.tz_convert(None)), p, prev=kept.to_dict())
        want = filtered_vt(v1, kept)
        pd.testing.assert_series_equal(model.targets(v1).sort_index(), want.sort_index(), check_names=False)
        got = tg.loc[t1][tg.loc[t1] != 0]                                   # and the engine's own sequence agrees
        pd.testing.assert_series_equal(got.sort_index(), want.sort_index(), check_names=False)
        checked += 1
    assert checked >= 3, "the sample needs days that drop a coin"


def test_vt_dual_holds_only_coins_in_an_up_trend_at_vt_moms_weights(market):
    p = M["book_vt_dual"]
    for t in ("2021-01-20 16:00", "2021-02-20 16:00", "2021-04-01 16:00"):
        for prev in ({}, {"BTCUSDT": 0.1}):
            v = view_at(market, t, p, prev=prev)
            w = discover()["book_vt_dual"].targets(v)
            if len(w):
                assert (trend_scores(v.close, v.t, w.index, TREND) >= TREND["up_threshold"]).all()
            full = VT_MOM.targets(dataclasses.replace(v, params=p["vt"]))
            assert set(w.index) <= set(full.index) and all(w[c] == full[c] for c in w.index)   # same weights, rest cash


def coin_trend_at(market, t, monkeypatch, s=None, **over):
    if s is not None:
        monkeypatch.setattr(book_coin_trend, "trend_scores", lambda close, tt, coins, q: pd.Series(s, index=list(coins)))
    v = view_at(market, t, {**M["book_coin_trend"], **over})
    return v, discover()["book_coin_trend"].targets(v)


@pytest.mark.parametrize("t", ["2020-11-01 16:00", "2021-01-15 16:00", "2021-04-20 16:00"])
def test_coin_trend_weights_are_long_capped_and_at_most_one(market, monkeypatch, t):
    _, w = coin_trend_at(market, t, monkeypatch)
    assert (w > 0).all() and w.sum() <= 1 + 1e-12 and (w <= 0.25 + 1e-12).all()


def test_coin_trend_is_cash_when_nothing_trends(market, monkeypatch):
    _, w = coin_trend_at(market, "2021-01-15 16:00", monkeypatch, s=0.0)
    assert w.empty


def test_coin_trend_is_inverse_volatility_when_everything_trends(market, monkeypatch):
    v, w = coin_trend_at(market, "2021-01-15 16:00", monkeypatch, s=1.0)
    inv = 1.0 / hourly_vol(v.close, v.t, liquid_universe(v, TREND), 30)
    inv = inv[np.isfinite(inv)]
    want = (inv / inv.sum()).clip(upper=0.25)
    assert (want < 0.25).all()                                              # the cap does not bind here
    pd.testing.assert_series_equal(w.sort_index(), want[want != 0].sort_index(), check_names=False)
    assert w.sum() == pytest.approx(1.0)


def test_coin_trend_variant_shorts_only_broken_coins_in_a_broken_market(market, monkeypatch):
    v, w = coin_trend_at(market, "2021-01-15 16:00", monkeypatch, s=0.0, shorts=True)
    inv = 1.0 / hourly_vol(v.close, v.t, liquid_universe(v, TREND), 30)
    inv = inv[np.isfinite(inv)]
    want = (-0.5 * inv / inv.sum()).clip(lower=-0.25)
    pd.testing.assert_series_equal(w.sort_index(), want.sort_index(), check_names=False)
    assert w.abs().sum() <= 1 + 1e-12
    _, w = coin_trend_at(market, "2021-01-15 16:00", monkeypatch, s=1.0, shorts=True)
    assert (w > 0).all()                                                    # breadth 1: no shorts
