"""Volume-confirmed timing study (research/baitoey/prereg/20261001-volume-timing.md).

    python -m research.baitoey.vt_study screen    # score the 12 runs, print SCREEN only, write choice.json
    python -m research.baitoey.vt_study confirm   # once, after choice.json: CONFIRM, REL, gates, compare

Runs are scored with backtest.scoring.score.score_model (the same engine, windows, field and gates as --score) but
are not registered on the team leaderboard. Output: results/baitoey/20261001-vt-study/.
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
from src.config import REPO_ROOT, load_config
from src.models import get

FAMILIES = {"A": ("baitoey_breakout", {}),
            "B0": ("baitoey_vt_mom", {"early_exit": False, "no_chase": False}),
            "B": ("baitoey_vt_mom", {"early_exit": True, "no_chase": False}),
            "C": ("baitoey_vt_mom", {"early_exit": True, "no_chase": True})}
HOURS = (1, 4, 24)
REF = "team_rot_ew"
PERIODS = {"SCREEN": ("2022-07-01 16:00", "2024-06-30 16:00"), "CONFIRM": ("2024-07-01 16:00", None)}
RULE = ["median_R", "worst10_R", "share_pos", "median_V1"]
PRIMARY = "FLOORED.REL.cs"
ROOT = REPO_ROOT.parent.parent if REPO_ROOT.parent.name == ".worktrees" else REPO_ROOT
OUT = ROOT / "results" / "baitoey" / "20261001-vt-study"
log = logging.getLogger("vt_study")


def label(fam: str, h: int) -> str:
    return f"{fam} @{h}h"


def variant(fam: str, h: int, cfg: dict):
    name, over = FAMILIES[fam]
    base = get(name)
    model = copy.copy(base)
    model.spec = dataclasses.replace(base.spec, rebalance_hours=h)
    model.spec.validate()
    cfg = copy.deepcopy(cfg)
    # the scoring cache keys on parameters, not on the spec, so the interval rides in the parameters too
    cfg["models"][name] = {**cfg["models"][name], **over, "_rebalance_hours": h}
    return model, cfg


def run_one(job: tuple[str, int]) -> str:
    fam, h = job
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    cfg = load_config()
    market = load_market(cfg)
    model, vcfg = variant(fam, h, cfg)
    score, _ = score_model(model, market, vcfg, use_cache=True, log=logging.getLogger(label(fam, h)))
    (OUT / f"{fam}_{h}h.json").write_text(json.dumps(score))
    return label(fam, h)


def per_window(score: dict) -> pd.DataFrame:
    d = pd.DataFrame(score["per_window"])
    d.index = pd.to_datetime(d["start"], utc=True)
    return d[d["scored"]]


def period(d: pd.DataFrame, name: str) -> pd.DataFrame:
    a, b = PERIODS[name]
    m = d.index >= pd.Timestamp(a, tz="UTC")
    if b:
        m &= d.index <= pd.Timestamp(b, tz="UTC")
    return d[m]


def stats(d: pd.DataFrame) -> dict:
    return {"median_R": d.R.median(), "worst10_R": d.R.quantile(0.1), "share_pos": (d.R > 0).mean(),
            "median_V1": d["FLOORED.V1.composite"].median(), "turnover_day": d.turnover.mean() / 14,
            "fees_pct": d.fees_e0.mean(), "spread_pct": d.spread_e0.mean(),
            "max_orders_decision": int(d.max_calls_decision.max()), "min_active_days": int(d.active_days.min())}


def fmt_row(name: str, s: dict) -> str:
    return (f"| {name} | {s['median_R']:+.2%} | {s['worst10_R']:+.2%} | {s['share_pos']:.0%} | {s['median_V1']:+.3f} | "
            f"{s['turnover_day']:.2f} | {s['fees_pct']:.2%} + {s['spread_pct']:.2%} | {s['max_orders_decision']} | "
            f"{s['min_active_days']} |")


HEAD = ("| Run | Median R | Worst 10% R | R > 0 | Median V1 | Turnover/day | Fees + spread per window | "
        "Max orders/decision | Min active days |\n|---|---|---|---|---|---|---|---|---|")


def load(name: str) -> dict:
    return json.loads((OUT / f"{name}.json").read_text())


def screen() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "choice.json").exists():
        raise SystemExit("choice.json exists: the SCREEN choice is frozen")
    jobs = sorted(((f, h) for f in FAMILIES for h in HOURS), key=lambda j: j[1])
    with ProcessPoolExecutor(max_workers=4) as ex:
        for done in ex.map(run_one, jobs):
            log.info("finished %s", done)
    cfg = load_config()
    ref, _ = score_model(get(REF), load_market(cfg), cfg, use_cache=True, log=log)
    (OUT / f"{REF}.json").write_text(json.dumps(ref))

    st = {(f, h): stats(period(per_window(load(f"{f}_{h}h")), "SCREEN")) for f in FAMILIES for h in HOURS}
    choice = {}
    for f in FAMILIES:
        rows = pd.DataFrame({h: st[(f, h)] for h in HOURS}).T
        rank = rows[RULE].rank(ascending=False).mean(axis=1)
        best = min(HOURS, key=lambda h: (rank[h], rows.loc[h, "turnover_day"]))
        choice[f] = {"hours": int(best), "mean_rank": {str(h): float(rank[h]) for h in HOURS}}
    (OUT / "choice.json").write_text(json.dumps(choice, indent=1))
    lines = ["# Volume timing study: SCREEN (2022-07 to 2024-06) only", "", HEAD,
             fmt_row(f"ref: {REF}", stats(period(per_window(ref), "SCREEN")))]
    lines += [fmt_row(label(f, h) + (" **chosen**" if choice[f]["hours"] == h else ""), st[(f, h)])
              for f in FAMILIES for h in HOURS]
    lines += ["", "Rule: per variant, lowest mean rank over median R, worst-10% R, R > 0 and median V1 (ties: lower "
              "turnover). Mean ranks: " + "; ".join(f"{f} {c['mean_rank']}" for f, c in choice.items())]
    text = "\n".join(lines)
    (OUT / "screen.md").write_text(text + "\n")
    print(text)
    return 0


def confirm() -> int:
    if not (OUT / "choice.json").exists():
        raise SystemExit("run the SCREEN phase first")
    if (OUT / "report.md").exists():
        raise SystemExit("report.md exists: CONFIRM was already opened once")
    choice = json.loads((OUT / "choice.json").read_text())
    cmp = load_config()["scoring"]
    ref = load(REF)
    rp = per_window(ref)
    L = ["# Volume timing study: full results (CONFIRM opened once)", "",
         "| Run | Median R SCREEN / CONFIRM | Worst 10% R SCREEN / CONFIRM | REL | Gates G1-G6 | Turnover/day | "
         "Fees + spread per window | Max orders/decision | vs team_rot_ew: REL diff [90%] |",
         "|---|---|---|---|---|---|---|---|---|"]
    robust = []
    names = [(f"ref: {REF}", ref)] + [(label(f, h) + (" **chosen**" if choice[f]["hours"] == h else ""),
                                      load(f"{f}_{h}h")) for f in FAMILIES for h in HOURS]
    for name, s in names:
        d = per_window(s)
        sc, cf, a = stats(period(d, "SCREEN")), stats(period(d, "CONFIRM")), s["activity"]
        gates = " ".join(f"{g[-1]}{'✓' if v['pass'] else '✗'}" for g, v in s["gates"].items())
        if name.startswith("ref"):
            vs = "—"
        else:
            diff = (d[PRIMARY] - rp[PRIMARY].reindex(d.index)).dropna()
            b = block_bootstrap(diff, d.w_live, d.w_rec, cmp["headline"], int(cmp["compare"]["block_windows"]),
                                int(cmp["compare"]["reps"]), float(cmp["compare"]["level"]), int(cmp["compare"]["seed"]))
            vs = f"{b['diff']:+.3f} [{b['lo']:+.3f}, {b['hi']:+.3f}]"
        L.append(f"| {name} | {sc['median_R']:+.2%} / {cf['median_R']:+.2%} | {sc['worst10_R']:+.2%} / "
                 f"{cf['worst10_R']:+.2%} | {s['primary']['headline']:.3f} | {gates} | {a['mean_turnover'] / 14:.2f} | "
                 f"{a['mean_fees_e0']:.2%} + {a['mean_spread_e0']:.2%} | {a['max_calls_one_decision']} | {vs} |")
        if "chosen" in name or name.startswith("ref"):
            h = s["headline"]["FLOORED"]["REL"]
            robust.append(f"| {name} | {h['live_like']:.3f} | {h['recency']:.3f} | "
                          f"{s['layers']['ALL_flat']['mean_cs_primary']:.3f} |")
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
