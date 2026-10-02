"""Robustness check of pol_switch_vt_tl_e20v45 (research/baitoey/prereg/20261003-e20v45-plateau.md).

E0 and the vt_mom reference are read from the registry; the six neighbours are scored one at a time with
score_model like --score, not registered.

    python -m research.baitoey.e20v45_plateau
"""
from __future__ import annotations

import copy
import json
import logging

import pandas as pd

from backtest.data import load_market
from backtest.scoring.registry import resolve
from backtest.scoring.score import dumps, score_model
from research.baitoey.shock_plateau import TYPES, volatile_hit
from research.baitoey.vt_dual import registered_score, summarize
from research.baitoey.vt_plateau import pct
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models import get

NAME = "pol_switch_vt_tl_e20v45"
OUT = ROOT / "results" / "baitoey" / "20261003-e20v45-plateau"
MARGIN, FALLS_EDGE = 0.03, 0.10


def switch(**kw):
    return lambda p: {**p, "switch": {**p["switch"], **kw}}


def cap(x: float):
    def f(p):
        q = copy.deepcopy(p)
        q["sleeves"]["baitoey_vt_mom"]["override"] = {**(q["sleeves"]["baitoey_vt_mom"].get("override") or {}),
                                                      "target_daily_vol": x}
        return q
    return f


RUNS = {"E1": ("switch EMA 15 days", switch(ema_days=15)), "E2": ("switch EMA 25 days", switch(ema_days=25)),
        "E3": ("switch band 2%", switch(hysteresis=0.02)), "E4": ("switch band 4%", switch(hysteresis=0.04)),
        "E5": ("momentum cap 3.5%/day", cap(0.035)), "E6": ("momentum cap 5.5%/day", cap(0.055))}


def report(rows: dict[str, dict]) -> str:
    lines = ["# Robustness check of pol_switch_vt_tl_e20v45 (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261003-e20v45-plateau.md`. One setting changed per run;",
             "neighbours scored like `--score`, not registered. Type columns: hit rate (mean of the three bars) by BTC's",
             "14-day move (<= -5% / -5..0% / 0..+5% / >= +5%) and in the most volatile windows.", "",
             "| Run | Change | HEADLINE_RET | vs E0 | without post-holdout | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Guard share | Fees | Hard gates |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    e0 = rows["E0"]["headline"]
    for x in rows.values():
        ty = " | ".join("—" if x["types"][k] is None else f"{100 * x['types'][k]:.0f}%" for k in TYPES)
        vol = "—" if x.get("volatile") is None else f"{100 * x['volatile']:.0f}%"
        rp = " · ".join(f"{pct(p['R'])} #{p['rank']}/{p['teams']}" for p in x["replay"]) or "—"
        lines.append(f"| {x['run']} | {x['change']} | **{x['headline']:.3f}** | {x['headline'] - e0:+.3f} | {x['in_sample']:.3f} | "
                     f"{ty} | {vol} | {pct(x['median_R'])} / {pct(x['mean_R'])} | {pct(x['worst_R'])} | {rp} | "
                     f"{100 * x['guard_share']:.0f}% | {pct(x['fees'], 2)} | {'pass' if x['eligible'] else 'FAIL'} |")
    lines.append("")
    done = [r for r in RUNS if r in rows]
    if len(done) < len(RUNS):
        lines.append(f"Verdict: pending ({len(done)} of {len(RUNS)} neighbours scored).")
        return "\n".join(lines) + "\n"
    bar, edge = e0 - MARGIN, rows["vt_mom"]["strong_fall"] + FALLS_EDGE
    low = [r for r in RUNS if not rows[r]["eligible"] or rows[r]["headline"] < bar]
    weak = [r for r in RUNS if rows[r]["strong_fall"] is None or rows[r]["strong_fall"] < edge]
    name = lambda rs: ", ".join(f"{r} ({RUNS[r][0]})" for r in rs) or "none"
    lines += [f"- Score holds (hard gates and HEADLINE_RET >= {bar:.3f}): {'yes' if not low else 'NO'}; below: {name(low)}.",
              f"- Falls edge holds (strong-fall hit >= {100 * edge:.1f}%, vt_mom + 10 points): {'yes' if not weak else 'NO'}; failing: {name(weak)}.",
              "", f"**Verdict: {'ROBUST' if not low and not weak else 'NOT ROBUST'}.**",
              f"Tool version(s): {', '.join(sorted({x['tool_version'] for x in rows.values()}))}."]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(OUT / "run.log"), logging.StreamHandler()])
    log = logging.getLogger("e20v45_plateau")
    cfg = load_config()
    btc = pd.read_parquet(resolve(cfg["harness"]["panel_dir"]) / "panel_close_1h.parquet", columns=["BTCUSDT"])["BTCUSDT"]
    rows = {}
    for label, model in (("E0", NAME), ("vt_mom", "baitoey_vt_mom")):
        s = registered_score(model)
        rows[label] = {**summarize(label, "none (base)" if label == "E0" else "reference", s, btc), "volatile": volatile_hit(s, btc)}
    market, model = load_market(cfg), get(NAME)
    for label, (change, edit) in RUNS.items():
        c = copy.deepcopy(cfg)
        c["models"][NAME] = edit(copy.deepcopy(cfg["models"][NAME]))
        log.info("%s (%s): scoring", label, change)
        score, _ = score_model(model, market, c, use_cache=True, log=log)
        (OUT / f"{label}-score.json").write_text(dumps(score))
        rows[label] = {**summarize(label, change, score, btc), "volatile": volatile_hit(score, btc)}
        (OUT / "report.md").write_text(report(rows))
        log.info("%s: HEADLINE_RET %.4f", label, rows[label]["headline"])
    (OUT / "rows.json").write_text(json.dumps(rows, indent=1, default=str))
    log.info("done: %s", OUT / "report.md")


if __name__ == "__main__":
    main()
