"""Score one model end to end (docs/EVALUATION.md): runs, field, weights, the return-first score, gates, score.json.

score.json holds no wall-clock time or registry state, so two runs of the same code on the same data produce
the same file byte for byte (ranks among other runs live in the report and the leaderboard instead).

Primary: HEADLINE_RET (backtest.scoring.returnfirst), on the full pool and on the in-sample pool (the same rules on
the windows ending by harness.holdout_from alone). Report-only: the previous primary, REL (field-best bar), on the
same windows with the live-like and recency weights, its robustness layers, and the gates G2, G3 and both G6 forms.
"""
from __future__ import annotations

import json
import logging
import math

import numpy as np
import pandas as pd

from backtest.data import Market
from backtest.evaluate import git_state, holdout_start
from backtest.scoring.competition import (add_rel, all_variants, field_bar, field_median, field_scale, gates, headline,
                                          regime_grid, rel_layers, return_gate)
from backtest.scoring.evaluate import Run, input_hashes, simulate
from backtest.scoring.leakage import leakage_gate
from backtest.scoring.metrics import FLOORS, RATIOS
from backtest.scoring.replay import replay
from backtest.scoring.returnfirst import BARS, bar_table, pol_bar_table, pol_period_rel, score_pool
from backtest.scoring.windows import (btc_up, final_weights, live_like_weights, pool_starts, post_holdout,
                                      recency_weights, regimes, scored_starts, window_sets)
from src.contracts import Model
from src.models import get

SCHEMA = "minimax-score/2"
PRIMARY = "HEADLINE_RET"


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
    pool = pool_starts(market, cfg)
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


def tail_table(win: pd.DataFrame, sets: dict) -> dict:
    """Report-only (plain R): worst, 5th percentile, max drawdown median and p90, STRESS crash and rebound medians."""
    R, M = win.R, win.MDD
    return {"worst_R": float(R.min()), "p5_R": float(R.quantile(0.05)), "median_MDD": float(M.median()),
            "p90_MDD": float(M.quantile(0.9)),
            "stress_drops_median_R": float(R.reindex(sets["STRESS_DROPS"]).median()),
            "stress_rebounds_median_R": float(R.reindex(sets["STRESS_REBOUNDS"]).median())}


def wquantile(x: pd.Series, w: pd.Series, q: float) -> float:
    o = np.argsort(x.to_numpy())
    c = np.cumsum(w.reindex(x.index).to_numpy()[o])
    return float(x.to_numpy()[o][np.searchsorted(c / c[-1], q)])


def weighted_block(win: pd.DataFrame, gate: pd.Series, w: pd.Series) -> dict:
    """The distribution behind a weighted layer: weighted median and 10th percentile of R, gate pass share."""
    return {"median_R": wquantile(win.R, w, 0.5), "worst10_R": wquantile(win.R, w, 0.1),
            "median_MDD": wquantile(win.MDD, w, 0.5),
            "gate_pass_share": float((gate * w.reindex(gate.index)).sum() / w.reindex(gate.index).sum())}


def layer_block(win: pd.DataFrame, cs: pd.DataFrame, gate: pd.Series, idx: pd.DatetimeIndex, sc: dict) -> dict:
    """Report-only layer: flat means over a window set (REL on the field-best bar, as before)."""
    if len(idx) == 0:
        return {"n": 0}
    p = f"{sc['rel']['convention']}.REL"
    w, c = win.loc[idx], cs.loc[idx]
    return {**summary(w.R, w.MDD), "gate_pass_share": float(gate.loc[idx].mean()),
            "mean_cs": {k[:-3]: float(v) for k, v in c.mean().items()},
            "mean_cs_rel": float(c[f"{p}.cs"].mean()), "median_composite_rel": float(w[f"{p}.composite"].median())}


def g4_long_only(model: Model, market: Market, cfg: dict, sim: pd.DatetimeIndex, starts: pd.DatetimeIndex,
                 btc_worst: float, use_cache: bool, log: logging.Logger) -> tuple[dict, Run | None]:
    """The live fallback if shorts are refused. Hard: it runs cleanly (finite numbers, every window, no negative
    target). Report-only: whether it passes G1 (activity) and G2 (worst fortnight better than BTC_HOLD's)."""
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
    return {"pass": True, "ran": True, "run_key": lo.key, "long_only_G1": a_ok, "long_only_G2": w_ok,
            "long_only_worst": worst, "long_only_min_active_days": int(w.active_days.min()),
            "detail": f"long-only run completes cleanly in {len(lo.windows)} windows. Report-only: "
                      f"{share:.1%} of windows have >= {g1['min_active_days']} active HKT days (G1 "
                      f"{'ok' if a_ok else 'fails'}); worst R {worst:+.2%} vs BTC_HOLD {btc_worst:+.2%} "
                      f"(G2 {'ok' if w_ok else 'fails'})"}, lo


