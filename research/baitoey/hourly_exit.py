"""The volume exit checked every hour, and a 5% cut-and-rebuy, on a 5% band
(research/baitoey/prereg/20261003-hourly-exit.md).

E0 and V0 are read from the registry; the other runs are scored with score_model like --score, not registered. Runs
can be started separately (one label per process); the report is rebuilt from every score file present.

    python -m research.baitoey.hourly_exit [EC EX ES5 VC VX]
"""
from __future__ import annotations

import copy
import json
import logging
import sys
from dataclasses import replace

import pandas as pd

from backtest.data import load_market
from backtest.scoring.registry import resolve
from backtest.scoring.score import dumps, score_model
from research.baitoey.shock_plateau import TYPES, volatile_hit
from research.baitoey.vt_dual import registered_score, summarize
from research.baitoey.vt_plateau import pct
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models.baitoey._hourly_exit import HourlyExit, HourlyExitVt
from src.models.baitoey._stop_loss import StopLoss

E20, VT = "pol_switch_vt_tl_e20v45", "baitoey_vt_mom"
OUT = ROOT / "results" / "baitoey" / "20261003-hourly-exit"
MARGIN, NOISE, WORST_GAIN, CS_GAIN, MOVED = 0.03, 0.01, 0.02, 0.02, 0.001


class StopLossBand5(StopLoss):
    spec = replace(StopLoss.spec, name="baitoey_stop_e20v45_b5", band=0.05)


def runs(cfg: dict) -> dict:
    e20, vt = cfg["models"][E20], cfg["models"][VT]
    return {"EC": ("hourly wrapper, no rule", HourlyExit(), {"vt": e20, "exit": vt, "hourly_exit": False}, "E0", None),
            "EX": ("volume exit every hour", HourlyExit(), {"vt": e20, "exit": vt, "hourly_exit": True}, "E0", "EC"),
            "ES5": ("cut at -5%, rebuy at 16:00", StopLossBand5(), {"vt": e20, "stop": 0.05}, "E0", "EC"),
            "VC": ("hourly wrapper, no rule", HourlyExitVt(), {"vt": vt, "exit": vt, "hourly_exit": False}, "V0", None),
            "VX": ("volume exit every hour", HourlyExitVt(), {"vt": vt, "exit": vt, "hourly_exit": True}, "V0", "VC")}


def row(label: str, change: str, score: dict, btc: pd.Series) -> dict:
    return {**summarize(label, change, score, btc), "volatile": volatile_hit(score, btc), "cs_hit": score["primary"]["cs_hit"],
            "R": score["per_window"]["R_liq"]}


def verdict(x: dict, b: dict, c: dict) -> str:
    if not x["eligible"] or x["headline"] < b["headline"] - MARGIN:
        return "worse"
    if (x["headline"] >= b["headline"] - NOISE and x["headline"] >= c["headline"] - NOISE
            and (x["worst_R"] - b["worst_R"] >= WORST_GAIN or x["cs_hit"] - b["cs_hit"] >= CS_GAIN
                 or x["headline"] >= b["headline"] + MARGIN)):
        return "better"
    return "no clear difference"


def effect(x: dict, c: dict) -> str:
    d = pd.Series(x["R"]) - pd.Series(c["R"])
    moved = d.abs() > MOVED
    if not moved.any():
        return "never changed R"
    return (f"changed {100 * moved.mean():.0f}% of rounds (helped {100 * (d > MOVED).mean():.0f}%, hurt "
            f"{100 * (d < -MOVED).mean():.0f}%), mean change there {pct(d[moved].mean(), 2)}")


