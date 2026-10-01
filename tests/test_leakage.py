"""PART E leakage tests. Synthetic-data versions always run; real-data versions run when the build's
intermediate files exist in data/validation/ (they are skipped otherwise)."""
import ast
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.config import REPO_ROOT, load_config
from src.validation import outcomes as outcomes_mod
from src.validation.features import FEATURES, MarketData, StateEngine, grid_labels
from src.validation.guard import LeakageError, forbid_outcome_access
from src.validation.selection import PickRules, pool_index, select_lookalikes, CORE_GROUPS
from src.validation.walkforward import run_walkforward
from tests.synth import LATE_LISTING, cpi_release, make_market, perturb_after

V = load_config()["validation"]
OUT = Path(os.environ.get("MM_VALIDATION_OUT", REPO_ROOT / "data" / "validation"))
RULES = PickRules(V["k"], V["min_separation_days"], V["span_days"], V["max_per_span"], V["horizon_days"])
H14 = pd.Timedelta(days=14)


@pytest.fixture(scope="module")
def market():
    return make_market()


@pytest.fixture(scope="module")
def engine(market):
    return StateEngine(market, V)


def _bits(df: pd.DataFrame) -> bytes:
    return np.ascontiguousarray(df.to_numpy(dtype=np.float64)).view(np.int64).tobytes()


def _random_times(index: pd.DatetimeIndex, n: int, seed: int, lo: str, hi: str) -> list[pd.Timestamp]:
    cand = index[(index >= pd.Timestamp(lo, tz="UTC")) & (index <= pd.Timestamp(hi, tz="UTC"))]
    return sorted(cand[np.random.default_rng(seed).choice(len(cand), n, replace=False)])


# ---- E1: future perturbation ------------------------------------------------------------------
def test_e1_future_perturbation_synthetic(market, engine):
    times = _random_times(engine.close_d.index, 20, 1, "2020-03-01", "2021-05-01")
    changed_later = 0
    for k, t in enumerate(times):
        t = pd.Timestamp(t)
        base = engine.features([t])
        pert = StateEngine(perturb_after(market, t, seed=100 + k, lags=V["macro_lag_days"]), V)
        assert _bits(pert.features([t])) == _bits(base), f"features at {t} changed when only later data changed"
        later = t + pd.Timedelta(days=20)
        if later <= engine.close_d.index[-1]:
            changed_later += _bits(pert.features([later])) != _bits(engine.features([later]))
    assert changed_later > 0, "perturbation never reached later features: the test would be vacuous"


@pytest.mark.skipif(not (OUT / "panel_close_1h.parquet").exists(), reason="no real panel yet (run the build)")
def test_e1_future_perturbation_real_data():
    from src.data.futures import load_funding, load_open_interest
    from src.data import fred
    cfg = load_config()
    close = pd.read_parquet(OUT / "panel_close_1h.parquet")
    qv = pd.read_parquet(OUT / "panel_quote_volume_1h.parquet")
    series, _ = fred.load(cfg)
    data = MarketData(close, qv, load_funding(cfg), load_open_interest(cfg), series)
    eng = StateEngine(data, V)
    times = _random_times(eng.close_d.index, 20, 2, "2020-07-01", str(eng.close_d.index[-40].date()))
    for k, t in enumerate(times):
        t = pd.Timestamp(t)
        pert = StateEngine(perturb_after(data, t, seed=200 + k, release_day=V["cpi_release_day"],
                                         lags=V["macro_lag_days"]), V)
        assert _bits(pert.features([t])) == _bits(eng.features([t])), f"real-data features at {t} changed"


# ---- E2: macro point-in-time --------------------------------------------------------------------
def test_e2_cpi_never_used_before_release(market, engine):
    cpi = market.fred["CPIAUCNS"]
    times = _random_times(engine.close_d.index, 60, 3, "2019-06-01", "2021-05-01")
    for t in map(pd.Timestamp, times):
        released = [m for m in cpi.index if cpi_release(m, V["cpi_release_day"]) <= t]
        m = released[-1]
        expected = cpi[m] / cpi[m - pd.DateOffset(years=1)] - 1
        assert engine.macro_features(pd.DatetimeIndex([t]))["X1"].iloc[0] == pytest.approx(expected, rel=0, abs=0)
        # altering the first unreleased month (and everything after) must not move X1 or X2
        s = cpi.copy()
        s[[cpi_release(x, V["cpi_release_day"]) > t for x in s.index]] *= 3.0
        alt = StateEngine(MarketData(market.close, market.quote_volume, market.funding, market.oi,
                                     {**market.fred, "CPIAUCNS": s}), V)
        a = alt.macro_features(pd.DatetimeIndex([t]))[["X1", "X2"]]
        b = engine.macro_features(pd.DatetimeIndex([t]))[["X1", "X2"]]
        assert _bits(a) == _bits(b)


