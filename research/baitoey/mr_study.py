"""Mean-reversion study (research/baitoey/prereg/20261001-mean-reversion.md).

    python -m research.baitoey.mr_study screen    # score the runs, print SCREEN only, write choice.json
    python -m research.baitoey.mr_study confirm   # once, after choice.json: CONFIRM, REL, gates, compare

Scored with backtest.scoring.score.score_model like --score, but not registered on the leaderboard.
Output: results/baitoey/20261001-mr-study/.
"""
from __future__ import annotations

import argparse
import copy
import dataclasses
import json
import logging
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from backtest.data import load_market
from backtest.scoring.competition import block_bootstrap
from backtest.scoring.score import score_model
from research.baitoey.rot_max_study import HEAD, row, stats
from research.baitoey.vt_study import ROOT, per_window, period
from src.config import load_config
from src.models import get

RUNS = {"MR_4h": ("MR", 4, "baitoey_mr_bbrsi", {"bar_hours": 4}),
        "MR_24h": ("MR", 24, "baitoey_mr_bbrsi", {"bar_hours": 24}),
        "DIP_4h": ("DIP", 4, "baitoey_rot_dip", {"bar_hours": 4, "dip_filter": True}),
        "DIP_24h": ("DIP", 24, "baitoey_rot_dip", {"bar_hours": 24, "dip_filter": True}),
        "CORE_4h": ("CORE", 4, "baitoey_rot_dip", {"bar_hours": 4, "dip_filter": False})}
CHOOSE = ("MR", "DIP")
REF = "team_rot_ew"
RULE = ["gate_pass", "median_R", "p75_R", "worst10_R"]
PRIMARY = "FLOORED.REL.cs"
OUT = ROOT / "results" / "baitoey" / "20261001-mr-study"
log = logging.getLogger("mr_study")


def run_one(run: str) -> str:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    _, h, name, over = RUNS[run]
    cfg = load_config()
    base = get(name)
    model = copy.copy(base)
    model.spec = dataclasses.replace(base.spec, rebalance_hours=h)
    model.spec.validate()
    vcfg = copy.deepcopy(cfg)
    # the scoring cache keys on parameters, not on the spec, so the interval rides in the parameters too
    vcfg["models"][name] = {**cfg["models"][name], **over, "_rebalance_hours": h}
    score, _ = score_model(model, load_market(cfg), vcfg, use_cache=True, log=logging.getLogger(run))
    (OUT / f"{run}.json").write_text(json.dumps(score))
    return run


def load(name: str) -> dict:
    return json.loads((OUT / f"{name}.json").read_text())


def screen() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "choice.json").exists():
        raise SystemExit("choice.json exists: the SCREEN choice is frozen")
    with ProcessPoolExecutor(max_workers=3) as ex:
        for r in ex.map(run_one, sorted(RUNS, key=lambda r: RUNS[r][1])):
            log.info("finished %s", r)
    cfg = load_config()
    ref, _ = score_model(get(REF), load_market(cfg), cfg, use_cache=True, log=log)
    (OUT / f"{REF}.json").write_text(json.dumps(ref))
    st = {r: stats(period(per_window(load(r)), "SCREEN")) for r in RUNS}
    choice = {}
    for fam in CHOOSE:
        runs = [r for r in RUNS if RUNS[r][0] == fam]
        rows = pd.DataFrame({r: st[r] for r in runs}).T
        rank = rows[RULE].rank(ascending=False).mean(axis=1)
        best = min(runs, key=lambda r: (rank[r], rows.loc[r, "turnover_day"]))
        choice[fam] = {"run": best, "mean_rank": rank.to_dict()}
    (OUT / "choice.json").write_text(json.dumps(choice, indent=1))
    chosen = {c["run"] for c in choice.values()}
    lines = ["# Mean-reversion study: SCREEN (2022-07 to 2024-06) only", "", HEAD,
             row(f"ref: {REF} (core @24h)", stats(period(per_window(ref), "SCREEN")))]
    lines += [row(r + (" **chosen**" if r in chosen else ""), st[r]) for r in RUNS]
    lines += ["", "Rule: per family, lowest mean rank over return-gate pass share, median R, 75th pct R and worst-10% R "
              "(ties: lower turnover). " + "; ".join(f"{f}: {c['mean_rank']}" for f, c in choice.items())]
    text = "\n".join(lines)
    (OUT / "screen.md").write_text(text + "\n")
    print(text)
    return 0


def confirm() -> int:
    if not (OUT / "choice.json").exists():
        raise SystemExit("run the SCREEN phase first")
    if (OUT / "report.md").exists():
        raise SystemExit("report.md exists: CONFIRM was already opened once")
    chosen = {c["run"] for c in json.loads((OUT / "choice.json").read_text()).values()}
    sc = load_config()["scoring"]
    ref = load(REF)
    rp = per_window(ref)
    L = ["# Mean-reversion study: full results (CONFIRM opened once)", "",
         "| Run | Gate passed S / C | Median R S / C | 75th pct R S / C | 90th pct R S / C | Worst 10% R S / C | REL | "
         "Gates G1-G6 | Turnover/day | Fees + spread per window | Max orders/decision | vs team_rot_ew: REL diff [90%] |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, s in [(f"ref: {REF}", ref)] + [(r + (" **chosen**" if r in chosen else ""), load(r)) for r in RUNS]:
        d = per_window(s)
        a, b = stats(period(d, "SCREEN")), stats(period(d, "CONFIRM"))
        gates = " ".join(f"{g[-1]}{'✓' if x['pass'] else '✗'}" for g, x in s["gates"].items())
        if name.startswith("ref"):
            vs = "—"
        else:
            diff = (d[PRIMARY] - rp[PRIMARY].reindex(d.index)).dropna()
            r = block_bootstrap(diff, d.w_live, d.w_rec, sc["headline"], int(sc["compare"]["block_windows"]),
                                int(sc["compare"]["reps"]), float(sc["compare"]["level"]), int(sc["compare"]["seed"]))
            vs = f"{r['diff']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}]"
        act = s["activity"]
        L.append(f"| {name} | {a['gate_pass']:.0%} / {b['gate_pass']:.0%} | {a['median_R']:+.2%} / {b['median_R']:+.2%} | "
                 f"{a['p75_R']:+.2%} / {b['p75_R']:+.2%} | {a['p90_R']:+.2%} / {b['p90_R']:+.2%} | "
                 f"{a['worst10_R']:+.2%} / {b['worst10_R']:+.2%} | {s['primary']['headline']:.3f} | {gates} | "
                 f"{act['mean_turnover'] / 14:.2f} | {act['mean_fees_e0']:.2%} + {act['mean_spread_e0']:.2%} | "
                 f"{act['max_calls_one_decision']} | {vs} |")
    L += ["", "Gate failures:"] + [f"- {r}: {g} {x['detail']}" for r in RUNS for g, x in load(r)["gates"].items()
                                   if not x["pass"]]
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
