"""Robustness check of the crash rule pol_abl_shock (research/baitoey/prereg/20261002-crash-rule-plateau.md).

S0 and the vt_mom reference are read from the registry; the six neighbours are scored one at a time with
score_model like --score, not registered. S3/S4 (the window) use the research-only subclass in
src/models/baitoey/_shock_window.py; with 4 h it is pol_abl_shock exactly.

    python -m research.baitoey.shock_plateau
"""
from __future__ import annotations

import copy
import json
import logging

import pandas as pd

from backtest.data import load_market
from backtest.scoring import explain
from backtest.scoring.registry import resolve
from backtest.scoring.score import dumps, score_model
from research.baitoey.vt_dual import registered_score, summarize
from research.baitoey.vt_plateau import pct
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models import get
from src.models.baitoey._shock_window import ShockWindow

NAME = "pol_abl_shock"
OUT = ROOT / "results" / "baitoey" / "20261002-crash-plateau"
MARGIN = 0.03
RUNS = {"S1": ("drop threshold 4%", {"shock_4h": 0.04}, False), "S2": ("drop threshold 6%", {"shock_4h": 0.06}, False),
        "S3": ("drop window 2 h", {"shock_hours": 2}, True), "S4": ("drop window 8 h", {"shock_hours": 8}, True),
        "S5": ("cash pause 12 h", {"cooldown_hours": 12}, False), "S6": ("cash pause 48 h", {"cooldown_hours": 48}, False)}
TYPES = ("strong fall", "mild fall", "mild rise", "strong rise")


def volatile_hit(score: dict, btc: pd.Series) -> float | None:
    pw = pd.DataFrame(score["per_window"])
    pw.index = pd.to_datetime(pw.pop("start"), utc=True)
    t = pw[pw.scored.astype(bool)]
    return explain.profile(t, explain.market_types(t.index, btc, t["regime"])).get("volatile", {}).get("hit")


def report(rows: dict[str, dict]) -> str:
    lines = ["# Robustness check of the crash rule pol_abl_shock (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261002-crash-rule-plateau.md`. One setting changed per run;",
             "neighbours scored like `--score`, not registered. Type columns: hit rate (mean of the three bars) by BTC's",
             "14-day move (<= -5% / -5..0% / 0..+5% / >= +5%) and in the most volatile windows.", "",
             "| Run | Change | HEADLINE_RET | vs S0 | without post-holdout | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Guard share | Fees | Hard gates |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    s0 = rows["S0"]["headline"]
    for x in rows.values():
        ty = " | ".join("—" if x["types"][k] is None else f"{100 * x['types'][k]:.0f}%" for k in TYPES)
        vol = "—" if x.get("volatile") is None else f"{100 * x['volatile']:.0f}%"
        rp = " · ".join(f"{pct(p['R'])} #{p['rank']}/{p['teams']}" for p in x["replay"]) or "—"
        lines.append(f"| {x['run']} | {x['change']} | **{x['headline']:.3f}** | {x['headline'] - s0:+.3f} | {x['in_sample']:.3f} | "
                     f"{ty} | {vol} | {pct(x['median_R'])} / {pct(x['mean_R'])} | {pct(x['worst_R'])} | {rp} | "
                     f"{100 * x['guard_share']:.0f}% | {pct(x['fees'], 2)} | {'pass' if x['eligible'] else 'FAIL'} |")
    bar, ref = s0 - MARGIN, rows["vt_mom"]["worst_R"]
    done = [r for r in RUNS if r in rows]
    lines.append("")
    if len(done) < len(RUNS):
        lines.append(f"Verdict: pending ({len(done)} of {len(RUNS)} neighbours scored).")
        return "\n".join(lines) + "\n"
    low = [r for r in RUNS if not rows[r]["eligible"] or rows[r]["headline"] < bar]
    weak = [r for r in RUNS if not rows[r]["worst_R"] > ref]
    name = lambda rs: ", ".join(f"{r} ({RUNS[r][0]})" for r in rs) or "none"
    lines += [f"- Score holds (hard gates and HEADLINE_RET >= {bar:.3f}): {'yes' if not low else 'NO'}; below: {name(low)}.",
              f"- Insurance holds (worst R above vt_mom's {pct(ref)}): {'yes' if not weak else 'NO'}; failing: {name(weak)}.",
              "", f"**Verdict: {'ROBUST' if not low and not weak else 'NOT ROBUST'}.**",
              f"Tool version(s): {', '.join(sorted({x['tool_version'] for x in rows.values()}))}."]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(OUT / "run.log"), logging.StreamHandler()])
    log = logging.getLogger("shock_plateau")
    cfg = load_config()
    btc = pd.read_parquet(resolve(cfg["harness"]["panel_dir"]) / "panel_close_1h.parquet", columns=["BTCUSDT"])["BTCUSDT"]
    rows = {}
    for label, model in (("S0", NAME), ("vt_mom", "baitoey_vt_mom")):
        s = registered_score(model)
        rows[label] = {**summarize(label, "none (base)" if label == "S0" else "reference", s, btc), "volatile": volatile_hit(s, btc)}
    market, shock, window = load_market(cfg), get(NAME), ShockWindow()
    for label, (change, params, use_window) in RUNS.items():
        model = window if use_window else shock
        c = copy.deepcopy(cfg)
        c["models"][model.spec.name] = {**copy.deepcopy(cfg["models"][NAME]), **params}
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
