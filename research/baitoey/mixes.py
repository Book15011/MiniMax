"""Split the money between two models (research/baitoey/prereg/20261004-mixes.md).

Two separate sub-accounts on the cached v2 equity paths, scored with the method of Pol's
results/pol/20261002-v2check/endgame2.py, without and with the live lock-in on the whole account.

    python -m research.baitoey.mixes
"""
from __future__ import annotations

import glob
import json
import logging

import numpy as np
import pandas as pd

from backtest.data import load_market
from backtest.scoring.evaluate import simulate
from backtest.scoring.metrics import window_metrics
from backtest.scoring.windows import pool_starts
from research.baitoey.vt_dual import registered_score
from research.baitoey.vt_study import ROOT
from src.config import load_config, resolve
from src.models import get

OUT = ROOT / "results" / "baitoey" / "20261004-mixes"
TOOL = "3036a0d8bfdaa6a0"
H, EXIT, LOCK, DAY = 336, 0.0013, 0.03, 10
E20, ABL, MR, VT = "pol_switch_vt_tl_e20v45", "pol_abl_shock", "pol_mr_cap", "baitoey_vt_mom"
MIXES = {"X1": (E20, ABL), "X2": (E20, MR), "X3": (VT, MR)}
WEIGHTS = (0.4, 0.5, 0.6)
MARGIN, NOISE, WORST_GAIN, CS_GAIN = 0.03, 0.01, 0.02, 0.02


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.WARNING)
    cfg = load_config(); sc = cfg["scoring"]; market = load_market(cfg)
    starts = pool_starts(market, cfg)
    liq = float(sc["liquidation_cost"])
    points = np.array([0] + list(range(4, H, 24)) + [H])
    ref = [json.load(open(f)) for f in glob.glob(str(ROOT / "results/*/*/team_rot_ew-*/score.json"))]
    ref = [s for s in ref if s.get("tool_version") == TOOL][-1]
    pw = pd.DataFrame(ref["per_window"]); pw.index = pd.to_datetime(pw.pop("start"), utc=True)
    pw = pw[pw.scored.astype(bool)].reindex(starts)
    up = pw.btc_up.astype(bool).to_numpy(); fmed = pw.field_median_R_liq.to_numpy()
    w = pw.w_final.to_numpy(); w = w / w.sum()
    bars = np.column_stack([np.where(up, 0.0, -0.014965215), np.zeros(len(starts)), np.maximum(0.0, fmed)])
    fr = {}
    for n in sc["field"]:
        rr = simulate(get(n), market, cfg, starts, use_cache=True)
        k = rr.windows.index.get_indexer(starts)
        fr[n] = rr.equity[k, -1] * (1 - liq * rr.gross[k, -1]) - 1
    cut150 = np.where(up, np.maximum(0, pd.DataFrame(fr).max(axis=1).to_numpy()), 0.006)

    def score(E, G):
        R = E[:, -1] * (1 - liq * G[:, -1]) / E[:, 0] - 1
        comp = window_metrics(E, G[:, -1], sc, points=points)["FLOORED.V1.composite"].to_numpy()
        ind = (R[:, None] >= bars).astype(float)
        ok = ind[:, 0] > 0
        return {"HR": float((w[:, None] * ind).sum(0).mean()), "CS_HIT": float((w[ok] * comp[ok]).sum() / w[ok].sum()),
                "cut": float((w * (R >= cut150)).sum()), "mean_R": float((w * R).sum()), "worst_R": float(R.min())}

    def lock(E, G):
        E, G = E.copy(), G.copy()
        R = E / E[:, :1] - 1
        for k in range(len(E)):
            hit = np.nonzero(R[k, DAY * 24:H - 1] >= LOCK)[0]
            if len(hit):
                h = DAY * 24 + hit[0] + 1
                E[k, h:] = E[k, h] * (1 - EXIT * G[k, h]); G[k, h:] = 0.0
        return E, G

    paths = {}
    for n in {E20, ABL, MR, VT}:
        run = simulate(get(n), market, cfg, starts, use_cache=True)
        sel = run.windows.index.get_indexer(starts)
        E, G = run.equity[sel].astype(float), run.gross[sel].astype(float)
        paths[n] = (E / E[:, :1], G)

    def mix(a, b, x):
        Ea, Ga = paths[a]; Eb, Gb = paths[b]
        E = x * Ea + (1 - x) * Eb
        return E, (x * Ea * Ga + (1 - x) * Eb * Gb) / E

    rp = cfg["scoring"]["replay"]; lb = pd.read_csv(resolve(rp["leaderboard_csv"]))
    comps = {wd["name"]: wd["competitions"] for wd in rp["windows"]}
    rep = {n: {x["name"]: x["R"] for x in registered_score(n)["replay"]["windows"]} for n in {E20, ABL, MR, VT}}

    def replay(parts):
        out = []
        for name, cs in comps.items():
            R = sum(x * rep[n][name] for n, x in parts)
            out.append("%+.1f%% %s" % (100 * R, "/".join("#%d" % (int((lb[lb.cpt == c].ret > R).sum()) + 1) for c in cs)))
        return " · ".join(out)

    sf = [s for s in (json.load(open(f)) for f in glob.glob(str(ROOT / f"results/*/*/{E20}-*/score.json"))) if s.get("tool_version") == TOOL][-1]
    raw = score(*paths[E20])
    rows = {"E0": (f"{E20} alone", score(*lock(*paths[E20])), raw, replay([(E20, 1.0)]))}
    for key, (a, b) in MIXES.items():
        for x in WEIGHTS:
            E, G = mix(a, b, x)
            rows[f"{key}-{int(100 * x)}"] = (f"{int(100 * x)}% {a} / {int(100 * (1 - x))}% {b}", score(*lock(E, G)), score(E, G),
                                             replay([(a, x), (b, 1 - x)]))
    e0 = rows["E0"][1]
    P = lambda v: f"{100 * v:+.1f}%"
    lines = ["# Split the money between two models (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261004-mixes.md`. Two separate sub-accounts on the cached v2 paths,",
             "method of Pol's endgame2.py. Main columns with the live lock-in on the whole account; the last two without it.", "",
             f"Check: e20v45's unmodified path gives HEADLINE_RET {raw['HR']:.4f} (score file {sf['return_first']['full']['headline_ret']:.4f}), "
             f"CS_HIT {raw['CS_HIT']:.3f} ({sf['return_first']['full']['cs_hit']:.3f}).", "",
             "| Run | Money split | HEADLINE_RET | vs E0 | CS_HIT | ~150-team cut | Mean R | Worst R | Without lock: HEADLINE_RET / CS_HIT | Real rounds (falling R1 HK/SG · rising Final) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for key, (lab, s, n, r) in rows.items():
        lines.append(f"| {key} | {lab} | **{s['HR']:.3f}** | {s['HR'] - e0['HR']:+.3f} | {s['CS_HIT']:.3f} | {s['cut']:.3f} | "
                     f"{P(s['mean_R'])} | {P(s['worst_R'])} | {n['HR']:.3f} / {n['CS_HIT']:.3f} | {r} |")
    lines.append("")
    for key in MIXES:
        mid, lo, hi = rows[f"{key}-50"][1], rows[f"{key}-40"][1], rows[f"{key}-60"][1]
        better = mid["HR"] >= e0["HR"] + MARGIN or (mid["HR"] >= e0["HR"] - NOISE and (mid["worst_R"] - e0["worst_R"] >= WORST_GAIN
                                                                                       or mid["CS_HIT"] - e0["CS_HIT"] >= CS_GAIN))
        hold = all(r["HR"] >= e0["HR"] - MARGIN for r in (lo, hi))
        lines.append(f"- {key} ({MIXES[key][0]} + {MIXES[key][1]}): 50/50 {'better' if better else 'not better'}, neighbours "
                     f"{'hold' if hold else 'do not hold'} -> **{'PROPOSE' if better and hold else 'KEEP E20V45 ALONE'}**.")
    lines += ["", f"Tool version: {TOOL}."]
    (OUT / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