def test_e2_release_boundary(market, engine):
    cpi = market.fred["CPIAUCNS"]
    may = pd.Timestamp("2020-05-01")
    before = pd.Timestamp("2020-06-15 16:00", tz="UTC")  # May CPI assumed released 2020-06-16 00:00 UTC
    after = pd.Timestamp("2020-06-16 16:00", tz="UTC")
    x_before = engine.macro_features(pd.DatetimeIndex([before]))["X1"].iloc[0]
    x_after = engine.macro_features(pd.DatetimeIndex([after]))["X1"].iloc[0]
    assert x_before == pytest.approx(cpi[pd.Timestamp("2020-04-01")] / cpi[pd.Timestamp("2019-04-01")] - 1)
    assert x_after == pytest.approx(cpi[may] / cpi[pd.Timestamp("2019-05-01")] - 1)


def test_e2_daily_fred_uses_previous_business_day(market, engine):
    t = pd.Timestamp("2020-06-15 16:00", tz="UTC")  # a Monday: must use Friday 2020-06-12
    vix = market.fred["VIXCLS"]
    assert engine.macro_features(pd.DatetimeIndex([t]))["X7"].iloc[0] == vix[pd.Timestamp("2020-06-12")]


def test_e2_dtwexbgs_is_lagged_seven_days(market, engine):
    assert V["macro_lag_days"]["DTWEXBGS"] == 7
    t = pd.Timestamp("2020-06-17 16:00", tz="UTC")  # Wednesday; 7 days earlier is Wed 2020-06-10
    s = market.fred["DTWEXBGS"]
    x5 = engine.macro_features(pd.DatetimeIndex([t]))["X5"].iloc[0]
    now = s[s.index < pd.Timestamp("2020-06-10")].iloc[-1]       # last value dated before 2020-06-10
    then = s[s.index < pd.Timestamp("2020-05-11")].iloc[-1]      # ... and 30 days before that
    assert x5 == now / then - 1
    # values from the last 7 days before t must not matter
    s2 = s.copy()
    s2[(s2.index >= pd.Timestamp("2020-06-10")) & (s2.index < pd.Timestamp("2020-06-17"))] *= 5.0
    alt = StateEngine(MarketData(market.close, market.quote_volume, market.funding, market.oi,
                                 {**market.fred, "DTWEXBGS": s2}), V)
    assert alt.macro_features(pd.DatetimeIndex([t]))["X5"].iloc[0] == x5


# ---- E3: embargo ----------------------------------------------------------------------------------
def test_e3_pool_and_selection_respect_end_limit(engine):
    feats = engine.features(engine.close_d.index[engine.close_d.index >= pd.Timestamp("2020-01-01", tz="UTC")])
    end = pd.Timestamp("2021-03-01 16:00", tz="UTC")
    earliest = pd.Timestamp("2020-06-01 16:00", tz="UTC")
    pool = pool_index(feats, CORE_GROUPS, end, 14, earliest)
    assert len(pool) and ((pool + H14) <= end).all() and pool.min() >= earliest
    q = feats.loc[pd.Timestamp("2021-06-01 16:00", tz="UTC")]
    from src.validation.selection import active_features
    act = active_features(CORE_GROUPS)
    picks, _ = select_lookalikes(feats.loc[pool, act], q[act], CORE_GROUPS, PickRules(k=8, horizon_days=14))
    assert ((picks.t0 + H14) <= end).all()


def test_e3_walkforward_pools_end_before_D(engine):
    feats = engine.features(engine.close_d.index[engine.close_d.index >= pd.Timestamp("2020-01-01", tz="UTC")])
    t0s = feats.index[feats.index + H14 <= feats.index[-1]]
    outc = outcomes_mod.compute_outcomes(engine, t0s[t0s >= pd.Timestamp("2020-06-01", tz="UTC")], 14)
    dates = pd.date_range("2020-12-01 16:00", "2021-05-01 16:00", freq="7D", tz="UTC")
    _, audit = run_walkforward(feats, outc, {"CORE": CORE_GROUPS}, PickRules(k=6, horizon_days=14), dates,
                               pd.Timestamp("2020-06-01 16:00", tz="UTC"), draws=3, seed=1)
    ok = audit[audit.status == "ok"]
    assert len(ok) > 0
    assert (audit.pool_max_end <= audit.D).all() and (ok.pick_max_end <= ok.D).all()


