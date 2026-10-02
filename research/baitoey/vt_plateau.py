"""Plateau check of baitoey_vt_mom under scoring v2 (research/baitoey/prereg/20261002-vt-plateau.md).

Scores the registered model and one-setting neighbours with score_model, exactly as `--score` does (same tool
version), but registers nothing: the leaderboard is untouched. One run at a time (the harness uses up to 8 workers);
finished runs are skipped on a restart, and the report is rewritten after every run.

    python -m research.baitoey.vt_plateau
"""
from __future__ import annotations

import copy
import json
import logging

import numpy as np
import pandas as pd

from backtest.data import load_market
from backtest.scoring import explain
from backtest.scoring.registry import resolve
from backtest.scoring.score import dumps, score_model, wquantile
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models import get

NAME = "baitoey_vt_mom"
OUT = ROOT / "results" / "baitoey" / "20261002-vt-plateau"
MARGIN = 0.03
RUNS = {                                     # the pre-registered order: base, the four first, then the rest
    "P0": ("none (base)", {}),
    "P1": ("volume rule off", {"early_exit": False}),
    "P2": ("lookbacks 3/7/14", {"lookback_days": [3, 7, 14]}),
    "P3": ("top 4, keep 8", {"k": 4, "keep_rank": 8}),
    "P4": ("top 8, keep 16", {"k": 8, "keep_rank": 16}),
    "P5": ("lookbacks 5/10", {"lookback_days": [5, 10]}),
    "P6": ("lookbacks 10/21", {"lookback_days": [10, 21]}),
    "P7": ("exit volume ratio 1.25", {"exit_volume_ratio": 1.25}),
    "P8": ("exit volume ratio 2.0", {"exit_volume_ratio": 2.0}),
    "P9": ("ban 12 h", {"exit_cooldown_hours": 12}),
    "P10": ("ban 48 h", {"exit_cooldown_hours": 48}),
    "P11": ("vol cap 2%/day", {"target_daily_vol": 0.02}),
}
NEIGHBOURS = [r for r in RUNS if r not in ("P0", "P1")]


def summarize(run: str, score: dict, btc: pd.Series) -> dict:
    rf = score["return_first"]["full"]
    pw = pd.DataFrame(score["per_window"])
    pw.index = pd.to_datetime(pw.pop("start"), utc=True)
    t = pw[pw.scored.astype(bool)]
    prof = explain.profile(t, explain.market_types(t.index, btc, t["regime"]))
    w = t.w_final.astype(float)
    act = score["activity"]
    return {"run": run, "change": RUNS[run][0], "params": RUNS[run][1],
            "headline": score["primary"]["headline"], "in_sample": score["primary"]["in_sample"],
            "hit": rf["hit"], "hit_up": rf["hit_up"], "hit_down": rf["hit_down"],
            "eligible": bool(score["eligible"]),
            "hard_fail": [g for g, v in score["gates"].items() if v["hard"] and not v["pass"]],
            "strong_fall": prof.get("strong fall", {}).get("hit"), "strong_rise": prof.get("strong rise", {}).get("hit"),
            "median_R": wquantile(t.R_liq.astype(float), w, 0.5),
            "mean_R": float((t.R_liq.astype(float) * w).sum() / w.sum()),
            "worst_R": float(t.R_liq.astype(float).min()),
            "replay": [{"name": x["name"], "R": x["R"], "rank": x["ranks"][0]["rank"], "teams": x["ranks"][0]["teams"]}
                       for x in (score.get("replay") or {}).get("windows", [])],
            "guard_share": act["guard_share_of_active_days"], "turnover": act["mean_turnover"], "fees": act["mean_fees_e0"],
            "tool_version": score["tool_version"], "run_key": score["model"]["run_key"]}


def pct(x, d=1) -> str:
    return "—" if x is None or not np.isfinite(x) else f"{100 * x:+.{d}f}%"


