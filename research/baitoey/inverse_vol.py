"""Inverse-volatility weights instead of equal weights? (research/baitoey/prereg/20261003-inverse-vol.md).

V0 and E0 are read from the registry; VIV and EIV are scored with score_model like --score, not registered.

    python -m research.baitoey.inverse_vol
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

OUT = ROOT / "results" / "baitoey" / "20261003-inverse-vol"
MARGIN, NOISE, WORST_GAIN, CS_GAIN = 0.03, 0.01, 0.02, 0.02


def vt_iv(p: dict) -> dict:
    return {**p, "weighting": "inverse_vol"}


def e20_iv(p: dict) -> dict:
    q = copy.deepcopy(p)
    s = q["sleeves"]["baitoey_vt_mom"]
    s["override"] = {**(s.get("override") or {}), "weighting": "inverse_vol"}
    return q


RUNS = {"VIV": ("V0", "baitoey_vt_mom", vt_iv), "EIV": ("E0", "pol_switch_vt_tl_e20v45", e20_iv)}


def row(label: str, change: str, score: dict, btc: pd.Series) -> dict:
    return {**summarize(label, change, score, btc), "volatile": volatile_hit(score, btc), "cs_hit": score["primary"]["cs_hit"]}


def verdict(x: dict, base: dict) -> str:
    if not x["eligible"] or x["headline"] < base["headline"] - MARGIN:
        return "worse"
    if x["headline"] >= base["headline"] - NOISE and (x["worst_R"] - base["worst_R"] >= WORST_GAIN
                                                      or x["cs_hit"] - base["cs_hit"] >= CS_GAIN):
        return "better"
    return "no clear difference"


def report(rows: dict[str, dict]) -> str:
    lines = ["# Inverse-volatility weights instead of equal weights? (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261003-inverse-vol.md`. Scored like `--score`, not registered.",
             "Type columns: hit rate (mean of the three bars) by BTC's 14-day move (<= -5% / -5..0% / 0..+5% / >= +5%)",
             "and in the most volatile windows.", "",
             "| Run | Weights | HEADLINE_RET | vs base | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Fees | Mean invested | Hard gates | Verdict |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, x in rows.items():
        base = rows[key[0] + "0"]
        ty = " | ".join("—" if x["types"][k] is None else f"{100 * x['types'][k]:.0f}%" for k in TYPES)
        vol = "—" if x.get("volatile") is None else f"{100 * x['volatile']:.0f}%"
        rp = " · ".join(f"{pct(p['R'])} #{p['rank']}/{p['teams']}" for p in x["replay"]) or "—"
        lines.append(f"| {key} | {x['change']} | **{x['headline']:.3f}** | {x['headline'] - base['headline']:+.3f} | "
                     f"{x['in_sample']:.3f} | {x['cs_hit']:.3f} | {ty} | {vol} | {pct(x['median_R'])} / {pct(x['mean_R'])} | "
                     f"{pct(x['worst_R'])} | {rp} | {pct(x['fees'], 2)} | {100 * x['mean_gross']:.0f}% | "
                     f"{'pass' if x['eligible'] else 'FAIL'} | {x.get('verdict', 'base')} |")
    lines.append("")
    if all(k in rows for k in RUNS):
        ok = rows["EIV"]["verdict"] == "better" and rows["VIV"]["verdict"] != "worse"
        lines.append(f"- VIV {rows['VIV']['verdict']}, EIV {rows['EIV']['verdict']} -> **{'PROPOSE' if ok else 'DO NOT PROPOSE'}**.")
    else:
        lines.append(f"- Verdict: pending ({len([k for k in RUNS if k in rows])} of {len(RUNS)} runs scored).")
    lines += ["", f"Tool version(s): {', '.join(sorted({x['tool_version'] for x in rows.values()}))}."]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(OUT / "run.log"), logging.StreamHandler()])
    log = logging.getLogger("inverse_vol")
    cfg = load_config()
    btc = pd.read_parquet(resolve(cfg["harness"]["panel_dir"]) / "panel_close_1h.parquet", columns=["BTCUSDT"])["BTCUSDT"]
    rows = {"V0": row("V0", "equal (base)", registered_score("baitoey_vt_mom"), btc),
            "E0": row("E0", "equal (base)", registered_score("pol_switch_vt_tl_e20v45"), btc)}
    market = load_market(cfg)
    for key, (base, name, edit) in RUNS.items():
        c = copy.deepcopy(cfg)
        c["models"][name] = edit(copy.deepcopy(cfg["models"][name]))
        log.info("%s (%s, inverse_vol): scoring", key, name)
        score, _ = score_model(get(name), market, c, use_cache=True, log=log)
        (OUT / f"{key}-score.json").write_text(dumps(score))
        rows[key] = {**row(key, "inverse vol", score, btc)}
        rows[key]["verdict"] = verdict(rows[key], rows[base])
        (OUT / "report.md").write_text(report(rows))
        log.info("%s: HEADLINE_RET %.4f (%s)", key, rows[key]["headline"], rows[key]["verdict"])
    (OUT / "rows.json").write_text(json.dumps(rows, indent=1, default=str))
    log.info("done: %s", OUT / "report.md")


if __name__ == "__main__":
    main()
