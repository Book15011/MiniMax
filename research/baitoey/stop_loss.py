"""A per-coin stop-loss on e20v45? (research/baitoey/prereg/20261003-stop-loss.md).

E0 is read from the registry; C0, S5 and S10 are scored with score_model like --score, not registered. Runs can be
started separately (one label per process); the report is rebuilt from every score file present.

    python -m research.baitoey.stop_loss [C0 S5 S10]
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
from src.models.baitoey._stop_loss import StopLoss

NAME = "pol_switch_vt_tl_e20v45"
OUT = ROOT / "results" / "baitoey" / "20261003-stop-loss"
RUNS = {"C0": ("stop 100% (never fires)", 1.0), "S5": ("stop 5%", 0.05), "S10": ("stop 10%", 0.10)}
MARGIN, NOISE, WORST_GAIN, CS_GAIN, MOVED = 0.03, 0.01, 0.02, 0.02, 0.001


def row(label: str, change: str, score: dict, btc: pd.Series) -> dict:
    return {**summarize(label, change, score, btc), "volatile": volatile_hit(score, btc), "cs_hit": score["primary"]["cs_hit"],
            "R": score["per_window"]["R_liq"]}


def verdict(x: dict, e0: dict, c0: dict) -> str:
    if not x["eligible"] or x["headline"] < e0["headline"] - MARGIN:
        return "worse"
    if (x["headline"] >= e0["headline"] - NOISE and x["headline"] >= c0["headline"] - NOISE
            and (x["worst_R"] - e0["worst_R"] >= WORST_GAIN or x["cs_hit"] - e0["cs_hit"] >= CS_GAIN)):
        return "better"
    return "no clear difference"


def effect(x: dict, c0: dict) -> str:
    d = pd.Series(x["R"]) - pd.Series(c0["R"])
    moved = d.abs() > MOVED
    if not moved.any():
        return "never changed R"
    return (f"changed {100 * moved.mean():.0f}% of rounds (helped {100 * (d > MOVED).mean():.0f}%, hurt "
            f"{100 * (d < -MOVED).mean():.0f}%), mean change there {pct(d[moved].mean(), 2)}")


def report(rows: dict[str, dict]) -> str:
    lines = ["# A per-coin stop-loss on e20v45? (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261003-stop-loss.md`. Scored like `--score`, not registered.",
             "Type columns: hit rate (mean of the three bars) by BTC's 14-day move (<= -5% / -5..0% / 0..+5% / >= +5%)",
             "and in the most volatile windows.", "",
             "| Run | Change | HEADLINE_RET | vs E0 | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Fees | Hard gates | Verdict |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    e0 = rows["E0"]
    for key, x in rows.items():
        ty = " | ".join("—" if x["types"][k] is None else f"{100 * x['types'][k]:.0f}%" for k in TYPES)
        vol = "—" if x.get("volatile") is None else f"{100 * x['volatile']:.0f}%"
        rp = " · ".join(f"{pct(p['R'])} #{p['rank']}/{p['teams']}" for p in x["replay"]) or "—"
        lines.append(f"| {key} | {x['change']} | **{x['headline']:.3f}** | {x['headline'] - e0['headline']:+.3f} | "
                     f"{x['in_sample']:.3f} | {x['cs_hit']:.3f} | {ty} | {vol} | {pct(x['median_R'])} / {pct(x['mean_R'])} | "
                     f"{pct(x['worst_R'])} | {rp} | {pct(x['fees'], 2)} | {'pass' if x['eligible'] else 'FAIL'} | "
                     f"{x.get('verdict', '—')} |")
    lines.append("")
    if "C0" in rows:
        for key in ("S5", "S10"):
            if key in rows:
                lines.append(f"- {key} against C0: {effect(rows[key], rows['C0'])}.")
    done = [k for k in ("S5", "S10") if "verdict" in rows.get(k, {})]
    if len(done) < 2:
        lines.append(f"- Verdict: pending ({len([k for k in RUNS if k in rows])} of {len(RUNS)} runs scored).")
    else:
        ok = all(rows[k]["verdict"] == "better" for k in done)
        lines.append("- " + ", ".join(f"{k} {rows[k]['verdict']}" for k in done) + f" -> **{'PROPOSE' if ok else 'DO NOT PROPOSE'}**.")
    lines += ["", f"Tool version(s): {', '.join(sorted({x['tool_version'] for x in rows.values()}))}."]
    return "\n".join(lines) + "\n"


def rebuild(btc: pd.Series) -> None:
    rows = {"E0": row("E0", "none (base)", registered_score(NAME), btc)}
    for key, (change, _) in RUNS.items():
        f = OUT / f"{key}-score.json"
        if f.exists():
            rows[key] = row(key, change, json.loads(f.read_text()), btc)
    for key in ("S5", "S10"):
        if key in rows and "C0" in rows:
            rows[key]["verdict"] = verdict(rows[key], rows["E0"], rows["C0"])
    (OUT / "report.md").write_text(report(rows))
    (OUT / "rows.json").write_text(json.dumps({k: {a: b for a, b in v.items() if a != "R"} for k, v in rows.items()},
                                              indent=1, default=str))


def main(labels: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tag = "-".join(labels) or "all"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(OUT / f"run-{tag}.log"), logging.StreamHandler()])
    log = logging.getLogger("stop_loss")
    cfg = load_config()
    btc = pd.read_parquet(resolve(cfg["harness"]["panel_dir"]) / "panel_close_1h.parquet", columns=["BTCUSDT"])["BTCUSDT"]
    market, model = load_market(cfg), StopLoss()
    for label in labels or list(RUNS):
        change, stop = RUNS[label]
        c = copy.deepcopy(cfg)
        c["models"][model.spec.name] = {"vt": copy.deepcopy(cfg["models"][NAME]), "stop": stop}
        log.info("%s (%s): scoring", label, change)
        score, _ = score_model(model, market, c, use_cache=True, log=log)
        (OUT / f"{label}-score.json").write_text(dumps(score))
        log.info("%s: HEADLINE_RET %.4f", label, score["primary"]["headline"])
        rebuild(btc)
    rebuild(btc)
    log.info("done: %s", OUT / "report.md")


if __name__ == "__main__":
    main(sys.argv[1:])
