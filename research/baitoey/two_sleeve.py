"""baitoey_two_sleeve variants A-D against the leaderboard (research/baitoey/prereg/20261004-two-sleeve.md).

    python -m research.baitoey.two_sleeve [A B C D]     score variants (one label per process; not registered)
    python -m research.baitoey.two_sleeve report         the comparison, with the lock-in numbers
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
from research.baitoey.vt_dual import summarize
from research.baitoey.vt_plateau import pct
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models import get
from src.models.baitoey._two_sleeve_variants import TwoSleeveLS, TwoSleeveStaggered
from src.models.baitoey.baitoey_two_sleeve import TwoSleeve

NAME = "baitoey_two_sleeve"
OUT = ROOT / "results" / "baitoey" / "20261004-two-sleeve"
TOOL = "3036a0d8bfdaa6a0"
REFS = {"pol_switch_vt_tl_e20v45": "e20v45 (live)", "baitoey_vt_mom": "vt_mom", "pol_abl_shock": "abl_shock", "book_orch": "H1"}
H, EXIT, LOCK, DAY = 336, 0.0013, 0.03, 10
MARGIN = 0.03


def variant(cfg: dict, name: str) -> dict:
    base = cfg["models"][NAME]
    p = copy.deepcopy(base)
    for k, v in (base["variants"].get(name) or {}).items():
        p[k] = {**p[k], **v} if isinstance(v, dict) else v
    return p


def model_for(name: str):
    return {"A": TwoSleeve(), "B": TwoSleeveLS(), "C": TwoSleeve(), "D": TwoSleeveStaggered()}[name]


def config_for(cfg: dict, name: str) -> dict:
    c = copy.deepcopy(cfg)
    c["models"][model_for(name).spec.name] = variant(cfg, name)
    return c


def registered(model: str) -> tuple[dict, str]:
    latest = None
    for line in open(resolve("results/scoring/registry.jsonl")):
        r = json.loads(line) if line.strip() else None
        if r and r.get("model") == model and r.get("full") and r.get("tool_version") == TOOL:
            latest = r
    return json.load(open(resolve(latest["score_json"]))), latest


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

    def lock(E, G):
        E, G = E.copy(), G.copy(); R0 = E / E[:, :1] - 1
        for k in range(len(E)):
            hit = np.nonzero(R0[k, DAY * 24:H - 1] >= LOCK)[0]
            if len(hit):
                h = DAY * 24 + hit[0] + 1; E[k, h:] = E[k, h] * (1 - EXIT * G[k, h]); G[k, h:] = 0.0
        return E, G

    def score(E, G):
        R = E[:, -1] * (1 - liq * G[:, -1]) / E[:, 0] - 1
        comp = window_metrics(E, G[:, -1], sc, points=points)["FLOORED.V1.composite"].to_numpy()
        ind = (R[:, None] >= bars).astype(float); ok = ind[:, 0] > 0
        return {"HR": float((w[:, None] * ind).sum(0).mean()), "CS": float((w[ok] * comp[ok]).sum() / w[ok].sum()),
                "cut": float((w * (R >= cut)).sum()), "worst": float(R.min())}

    def paths_of(key: str):
        if key == "book_orch":
            _, r = registered("book_orch")
            base = ROOT / "results" / "scoring" / "cache" / "book_orch" / r.get("run_key", "033c466d54a7766f")
            a = np.load(str(base) + ".arrays.npz"); widx = pd.read_parquet(str(base) + ".windows.parquet").index
            sel = widx.get_indexer(starts)
            return a["equity"][sel].astype(float), a["gross"][sel].astype(float)
        if key in REFS:
            run = simulate(get(key), market, cfg, starts, use_cache=True)
        else:
            run = simulate(model_for(key), market, config_for(cfg, key), starts, use_cache=True)
        k = run.windows.index.get_indexer(starts)
        return run.equity[k].astype(float), run.gross[k].astype(float)

    rows = {}
    for key, lab in REFS.items():
        s, _ = registered(key)
        rows[lab] = (key, summarize(lab, "", s, btc), s)
    for v in ("A", "B", "C", "D"):
        f = OUT / f"{v}-score.json"
        if f.exists():
            s = json.loads(f.read_text())
            rows[f"{v}{' (research only)' if v == 'B' else ''}"] = (v, summarize(v, "", s, btc), s)
    lines = ["# baitoey_two_sleeve, variants A-D, against the leaderboard (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261004-two-sleeve.md`. Variants scored like `--score`, not registered;",
             "references are the registered runs. Type columns: hit rate (mean of the three bars) by BTC's 14-day move.", "",
             "| Model | HEADLINE_RET | CS_HIT | Top-20 proxy | Strong fall | Mild fall | Mild rise | Strong rise | Median / mean R | Worst R | Round 1 · Final | Fees | Gates | With lock-in: HEADLINE_RET / CS_HIT / top-20 proxy |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    locked = {}
    for lab, (key, x, s) in rows.items():
        E, G = paths_of(key)
        n0, l1 = score(E, G), score(*lock(E, G))
        locked[key] = l1
        ty = " | ".join("—" if x["types"][k] is None else f"{100 * x['types'][k]:.0f}%" for k in TYPES)
        rp = " · ".join(f"{pct(p['R'])} #{p['rank']}/{p['teams']}" for p in x["replay"]) or "—"
        lines.append(f"| {lab} | **{x['headline']:.3f}** | {s['primary']['cs_hit']:.3f} | {n0['cut']:.3f} | {ty} | "
                     f"{pct(x['median_R'])} / {pct(x['mean_R'])} | {pct(x['worst_R'])} | {rp} | {pct(x['fees'], 2)} | "
                     f"{'pass' if x['eligible'] else 'FAIL'} | {l1['HR']:.3f} / {l1['CS']:.3f} / {l1['cut']:.3f} |")
    lines.append("")
    e0 = locked["pol_switch_vt_tl_e20v45"]
    for v in ("A", "C", "D"):
        if v not in locked:
            continue
        x = [r for r in rows.values() if r[0] == v][0][1]
        ok = x["eligible"] and locked[v]["HR"] >= e0["HR"] + MARGIN and locked[v]["cut"] >= e0["cut"]
        lines.append(f"- {v}: with the lock-in HEADLINE_RET {locked[v]['HR']:.3f} vs e20v45 {e0['HR']:.3f}, top-20 proxy "
                     f"{locked[v]['cut']:.3f} vs {e0['cut']:.3f} -> **{'CANDIDATE' if ok else 'no candidate'}**.")
    lines += ["", f"Tool version: {TOOL}."]
    (OUT / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(args: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(OUT / f"run-{'-'.join(args) or 'all'}.log"), logging.StreamHandler()])
    log = logging.getLogger("two_sleeve")
    cfg = load_config()
    if args == ["report"]:
        report(cfg)
        return
    market = load_market(cfg)
    for v in args or ["A", "B", "C", "D"]:
        log.info("%s (%s): scoring", v, model_for(v).spec.name)
        score, _ = score_model(model_for(v), market, config_for(cfg, v), use_cache=True, log=log)
        (OUT / f"{v}-score.json").write_text(dumps(score))
        log.info("%s: HEADLINE_RET %.4f", v, score["primary"]["headline"])


if __name__ == "__main__":
    main(sys.argv[1:])