def report(rows: dict[str, dict]) -> str:
    lines = ["# Plateau check of baitoey_vt_mom (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261002-vt-plateau.md`. One setting changed per run; scored with",
             "`score_model` like `--score`, not registered. Strong fall / rise = hit rate (mean of the three bars) in",
             "windows where BTC moved <= -5% / >= +5%.", "",
             "| Run | Change | HEADLINE_RET | vs P0 | without post-holdout | HIT L / M / S | Strong fall / rise | Median / mean R | Worst R | Round 1 · Final | Guard share | Fees | Hard gates |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    base = rows.get("P0", {}).get("headline")
    for r in RUNS:
        if r not in rows:
            lines.append(f"| {r} | {RUNS[r][0]} | (not run yet) | | | | | | | | | | |")
            continue
        x = rows[r]
        h = x["hit"]
        diff = "—" if base is None else f"{x['headline'] - base:+.3f}"
        rp = " · ".join(f"{pct(p['R'])} #{p['rank']}/{p['teams']}" for p in x["replay"]) or "—"
        sf = "—" if x["strong_fall"] is None else f"{100 * x['strong_fall']:.0f}%"
        sr = "—" if x["strong_rise"] is None else f"{100 * x['strong_rise']:.0f}%"
        lines.append(f"| {r} | {x['change']} | **{x['headline']:.3f}** | {diff} | {x['in_sample']:.3f} | "
                     f"{h['LENIENT']:.2f} / {h['MIDDLE']:.2f} / {h['STRICT']:.2f} | {sf} / {sr} | "
                     f"{pct(x['median_R'])} / {pct(x['mean_R'])} | {pct(x['worst_R'])} | {rp} | "
                     f"{100 * x['guard_share']:.0f}% | {pct(x['fees'], 2)} | {'pass' if x['eligible'] else 'FAIL ' + ', '.join(x['hard_fail'])} |")
    lines.append("")
    done = [r for r in NEIGHBOURS if r in rows]
    if base is None or len(done) < len(NEIGHBOURS):
        lines.append(f"Verdict: pending ({len(done)} of {len(NEIGHBOURS)} neighbours scored).")
    else:
        low = [r for r in NEIGHBOURS if not rows[r]["eligible"] or rows[r]["headline"] < base - MARGIN]
        lines.append(f"**Verdict: {'PLATEAU' if not low else 'PEAK'}** (every neighbour must pass the hard gates and score "
                     f">= P0 - {MARGIN} = {base - MARGIN:.3f})." + (f" Below: {', '.join(f'{r} ({RUNS[r][0]})' for r in low)}." if low else ""))
    if "P0" in rows and "P1" in rows:
        lines.append(f"Volume rule's contribution (P0 - P1): {rows['P0']['headline'] - rows['P1']['headline']:+.3f}.")
    tools = {x["tool_version"] for x in rows.values()}
    lines.append(f"Tool version(s): {', '.join(sorted(tools))}.")
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(OUT / "run.log"), logging.StreamHandler()])
    log = logging.getLogger("vt_plateau")
    rows_path = OUT / "rows.jsonl"
    rows = {}
    if rows_path.exists():
        rows = {d["run"]: d for d in map(json.loads, rows_path.read_text().splitlines()) if d}
    cfg = load_config()
    market = load_market(cfg)
    btc = pd.read_parquet(resolve(cfg["harness"]["panel_dir"]) / "panel_close_1h.parquet", columns=["BTCUSDT"])["BTCUSDT"]
    model = get(NAME)
    for run, (label, change) in RUNS.items():
        if run in rows:
            continue
        c = copy.deepcopy(cfg)
        c["models"][NAME] = {**copy.deepcopy(cfg["models"][NAME]), **change}
        log.info("%s (%s): scoring", run, label)
        score, _ = score_model(model, market, c, use_cache=True, log=log)
        (OUT / f"{run}-score.json").write_text(dumps(score))
        rows[run] = summarize(run, score, btc)
        with rows_path.open("a") as f:
            f.write(json.dumps(rows[run]) + "\n")
        (OUT / "report.md").write_text(report(rows))
        log.info("%s: HEADLINE_RET %.4f, eligible %s", run, rows[run]["headline"], rows[run]["eligible"])
    log.info("done: %s", OUT / "report.md")


if __name__ == "__main__":
    main()
