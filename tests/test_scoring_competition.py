"""Section 3 toy tables: return gate, CS, weighted HEADLINE (incl. a stride), recency weights, gates, bootstrap."""
from __future__ import annotations

import copy
import json

import numpy as np
import pandas as pd
import pytest

from backtest.scoring.competition import block_bootstrap, field_median, gates, headline, return_gate
from backtest.scoring.windows import live_like_weights, recency_weights, thin
from src.config import load_config

CFG = load_config()
SPLIT = {"live_like": 0.70, "recency": 0.30}
IDX = pd.date_range("2024-01-01 16:00", periods=4, freq="D", tz="UTC")


def test_return_gate_against_the_field_median_and_zero():
    field = pd.DataFrame([[-0.02, 0.00, 0.01, 0.03, -0.01, 0.02],      # median (0.00 + 0.01) / 2 = 0.005
                          [-0.02, 0.00, 0.01, 0.03, -0.01, 0.02],      # same field
                          [-0.05, -0.04, -0.03, -0.01, -0.02, -0.06],  # median -0.035 -> the bar is max(0, -0.035) = 0
                          [-0.05, -0.04, -0.03, -0.01, -0.02, -0.06]], index=IDX)
    med = field_median(field)
    assert med.tolist() == pytest.approx([0.005, 0.005, -0.035, -0.035])
    R = pd.Series([0.010, 0.004, -0.001, 0.0], index=IDX)
    # 0.010 >= 0.005 -> 1 · 0.004 < 0.005 -> 0 · -0.001 < 0 -> 0 · 0.0 >= 0 -> 1 (ties pass)
    assert return_gate(R, med).tolist() == [1, 0, 0, 1]


def test_cs_and_weighted_headline():
    gate = pd.Series([1, 0, 1, 1], index=IDX)
    comp = pd.Series([2.0, 5.0, -1.0, 4.0], index=IDX)
    cs = gate * comp                                                  # [2, 0, -1, 4]
    w_live = pd.Series([1.0, 1.0, 2.0, 0.0], index=IDX)
    w_rec = pd.Series([0.0, 1.0, 1.0, 2.0], index=IDX)
    h = headline(cs, w_live, w_rec, SPLIT)
    # live = (2*1 + 0*1 + -1*2 + 4*0) / 4 = 0 · recency = (0 + 0 - 1 + 8) / 4 = 1.75 · HEADLINE = 0.7*0 + 0.3*1.75 = 0.525
    assert h["live_like"] == pytest.approx(0.0)
    assert h["recency"] == pytest.approx(1.75)
    assert h["headline"] == pytest.approx(0.525)
    # scaling a weight vector changes nothing (each layer divides by its own sum)
    assert headline(cs, 10 * w_live, 0.1 * w_rec, SPLIT)["headline"] == pytest.approx(0.525)


def test_stride_keeps_the_newest_window_and_renormalizes(tmp_path):
    pool = pd.date_range("2024-01-01 16:00", periods=6, freq="D", tz="UTC")
    kept = thin(pool, 2)
    assert kept.tolist() == [pool[1], pool[3], pool[5]]               # counted back from the newest start
    raw = [0.1, 0.2, 0.3, 0.1, 0.2, 0.1]
    art = {"weights": {"all": {str(t): w for t, w in zip(pool, raw)}, "direction_factor_applied": False}}
    p = tmp_path / "ll.json"
    p.write_text(json.dumps(art))
    cfg = copy.deepcopy(CFG)
    cfg["scoring"]["live_like"] = str(p)
    w, info = live_like_weights(kept, cfg)
    # kept raw weights 0.2, 0.1, 0.1 (sum 0.4) -> 0.5, 0.25, 0.25
    assert w.tolist() == pytest.approx([0.5, 0.25, 0.25])
    assert info["dropped_by_stride"] == 3 and info["mass_dropped"] == pytest.approx(0.6)
    w2, info2 = live_like_weights(kept, cfg, pool=pool.delete(0))      # a start the harness cannot run is listed apart
    assert info2["not_in_harness_pool"] == [str(pool[0])] and info2["dropped_by_stride"] == 2
    cs = pd.Series([1.0, 2.0, 3.0], index=kept)
    flat = pd.Series(1.0, index=kept)
    # live layer = 0.5*1 + 0.25*2 + 0.25*3 = 1.75; recency layer with flat weights = 2 -> 0.7*1.75 + 0.3*2 = 1.825
    assert headline(cs, w, flat, SPLIT)["headline"] == pytest.approx(1.825)
    with pytest.raises(ValueError, match="no weight"):
        live_like_weights(pool.union(pd.DatetimeIndex([pool[-1] + pd.Timedelta(days=1)])), cfg)


