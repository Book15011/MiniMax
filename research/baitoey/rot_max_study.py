"""Return-maximizing ROT_EW study (research/baitoey/prereg/20261001-return-max-rotation.md).

    python -m research.baitoey.rot_max_study screen    # score A-D, print SCREEN only, write choice.json
    python -m research.baitoey.rot_max_study confirm   # once, after choice.json: CONFIRM, REL, gates, compare

Scored with backtest.scoring.score.score_model like --score, but not registered on the leaderboard.
Output: results/baitoey/20261001-rot-max-study/.
"""
from __future__ import annotations

import argparse
import copy
import json
import logging
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from backtest.data import load_market
from backtest.scoring.competition import block_bootstrap
from backtest.scoring.score import score_model
from research.baitoey.vt_study import ROOT, per_window, period
from src.config import load_config
from src.models import get

NAME = "baitoey_rot_max"
VARIANTS = {"A": {"k": 6, "btc_gate": False}, "B": {"k": 4, "btc_gate": False},
            "C": {"k": 3, "btc_gate": False}, "D": {"k": 4, "btc_gate": True}}
REF = "team_rot_ew"
RULE = ["gate_pass", "median_R", "p75_R", "worst10_R"]
PRIMARY = "FLOORED.REL.cs"
OUT = ROOT / "results" / "baitoey" / "20261001-rot-max-study"
log = logging.getLogger("rot_max_study")


def run_one(v: str) -> str:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    cfg = load_config()
    vcfg = copy.deepcopy(cfg)
    vcfg["models"][NAME] = {**cfg["models"][NAME], **VARIANTS[v]}
    score, _ = score_model(get(NAME), load_market(cfg), vcfg, use_cache=True, log=logging.getLogger(v))
    (OUT / f"{v}.json").write_text(json.dumps(score))
    return v


def stats(d: pd.DataFrame) -> dict:
    return {"gate_pass": d.gate.mean(), "median_R": d.R.median(), "p75_R": d.R.quantile(0.75),
            "p90_R": d.R.quantile(0.9), "worst10_R": d.R.quantile(0.1), "turnover_day": d.turnover.mean() / 14,
            "fees_pct": d.fees_e0.mean(), "spread_pct": d.spread_e0.mean(), "min_active_days": int(d.active_days.min())}


def row(name: str, s: dict) -> str:
    return (f"| {name} | {s['gate_pass']:.0%} | {s['median_R']:+.2%} | {s['p75_R']:+.2%} | {s['p90_R']:+.2%} | "
            f"{s['worst10_R']:+.2%} | {s['turnover_day']:.2f} | {s['fees_pct']:.2%} + {s['spread_pct']:.2%} | "
            f"{s['min_active_days']} |")


HEAD = ("| Run | Return gate passed | Median R | 75th pct R | 90th pct R | Worst 10% R | Turnover/day | "
        "Fees + spread per window | Min active days |\n|---|---|---|---|---|---|---|---|---|")


def load(name: str) -> dict:
    return json.loads((OUT / f"{name}.json").read_text())


def screen() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "choice.json").exists():
        raise SystemExit("choice.json exists: the SCREEN choice is frozen")
    with ProcessPoolExecutor(max_workers=2) as ex:
        for v in ex.map(run_one, VARIANTS):
            log.info("finished %s", v)
    cfg = load_config()
    ref, _ = score_model(get(REF), load_market(cfg), cfg, use_cache=True, log=log)
    (OUT / f"{REF}.json").write_text(json.dumps(ref))
    st = {v: stats(period(per_window(load(v)), "SCREEN")) for v in VARIANTS}
    rows = pd.DataFrame(st).T
    rank = rows[RULE].rank(ascending=False).mean(axis=1)
    best = min(VARIANTS, key=lambda v: (rank[v], rows.loc[v, "turnover_day"]))
    (OUT / "choice.json").write_text(json.dumps({"preferred": best, "mean_rank": rank.to_dict()}, indent=1))
    lines = ["# Return-max rotation: SCREEN (2022-07 to 2024-06) only", "", HEAD,
             row(f"ref: {REF}", stats(period(per_window(ref), "SCREEN")))]
    lines += [row(f"{v} (k={VARIANTS[v]['k']}{', BTC gate' if VARIANTS[v]['btc_gate'] else ''})"
                  + (" **preferred**" if v == best else ""), st[v]) for v in VARIANTS]
    lines += ["", "Rule: lowest mean rank over return-gate pass share, median R, 75th pct R and worst-10% R "
              f"(ties: lower turnover). Mean ranks: {rank.round(2).to_dict()}"]
    text = "\n".join(lines)
    (OUT / "screen.md").write_text(text + "\n")
    print(text)
    return 0