def report(rows: dict[str, dict], spec: dict) -> str:
    lines = ["# Volume exit every hour, and a 5% cut-and-rebuy, on a 5% band (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261003-hourly-exit.md`. Scored like `--score`, not registered.",
             "Type columns: hit rate (mean of the three bars) by BTC's 14-day move (<= -5% / -5..0% / 0..+5% / >= +5%)",
             "and in the most volatile windows.", "",
             "| Run | Change | HEADLINE_RET | vs base | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Fees | Hard gates | Verdict |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key in ("E0", "EC", "EX", "ES5", "V0", "VC", "VX"):
        if key not in rows:
            continue
        x = rows[key]
        base = rows["E0" if key.startswith("E") else "V0"]
        ty = " | ".join("—" if x["types"][k] is None else f"{100 * x['types'][k]:.0f}%" for k in TYPES)
        vol = "—" if x.get("volatile") is None else f"{100 * x['volatile']:.0f}%"
        rp = " · ".join(f"{pct(p['R'])} #{p['rank']}/{p['teams']}" for p in x["replay"]) or "—"
        lines.append(f"| {key} | {x['change']} | **{x['headline']:.3f}** | {x['headline'] - base['headline']:+.3f} | "
                     f"{x['in_sample']:.3f} | {x['cs_hit']:.3f} | {ty} | {vol} | {pct(x['median_R'])} / {pct(x['mean_R'])} | "
                     f"{pct(x['worst_R'])} | {rp} | {pct(x['fees'], 2)} | {'pass' if x['eligible'] else 'FAIL'} | "
                     f"{x.get('verdict', '—')} |")
    lines.append("")
    if "EC" in rows:
        gap = rows["EC"]["headline"] - rows["E0"]["headline"]
        lines.append(f"- Control on the 5% band vs the daily model: {gap:+.3f} ({'within' if abs(gap) <= NOISE else 'outside'} 0.01).")
    for key, (_, _, _, _, ctl) in spec.items():
        if ctl and key in rows and ctl in rows:
            lines.append(f"- {key} against {ctl}: {effect(rows[key], rows[ctl])}.")
    v = {k: rows[k].get("verdict") for k in ("EX", "VX", "ES5") if k in rows}
    if "EX" in v and "VX" in v and v["EX"] and v["VX"]:
        ok = v["EX"] == "better" and v["VX"] != "worse"
        lines.append(f"- Hourly volume exit: EX {v['EX']}, VX {v['VX']} -> **{'PROPOSE' if ok else 'DO NOT PROPOSE'}**.")
    if v.get("ES5"):
        lines.append(f"- 5% cut-and-rebuy: ES5 {v['ES5']} -> **{'PROPOSE' if v['ES5'] == 'better' else 'DO NOT PROPOSE'}**.")
    if len([k for k in spec if k in rows]) < len(spec):
        lines.append(f"- Pending: {len([k for k in spec if k in rows])} of {len(spec)} runs scored.")
    lines += ["", f"Tool version(s): {', '.join(sorted({x['tool_version'] for x in rows.values()}))}."]
    return "\n".join(lines) + "\n"


def rebuild(cfg: dict, btc: pd.Series) -> None:
    spec = runs(cfg)
    rows = {"E0": row("E0", "none (daily, base)", registered_score(E20), btc),
            "V0": row("V0", "none (daily, base)", registered_score(VT), btc)}
    for key, (change, *_rest) in spec.items():
        f = OUT / f"{key}-score.json"
        if f.exists():
            rows[key] = row(key, change, json.loads(f.read_text()), btc)
    for key, (_, _, _, base, ctl) in spec.items():
        if ctl and key in rows and ctl in rows:
            rows[key]["verdict"] = verdict(rows[key], rows[base], rows[ctl])
    (OUT / "report.md").write_text(report(rows, spec))
    (OUT / "rows.json").write_text(json.dumps({k: {a: b for a, b in v.items() if a != "R"} for k, v in rows.items()},
                                              indent=1, default=str))


def main(labels: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tag = "-".join(labels) or "all"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(OUT / f"run-{tag}.log"), logging.StreamHandler()])
    log = logging.getLogger("hourly_exit")
    cfg = load_config()
    btc = pd.read_parquet(resolve(cfg["harness"]["panel_dir"]) / "panel_close_1h.parquet", columns=["BTCUSDT"])["BTCUSDT"]
    market, spec = load_market(cfg), runs(cfg)
    for label in labels or list(spec):
        change, model, params, _, _ = spec[label]
        c = copy.deepcopy(cfg)
        c["models"][model.spec.name] = copy.deepcopy(params)
        log.info("%s (%s, %s): scoring", label, model.spec.name, change)
        score, _ = score_model(model, market, c, use_cache=True, log=log)
        (OUT / f"{label}-score.json").write_text(dumps(score))
        log.info("%s: HEADLINE_RET %.4f", label, score["primary"]["headline"])
        rebuild(cfg, btc)
    rebuild(cfg, btc)
    log.info("done: %s", OUT / "report.md")


if __name__ == "__main__":
    main(sys.argv[1:])
