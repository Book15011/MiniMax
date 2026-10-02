"""Dual-momentum study (research/baitoey/prereg/20261002-dual-momentum.md).

D0 is scored first with `python -m backtest.run --model baitoey_vt_dual --score` (registered: on the leaderboard).
This script then scores the two neighbours with score_model like --score, without registering them (one at a
time), reads D0 and the references from the registry, and writes the report with the pre-registered verdict.

    python -m research.baitoey.vt_dual
"""
from __future__ import annotations

import copy
import json
import logging

import pandas as pd

from backtest.data import load_market
from backtest.scoring import explain
from backtest.scoring.registry import resolve
from backtest.scoring.score import dumps, score_model, wquantile
from research.baitoey.vt_plateau import pct
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models import get

NAME, BASE = "baitoey_vt_dual", "baitoey_vt_mom"
OUT = ROOT / "results" / "baitoey" / "20261002-vt-dual"
TOOL = "3036a0d8bfdaa6a0"
MARGIN, FALL_GAIN = 0.03, 0.05
NEIGHBOURS = {"Dm": ("min_score -0.25", {"min_score": -0.25}), "Dp": ("min_score +0.25", {"min_score": 0.25})}
REGISTERED = {"D0": ("min_score 0 (registered)", NAME), "vt_mom": ("reference", BASE),
              "vt_mom + crash rule": ("reference", "pol_abl_shock")}
TYPES = ("strong fall", "mild fall", "mild rise", "strong rise")


def summarize(label: str, change: str, score: dict, btc: pd.Series) -> dict:
    pw = pd.DataFrame(score["per_window"])
    pw.index = pd.to_datetime(pw.pop("start"), utc=True)
    t = pw[pw.scored.astype(bool)]
    prof = explain.profile(t, explain.market_types(t.index, btc, t["regime"]))
    w, R = t.w_final.astype(float), t.R_liq.astype(float)
    rp = (score.get("replay") or {}).get("windows", [])
    return {"run": label, "change": change, "headline": score["primary"]["headline"],
            "in_sample": score["primary"]["in_sample"], "hit": score["return_first"]["full"]["hit"],
            "eligible": bool(score["eligible"]), "types": {k: prof.get(k, {}).get("hit") for k in TYPES},
            "strong_fall": prof.get("strong fall", {}).get("hit"),
            "median_R": wquantile(R, w, 0.5), "mean_R": float((R * w).sum() / w.sum()), "worst_R": float(R.min()),
            "replay": [{"name": x["name"], "R": x["R"], "rank": x["ranks"][0]["rank"], "teams": x["ranks"][0]["teams"]}
                       for x in rp],
            "guard_share": score["activity"]["guard_share_of_active_days"], "fees": score["activity"]["mean_fees_e0"],
            "mean_gross": score["activity"]["mean_gross"], "tool_version": score["tool_version"]}


def registered_score(model: str) -> dict:
    latest = None
    for line in open(resolve("results/scoring/registry.jsonl")):
        r = json.loads(line) if line.strip() else None
        if r and r.get("model") == model and r.get("full") and r.get("tool_version") == TOOL:
            latest = r
    if latest is None:
        raise SystemExit(f"{model}: no full run at tool version {TOOL} in the registry (run --score first)")
    return json.load(open(resolve(latest["score_json"])))


def tie_text() -> str:
    for line in resolve("results/scoring/leaderboard.md").read_text().splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) > 6 and cells[1] == NAME:
            return f"rank {cells[0]} of the candidates; tie group vs the top: {cells[6]}"
    return "not found on the leaderboard"


def report(rows: dict[str, dict]) -> str:
    lines = ["# Dual-momentum study (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261002-dual-momentum.md`. D0 is on the leaderboard; Dm and Dp",
             "are scored like `--score` but not registered. Type columns: hit rate (mean of the three bars) in windows where",
             "BTC moved <= -5% / -5..0% / 0..+5% / >= +5% over the 14 days.", "",
             "| Run | Change | HEADLINE_RET | without post-holdout | Strong fall | Mild fall | Mild rise | Strong rise | Median / mean R | Worst R | Round 1 · Final | Mean gross | Guard share | Fees | Hard gates |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in rows.values():
        ty = " | ".join("—" if x["types"][k] is None else f"{100 * x['types'][k]:.0f}%" for k in TYPES)
        rp = " · ".join(f"{pct(p['R'])} #{p['rank']}/{p['teams']}" for p in x["replay"]) or "—"
        lines.append(f"| {x['run']} | {x['change']} | **{x['headline']:.3f}** | {x['in_sample']:.3f} | {ty} | "
                     f"{pct(x['median_R'])} / {pct(x['mean_R'])} | {pct(x['worst_R'])} | {rp} | {100 * x['mean_gross']:.0f}% | "
                     f"{100 * x['guard_share']:.0f}% | {pct(x['fees'], 2)} | {'pass' if x['eligible'] else 'FAIL'} |")
    base, d0 = rows["vt_mom"], rows["D0"]
    bar = base["headline"] - MARGIN
    keeps = {r: rows[r]["eligible"] and rows[r]["headline"] >= bar for r in ("D0", *NEIGHBOURS)}
    falls = d0["strong_fall"] >= base["strong_fall"] + FALL_GAIN and d0["worst_R"] > base["worst_R"]
    cand = keeps["D0"] and falls and all(keeps[r] for r in NEIGHBOURS)
    lines += ["", f"D0 on the leaderboard: {tie_text()}.", "",
              f"- Keeps the score (hard gates pass and HEADLINE_RET >= {bar:.3f}): D0 {'yes' if keeps['D0'] else 'NO'}, "
              f"Dm {'yes' if keeps['Dm'] else 'NO'}, Dp {'yes' if keeps['Dp'] else 'NO'}.",
              f"- Improves falls (strong-fall hit >= {100 * (base['strong_fall'] + FALL_GAIN):.1f}% and worst R above "
              f"{pct(base['worst_R'])}): {'yes' if falls else 'NO'} (D0: {100 * d0['strong_fall']:.1f}%, {pct(d0['worst_R'])}).",
              f"", f"**Verdict: {'CANDIDATE for the team' if cand else 'NOT A CANDIDATE'}.**",
              f"Tool version(s): {', '.join(sorted({x['tool_version'] for x in rows.values()}))}."]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(OUT / "run.log"), logging.StreamHandler()])
    log = logging.getLogger("vt_dual")
    cfg = load_config()
    btc = pd.read_parquet(resolve(cfg["harness"]["panel_dir"]) / "panel_close_1h.parquet", columns=["BTCUSDT"])["BTCUSDT"]
    rows = {label: summarize(label, change, registered_score(model), btc) for label, (change, model) in REGISTERED.items()}
    market, model = load_market(cfg), get(NAME)
    for label, (change, params) in NEIGHBOURS.items():
        c = copy.deepcopy(cfg)
        c["models"][NAME] = {**copy.deepcopy(cfg["models"][NAME]), **params}
        log.info("%s (%s): scoring", label, change)
        score, _ = score_model(model, market, c, use_cache=True, log=log)
        (OUT / f"{label}-score.json").write_text(dumps(score))
        rows[label] = summarize(label, change, score, btc)
        log.info("%s: HEADLINE_RET %.4f", label, rows[label]["headline"])
    (OUT / "rows.json").write_text(json.dumps(rows, indent=1, default=str))
    (OUT / "report.md").write_text(report(rows))
    log.info("done: %s", OUT / "report.md")


if __name__ == "__main__":
    main()
