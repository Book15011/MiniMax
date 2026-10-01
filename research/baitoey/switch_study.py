"""Calm/trend switch study (research/baitoey/prereg/20261001-calm-switch.md).

    python -m research.baitoey.switch_study screen    # score S50/S40/S60, SCREEN-only verdict -> verdict.json
    python -m research.baitoey.switch_study confirm   # once, after verdict.json: CONFIRM, REL, gates, compares

Scored with backtest.scoring.score.score_model like --score, but not registered on the leaderboard.
"""
from __future__ import annotations

import argparse
import copy
import json
import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

from backtest.data import load_market
from backtest.scoring.competition import block_bootstrap
from backtest.scoring.score import score_model
from research.baitoey.rot_max_study import row, stats
from research.baitoey.vt_study import PERIODS, ROOT, per_window, period
from src.config import load_config
from src.models import get

NAME = "baitoey_switch_mr"
RUNS = {"S50": 0.5, "S40": 0.4, "S60": 0.6}
SLEEVES = ("MR_4h", "CORE_4h")
RULE = ["gate_pass", "median_R", "p75_R", "worst10_R"]
PRIMARY = "FLOORED.REL.cs"
MR_STUDY = ROOT / "results" / "baitoey" / "20261001-mr-study"
OUT = ROOT / "results" / "baitoey" / "20261001-switch-study"
log = logging.getLogger("switch_study")


def run_one(run: str) -> str:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    cfg = load_config()
    vcfg = copy.deepcopy(cfg)
    vcfg["models"][NAME] = {**cfg["models"][NAME], "calm_quantile": RUNS[run]}
    score, _ = score_model(get(NAME), load_market(cfg), vcfg, use_cache=True, log=logging.getLogger(run))
    (OUT / f"{run}.json").write_text(json.dumps(score))
    return run


def registered(model: str, tool: str) -> dict:
    reg = [json.loads(x) for x in (ROOT / "results" / "scoring" / "registry.jsonl").read_text().splitlines()]
    p = Path([r for r in reg if r["model"] == model and r["tool_version"] == tool and r.get("full")][-1]["score_json"])
    return json.loads((p if p.is_absolute() else ROOT / p).read_text())


def scores() -> dict[str, dict]:
    s = {r: json.loads((OUT / f"{r}.json").read_text()) for r in RUNS}
    s.update({r: json.loads((MR_STUDY / f"{r}.json").read_text()) for r in SLEEVES})
    s["team_rot_ew"] = json.loads((MR_STUDY / "team_rot_ew.json").read_text())
    s["pol_switch_rt"] = registered("pol_switch_rt", s["S50"]["tool_version"])
    return s


def calm_share(cfg: dict) -> dict:
    m = load_market(cfg)
    p = cfg["models"][NAME]
    c = m.close["BTCUSDT"]
    vol = c.pct_change(fill_method=None).rolling(p["vol_days"] * 24, min_periods=p["vol_days"] * 12).std()
    daily = vol[vol.index.hour == cfg["harness"]["grid_hour_utc"]]
    q = daily.rolling(p["regime_days"], min_periods=p["regime_days"]).quantile(p["calm_quantile"])
    calm = (daily < q)[q.notna()]
    out = {}
    for name, (a, b) in PERIODS.items():
        x = calm[calm.index >= pd.Timestamp(a, tz="UTC")]
        x = x[x.index <= pd.Timestamp(b, tz="UTC") + pd.Timedelta(days=14)] if b else x
        out[name] = float(x.mean())
    return out


