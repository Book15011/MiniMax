"""Which hour of the day should e20v45 decide at? (research/baitoey/prereg/20261003-decision-hour.md).

Each run scores the hourly wrapper with one decision hour (like --score, not registered). Runs can be started
separately (one label per process); the report is rebuilt from every score file present.

    python -m research.baitoey.decision_hour [H00 H04 H08 H12 H16 H20]
"""
from __future__ import annotations

import copy
import json
import logging
import sys

import pandas as pd

from backtest.data import load_market
from backtest.scoring.registry import resolve
from backtest.scoring.score import dumps, score_model
from research.baitoey.shock_plateau import TYPES, volatile_hit
from research.baitoey.vt_dual import summarize
from research.baitoey.vt_plateau import pct
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models.baitoey._decision_hour import DecisionHour

NAME = "pol_switch_vt_tl_e20v45"
OUT = ROOT / "results" / "baitoey" / "20261003-decision-hour"
HOURS = (0, 4, 8, 12, 16, 20)
RUNS = {f"H{h:02d}": h for h in HOURS}
CONTROL, MARGIN = "H16", 0.03


def row(label: str, score: dict, btc: pd.Series) -> dict:
    h = RUNS[label]
    return {**summarize(label, f"{h:02d}:00 UTC ({(h + 8) % 24:02d}:00 HKT)", score, btc), "volatile": volatile_hit(score, btc),
            "cs_hit": score["primary"]["cs_hit"]}


def verdict(rows: dict[str, dict]) -> str:
    if len(rows) < len(RUNS):
        return f"Verdict: pending ({len(rows)} of {len(RUNS)} hours scored)."
    base = rows[CONTROL]["headline"]
    move = []
    for k, h in RUNS.items():
        if k == CONTROL:
            continue
        nb = [f"H{(h - 4) % 24:02d}", f"H{(h + 4) % 24:02d}"]
        if (rows[k]["eligible"] and rows[k]["headline"] >= base + MARGIN
                and all(rows[n]["headline"] >= base for n in nb)):
            move.append(k)
    spread = max(x["headline"] for x in rows.values()) - min(x["headline"] for x in rows.values())
    head = f"Spread of HEADLINE_RET across the six hours: {spread:.3f}."
    if move:
        return head + " Hours that beat 16:00 by the margin on a plateau: " + ", ".join(move) + " -> **MOVE (team to choose)**."
    return head + " No hour beats 16:00 UTC by the margin on a plateau -> **KEEP 16:00 UTC**."


def report(rows: dict[str, dict]) -> str:
    lines = ["# Which hour should e20v45 decide at? (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261003-decision-hour.md`. All runs use the same hourly wrapper;",
             "H16 (today's hour) is the control. Scored like `--score`, not registered. Type columns: hit rate (mean of the",
             "three bars) by BTC's 14-day move (<= -5% / -5..0% / 0..+5% / >= +5%) and in the most volatile windows.", "",
             "| Run | Decision hour | HEADLINE_RET | vs H16 | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Fees | Hard gates |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    base = rows.get(CONTROL, {}).get("headline")
    for key in RUNS:
        if key not in rows:
            continue
        x = rows[key]
        ty = " | ".join("—" if x["types"][k] is None else f"{100 * x['types'][k]:.0f}%" for k in TYPES)
        vol = "—" if x.get("volatile") is None else f"{100 * x['volatile']:.0f}%"
        rp = " · ".join(f"{pct(p['R'])} #{p['rank']}/{p['teams']}" for p in x["replay"]) or "—"
        vs = "—" if base is None else f"{x['headline'] - base:+.3f}"
        lines.append(f"| {key} | {x['change']} | **{x['headline']:.3f}** | {vs} | {x['in_sample']:.3f} | {x['cs_hit']:.3f} | "
                     f"{ty} | {vol} | {pct(x['median_R'])} / {pct(x['mean_R'])} | {pct(x['worst_R'])} | {rp} | "
                     f"{pct(x['fees'], 2)} | {'pass' if x['eligible'] else 'FAIL'} |")
    lines += ["", "- " + verdict(rows), "",
              f"Tool version(s): {', '.join(sorted({x['tool_version'] for x in rows.values()}))}."]
    return "\n".join(lines) + "\n"


def rebuild(btc: pd.Series) -> None:
    rows = {}
    for key in RUNS:
        f = OUT / f"{key}-score.json"
        if f.exists():
            rows[key] = row(key, json.loads(f.read_text()), btc)
    (OUT / "report.md").write_text(report(rows))
    (OUT / "rows.json").write_text(json.dumps(rows, indent=1, default=str))


def main(labels: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tag = "-".join(labels) or "all"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(OUT / f"run-{tag}.log"), logging.StreamHandler()])
    log = logging.getLogger("decision_hour")
    cfg = load_config()
    btc = pd.read_parquet(resolve(cfg["harness"]["panel_dir"]) / "panel_close_1h.parquet", columns=["BTCUSDT"])["BTCUSDT"]
    market, model = load_market(cfg), DecisionHour()
    for label in labels or list(RUNS):
        c = copy.deepcopy(cfg)
        c["models"][model.spec.name] = {"vt": copy.deepcopy(cfg["models"][NAME]), "decision_hour": RUNS[label]}
        log.info("%s (decision at %02d:00 UTC): scoring", label, RUNS[label])
        score, _ = score_model(model, market, c, use_cache=True, log=log)
        (OUT / f"{label}-score.json").write_text(dumps(score))
        log.info("%s: HEADLINE_RET %.4f", label, score["primary"]["headline"])
        rebuild(btc)
    rebuild(btc)
    log.info("done: %s", OUT / "report.md")


if __name__ == "__main__":
    main(sys.argv[1:])
