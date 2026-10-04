"""v2 of the fast-switch check: flips read on the decision grid (research/baitoey/prereg/20261004-fast-switch-v2.md).

    python -m research.baitoey.fast_switch_v2 [G20 GD20 G15 G25]   score runs (one label per process)
    python -m research.baitoey.fast_switch_v2 report                rebuild the report
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
from research.baitoey.fast_switch import MARGIN, NOISE, WORST_GAIN, CS_GAIN, NAME, PLATEAU, row
from research.baitoey.fast_switch import OUT as V1
from research.baitoey.shock_plateau import TYPES
from research.baitoey.vt_dual import registered_score
from research.baitoey.vt_plateau import pct
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models.baitoey._fast_switch import FastSwitch

OUT = ROOT / "results" / "baitoey" / "20261004-fast-switch-v2"
RUNS = {"G20": ("up_and_down", 20), "GD20": ("down", 20), "G15": ("up_and_down", 15), "G25": ("up_and_down", 25)}


def report(btc: pd.Series) -> None:
    rows = {"E0": row("E0", "daily at 16:00, EMA 20 (base)", registered_score(NAME), btc),
            "C20": row("C20", "hourly wrapper, never at once, EMA 20 (v1 control)", json.loads((V1 / "C20-score.json").read_text()), btc),
            "E1": row("E1", "daily at 16:00, EMA 15", json.loads((PLATEAU / "E1-score.json").read_text()), btc),
            "E2": row("E2", "daily at 16:00, EMA 25", json.loads((PLATEAU / "E2-score.json").read_text()), btc)}
    for k, (fast, ema) in RUNS.items():
        f = OUT / f"{k}-score.json"
        if f.exists():
            rows[k] = row(k, f"at once on real {fast} flips (decision grid), EMA {ema}", json.loads(f.read_text()), btc)
    e0 = rows["E0"]
    lines = ["# Act at once on real BTC state flips, v2 on the decision grid (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261004-fast-switch.md` and its addendum `20261004-fast-switch-v2.md`.",
             "Scored like `--score`, not registered.", "",
             "| Run | Rule | HEADLINE_RET | vs E0 | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Median / mean R | Worst R | Round 1 · Final | Fees | Hard gates |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key in ("E0", "C20", "G20", "GD20", "E1", "G15", "E2", "G25"):
        if key not in rows:
            continue
        x = rows[key]
        ty = " | ".join("—" if x["types"][k] is None else f"{100 * x['types'][k]:.0f}%" for k in TYPES)
        rp = " · ".join(f"{pct(p['R'])} #{p['rank']}/{p['teams']}" for p in x["replay"]) or "—"
        lines.append(f"| {key} | {x['change']} | **{x['headline']:.3f}** | {x['headline'] - e0['headline']:+.3f} | {x['in_sample']:.3f} | "
                     f"{x['cs_hit']:.3f} | {ty} | {pct(x['median_R'])} / {pct(x['mean_R'])} | {pct(x['worst_R'])} | {rp} | "
                     f"{pct(x['fees'], 2)} | {'pass' if x['eligible'] else 'FAIL'} |")
    lines.append("")
    if all(k in rows for k in ("G20", "G15", "G25")):
        g, c = rows["G20"], rows["C20"]
        better = g["eligible"] and g["headline"] >= c["headline"] - NOISE and (g["headline"] >= e0["headline"] + MARGIN or (
            g["headline"] >= e0["headline"] - NOISE and (g["worst_R"] - e0["worst_R"] >= WORST_GAIN or g["cs_hit"] - e0["cs_hit"] >= CS_GAIN)))
        hold = all(rows[k]["eligible"] and rows[k]["headline"] >= rows[r]["headline"] - MARGIN for k, r in (("G15", "E1"), ("G25", "E2")))
        lines.append(f"- G20 {'better' if better else 'not better'}; neighbours {'hold' if hold else 'do not hold'} -> "
                     f"**{'PROPOSE' if better and hold else 'KEEP DECIDING AT 16:00 UTC'}**.")
    else:
        lines.append("- Verdict: pending.")
    lines += ["", f"Tool version(s): {', '.join(sorted({x['tool_version'] for x in rows.values()}))}."]
    (OUT / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(args: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(OUT / f"run-{'-'.join(args) or 'all'}.log"), logging.StreamHandler()])
    log = logging.getLogger("fast_switch_v2")
    cfg = load_config()
    btc = pd.read_parquet(resolve(cfg["harness"]["panel_dir"]) / "panel_close_1h.parquet", columns=["BTCUSDT"])["BTCUSDT"]
    if args == ["report"]:
        report(btc)
        return
    market, model = load_market(cfg), FastSwitch()
    for label in args or list(RUNS):
        fast, ema = RUNS[label]
        vt = copy.deepcopy(cfg["models"][NAME]); vt["switch"] = {**vt["switch"], "ema_days": ema}
        c = copy.deepcopy(cfg); c["models"][model.spec.name] = {"vt": vt, "fast": fast, "grid": "decision"}
        log.info("%s (fast %s on the decision grid, EMA %d): scoring", label, fast, ema)
        score, _ = score_model(model, market, c, use_cache=True, log=log)
        (OUT / f"{label}-score.json").write_text(dumps(score))
        log.info("%s: HEADLINE_RET %.4f", label, score["primary"]["headline"])


if __name__ == "__main__":
    main(sys.argv[1:])
