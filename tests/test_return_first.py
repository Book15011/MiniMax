"""Return-first score (scoring v2), pre-registered in reports/review/20261002-prereg-return-first.md, PART 6.1:
weights and the direction rebalance, the bars, HIT and HEADLINE_RET by hand, the month bootstrap, the LENIENT
constant, the 15 + 15 day buckets of a 12:00 UTC start, and the first decision at the window start."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest.data import Market, universe_from_panel
from backtest.engine import Costs, Simulator, compute_targets, decision_times
from backtest.scoring.evaluate import bucket_of, first_decisions
from backtest.scoring.metrics import day_points, returns
from backtest.scoring.returnfirst import (bar_table, boot_headline, cs_hit, headline_ret, hits, month_multiplicity,
                                          pick_order, tie_test)
from backtest.scoring.windows import final_weights
from src.config import REPO_ROOT, load_config
from src.contracts import ModelSpec
from tests.synth import make_market

CFG = load_config()
SC = CFG["scoring"]
SPLIT = SC["headline"]
LB_FILE = REPO_ROOT / "results" / "pol" / "20261001-final" / "past_leaderboards_numeric.csv"
CUT_HK, CUT_SG = -0.0141860899999999, -0.0157443399999999       # the #20 final returns of rounds 455 and 456


# ---------------- weights ----------------

def test_final_weights_by_hand():
    idx = pd.date_range("2024-01-01 12:00", periods=4, freq="D", tz="UTC")
    ll, rec = pd.Series([1.0, 2.0, 3.0, 4.0], index=idx), pd.Series([4.0, 3.0, 2.0, 1.0], index=idx)
    up = pd.Series([True, False, True, False], index=idx)
    w, wf, pi_up = final_weights(ll, rec, up, SPLIT)
    # w = 0.7 LL / 10 + 0.3 REC / 10 = [0.19, 0.23, 0.27, 0.31]; pi_up = 2 / 4
    assert w.tolist() == pytest.approx([0.19, 0.23, 0.27, 0.31], abs=1e-15) and pi_up == 0.5
    # UP: 0.19, 0.27 (sum 0.46) -> x 0.5 / 0.46 · DOWN: 0.23, 0.31 (sum 0.54) -> x 0.5 / 0.54
    assert wf.tolist() == pytest.approx([0.19 * 0.5 / 0.46, 0.23 * 0.5 / 0.54, 0.27 * 0.5 / 0.46, 0.31 * 0.5 / 0.54], abs=1e-15)


def test_final_weights_sum_to_one_and_up_share_is_pi_up():
    rng = np.random.default_rng(11)
    idx = pd.date_range("2021-01-01 12:00", periods=500, freq="D", tz="UTC")
    up = pd.Series(rng.random(500) < 0.37, index=idx)
    w, wf, pi_up = final_weights(pd.Series(rng.random(500), index=idx), pd.Series(rng.random(500), index=idx), up, SPLIT)
    assert w.sum() == pytest.approx(1.0, abs=1e-12) and wf.sum() == pytest.approx(1.0, abs=1e-12)
    assert pi_up == up.mean() and wf[up].sum() == pytest.approx(pi_up, abs=1e-12)
    assert (wf > 0).all()


# ---------------- bars, HIT, HEADLINE_RET, CS_HIT ----------------

IDX5 = pd.date_range("2024-03-01 12:00", periods=5, freq="D", tz="UTC")
UP5 = pd.Series([True, False, False, True, False], index=IDX5)
FIELD5 = pd.DataFrame([[0.01, 0.02, 0.03, 0.04, 0.05, 0.06],          # median 0.035
                       [-0.05, -0.04, -0.03, -0.02, -0.01, 0.00],      # median -0.025 -> STRICT 0
                       [-0.01, 0.00, 0.01, 0.02, 0.03, 0.04],          # median 0.015
                       [-0.01] * 6,                                    # median -0.01 -> STRICT 0
                       [0.1, 0.1, 0.1, -0.1, -0.1, -0.1]], index=IDX5)  # median 0
W5 = pd.Series([0.1, 0.2, 0.3, 0.15, 0.25], index=IDX5)


def test_bars_on_five_hand_built_windows():
    b = bar_table(UP5, FIELD5, SC["bars"])
    d = SC["bars"]["LENIENT"]["down"]
    assert b.LENIENT.tolist() == [0.0, d, d, 0.0, d]                   # UP windows 0%, DOWN windows the #20 cut
    assert b.MIDDLE.tolist() == [0.0] * 5
    assert b.STRICT.tolist() == pytest.approx([0.035, 0.0, 0.015, 0.0, 0.0], abs=1e-15)


def test_hit_and_headline_ret_by_hand():
    b = bar_table(UP5, FIELD5, SC["bars"])
    a = pd.Series([0.01, -0.01, 0.02, -0.005, -0.02], index=IDX5)
    # LENIENT: 1, 2, 3 clear (-0.005 < 0 in an UP window; -0.02 < -1.4965%) -> 0.1 + 0.2 + 0.3
    # MIDDLE: 1 and 3 -> 0.4 · STRICT: only 3 (0.02 >= 0.015; 0.01 < 0.035) -> 0.3
    ha = hits(a, b, W5)
    assert ha == pytest.approx({"LENIENT": 0.6, "MIDDLE": 0.4, "STRICT": 0.3}, abs=1e-15)
    assert headline_ret(ha) == pytest.approx(1.3 / 3, abs=1e-15)
    bb = pd.Series([0.04, 0.0, -0.015, 0.0, 0.0], index=IDX5)
    # -0.015 misses LENIENT's -0.014965215 (and the other two); every other window clears all three bars
    hb = hits(bb, b, W5)
    assert hb == pytest.approx({"LENIENT": 0.7, "MIDDLE": 0.7, "STRICT": 0.7}, abs=1e-15)
    assert headline_ret(hb) == pytest.approx(0.7, abs=1e-15)
    comp = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=IDX5)
    assert cs_hit(comp, a, b.LENIENT, W5) == pytest.approx((0.1 * 1 + 0.2 * 2 + 0.3 * 3) / 0.6, abs=1e-14)
    assert cs_hit(comp, a - 1.0, b.LENIENT, W5) == 0.0                # no window clears: 0


# ---------------- the LENIENT constant ----------------

def test_lenient_constant_is_the_mean_of_the_two_number_20_cuts():
    assert SC["bars"]["LENIENT"]["down"] == pytest.approx((CUT_HK + CUT_SG) / 2, abs=1e-9)
    assert SC["bars"]["LENIENT"]["up"] == 0.0 and SC["bars"]["MIDDLE"] == 0.0


@pytest.mark.skipif(not LB_FILE.exists(), reason="the previous edition's leaderboard file is on the research server")
def test_pinned_cuts_match_the_past_leaderboard_file():
    lb = pd.read_csv(LB_FILE)
    cut = {c: float(lb[(lb.cpt == c) & (lb["rank"] == 20)].ret.iloc[0]) for c in (455, 456)}
    assert cut[455] == pytest.approx(CUT_HK, abs=1e-15) and cut[456] == pytest.approx(CUT_SG, abs=1e-15)
    assert SC["bars"]["LENIENT"]["down"] == pytest.approx((cut[455] + cut[456]) / 2, abs=1e-9)


# ---------------- tie test ----------------

def test_month_bootstrap_is_deterministic_and_paired():
    starts = pd.date_range("2023-01-01 12:00", "2024-12-31 12:00", freq="D", tz="UTC")
    m1, m2 = month_multiplicity(starts, 200, 20261002), month_multiplicity(starts, 200, 20261002)
    assert np.array_equal(m1, m2) and not np.array_equal(m1, month_multiplicity(starts, 200, 1))
    # every window of a month is drawn together, and each draw takes as many months as the pool has (24)
    jan = np.asarray((starts.year == 2023) & (starts.month == 1))
    assert (m1[:, jan] == m1[:, [np.flatnonzero(jan)[0]]]).all()
    firsts = np.r_[True, starts.month[1:] != starts.month[:-1]]          # one window of each month
    assert (m1[:, firsts].sum(axis=1) == 24).all()
    rng = np.random.default_rng(3)
    n = len(starts)
    w = rng.random(n)
    good = (rng.random((n, 3)) < 0.6).astype(float)
    worse = good * (rng.random((n, 3)) < 0.8)                          # never clears where `good` does not
    inds = {"good": good, "worse": worse, "same": good.copy()}
    t1 = tie_test(inds, w, "good", m1, 0.90)
    assert t1 == tie_test(inds, w, "good", m2, 0.90)                    # same seed, same intervals
    assert t1["good"]["tied"] and t1["same"]["tied"] and t1["same"]["lo"] == t1["same"]["hi"] == 0.0
    assert not t1["worse"]["tied"] and t1["worse"]["hi"] < 0
    assert boot_headline(good, w, m1).shape == (200,)


def test_pick_order_uses_cs_hit_inside_the_tie_group_then_the_period_check():
    rows = {"a": {"eligible": True, "headline_ret": 0.60, "cs_hit": 0.50, "min_sc": 1.0},
            "b": {"eligible": True, "headline_ret": 0.58, "cs_hit": 0.53, "min_sc": 2.0},   # within 0.05 of a, better SC
            "c": {"eligible": True, "headline_ret": 0.59, "cs_hit": 0.20, "min_sc": 9.0},   # tied, low CS_HIT
            "d": {"eligible": True, "headline_ret": 0.40, "cs_hit": 0.90, "min_sc": 9.0},   # not tied
            "e": {"eligible": False, "headline_ret": 0.90, "cs_hit": 0.90, "min_sc": 9.0}}  # fails a hard gate
    tie = {"a": {"tied": True}, "b": {"tied": True}, "c": {"tied": True}, "d": {"tied": False}, "e": {"tied": True}}
    assert pick_order(rows, tie, 0.05) == ["b", "a", "c", "d", "e"]
    rows["b"]["cs_hit"] = 0.70                                          # now b leads by more than 0.05: CS_HIT decides
    rows["a"]["min_sc"] = 5.0
    assert pick_order(rows, tie, 0.05)[0] == "b"


# ---------------- days of a 12:00 UTC start ----------------

def test_day_buckets_of_a_1200_utc_start():
    t0 = pd.Timestamp("2026-10-04 12:00", tz="UTC")
    hkt, utc = day_points(t0, 336, 16), day_points(t0, 336, 0)
    assert len(hkt) - 1 == 15 and len(utc) - 1 == 15
    assert np.diff(hkt).tolist() == [4] + [24] * 13 + [20]             # the first HKT day 4 h, the last 20 h
    assert np.diff(utc).tolist() == [12] + [24] * 13 + [12]
    assert all((t0 + pd.Timedelta(hours=int(k))).hour == 16 for k in hkt[1:-1])
    assert all((t0 + pd.Timedelta(hours=int(k))).hour == 0 for k in utc[1:-1])
    # a fill at clock time t belongs to the day containing t; the window's end is after it
    assert [bucket_of(k, hkt, 336) for k in (1, 3, 4, 5, 316, 335, 336)] == [0, 0, 1, 1, 14, 14, -1]
    E = np.linspace(1.0, 1.15, 337)
    r, _ = returns(E, 24, hkt)
    assert r.shape == (1, 15) and r[0, 0] == pytest.approx(E[4] / E[0] - 1) and r[0, -1] == pytest.approx(E[336] / E[316] - 1)
    s = day_points(pd.Timestamp("2026-10-04 16:00", tz="UTC"), 336, 16)  # a 16:00 start: 14 whole HKT days
    assert np.diff(s).tolist() == [24] * 14


# ---------------- the first decision at the window start ----------------

class AtTheHour:
    """Holds BTC when decided at 12:00 UTC, ETH at any other hour; records every view it is given."""
    spec = ModelSpec(name="book_at_the_hour", method="momentum", author="book", rebalance_hours=24, band=0.0)

    def __init__(self):
        self.seen = []

    def targets(self, view):
        self.seen.append((view.t, dict(view.prev_targets)))
        return pd.Series({"BTCUSDT" if view.t.hour == 12 else "ETHUSDT": 0.5})


@pytest.fixture(scope="module")
def market() -> Market:
    md = make_market()
    uni = universe_from_panel(md.close, md.quote_volume, top_n=10, min_history_days=45)
    return Market(md.close, md.quote_volume, uni, pd.Series(0.0005, index=md.close.columns), {"synthetic": True})


def test_first_decision_is_at_the_window_start_with_no_previous_targets(market):
    model = AtTheHour()
    t0 = pd.Timestamp("2021-03-10 12:00", tz="UTC")
    idx = market.close.index
    times = decision_times(idx, 24, 16, t0 - pd.Timedelta(days=3), t0 + pd.Timedelta(days=14))
    tg, shared = compute_targets(model, market, times, {}, keep_raw=True)
    model.seen.clear()
    f = first_decisions(model, market, pd.DatetimeIndex([t0]), times, shared, {}, 336)[t0]
    assert model.seen[0] == (t0, {})                                    # decided at 12:00, nothing carried over
    assert f.times == [t0] and f.decisions[0].to_dict() == {"BTCUSDT": 0.5}
    assert f.until == t0 + pd.Timedelta(hours=4)                         # 16:00: back on the shared decisions
    sim = Simulator(market, tg, 0.0, Costs(0.001, 0.001), 1, 16, 11, guard_utc_day=True,
                    extra_cols=sorted({c for x in f.decisions for c in x.index}))
    i0 = sim.index.get_loc(t0)
    res = sim.run(i0, 336, trace=True, first=(np.array([i0]), sim.rows(f.decisions), sim.index.get_loc(f.until)))
    first_trade, second = res.trace["trades"][0], res.trace["trades"][1]
    btc, eth = sim.cols.index("BTCUSDT"), sim.cols.index("ETHUSDT")
    assert first_trade[0] == 1 and first_trade[3][btc] == pytest.approx(0.5) and first_trade[3][eth] == 0.0
    assert second[0] == 5 and second[3][eth] == pytest.approx(0.5) and second[3][btc] == 0.0   # 16:00 decision, 17:00 fill
    old = sim.run(i0, 336, trace=True)                                  # without it: yesterday's 16:00 decision
    assert old.trace["trades"][0][3][eth] == pytest.approx(0.5)


def test_cash_is_active_on_all_15_hkt_and_utc_days_of_a_1200_start(market, tmp_path):
    from backtest.scoring.evaluate import simulate
    from src.models import discover
    import copy
    cfg = copy.deepcopy(CFG)
    cfg["scoring"]["cache_dir"] = str(tmp_path)
    starts = pd.date_range("2021-02-01 12:00", periods=5, freq="D", tz="UTC")
    run = simulate(discover()["team_cash"], market, cfg, starts, use_cache=False)
    w = run.windows
    assert (w.day_buckets == 15).all() and (w.day_buckets_utc == 15).all()
    assert (w.active_days == 15).all() and (w.active_days_utc == 15).all()


def test_return_view_ranks_by_weighted_mean_r_liq_and_keeps_the_main_order():
    from backtest.scoring.registry import return_stats, return_view
    idx = pd.date_range("2024-03-01 12:00", periods=4, freq="D", tz="UTC")

    def table(r):
        return pd.DataFrame({"post_holdout": [False, False, False, True], "w_final": [0.1, 0.2, 0.3, 0.4],
                             "w_final_in_sample": [0.5, 0.25, 0.25, np.nan], "R": r, "R_liq": r}, index=idx)

    a, b = table([0.10, 0.00, 0.00, -0.05]), table([-0.02, 0.01, 0.02, 0.03])
    sa, sb = return_stats(a, "full"), return_stats(b, "full")
    assert sa["mean"] == pytest.approx(0.1 * 0.10 - 0.4 * 0.05)             # -0.010
    assert sb["mean"] == pytest.approx(-0.1 * 0.02 + 0.2 * 0.01 + 0.3 * 0.02 + 0.4 * 0.03)   # +0.018
    assert return_stats(a, "in_sample")["mean"] == pytest.approx(0.5 * 0.10)  # the post-holdout window is left out
    assert sa["median"] == 0.0 and sb["positive"] == pytest.approx(0.9)
    rows = {n: {"candidate": True, "eligible": True} for n in ("a", "b")}
    lines = return_view(rows, {"a": a, "b": b}, ["a", "b"])                 # main order: a first
    body = [ln for ln in lines if ln.startswith("| 1 ") or ln.startswith("| 2 ")]
    assert body[0].startswith("| 1 | b |") and body[0].endswith("| #2 | yes |")   # b has the larger return
    assert body[1].startswith("| 2 | a |") and body[1].endswith("| #1 | yes |")