@pytest.mark.skipif(not (REPO_ROOT / "validation" / "validation_set_v1.json").exists(), reason="no artifact yet")
def test_e3_real_artifact_embargo():
    a = json.loads((REPO_ROOT / "validation" / "validation_set_v1.json").read_text())
    H = pd.Timestamp(a["holdout_H"])
    assert all(pd.Timestamp(w["end"]) <= H for w in a["windows"])
    assert pd.Timestamp(a["pool"]["last_start"]) + H14 <= H
    audit = pd.read_parquet(OUT / "walkforward_audit.parquet")
    assert (audit.pool_max_end.dropna() <= audit.D[audit.pool_max_end.notna()]).all()
    ok = audit[audit.status == "ok"]
    assert (ok.pick_max_end <= ok.D).all()


# ---- E4: selection never touches the outcome table ------------------------------------------------
def test_e4_selection_module_does_not_import_outcomes():
    src = (REPO_ROOT / "src" / "validation" / "selection.py").read_text()
    tree = ast.parse(src)
    imported = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)] + \
               [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    assert not any("outcomes" in (m or "") for m in imported)
    assert "read_parquet" not in src and "outcomes.parquet" not in src


def test_e4_outcome_access_raises_inside_selection(tmp_path):
    p = tmp_path / "o.parquet"
    pd.DataFrame({"Y1": [0.1]}).to_parquet(p)
    outcomes_mod.load_outcomes(p)  # fine outside selection
    with forbid_outcome_access():
        with pytest.raises(LeakageError):
            outcomes_mod.load_outcomes(p)


def test_e4_selection_rejects_outcome_columns_and_never_reads_files(engine, monkeypatch):
    feats = engine.features(engine.close_d.index[engine.close_d.index >= pd.Timestamp("2020-06-01", tz="UTC")])
    from src.validation.selection import active_features
    act = active_features(CORE_GROUPS)
    pool = pool_index(feats, CORE_GROUPS, pd.Timestamp("2021-03-01 16:00", tz="UTC"), 14,
                      pd.Timestamp("2020-06-01 16:00", tz="UTC"))
    bad = feats.loc[pool, act].assign(Y1=0.0)
    with pytest.raises(LeakageError):
        select_lookalikes(bad, feats.loc[pool[-1], act], CORE_GROUPS, PickRules(k=5))

    def boom(*a, **k):
        raise AssertionError("selection code read a file / the outcome table")
    monkeypatch.setattr(pd, "read_parquet", boom)
    monkeypatch.setattr(outcomes_mod, "load_outcomes", boom)
    picks, _ = select_lookalikes(feats.loc[pool, act], feats.loc[pool[-1], act], CORE_GROUPS, PickRules(k=5))
    assert len(picks) == 5


# ---- E5: point-in-time universe -------------------------------------------------------------------
def _daily_history_counts(close_h: pd.DataFrame, hour: int) -> pd.DataFrame:
    """Independent count: number of grid days with >= 1 hourly bar, strictly before each grid day."""
    lab = grid_labels(close_h.index, hour)
    exists = close_h.notna().groupby(lab).any()
    full = pd.date_range(exists.index[0], exists.index[-1], freq="D")
    exists = exists.reindex(full, fill_value=False).astype(int)
    return exists.cumsum() - exists


def test_e5_universe_needs_90_days_synthetic(market, engine):
    counts = _daily_history_counts(market.close, V["grid_hour_utc"])
    times = engine.close_d.index[engine.close_d.index >= pd.Timestamp("2019-05-01", tz="UTC")]
    coin, listed = LATE_LISTING
    for t in times:
        u = engine.universe(t)
        assert all(counts.at[t, s] >= V["universe"]["min_history_days"] for s in u)
        assert "PAXGUSDT" not in u and "USDCUSDT" not in u
        if t < listed + pd.Timedelta(days=V["universe"]["min_history_days"]):
            assert coin not in u
    assert any(coin in engine.universe(t) for t in times[-30:])


@pytest.mark.skipif(not (OUT / "universe.parquet").exists(), reason="no real universe yet (run the build)")
def test_e5_universe_needs_90_days_real_data():
    close = pd.read_parquet(OUT / "panel_close_1h.parquet")
    counts = _daily_history_counts(close, V["grid_hour_utc"])
    uni = pd.read_parquet(OUT / "universe.parquet")
    got = counts.stack().rename("n")
    have = got.reindex(pd.MultiIndex.from_frame(uni[["t", "series"]]))
    assert have.notna().all() and (have >= V["universe"]["min_history_days"]).all()
    assert not uni.series.str.startswith("PAXG").any()
