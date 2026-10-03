"""Switch read from altcoins or the momentum basket instead of BTC (research/baitoey/prereg/20261004-alt-switch.md).

E0 is read from the registry; the other runs are scored with score_model like --score, not registered. Runs can be
started separately (one label per process); the report is rebuilt from every score file present.

    python -m research.baitoey.alt_switch [A15 A20 A25 M15 M20 M25 AB]
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
from src.models.baitoey._alt_switch import AltSwitch

NAME = "pol_switch_vt_tl_e20v45"
OUT = ROOT / "results" / "baitoey" / "20261004-alt-switch"
RUNS = {"A15": ("alts", 15), "A20": ("alts", 20), "A25": ("alts", 25),
        "M15": ("momentum", 15), "M20": ("momentum", 20), "M25": ("momentum", 25), "AB": ("both", 20)}
MARGIN, NOISE, WORST_GAIN, CS_GAIN = 0.03, 0.01, 0.02, 0.02


def row(label: str, change: str, score: dict, btc: pd.Series) -> dict:
    return {**summarize(label, change, score, btc), "volatile": volatile_hit(score, btc), "cs_hit": score["primary"]["cs_hit"]}


def better(x: dict, e0: dict) -> bool:
    return x["eligible"] and (x["headline"] >= e0["headline"] + MARGIN or (
        x["headline"] >= e0["headline"] - NOISE and (x["worst_R"] - e0["worst_R"] >= WORST_GAIN or x["cs_hit"] - e0["cs_hit"] >= CS_GAIN)))


def holds(x: dict, e0: dict) -> bool:
    return x["eligible"] and x["headline"] >= e0["headline"] - MARGIN


def report(rows: dict[str, dict]) -> str:
    lines = ["# e20v45 switch read from altcoins or the momentum basket (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261004-alt-switch.md`. Scored like `--score`, not registered. Type",
             "columns: hit rate (mean of the three bars) by BTC's 14-day move (<= -5% / -5..0% / 0..+5% / >= +5%) and in the",
             "most volatile windows.", "",
             "| Run | Switch | HEADLINE_RET | vs E0 | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Fees | Hard gates |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    e0 = rows["E0"]
    for key in ["E0"] + list(RUNS):
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
    for fam, p in (("altcoin index", "A"), ("momentum basket", "M")):
        ks = [f"{p}15", f"{p}20", f"{p}25"]
        if not all(k in rows for k in ks):
            lines.append(f"- {fam}: pending ({sum(k in rows for k in ks)} of 3 scored).")
            continue
        b, h = better(rows[f"{p}20"], e0), [holds(rows[k], e0) for k in (f"{p}15", f"{p}25")]
        lines.append(f"- {fam}: {p}20 {'better' if b else 'not better'} than E0; neighbours "
                     f"{'hold' if all(h) else 'do not hold'} -> **{'PROPOSE' if b and all(h) else 'KEEP THE BTC SWITCH'}**.")
    lines += ["", f"Tool version(s): {', '.join(sorted({x['tool_version'] for x in rows.values()}))}."]
    return "\n".join(lines) + "\n"


def rebuild(btc: pd.Series) -> None:
    rows = {"E0": row("E0", "BTC (base)", registered_score(NAME), btc)}
    for key, (market, ema) in RUNS.items():
        f = OUT / f"{key}-score.json"
        if f.exists():
            rows[key] = row(key, f"{market}, EMA {ema} d", json.loads(f.read_text()), btc)
    (OUT / "report.md").write_text(report(rows))
    (OUT / "rows.json").write_text(json.dumps(rows, indent=1, default=str))


def main(labels: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tag = "-".join(labels) or "all"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(OUT / f"run-{tag}.log"), logging.StreamHandler()])
    log = logging.getLogger("alt_switch")
    cfg = load_config()
    btc = pd.read_parquet(resolve(cfg["harness"]["panel_dir"]) / "panel_close_1h.parquet", columns=["BTCUSDT"])["BTCUSDT"]
    market, model = load_market(cfg), AltSwitch()
    for label in labels or list(RUNS):
        mk, ema = RUNS[label]
        params = copy.deepcopy(cfg["models"][NAME])
        params["market"] = mk
        params["switch"] = {**params["switch"], "ema_days": ema}
        c = copy.deepcopy(cfg)
        c["models"][model.spec.name] = params
        log.info("%s (switch from %s, EMA %d days): scoring", label, mk, ema)
        score, _ = score_model(model, market, c, use_cache=True, log=log)
        (OUT / f"{label}-score.json").write_text(dumps(score))
        log.info("%s: HEADLINE_RET %.4f", label, score["primary"]["headline"])
        rebuild(btc)
    rebuild(btc)
    log.info("done: %s", OUT / "report.md")


if __name__ == "__main__":
    main(sys.argv[1:])
