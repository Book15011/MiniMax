"""Score one model end to end (docs/EVALUATION.md): runs, field, weights, HEADLINE, gates and score.json content.

score.json holds no wall-clock time or registry state, so two runs of the same code on the same data produce
the same file byte for byte (ranks among other runs live in the report and the leaderboard instead).
"""
from __future__ import annotations

import json
import logging
import math

import numpy as np
import pandas as pd

from backtest.data import Market
from backtest.evaluate import git_state, holdout_start, window_starts
from backtest.scoring.competition import (add_rel, all_variants, field_median, field_scale, gates, headline,
                                          regime_grid, return_gate)
from backtest.scoring.evaluate import Run, simulate
from backtest.scoring.leakage import leakage_gate
from backtest.scoring.metrics import FLOORS, RATIOS
from backtest.scoring.windows import (live_like_weights, recency_weights, regimes, scored_starts, window_sets)
from src.config import resolve
from src.contracts import Model
from src.models import get

SCHEMA = "minimax-score/1"


def clean(x):
    """JSON-safe, deterministic: numpy scalars to Python, NaN and inf to None, timestamps to ISO strings."""
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    if isinstance(x, (np.bool_, bool)):
        return bool(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return float(x) if math.isfinite(x) else None
    if isinstance(x, pd.Timestamp):
        return x.isoformat()
    return x


def dumps(score: dict) -> str:
    """Compact (the per-window table is large); read it with `python -m json.tool score.json`."""
    return json.dumps(clean(score), separators=(",", ":"), allow_nan=False) + "\n"


def simulated_starts(market: Market, cfg: dict, starts: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """The scored windows plus every set window in the pool (needed for G6 and the sets when stride > 1)."""
    pool = window_starts(market, cfg, holdout=False)
    extra = pd.DatetimeIndex([], tz="UTC")
    for s in window_sets(cfg).values():
        extra = extra.union(s.intersection(pool))
    out = starts.union(extra).sort_values()
    assert isinstance(out, pd.DatetimeIndex) and str(out.tz) == "UTC"
    return out


def field_runs(market: Market, cfg: dict, sim: pd.DatetimeIndex, use_cache: bool, log: logging.Logger,
               have: dict | None = None) -> dict[str, Run]:
    have = have or {}
    return {n: have.get(n) or simulate(get(n), market, cfg, sim, use_cache=use_cache, log=log)
            for n in cfg["scoring"]["field"]}


def cs_table(win: pd.DataFrame, gate: pd.Series, sc: dict) -> pd.DataFrame:
    return pd.DataFrame({f"{c}.{v}.cs": gate * win[f"{c}.{v}.composite"]
                         for c in sc["conventions"] for v in sc["variants"]})


def summary(R: pd.Series, mdd: pd.Series) -> dict:
    return {"n": int(len(R)), "median_R": float(R.median()), "worst10_R": float(R.quantile(0.1)),
            "worst_R": float(R.min()), "best_R": float(R.max()), "share_R_positive": float((R > 0).mean()),
            "median_MDD": float(mdd.median()), "worst_MDD": float(mdd.max())}


def wquantile(x: pd.Series, w: pd.Series, q: float) -> float:
    o = np.argsort(x.to_numpy())
    c = np.cumsum(w.reindex(x.index).to_numpy()[o])
    return float(x.to_numpy()[o][np.searchsorted(c / c[-1], q)])


def weighted_block(win: pd.DataFrame, gate: pd.Series, w: pd.Series) -> dict:
    """The distribution behind a weighted HEADLINE layer: weighted median and 10th percentile of R, gate pass share."""
    return {"median_R": wquantile(win.R, w, 0.5), "worst10_R": wquantile(win.R, w, 0.1),
            "median_MDD": wquantile(win.MDD, w, 0.5),
            "gate_pass_share": float((gate * w.reindex(gate.index)).sum() / w.reindex(gate.index).sum())}


def layer_block(win: pd.DataFrame, cs: pd.DataFrame, gate: pd.Series, idx: pd.DatetimeIndex, sc: dict) -> dict:
    """Report-only layer: flat means over a window set."""
    if len(idx) == 0:
        return {"n": 0}
    p = f"{sc['primary']['convention']}.{sc['primary']['variant']}"
    w, c = win.loc[idx], cs.loc[idx]
    return {**summary(w.R, w.MDD), "gate_pass_share": float(gate.loc[idx].mean()),
            "mean_cs": {k[:-3]: float(v) for k, v in c.mean().items()},
            "mean_cs_primary": float(c[f"{p}.cs"].mean()), "median_composite_primary": float(w[f"{p}.composite"].median())}


def g4_long_only(model: Model, market: Market, cfg: dict, sim: pd.DatetimeIndex, starts: pd.DatetimeIndex,
                 btc_worst: float, use_cache: bool, log: logging.Logger) -> tuple[dict, Run | None]:
    """The live fallback if shorts are refused: it must run cleanly AND still pass G1 (activity) and G2 (worst
    fortnight better than BTC_HOLD's), because it is the bot that would then trade."""
    if not model.spec.uses_shorts:
        return {"pass": True, "detail": "no shorts: the long-only run is the main run", "ran": False}, None
    try:
        lo = simulate(model, market, cfg, sim, long_only=True, use_cache=use_cache, log=log)
    except Exception as e:                                   # noqa: BLE001 - a crash is exactly what G4 reports
        return {"pass": False, "detail": f"long-only run failed: {type(e).__name__}: {e}", "ran": True}, None
    num = lo.windows.select_dtypes("number")
    finite = bool(np.isfinite(num.to_numpy(dtype=float)).all())
    neg = bool((lo.targets < 0).any().any())
    if not (finite and not neg and len(lo.windows) == len(sim)):
        return {"pass": False, "ran": True, "run_key": lo.key,
                "detail": f"long-only run incomplete: finite={finite}, negative targets={neg}, windows={len(lo.windows)}"}, lo
    g1 = cfg["scoring"]["gates"]["G1"]
    w = lo.windows.loc[starts]
    share, worst = float((w.active_days >= g1["min_active_days"]).mean()), float(w.R.min())
    a_ok, w_ok = share >= g1["share_of_windows"], worst > btc_worst
    return {"pass": a_ok and w_ok, "ran": True, "run_key": lo.key, "long_only_G1": a_ok, "long_only_G2": w_ok,
            "long_only_worst": worst,
            "detail": f"long-only run: {share:.1%} of windows have >= {g1['min_active_days']} active days (G1 "
                      f"{'ok' if a_ok else 'FAILS'}); worst R {worst:+.2%} vs BTC_HOLD {btc_worst:+.2%} "
                      f"(G2 {'ok' if w_ok else 'FAILS'})"}, lo


def leakage(run: Run, model: Model, market: Market, cfg: dict, use_cache: bool) -> dict:
    """G5, cached next to the run (same key: same code, parameters and data)."""
    path = resolve(cfg["scoring"]["cache_dir"]) / run.name / f"{run.key}.g5.json"
    if use_cache and path.exists():
        return json.loads(path.read_text())
    out = leakage_gate(model, market, run.targets, run.params, cfg["scoring"]["gates"]["G5"])
    path.write_text(json.dumps(out))
    return out


def score_model(model: Model, market: Market, cfg: dict, use_cache: bool = True, stride: int | None = None,
                log: logging.Logger | None = None) -> tuple[dict, dict]:
    """Returns (score, context): score is the content of score.json; context holds the runs for the report."""
    log = log or logging.getLogger(__name__)
    sc, h = cfg["scoring"], cfg["harness"]
    starts = scored_starts(market, cfg, stride)
    sim = simulated_starts(market, cfg, starts)
    run = simulate(model, market, cfg, sim, use_cache=use_cache, log=log)
    field = field_runs(market, cfg, sim, use_cache, log, {model.spec.name: run})
    fieldR = pd.DataFrame({n: r.windows.R for n, r in field.items()})
    med = field_median(fieldR)
    floor = float(sc["return_gate_floor"])
    w_live, live_info = live_like_weights(starts, cfg, window_starts(market, cfg, holdout=False))
    w_rec, rec_info = recency_weights(starts, cfg)
    field_cs = {n: cs_table(r.windows, return_gate(r.windows.R, med, floor), sc).loc[starts] for n, r in field.items()}
    scale = field_scale(field_cs, w_live, w_rec, sc)
    win = add_rel(run.windows, scale, sc, "composite")
    gate = return_gate(win.R, med, floor)
    cs = add_rel(cs_table(win, gate, sc), scale, sc, "cs")
    head = {c: {v: headline(cs.loc[starts, f"{c}.{v}.cs"], w_live, w_rec, sc["headline"]) for v in all_variants(sc)}
            for c in sc["conventions"]}
    prim = sc["primary"]
    sets = window_sets(cfg)
    regime = regimes(sim, cfg)
    btc = field[sc["btc_hold"]].windows
    g4, lo = g4_long_only(model, market, cfg, sim, starts, float(btc.R.loc[starts].min()), use_cache, log)
    g5 = leakage(run, model, market, cfg, use_cache)
    gres = gates(win.loc[starts], btc.loc[starts], regime.loc[starts], sets["STRESS"].intersection(sim),
                 g4, g5, sc["gates"])
    if lo is not None:
        lo_gate = return_gate(lo.windows.R, med, floor)
        lo_cs = add_rel(cs_table(lo.windows, lo_gate, sc), scale, sc, "cs")
        key = f"{prim['convention']}.{prim['variant']}.cs"
        g4["headline_primary_long_only"] = headline(lo_cs.loc[starts, key], w_live, w_rec, sc["headline"])["headline"]

    grid = regime_grid(win.R.loc[starts], regime.loc[starts])
    floor_hits = {c: {f: int(win.loc[starts, f"{c}.hit.{f}"].sum()) for f in FLOORS} for c in sc["conventions"]}
    layers = {"ALL_flat": layer_block(win, cs, gate, starts, sc),
              "weighted": {"live_like": weighted_block(win.loc[starts], gate.loc[starts], w_live),
                           "recency": weighted_block(win.loc[starts], gate.loc[starts], w_rec)}}
    for name, s in sets.items():
        layers[name] = layer_block(win, cs, gate, s.intersection(sim), sc)
    layers["regime_grid"] = {"median_R": grid["median"].round(12).to_dict(orient="index"),
                             "count": grid["count"].to_dict(orient="index")}

    per = pd.concat([win, cs], axis=1).loc[sim]
    per.insert(0, "end", per.index + pd.Timedelta(days=h["window_days"]))
    per.insert(1, "scored", per.index.isin(starts))
    per.insert(2, "w_live", w_live.reindex(per.index))
    per.insert(3, "w_rec", w_rec.reindex(per.index))
    per.insert(4, "field_median_R", med.reindex(per.index))
    per.insert(5, "gate", gate.reindex(per.index))
    per.insert(6, "regime", regime.reindex(per.index))
    for name, s in sets.items():
        per[f"in_{name}"] = per.index.isin(s)
    per_cols = {"start": [t.isoformat() for t in per.index]}
    for col in per.columns:
        vals = per[col].tolist()
        per_cols[col] = [v.isoformat() if isinstance(v, pd.Timestamp) else v for v in vals]

    spec = model.spec
    score = {
        "schema": SCHEMA,
        "scoring_version": sc["version"],
        "tool_version": run.meta["tool_version"],
        "model": {"name": spec.name, "author": spec.author, "method": spec.method,
                  "rebalance_hours": spec.rebalance_hours, "band": spec.band, "uses_shorts": spec.uses_shorts,
                  "description": spec.description, "params": run.params, "run_key": run.key},
        "data": market.notes,
        "code": git_state(),
        "code_when_cached": run.meta.get("git"),
        "windows": {"scored": len(starts), "simulated": len(sim), "stride_days": int(sc["stride_days"] if stride is None else stride),
                    "first_start": starts[0], "last_start": starts[-1], "days": h["window_days"],
                    "holdout_sealed_from": holdout_start(cfg), "full_run": (stride or int(sc["stride_days"])) == 1},
        "weights": {"live_like": live_info, "recency": rec_info, "headline_split": sc["headline"]},
        "field": {"members": list(sc["field"]), "run_keys": {n: r.key for n, r in field.items()},
                  "return_gate_floor": sc["return_gate_floor"], "rel_unit": scale},
        "primary": {"variant": prim["variant"], "convention": prim["convention"],
                    **head[prim["convention"]][prim["variant"]]},
        "headline": head,
        "eligible": all(g["pass"] for g in gres.values()),
        "gates": gres,
        "summary": summary(win.loc[starts].R, win.loc[starts].MDD),
        "returns_liquidated": summary(win.loc[starts].R_liq, win.loc[starts].MDD),
        "activity": {"min_active_days": int(win.loc[starts].active_days.min()),
                     "median_active_days": float(win.loc[starts].active_days.median()),
                     "guard_share_of_active_days": gres["G1"]["guard_share_of_active_days"],
                     "mean_fees_e0": float(win.loc[starts].fees_e0.mean()),
                     "mean_spread_e0": float(win.loc[starts].spread_e0.mean()),
                     "mean_turnover": float(win.loc[starts].turnover.mean()),
                     "mean_gross": float(win.loc[starts].gross_avg.mean()),
                     "max_gross": float(win.loc[starts].gross_max.max()),
                     "mean_net": float(win.loc[starts].net_avg.mean()),
                     "mean_orders": float(win.loc[starts].orders.mean()),
                     "max_calls_one_decision": int(win.loc[starts].max_calls_decision.max())},
        "floor_hits": floor_hits,
        "layers": layers,
        "ratios": list(RATIOS),
        "per_window": per_cols,
    }
    ctx = {"run": run, "field": field, "long_only": lo, "starts": starts, "sim": sim, "w_live": w_live,
           "w_rec": w_rec, "gate": gate, "cs": cs, "grid": grid, "sets": sets, "regime": regime, "field_median": med,
           "field_cs": field_cs, "field_scale": scale}
    return json.loads(dumps(score)), ctx