def leakage(run: Run, model: Model, market: Market, cfg: dict, use_cache: bool) -> dict:
    """G5, cached next to the run (same key: same code, parameters and data)."""
    from src.config import resolve
    path = resolve(cfg["scoring"]["cache_dir"]) / run.name / f"{run.key}.g5.json"
    if use_cache and path.exists():
        return json.loads(path.read_text())
    out = leakage_gate(model, market, run.targets, run.params, cfg["scoring"]["gates"]["G5"])
    path.write_text(json.dumps(out))
    return out


def return_first(win: pd.DataFrame, field: dict[str, Run], market: Market, cfg: dict,
                 starts: pd.DatetimeIndex) -> tuple[dict, dict, pd.DataFrame]:
    """The return-first numbers on the full pool and on the in-sample pool, their weights, and the per-window
    columns (bars, cleared or not, weights)."""
    sc = cfg["scoring"]
    risk = sc["risk"]["primary"]
    prim_col = f"{risk['convention']}.{risk['variant']}.composite"
    utc_col = f"UTC.{prim_col}"
    up = btc_up(market, starts, cfg)
    fR = pd.DataFrame({n: r.windows.R_liq for n, r in field.items()}).reindex(starts)
    fRp = pd.DataFrame({n: r.windows.R for n, r in field.items()}).reindex(starts)
    bars = bar_table(up, fR, sc["bars"])
    bars_plain = bar_table(up, fRp, sc["bars"])
    pbars = pol_bar_table(fR, starts)
    hold = post_holdout(starts, cfg)
    pools = {"full": starts, "in_sample": starts[~hold]}
    blocks, weights = {}, {}
    for name, pool in pools.items():
        if len(pool) == 0:
            continue
        w_live, live_info = live_like_weights(pool, cfg, starts)
        w_rec, rec_info = recency_weights(pool, cfg)
        w, wf, pi_up = final_weights(w_live, w_rec, up.reindex(pool), sc["headline"])
        b = score_pool(win.loc[pool], bars.loc[pool], pbars.loc[pool], bars_plain.loc[pool], up.loc[pool], wf,
                       prim_col, utc_col)
        b.update(pi_up=pi_up, n_up=int(up.loc[pool].sum()), first_start=pool[0], last_start=pool[-1],
                 weights={"live_like": live_info, "recency": rec_info,
                          "effective_n_final": float(1.0 / (wf ** 2).sum())})
        blocks[name] = b
        weights[name] = {"w_live": w_live, "w_rec": w_rec, "w": w, "w_final": wf}
    cols = pd.DataFrame(index=starts)
    cols["post_holdout"] = hold
    cols["btc_up"] = up
    cols["month"] = starts.year * 12 + starts.month
    cols["field_median_R_liq"] = fR.median(axis=1)
    for k in BARS:
        cols[f"bar_{k}"] = bars[k]
        cols[f"hit_{k}"] = (win.R_liq.reindex(starts) >= bars[k]).astype(int)
    for name, ws in weights.items():
        sfx = "" if name == "full" else "_in_sample"
        for k, s in ws.items():
            cols[f"{k}{sfx}"] = s.reindex(starts)
    return blocks, weights, cols


