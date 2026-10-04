"""Act at once when the BTC state flips (research/baitoey/prereg/20261004-fast-switch.md).

    python -m research.baitoey.fast_switch [C20 F20 FD20 F15 F25]   score runs (one label per process)
    python -m research.baitoey.fast_switch report                    rebuild the report
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
from research.baitoey.vt_dual import registered_score, summarize
from research.baitoey.vt_plateau import pct
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models.baitoey._fast_switch import FastSwitch

NAME = "pol_switch_vt_tl_e20v45"
OUT = ROOT / "results" / "baitoey" / "20261004-fast-switch"
PLATEAU = ROOT / "results" / "baitoey" / "20261003-e20v45-plateau"
RUNS = {"C20": ("never", 20), "F20": ("up_and_down", 20), "FD20": ("down", 20), "F15": ("up_and_down", 15), "F25": ("up_and_down", 25)}
MARGIN, NOISE, WORST_GAIN, CS_GAIN = 0.03, 0.01, 0.02, 0.02


def row(label: str, change: str, score: dict, btc: pd.Series) -> dict:
    return {**summarize(label, change, score, btc), "volatile": volatile_hit(score, btc), "cs_hit": score["primary"]["cs_hit"]}


def report(btc: pd.Series) -> None:
    rows = {"E0": row("E0", "daily at 16:00, EMA 20 (base)", registered_score(NAME), btc)}
    for k, lab in (("E1", "daily at 16:00, EMA 15"), ("E2", "daily at 16:00, EMA 25")):
        f = PLATEAU / f"{k}-score.json"
        if f.exists():
            rows[k] = row(k, lab, json.loads(f.read_text()), btc)
    for k, (fast, ema) in RUNS.items():
        f = OUT / f"{k}-score.json"
        if f.exists():
            rows[k] = row(k, f"hourly, at once on {fast} flips, EMA {ema}" if fast != "never" else f"hourly wrapper, never at once, EMA {ema}",
                          json.loads(f.read_text()), btc)
    e0 = rows["E0"]
    lines = ["# Act at once when the BTC state flips (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261004-fast-switch.md`. Scored like `--score`, not registered. Type",
             "columns: hit rate (mean of the three bars) by BTC's 14-day move (<= -5% / -5..0% / 0..+5% / >= +5%) and in the",
             "most volatile windows.", "",
             "| Run | Rule | HEADLINE_RET | vs E0 | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Fees | Hard gates |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key in ("E0", "C20", "F20", "FD20", "E1", "F15", "E2", "F25"):
        if key not in rows:
            continue
        x = rows[key]
        ty = " | ".join("—" if x["types"][k] is None else f"{100 * x['types'][k]:.0f}%" for k in TYPES)
        vol = "—" if x.get("volatile") is None else f"{100 * x['volatile']:.0f}%"
        rp = " · ".join(f"{pct(p['R'])} #{p['rank']}/{p['teams']}" for p in x["replay"]) or "—"
        lines.append(f"| {key} | {x['change']} | **{x['headline']:.3f}** | {x['headline'] - e0['headline']:+.3f} | {x['in_sample']:.3f} | "
                     f"{x['cs_hit']:.3f} | {ty} | {vol} | {pct(x['median_R'])} / {pct(x['mean_R'])} | {pct(x['worst_R'])} | {rp} | "
                     f"{pct(x['fees'], 2)} | {'pass' if x['eligible'] else 'FAIL'} |")
    lines.append("")
    if all(k in rows for k in ("C20", "F20", "F15", "F25", "E1", "E2")):
        f, c = rows["F20"], rows["C20"]
        better = f["eligible"] and f["headline"] >= c["headline"] - NOISE and (f["headline"] >= e0["headline"] + MARGIN or (
            f["headline"] >= e0["headline"] - NOISE and (f["worst_R"] - e0["worst_R"] >= WORST_GAIN or f["cs_hit"] - e0["cs_hit"] >= CS_GAIN)))
        hold = all(rows[k]["eligible"] and rows[k]["headline"] >= rows[r]["headline"] - MARGIN for k, r in (("F15", "E1"), ("F25", "E2")))
        lines.append(f"- F20 {'better' if better else 'not better'}; neighbours {'hold' if hold else 'do not hold'} -> "
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
    log = logging.getLogger("fast_switch")
    cfg = load_config()
    btc = pd.read_parquet(resolve(cfg["harness"]["panel_dir"]) / "panel_close_1h.parquet", columns=["BTCUSDT"])["BTCUSDT"]
    if args == ["report"]:
        report(btc)
        return
    market, model = load_market(cfg), FastSwitch()
    for label in args or list(RUNS):
        fast, ema = RUNS[label]
        vt = copy.deepcopy(cfg["models"][NAME]); vt["switch"] = {**vt["switch"], "ema_days": ema}
        c = copy.deepcopy(cfg); c["models"][model.spec.name] = {"vt": vt, "fast": fast}
        log.info("%s (fast %s, EMA %d): scoring", label, fast, ema)
        score, _ = score_model(model, market, c, use_cache=True, log=log)
        (OUT / f"{label}-score.json").write_text(dumps(score))
        log.info("%s: HEADLINE_RET %.4f", label, score["primary"]["headline"])


if __name__ == "__main__":
    main(sys.argv[1:])
