"""Scoring runs on synthetic data: engine trace, determinism, leakage gate, registry under concurrent writers,
the field benchmarks' contract."""
from __future__ import annotations

import copy
import json
import multiprocessing as mp

import numpy as np
import pandas as pd
import pytest

from backtest.data import Market, universe_from_panel
from backtest.engine import Costs, Simulator, compute_targets, decision_times
from backtest.scoring import registry
from backtest.scoring.evaluate import LongOnly, planner_orders, simulate, tool_version
from backtest.scoring.leakage import leakage_gate
from backtest.scoring.score import dumps, score_model
from src.config import load_config
from src.contracts import MarketView, ModelSpec
from src.models import discover
from tests.synth import make_market

CFG = load_config()
FIELD = ["team_cash", "team_btc_hold", "team_ew_daily", "team_rot_ew", "team_rot_iv", "team_trend_2", "team_mom_ss25"]


@pytest.fixture(scope="module")
def market() -> Market:
    md = make_market()
    uni = universe_from_panel(md.close, md.quote_volume, top_n=10, min_history_days=45)
    return Market(md.close, md.quote_volume, uni, pd.Series(0.0005, index=md.close.columns), {"synthetic": True})


def synth_cfg(tmp_path, market: Market) -> dict:
    """Real config, pointed at a short synthetic pool and temporary weight, set and cache files."""
    cfg = copy.deepcopy(CFG)
    h, sc = cfg["harness"], cfg["scoring"]
    h.update(first_window="2021-02-01", holdout_from="2021-04-15 16:00")
    pool = pd.date_range("2021-02-01 16:00", "2021-04-01 16:00", freq="D", tz="UTC")
    rng = np.random.default_rng(5)
    (tmp_path / "ll.json").write_text(json.dumps({"weights": {"all": {str(t): float(w) for t, w in zip(pool, rng.uniform(0.1, 1, len(pool)))},
                                                              "direction_factor_applied": False}}))
    pick = lambda k: [{"start": str(t)} for t in pool[::k][:6]]
    (tmp_path / "vs.json").write_text(json.dumps({"windows": pick(5), "recent": pick(14),
                                                  "stress": {"drops": pick(7)[:3], "rebounds": pick(9)[:3]}}))
    terc = lambda: rng.choice(["down", "flat", "up"], len(pool))
    pd.DataFrame({"y1_tercile": terc(), "y2_tercile": rng.choice(["lowvol", "midvol", "highvol"], len(pool))},
                 index=pool).to_parquet(tmp_path / "reg.parquet")
    sc.update(t_star="2021-04-29 16:00", live_like=str(tmp_path / "ll.json"), validation_set=str(tmp_path / "vs.json"),
              regimes=str(tmp_path / "reg.parquet"), cache_dir=str(tmp_path / "cache"),
              registry=str(tmp_path / "registry.jsonl"), leaderboard=str(tmp_path / "lb.md"))
    sc["gates"]["G5"]["decisions"] = 6
    return cfg


# ---------------- engine trace (the one change to backtest/engine.py) ----------------

def test_trace_changes_nothing_and_costs_add_up(market):
    idx = market.close.index
    i0 = idx.get_loc(pd.Timestamp("2021-03-01 16:00", tz="UTC"))
    model = discover()["team_mom_ss25"]
    params = CFG["models"]["team_mom_ss25"]
    times = decision_times(idx, 24, 16, idx[i0], idx[i0 + 336])
    tg = compute_targets(model, market, times, params)
    costs = Costs(0.001, 0.001)
    sim = Simulator(market, tg, model.spec.band, costs, 1, 16, 20)
    plain, traced = sim.run(i0, 336), sim.run(i0, 336, trace=True)
    assert np.array_equal(plain.equity, traced.equity) and plain.trace is None
    assert (plain.active_days, plain.turnover, plain.fees) == (traced.active_days, traced.turnover, traced.fees)
    tr = traced.trace
    total = 0.0
    for _h, _kind, w0, w1, _eq, cost in tr["trades"]:
        fee = (np.abs(np.maximum(w1, 0) - np.maximum(w0, 0)) + np.abs(np.minimum(w1, 0) - np.minimum(w0, 0))) * 0.001
        assert fee.sum() + (np.abs(w1 - w0) * sim.half).sum() == pytest.approx(cost, rel=1e-12)
        total += cost
    assert total == pytest.approx(traced.fees, rel=1e-12)
    assert int(tr["strategy_day"].sum() + (tr["guard_day"] & ~tr["strategy_day"]).sum()) == traced.active_days


