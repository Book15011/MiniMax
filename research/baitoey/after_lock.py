"""After the lock-in fires, switch to another strategy instead of cash? (research/baitoey/prereg/20261005-after-lock.md).

    python -m research.baitoey.after_lock
"""
from __future__ import annotations

import glob
import json

import numpy as np
import pandas as pd

from backtest.data import load_market
from backtest.scoring.evaluate import simulate
from backtest.scoring.metrics import window_metrics
from backtest.scoring.windows import pool_starts
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models import get

NAME = "pol_switch_vt_tl_e20v45"
OUT = ROOT / "results" / "baitoey" / "20261005-after-lock"
TOOL = "3036a0d8bfdaa6a0"
H, EXIT, LOCK, DAY = 336, 0.0013, 0.03, 10
NOISE, MARGIN, CS_GAIN, WORST_GAIN = 0.01, 0.03, 0.02, 0.02


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_config(); sc = cfg["scoring"]; market = load_market(cfg); starts = pool_starts(market, cfg)
    liq = float(sc["liquidation_cost"]); points = np.array([0] + list(range(4, H, 24)) + [H])
    ref = [json.load(open(f)) for f in glob.glob(str(ROOT / "results/*/*/team_rot_ew-*/score.json"))]
    ref = [s for s in ref if s.get("tool_version") == TOOL][-1]
    pw = pd.DataFrame(ref["per_window"]); pw.index = pd.to_datetime(pw.pop("start"), utc=True); pw = pw[pw.scored.astype(bool)].reindex(starts)
    up = pw.btc_up.astype(bool).to_numpy(); w = pw.w_final.to_numpy(); w = w / w.sum()
    bars = np.column_stack([np.where(up, 0.0, -0.014965215), np.zeros(len(starts)), np.maximum(0.0, pw.field_median_R_liq.to_numpy())])
    fr = {}
    for n in sc["field"]:
        rr = simulate(get(n), market, cfg, starts, use_cache=True); k = rr.windows.index.get_indexer(starts)
        fr[n] = rr.equity[k, -1] * (1 - liq * rr.gross[k, -1]) - 1
    cut = np.where(up, np.maximum(0, pd.DataFrame(fr).max(axis=1).to_numpy()), 0.006)

    def path(name):
        r = simulate(get(name), market, cfg, starts, use_cache=True); k = r.windows.index.get_indexer(starts)
        return r.equity[k].astype(float), r.gross[k].astype(float)

    Ee, Ge = path(NAME)
    alts = {"AMR": path("pol_mr_cap"), "ATR": path("team_trend_2")}

    def run(mode):
        E, G = Ee.copy(), Ge.copy()
        R0 = E / E[:, :1] - 1
        for i in range(len(E)):
            hit = np.nonzero(R0[i, DAY * 24:H - 1] >= LOCK)[0]
            if not len(hit):
                continue
            h = DAY * 24 + hit[0] + 1
            if mode == "AHALF":
                x = E[i, h] * (1 - EXIT * 0.5 * G[i, h])
                rel = Ee[i, h:] / Ee[i, h]
                E[i, h:] = x * 0.5 + x * 0.5 * rel
                G[i, h:] = (x * 0.5 * rel * Ge[i, h:]) / E[i, h:]
                continue
            x = E[i, h] * (1 - EXIT * G[i, h])
            if mode == "L0":
                E[i, h:] = x; G[i, h:] = 0.0
            else:
                Ea, Ga = alts[mode]
                x = x * (1 - EXIT * Ga[i, h])
                E[i, h:] = x * Ea[i, h:] / Ea[i, h]; G[i, h:] = Ga[i, h:]
        R = E[:, -1] * (1 - liq * G[:, -1]) / E[:, 0] - 1
        comp = window_metrics(E, G[:, -1], sc, points=points)["FLOORED.V1.composite"].to_numpy()
        ind = (R[:, None] >= bars).astype(float); ok = ind[:, 0] > 0
        return {"HR": float((w[:, None] * ind).sum(0).mean()), "CS": float((w[ok] * comp[ok]).sum() / w[ok].sum()),
                "cut": float((w * (R >= cut)).sum()), "mean": float((w * R).sum()), "worst": float(R.min())}

    R_raw = Ee[:, -1] * (1 - liq * Ge[:, -1]) / Ee[:, 0] - 1
    raw_hr = float((w[:, None] * (R_raw[:, None] >= bars)).sum(0).mean())
    labels = {"L0": "cash (as launched)", "AMR": "mean reversion (pol_mr_cap)", "ATR": "BTC/ETH trend (team_trend_2)", "AHALF": "keep half in e20v45"}
    res = {k: run(k) for k in labels}
    P = lambda v: f"{100 * v:+.2f}%"
    lines = ["# After the lock-in fires: cash or another strategy? (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261005-after-lock.md`. e20v45's cached paths, method of Pol's endgame2.py.",
             f"Check: e20v45 without the lock gives HEADLINE_RET {raw_hr:.4f} (registered 0.5682).", "",
             "| Run | After the lock fires | HEADLINE_RET | vs L0 | CS_HIT | Top-20 proxy | Mean R | Worst R |", "|---|---|---|---|---|---|---|---|"]
    for k, lab in labels.items():
        s = res[k]
        lines.append(f"| {k} | {lab} | **{s['HR']:.3f}** | {s['HR'] - res['L0']['HR']:+.3f} | {s['CS']:.3f} | {s['cut']:.3f} | {P(s['mean'])} | {P(s['worst'])} |")
    l0 = res["L0"]; better = []
    for k in ("AMR", "ATR", "AHALF"):
        s = res[k]
        good = (s["HR"] >= l0["HR"] + MARGIN or (s["HR"] >= l0["HR"] - NOISE and (s["CS"] - l0["CS"] >= CS_GAIN or s["worst"] - l0["worst"] >= WORST_GAIN))) and s["cut"] >= l0["cut"]
        if good:
            better.append(k)
    lines += ["", f"- Better than cash: {', '.join(better) or 'none'} -> **{'PROPOSE ' + ', '.join(better) if better else 'KEEP CASH AFTER THE LOCK'}**.", "", f"Tool version: {TOOL}."]
    (OUT / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