def screen() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "verdict.json").exists():
        raise SystemExit("verdict.json exists: the SCREEN verdict is frozen")
    with ProcessPoolExecutor(max_workers=3) as ex:
        for r in ex.map(run_one, RUNS):
            log.info("finished %s", r)
    s = scores()
    st = {k: stats(period(per_window(v), "SCREEN")) for k, v in s.items()}

    def beats_both(run: str) -> tuple[bool, dict]:
        rows = pd.DataFrame({k: st[k] for k in (run, *SLEEVES)}).T
        rank = rows[RULE].rank(ascending=False).mean(axis=1)
        return bool(all(rank[run] < rank[x] for x in SLEEVES)), rank.round(3).to_dict()

    res = {r: beats_both(r) for r in RUNS}
    verdict = {"adds_value": res["S50"][0], "robust": all(res[r][0] for r in RUNS),
               "mean_ranks": {r: res[r][1] for r in RUNS}}
    (OUT / "verdict.json").write_text(json.dumps(verdict, indent=1))
    head = ("| Run | Return gate passed | Median R | 75th pct R | 90th pct R | Worst 10% R | Turnover/day | "
            "Fees + spread per window | Min active days |\n|---|---|---|---|---|---|---|---|---|")
    lines = ["# Calm/trend switch: SCREEN (2022-07 to 2024-06) only", "", head]
    lines += [row(k, st[k]) for k in (*RUNS, *SLEEVES, "team_rot_ew", "pol_switch_rt")]
    lines += ["", f"Switch adds value (S50 beats both sleeves on mean rank): **{verdict['adds_value']}**; "
              f"robust (S40 and S60 too): **{verdict['robust']}**.", f"Mean ranks: {verdict['mean_ranks']}"]
    text = "\n".join(lines)
    (OUT / "screen.md").write_text(text + "\n")
    print(text)
    return 0


def confirm() -> int:
    if not (OUT / "verdict.json").exists():
        raise SystemExit("run the SCREEN phase first")
    if (OUT / "report.md").exists():
        raise SystemExit("report.md exists: CONFIRM was already opened once")
    cfg = load_config()
    sc = cfg["scoring"]
    s = scores()
    d = {k: per_window(v) for k, v in s.items()}
    L = ["# Calm/trend switch: full results (CONFIRM opened once)", "",
         "| Run | Gate passed S / C | Median R S / C | 75th pct R S / C | 90th pct R S / C | Worst 10% R S / C | REL | "
         "REL live-like / recency / flat | Gates G1-G6 | Turnover/day | Fees + spread | Max orders/decision |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, v in s.items():
        a, b = stats(period(d[k], "SCREEN")), stats(period(d[k], "CONFIRM"))
        h = v["headline"]["FLOORED"]["REL"]
        gates = " ".join(f"{g[-1]}{'✓' if x['pass'] else '✗'}" for g, x in v["gates"].items())
        act = v["activity"]
        L.append(f"| {k} | {a['gate_pass']:.0%} / {b['gate_pass']:.0%} | {a['median_R']:+.2%} / {b['median_R']:+.2%} | "
                 f"{a['p75_R']:+.2%} / {b['p75_R']:+.2%} | {a['p90_R']:+.2%} / {b['p90_R']:+.2%} | "
                 f"{a['worst10_R']:+.2%} / {b['worst10_R']:+.2%} | {v['primary']['headline']:.3f} | "
                 f"{h['live_like']:.2f} / {h['recency']:.2f} / {v['layers']['ALL_flat']['mean_cs_primary']:.2f} | "
                 f"{gates} | {act['mean_turnover'] / 14:.2f} | {act['mean_fees_e0']:.2%} + {act['mean_spread_e0']:.2%} | "
                 f"{act['max_calls_one_decision']} |")
    L += ["", "Compare S50 against (paired REL CS difference, 90% block bootstrap, blocks of 56):", ""]
    for ref in ("team_rot_ew", "MR_4h", "pol_switch_rt"):
        diff = (d["S50"][PRIMARY] - d[ref][PRIMARY].reindex(d["S50"].index)).dropna()
        r = block_bootstrap(diff, d["S50"].w_live, d["S50"].w_rec, sc["headline"], int(sc["compare"]["block_windows"]),
                            int(sc["compare"]["reps"]), float(sc["compare"]["level"]), int(sc["compare"]["seed"]))
        L.append(f"- vs {ref}: {r['diff']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}]")
    share = calm_share(cfg)
    L += ["", f"Share of decision days that were calm (S50 rule): SCREEN {share['SCREEN']:.0%}, CONFIRM {share['CONFIRM']:.0%}"]
    L += ["", "Gate failures:"] + [f"- {k}: {g} {x['detail']}" for k, v in s.items() for g, x in v["gates"].items()
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