def test_planner_order_count():
    assert planner_orders(np.array([0.5, -0.2, 0.0]), np.array([-0.3, -0.1, 0.2])) == 4   # flip = 2, reduce, buy


# ---------------- 5.4 determinism, CASH, BTC_HOLD ----------------

def test_two_runs_give_identical_score_json(tmp_path, market):
    cfg = synth_cfg(tmp_path, market)
    model = discover()["team_mom_ss25"]
    s1, ctx = score_model(model, market, cfg, use_cache=False)
    s2, _ = score_model(model, market, cfg, use_cache=False)
    assert dumps(s1) == dumps(s2)
    s3, _ = score_model(model, market, cfg, use_cache=True)            # and the cache returns the same thing
    assert dumps(s3) == dumps(s1)
    assert s1["windows"]["scored"] == 60 and s1["gates"]["G4"]["ran"]  # MOM_SS25 shorts, so G4 really runs
    assert set(s1["headline"]) == {"FLOORED", "POL"} and set(s1["headline"]["POL"]) == {"V1", "V2", "V3", "V4", "REL"}
    rob = s1["robustness"]
    assert set(rob) >= {"headline", "live_like", "recency", "flat", "min", "pass"}
    assert rob["headline"] == pytest.approx(s1["headline"]["FLOORED"]["REL"]["headline"])
    assert s1["gate_sensitivity"]["primary_stat"] == CFG["scoring"]["return_gate_stat"]
    assert set(s1["gate_sensitivity"]["rel_headline"]) == set(CFG["scoring"]["return_gate_report"])
    g4 = s1["gates"]["G4"]
    assert {"long_only_G1", "long_only_G2"} <= set(g4) and g4["pass"] == (g4["long_only_G1"] and g4["long_only_G2"])


def test_tool_version_changes_with_the_field(market):
    """A field member's code or parameters set every model's return gate, so they are part of the version."""
    cfg = copy.deepcopy(CFG)
    v0 = tool_version(cfg, market)
    cfg["models"]["team_rot_ew"]["k"] = 7
    assert tool_version(cfg, market) != v0
    cfg = copy.deepcopy(CFG)
    cfg["models"]["pol_trend_ls"]["threshold"] = 0.9                    # not a field member: no change
    assert tool_version(cfg, market) == v0


def test_cash_scores_zero_and_fails_g1(tmp_path, market):
    cfg = synth_cfg(tmp_path, market)
    cfg["harness"]["keep_alive_weight"] = 0.0                          # the pure model; with it, see the next test
    s, ctx = score_model(discover()["team_cash"], market, cfg)
    for c in s["headline"].values():
        for v in c.values():
            assert v["headline"] == 0.0 and v["live_like"] == 0.0 and v["recency"] == 0.0
    assert not s["gates"]["G1"]["pass"] and not s["eligible"]
    assert (ctx["run"].windows.R == 0).all() and (ctx["run"].windows.active_days == 0).all()


def test_keep_alive_makes_cash_active_at_almost_no_cost(tmp_path, market):
    cfg = synth_cfg(tmp_path, market)
    run = simulate(discover()["team_cash"], market, cfg, pd.date_range("2021-02-01 16:00", periods=10, freq="D", tz="UTC"))
    assert (run.windows.active_days == 14).all()
    # band 0: the next decision unwinds the nudge (a "strategy" day), the guard nudges again the day after
    assert (run.windows.guard_days >= 7).all()
    assert run.windows.R.abs().max() < 0.001
    assert run.windows.gross_max.max() <= 1.25 * cfg["harness"]["keep_alive_weight"]   # the nudge, plus its price drift


def test_btc_hold_return_is_btc_move_minus_entry_cost(tmp_path, market):
    cfg = synth_cfg(tmp_path, market)
    cfg["harness"]["keep_alive_weight"] = 0.0                          # the exact formula below is the pure hold
    run = simulate(discover()["team_btc_hold"], market, cfg, pd.date_range("2021-02-01 16:00", periods=10, freq="D", tz="UTC"))
    px = market.close["BTCUSDT"].ffill()                                # the engine carries a missing hour forward
    for t0, R in run.windows.R.items():
        entry, end = px[t0 + pd.Timedelta(hours=1)], px[t0 + pd.Timedelta(hours=336)]   # 1-bar lag
        assert R == pytest.approx((1 - 0.001 - 0.0005) * end / entry - 1, rel=1e-12)      # taker + half-spread
    assert (run.windows.active_days == 1).all()                          # it trades once: fails G1


# ---------------- 5.4 leakage ----------------