def confirm() -> int:
    if not (OUT / "choice.json").exists():
        raise SystemExit("run the SCREEN phase first")
    if (OUT / "report.md").exists():
        raise SystemExit("report.md exists: CONFIRM was already opened once")
    best = json.loads((OUT / "choice.json").read_text())["preferred"]
    sc = load_config()["scoring"]
    ref = load(REF)
    rp = per_window(ref)
    L = ["# Return-max rotation: full results (CONFIRM opened once)", "",
         "| Run | Gate passed SCREEN / CONFIRM | Median R S / C | 75th pct R S / C | 90th pct R S / C | "
         "Worst 10% R S / C | REL | Gates G1-G6 | Fees + spread per window | vs team_rot_ew: REL diff [90%] |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    robust = []
    for v, s in [(f"ref: {REF}", ref)] + [(v + (" **preferred**" if v == best else ""), load(v)) for v in VARIANTS]:
        d = per_window(s)
        a, b = stats(period(d, "SCREEN")), stats(period(d, "CONFIRM"))
        gates = " ".join(f"{g[-1]}{'✓' if x['pass'] else '✗'}" for g, x in s["gates"].items())
        if v.startswith("ref"):
            vs = "—"
        else:
            diff = (d[PRIMARY] - rp[PRIMARY].reindex(d.index)).dropna()
            r = block_bootstrap(diff, d.w_live, d.w_rec, sc["headline"], int(sc["compare"]["block_windows"]),
                                int(sc["compare"]["reps"]), float(sc["compare"]["level"]), int(sc["compare"]["seed"]))
            vs = f"{r['diff']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}]"
        act = s["activity"]
        L.append(f"| {v} | {a['gate_pass']:.0%} / {b['gate_pass']:.0%} | {a['median_R']:+.2%} / {b['median_R']:+.2%} | "
                 f"{a['p75_R']:+.2%} / {b['p75_R']:+.2%} | {a['p90_R']:+.2%} / {b['p90_R']:+.2%} | "
                 f"{a['worst10_R']:+.2%} / {b['worst10_R']:+.2%} | {s['primary']['headline']:.3f} | {gates} | "
                 f"{act['mean_fees_e0']:.2%} + {act['mean_spread_e0']:.2%} | {vs} |")
        h = s["headline"]["FLOORED"]["REL"]
        robust.append(f"| {v} | {h['live_like']:.3f} | {h['recency']:.3f} | {s['layers']['ALL_flat']['mean_cs_primary']:.3f} |")
    L += ["", "Gate failures:"] + [f"- {v}: {g} {x['detail']}" for v in VARIANTS for g, x in load(v)["gates"].items()
                                   if not x["pass"]]
    L += ["", "Report-only robustness (REL FLOORED by layer):", "", "| Run | Live-like | Recency | Flat (all windows) |",
          "|---|---|---|---|"] + robust
    text = "\n".join(L)
    (OUT / "report.md").write_text(text + "\n")
    print(text)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phase", choices=["screen", "confirm"])
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    return screen() if a.phase == "screen" else confirm()


if __name__ == "__main__":
    raise SystemExit(main())