def score_model(model: Model, market: Market, cfg: dict, use_cache: bool = True, stride: int | None = None,
                log: logging.Logger | None = None) -> tuple[dict, dict]:
    """Returns (score, context): score is the content of score.json; context holds the runs for the report."""
    log = log or logging.getLogger(__name__)
    sc, h = cfg["scoring"], cfg["harness"]
    starts = scored_starts(market, cfg, stride)
    sim = simulated_starts(market, cfg, starts)
    run = simulate(model, market, cfg, sim, use_cache=use_cache, log=log)
    field = field_runs(market, cfg, sim, use_cache, log, {model.spec.name: run})

    # ---- primary: return first
    rf, weights, rf_cols = return_first(run.windows, field, market, cfg, starts)
    full = weights["full"]
    w_live, w_rec, w_final = full["w_live"], full["w_rec"], full["w_final"]

    # ---- report-only: the previous primary (REL on the field-best bar) on the same windows
    rel = sc["rel"]
    fieldR = pd.DataFrame({n: r.windows.R for n, r in field.items()})
    med = field_median(fieldR)
    stat = str(rel["bar_stat"])
    bar = field_bar(fieldR, stat)
    floor = float(rel["bar_floor"])

    def gated(bar_s: pd.Series) -> tuple[dict, dict]:
        fcs = {n: cs_table(r.windows, return_gate(r.windows.R, bar_s, floor), sc).loc[starts] for n, r in field.items()}
        return fcs, field_scale(fcs, w_live, w_rec, sc)

    field_cs, scale = gated(bar)
    win = add_rel(run.windows, scale, sc, "composite")
    gate = return_gate(win.R, bar, floor)
    cs = add_rel(cs_table(win, gate, sc), scale, sc, "cs")
    head = {c: {v: headline(cs.loc[starts, f"{c}.{v}.cs"], w_live, w_rec, sc["headline"]) for v in all_variants(sc)}
            for c in sc["conventions"]}
    pc = rel["convention"]
    robust = rel_layers(cs.loc[starts], field_cs, w_live, w_rec, sc, pc)
    robust.update(min=min(robust.values()), threshold=float(rel.get("robust_min", 1.0)))
    robust["pass"] = bool(robust["min"] >= robust["threshold"])

    # ---- Pol's period check on the new windows (tie-break 4)
    per = {}
    for name, (a, b) in h["periods"].items():
        d = starts.normalize()
        m = np.asarray((d >= pd.Timestamp(a, tz="UTC")) & (d <= pd.Timestamp(b, tz="UTC")))
        per[name] = pol_period_rel(run.windows.loc[starts], {n: r.windows.loc[starts] for n, r in field.items()},
                                   w_live, w_rec, m, sc) if m.any() else None
    vals = [v for v in per.values() if v is not None]
    per["min"] = min(vals) if vals else None

    # ---- gates: G1, G4, G5 hard; G2, G3, G6 (both forms) report-only
    sets = window_sets(cfg)
    regime = regimes(sim, cfg)
    btc = field[sc["btc_hold"]].windows
    g4, lo = g4_long_only(model, market, cfg, sim, starts, float(btc.R.loc[starts].min()), use_cache, log)
    g5 = leakage(run, model, market, cfg, use_cache)
    gres = gates(win.loc[starts], btc.loc[starts], regime.loc[starts], sets["STRESS"].intersection(sim),
                 g4, g5, sc["gates"])
    eligible = all(g["pass"] for g in gres.values() if g["hard"])

    grid = regime_grid(win.R.loc[starts], regime.loc[starts])
    floor_hits = {c: {f: int(win.loc[starts, f"{c}.hit.{f}"].sum()) for f in FLOORS} for c in sc["conventions"]}
    layers = {"ALL_flat": layer_block(win, cs, gate, starts, sc),
              "weighted": {"final": weighted_block(win.loc[starts], gate.loc[starts], w_final),
                           "live_like": weighted_block(win.loc[starts], gate.loc[starts], w_live),
                           "recency": weighted_block(win.loc[starts], gate.loc[starts], w_rec)}}
    for name, s in sets.items():
        layers[name] = layer_block(win, cs, gate, s.intersection(sim), sc)
    layers["regime_grid"] = {"median_R": grid["median"].round(12).to_dict(orient="index"),
                             "count": grid["count"].to_dict(orient="index")}
    tail = {"full": tail_table(win.loc[starts], sets)}
    ins = starts[~post_holdout(starts, cfg)]
    if len(ins):
        tail["in_sample"] = tail_table(win.loc[ins], sets)
    field_rf = {n: {p: {"headline_ret": b["headline_ret"], "hit": b["hit"]} for p, b in
                    return_first(r.windows, field, market, cfg, starts)[0].items()} for n, r in field.items()}
    rp = replay(model, market, cfg, run.params)

    per_w = pd.concat([win, cs, rf_cols], axis=1).loc[sim]
    per_w.insert(0, "end", per_w.index + pd.Timedelta(days=h["window_days"]))
    per_w.insert(1, "scored", per_w.index.isin(starts))
    per_w.insert(2, "field_median_R", med.reindex(per_w.index))
    per_w.insert(3, "rel_bar_R", bar.reindex(per_w.index))
    per_w.insert(4, "rel_gate", gate.reindex(per_w.index))
    per_w.insert(5, "regime", regime.reindex(per_w.index))
    for name, s in sets.items():
        per_w[f"in_{name}"] = per_w.index.isin(s)
    per_cols = {"start": [t.isoformat() for t in per_w.index]}
    for col in per_w.columns:
        vals = per_w[col].tolist()
        per_cols[col] = [v.isoformat() if isinstance(v, pd.Timestamp) else v for v in vals]

    spec = model.spec
    s0 = win.loc[starts]
    score = {
        "schema": SCHEMA,
        "scoring_version": sc["version"],
        "tool_version": run.meta["tool_version"],
        "model": {"name": spec.name, "author": spec.author, "method": spec.method,
                  "rebalance_hours": spec.rebalance_hours, "band": spec.band, "uses_shorts": spec.uses_shorts,
                  "description": spec.description, "params": run.params, "run_key": run.key,
                  "candidate": spec.name not in sc["reference_models"]},
        "data": market.notes,
        "inputs_sha256": input_hashes(cfg),
        "code": git_state(),
        "code_when_cached": run.meta.get("git"),
        "windows": {"scored": len(starts), "simulated": len(sim), "stride_days": int(sc["stride_days"] if stride is None else stride),
                    "first_start": starts[0], "last_start": starts[-1], "days": h["window_days"],
                    "start_hour_utc": int(sc["window_hour_utc"]), "holdout_from": holdout_start(cfg),
                    "include_spent_holdout": bool(sc["include_spent_holdout"]),
                    "post_holdout": int(post_holdout(starts, cfg).sum()),
                    "full_run": (stride or int(sc["stride_days"])) == 1,
                    "first_decision_calls": run.meta.get("first_decision_calls"),
                    "first_decisions_not_converged": run.meta.get("first_decisions_not_converged")},
        "primary": {"variant": PRIMARY, "headline": rf["full"]["headline_ret"],
                    "in_sample": rf.get("in_sample", {}).get("headline_ret"), "cs_hit": rf["full"]["cs_hit"]},
        "return_first": rf,
        "field_return_first": field_rf,
        "replay": rp,
        "bars": sc["bars"],
        "eligible": eligible,
        "gates": gres,
        "period_check": per,
        "rel": {"bar_stat": stat, "bar_floor": floor, "convention": pc, "rel_unit": scale, "robustness": robust,
                "headline": head, "note": "report-only: the previous primary, on these windows and weights"},
        "field": {"members": list(sc["field"]), "run_keys": {n: r.key for n, r in field.items()}},
        "summary": summary(s0.R, s0.MDD),
        "returns_liquidated": summary(s0.R_liq, s0.MDD),
        "tail": tail,
        "activity": {"min_active_days": int(s0.active_days.min()),
                     "median_active_days": float(s0.active_days.median()),
                     "min_active_days_utc": int(s0.active_days_utc.min()),
                     "day_buckets": int(s0.day_buckets.max()), "day_buckets_utc": int(s0.day_buckets_utc.max()),
                     "guard_share_of_active_days": gres["G1"]["guard_share_of_active_days"],
                     "guard_share_of_active_days_utc": float(s0.guard_days_utc.sum() / max(s0.active_days_utc.sum(), 1)),
                     "mean_fees_e0": float(s0.fees_e0.mean()),
                     "mean_spread_e0": float(s0.spread_e0.mean()),
                     "mean_turnover": float(s0.turnover.mean()),
                     "mean_gross": float(s0.gross_avg.mean()),
                     "max_gross": float(s0.gross_max.max()),
                     "mean_net": float(s0.net_avg.mean()),
                     "mean_orders": float(s0.orders.mean()),
                     "max_calls_one_decision": int(s0.max_calls_decision.max())},
        "floor_hits": floor_hits,
        "layers": layers,
        "ratios": list(RATIOS),
        "per_window": per_cols,
    }
    ctx = {"run": run, "field": field, "long_only": lo, "starts": starts, "sim": sim, "w_live": w_live,
           "w_rec": w_rec, "w_final": w_final, "weights": weights, "gate": gate, "cs": cs, "grid": grid, "sets": sets,
           "regime": regime, "field_median": med, "field_cs": field_cs, "field_scale": scale, "field_bar": bar,
           "rf_cols": rf_cols}
    return json.loads(dumps(score)), ctx