class Peek:
    """Deliberately leaky: follows the next hour's move, read through the array behind the view."""
    spec = ModelSpec(name="book_peek", method="momentum", author="book")

    def targets(self, view: MarketView) -> pd.Series:
        a = view.close.to_numpy()
        root = a
        while isinstance(root.base, np.ndarray):
            root = root.base
        full = root if root.shape[0] != view.close.shape[1] else root.T     # (time, coins)
        n = len(view.close)
        j = list(view.close.columns).index("BTCUSDT")
        if "BTCUSDT" in view.universe and full.shape[0] > n and full[n, j] > full[n - 1, j]:
            return pd.Series({"BTCUSDT": 1.0})
        return pd.Series(dtype=float)


class ReadsDisk:
    spec = ModelSpec(name="book_disk", method="momentum", author="book")

    def targets(self, view: MarketView) -> pd.Series:
        try:
            with open(__file__):
                pass
        except PermissionError:
            pass                                                         # swallowing it does not hide the attempt
        return pd.Series({"BTCUSDT": 0.5}) if "BTCUSDT" in view.universe else pd.Series(dtype=float)


def _targets(model, market):
    idx = market.close.index
    times = decision_times(idx, 24, 16, pd.Timestamp("2021-02-01 16:00", tz="UTC"), pd.Timestamp("2021-03-15 16:00", tz="UTC"))
    return compute_targets(model, market, times, {})


def test_leakage_gate_catches_a_model_that_reads_past_t(market):
    model = Peek()
    tg = _targets(model, market)
    assert tg["BTCUSDT"].between(0, 1).all() and 0 < tg["BTCUSDT"].mean() < 1   # it did see the future in the run
    out = leakage_gate(model, market, tg, {}, {"decisions": 30, "seed": 1, "noise_sigma": 0.01})
    assert not out["pass"] and out["future_noise"] and not out["determinism"]   # Pol's determinism check alone passes it


def test_leakage_gate_catches_file_access_and_passes_honest_models(market):
    out = leakage_gate(ReadsDisk(), market, _targets(ReadsDisk(), market), {}, {"decisions": 5, "seed": 1, "noise_sigma": 0.01})
    assert not out["pass"] and out["io"]
    honest = discover()["team_ew_daily"]
    out = leakage_gate(honest, market, _targets(honest, market), {}, {"decisions": 10, "seed": 1, "noise_sigma": 0.01})
    assert out["pass"], out


def test_long_only_wrapper_drops_shorts(market):
    model = LongOnly(discover()["team_mom_ss25"])
    assert not model.spec.uses_shorts
    idx = market.close.index
    times = decision_times(idx, 24, 16, pd.Timestamp("2021-02-01 16:00", tz="UTC"), pd.Timestamp("2021-02-20 16:00", tz="UTC"))
    tg = compute_targets(model, market, times, CFG["models"]["team_mom_ss25"])
    assert (tg >= 0).all().all()


# ---------------- 5.4 registry under 8 concurrent writers ----------------

def _writer(args):
    path, lockdir, k = args
    for j in range(50):
        registry.append(path, {"writer": k, "j": j, "pad": "x" * 2000}, lock_dir=lockdir)


def test_registry_stays_valid_under_8_concurrent_writers(tmp_path):
    path = tmp_path / "registry.jsonl"
    with mp.get_context("fork").Pool(8) as pool:
        pool.map(_writer, [(str(path), str(tmp_path / "locks"), k) for k in range(8)])
    entries, bad = registry.read(path)
    assert bad == 0 and len(entries) == 400
    assert sorted((e["writer"], e["j"]) for e in entries) == [(k, j) for k in range(8) for j in range(50)]


# ---------------- the field benchmarks keep the contract ----------------

@pytest.mark.parametrize("name", FIELD)
def test_field_benchmarks_keep_the_contract(name, market):
    model = discover()[name]
    assert model.spec.method == "reference" and model.spec.author == "team"
    idx = market.close.index
    times = decision_times(idx, model.spec.rebalance_hours, 16, pd.Timestamp("2021-01-10 16:00", tz="UTC"),
                           pd.Timestamp("2021-02-10 16:00", tz="UTC"))
    tg = compute_targets(model, market, times, CFG["models"].get(name, {}) or {})   # raises on any contract break
    assert (tg.abs().sum(axis=1) <= 1 + 1e-9).all()
    if name not in ("team_cash",):
        assert (tg.abs().sum(axis=1) > 0).mean() > 0.5
    if not model.spec.uses_shorts:
        assert (tg >= 0).all().all()