def test_recency_weight_halves_every_60_days():
    cfg = copy.deepcopy(CFG)
    t_star = pd.Timestamp(cfg["scoring"]["t_star"], tz="UTC")
    end_ages = [0, 60, 120]                                            # days from the window's end to T*
    starts = pd.DatetimeIndex([t_star - pd.Timedelta(days=14 + a) for a in end_ages])
    w, info = recency_weights(starts, cfg)
    by_age = dict(zip(end_ages, w.reindex(starts).to_numpy()))
    assert by_age[60] / by_age[0] == pytest.approx(0.5)
    assert by_age[120] / by_age[60] == pytest.approx(0.5)
    assert info["half_life_days"] == 60


def toy_window(R, active, guard=0):
    n = len(R)
    return pd.DataFrame({"R": R, "active_days": [active] * n, "guard_days": [guard] * n},
                        index=pd.date_range("2023-01-01 16:00", periods=n, freq="D", tz="UTC"))


def test_gates_toy():
    g = CFG["scoring"]["gates"]
    win = toy_window([0.02, -0.05, 0.01, 0.03], active=12, guard=4)
    btc = toy_window([0.05, -0.20, 0.10, -0.01], active=1)
    regime = pd.Series(["up/lowvol", "down/highvol", "flat/midvol", "up/lowvol"], index=win.index)
    stress = win.index[:2]
    ok = {"pass": True, "detail": ""}
    leak = {"pass": True, "decisions": 30}
    out = gates(win, btc, regime, stress, ok, leak, g)
    assert out["G1"]["pass"] and out["G1"]["relies_on_guard"]          # 4 of 12 active days from the guard: 33% > 25%
    assert out["G2"]["pass"]                                           # worst -5% > BTC's worst -20%
    assert out["G3"]["pass"]                                           # lowest cell median -5% > -10%
    # STRESS: worst -5% >= -20% and median (0.02 - 0.05)/2 = -1.5% >= BTC's (0.05 - 0.20)/2 = -7.5%
    assert out["G6"]["pass"]
    bad = toy_window([0.02, -0.25, 0.01, 0.03], active=9)
    out = gates(bad, btc, regime, stress, ok, leak, g)
    assert not out["G1"]["pass"] and not out["G2"]["pass"] and not out["G3"]["pass"] and not out["G6"]["pass"]


def test_block_bootstrap_brackets_the_truth():
    idx = pd.date_range("2022-01-01 16:00", periods=400, freq="D", tz="UTC")
    w = pd.Series(1.0, index=idx)
    const = block_bootstrap(pd.Series(0.3, index=idx), w, w, SPLIT, 14, 500, 0.9, 1)
    assert const["diff"] == pytest.approx(0.3) and const["lo"] == pytest.approx(0.3) and const["hi"] == pytest.approx(0.3)
    noise = pd.Series(np.random.default_rng(3).normal(0, 1, 400), index=idx)
    r = block_bootstrap(noise, w, w, SPLIT, 14, 1000, 0.9, 1)
    assert r["lo"] < r["diff"] < r["hi"] and r["lo"] < 0 < r["hi"]
