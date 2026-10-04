"""Momentum long-short at 60/40 and 50/50 (research/baitoey/prereg/20261005-long-short-split.md).

    python -m research.baitoey.long_short_split [L60 L50]   score runs (one label per process; not registered)
    python -m research.baitoey.long_short_split report       the comparison, with the lock-in numbers
"""
from __future__ import annotations

import copy
import glob
import json
import logging
import sys

import numpy as np
import pandas as pd

from backtest.data import load_market
from backtest.scoring.evaluate import simulate
from backtest.scoring.metrics import window_metrics
from backtest.scoring.registry import resolve
from backtest.scoring.score import dumps, score_model
from backtest.scoring.windows import pool_starts
from research.baitoey.shock_plateau import TYPES
from research.baitoey.vt_dual import registered_score, summarize
from research.baitoey.vt_plateau import pct
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models import get

NAME = "pol_mom_ss"
OUT = ROOT / "results" / "baitoey" / "20261005-long-short-split"
RUNS = {"L60": (0.60, 0.40), "L50": (0.50, 0.50)}
TOOL = "3036a0d8bfdaa6a0"
H, EXIT, LOCK, DAY, MARGIN = 336, 0.0013, 0.03, 10, 0.03


def config_for(cfg: dict, label: str) -> dict:
    c = copy.deepcopy(cfg)
    lg, sg = RUNS[label]
    c["models"][NAME] = {**copy.deepcopy(cfg["models"][NAME]), "long_gross": lg, "short_gross": sg}
    return c


def report(cfg: dict) -> None:
    sc = cfg["scoring"]; market = load_market(cfg); starts = pool_starts(market, cfg); liq = float(sc["liquidation_cost"])
    btc = pd.read_parquet(resolve(cfg["harness"]["panel_dir"]) / "panel_close_1h.parquet", columns=["BTCUSDT"])["BTCUSDT"]
    points = np.array([0] + list(range(4, H, 24)) + [H])
    ref = [json.load(open(f)) for f in glob.glob(str(ROOT / "results/*/*/team_rot_ew-*/score.json"))]
    ref = [s for s in ref if s.get("tool_version") == TOOL][-1]
    pw = pd.DataFrame(ref["per_window"]); pw.index = pd.to_datetime(pw.pop("start"), utc=True); pw = pw[pw.scored.astype(bool)].reindex(starts)
    up = pw.btc_up.astype(bool).to_numpy(); w = pw.w_final.to_numpy(); w = w / w.sum()
    bars = np.column_stack([np.where(up, 0.0, -0.014965215), np.zeros(len(starts)), np.maximum(0.0, pw.field_median_R_liq.to_numpy())])
    fr = {}
    for n in sc["field"]:
        rr = simulate(get(n), market, cfg, starts, use_cache=True); k = rr.windows.index.get_indexer(starts)
        fr[n] = rr.equity[k, -1] * (1 - liq * rr.gross[k, -1]) - 1
    cut = np.where(up, np.maximum(0, pd.DataFrame(fr).max(axis=1).to_numpy()), 0.006)

    def scored(E, G, locked):
        E, G = E.copy(), G.copy()
        if locked:
            R0 = E / E[:, :1] - 1
            for k in range(len(E)):
                hit = np.nonzero(R0[k, DAY * 24:H - 1] >= LOCK)[0]
                if len(hit):
                    h = DAY * 24 + hit[0] + 1; E[k, h:] = E[k, h] * (1 - EXIT * G[k, h]); G[k, h:] = 0.0
        R = E[:, -1] * (1 - liq * G[:, -1]) / E[:, 0] - 1
        comp = window_metrics(E, G[:, -1], sc, points=points)["FLOORED.V1.composite"].to_numpy()
        ind = (R[:, None] >= bars).astype(float); ok = ind[:, 0] > 0
        return float((w[:, None] * ind).sum(0).mean()), float((w[ok] * comp[ok]).sum() / w[ok].sum()), float((w * (R >= cut)).sum())

    rows = [("e20v45 (live)", "pol_switch_vt_tl_e20v45", cfg, registered_score("pol_switch_vt_tl_e20v45")),
            ("L75 (pol_mom_ss, registered)", NAME, cfg, registered_score(NAME))]
    for label in RUNS:
        f = OUT / f"{label}-score.json"
        if f.exists():
            lg, sg = RUNS[label]
            rows.append((f"{label} ({int(100 * lg)}/{int(100 * sg)}){' research only' if label == 'L50' else ''}", NAME, config_for(cfg, label), json.loads(f.read_text())))
    lines = ["# Momentum long-short at 60/40 and 50/50 (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261005-long-short-split.md`. Scored like `--score`, not registered.", "",
             "| Model | HEADLINE_RET | Top-20 proxy | Strong fall | Mild fall | Mild rise | Strong rise | Median / mean R | Worst R | Round 1 · Final | With lock-in: HEADLINE_RET / CS_HIT / top-20 |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    lock = {}
    for lab, name, c, s in rows:
        x = summarize(lab, "", s, btc)
        run = simulate(get(name), market, c, starts, use_cache=True); k = run.windows.index.get_indexer(starts)
        E, G = run.equity[k].astype(float), run.gross[k].astype(float)
        n0, l1 = scored(E, G, False), scored(E, G, True)
        lock[lab] = l1
        ty = " | ".join("—" if x["types"][q] is None else f"{100 * x['types'][q]:.0f}%" for q in TYPES)
        rp = " · ".join(f"{pct(p['R'])} #{p['rank']}/{p['teams']}" for p in x["replay"]) or "—"
        lines.append(f"| {lab} | **{x['headline']:.3f}** | {n0[2]:.3f} | {ty} | {pct(x['median_R'])} / {pct(x['mean_R'])} | {pct(x['worst_R'])} | {rp} | "
                     f"{l1[0]:.3f} / {l1[1]:.3f} / {l1[2]:.3f} |")
    e0 = lock["e20v45 (live)"]
    l60 = [v for k, v in lock.items() if k.startswith("L60")]
    if l60:
        ok = l60[0][0] >= e0[0] + MARGIN and l60[0][2] >= e0[2]
        lines += ["", f"- L60 with the lock-in: HEADLINE_RET {l60[0][0]:.3f} vs e20v45 {e0[0]:.3f}, top-20 proxy {l60[0][2]:.3f} vs {e0[2]:.3f} -> "
                  f"**{'CANDIDATE' if ok else 'no candidate'}**."]
    lines += ["", f"Tool version: {TOOL}."]
    (OUT / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(args: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(OUT / f"run-{'-'.join(args) or 'all'}.log"), logging.StreamHandler()])
    log = logging.getLogger("long_short_split")
    cfg = load_config()
    if args == ["report"]:
        report(cfg)
        return
    market = load_market(cfg)
    for label in args or list(RUNS):
        log.info("%s %s: scoring", label, RUNS[label])
        score, _ = score_model(get(NAME), market, config_for(cfg, label), use_cache=True, log=log)
        (OUT / f"{label}-score.json").write_text(dumps(score))
        log.info("%s: HEADLINE_RET %.4f", label, score["primary"]["headline"])


if __name__ == "__main__":
    main(sys.argv[1:])
