"""Skim profits to cash and keep trading only the original money (research/baitoey/prereg/20261005-profit-skim.md).

    python -m research.baitoey.profit_skim
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
OUT = ROOT / "results" / "baitoey" / "20261005-profit-skim"
TOOL = "3036a0d8bfdaa6a0"
H, EXIT, LOCK, DAY, MARGIN = 336, 0.0013, 0.03, 10, 0.03


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
    run = simulate(get(NAME), market, cfg, starts, use_cache=True); k = run.windows.index.get_indexer(starts)
    E0, G0 = run.equity[k].astype(float), run.gross[k].astype(float)

    def apply(x: float | None, locked: bool):
        n, T = E0.shape
        r = E0[:, 1:] / E0[:, :-1] - 1.0
        I = np.ones(n); C = np.zeros(n); eq = np.ones((n, T)); g = G0.copy(); pending = np.zeros(n, dtype=bool); fired = np.zeros(n, dtype=bool)
        for h in range(1, T):
            I = I * (1.0 + r[:, h - 1])
            if x is not None:
                amt = np.where(pending, np.maximum(I - 1.0, 0.0), 0.0)
                C = C + amt * (1 - EXIT); I = I - amt
                pending = I >= 1.0 + x; fired |= pending
            eq[:, h] = I + C
            g[:, h] = G0[:, h] * I / eq[:, h]
        E = eq * E0[:, :1]
        if locked:
            R0 = E / E[:, :1] - 1
            for i in range(n):
                hit = np.nonzero(R0[i, DAY * 24:H - 1] >= LOCK)[0]
                if len(hit):
                    h = DAY * 24 + hit[0] + 1; E[i, h:] = E[i, h] * (1 - EXIT * g[i, h]); g[i, h:] = 0.0
        R = E[:, -1] * (1 - liq * g[:, -1]) / E[:, 0] - 1
        comp = window_metrics(E, g[:, -1], sc, points=points)["FLOORED.V1.composite"].to_numpy()
        ind = (R[:, None] >= bars).astype(float); ok = ind[:, 0] > 0
        return {"HR": float((w[:, None] * ind).sum(0).mean()), "CS": float((w[ok] * comp[ok]).sum() / w[ok].sum()),
                "cut": float((w * (R >= cut)).sum()), "mean": float((w * R).sum()), "worst": float(R.min()), "fired": float(fired.mean())}

    raw = apply(None, False)
    sf = [s for s in (json.load(open(f)) for f in glob.glob(str(ROOT / f"results/*/*/{NAME}-*/score.json"))) if s.get("tool_version") == TOOL][-1]
    runs = {"L0": ("e20v45 + lock-in (as launched)", None, True), "S2": ("skim at +2%, plus lock-in", 0.02, True),
            "S3": ("skim at +3%, plus lock-in", 0.03, True), "S5": ("skim at +5%, plus lock-in", 0.05, True),
            "N3": ("skim at +3%, no lock-in", 0.03, False), "N0": ("e20v45, no lock-in, no skim", None, False)}
    res = {k: apply(x, lk) for k, (_, x, lk) in runs.items()}
    P = lambda v: f"{100 * v:+.2f}%"
    lines = ["# Skim profits to cash and keep trading only the original money (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261005-profit-skim.md`. e20v45's cached paths, method of Pol's endgame2.py.",
             f"Check: the unmodified path gives HEADLINE_RET {raw['HR']:.4f} (score file {sf['return_first']['full']['headline_ret']:.4f}).", "",
             "| Run | Rule | HEADLINE_RET | vs L0 | CS_HIT | Top-20 proxy | Mean R | Worst R | Skim fired in |", "|---|---|---|---|---|---|---|---|---|"]
    for key, (lab, x, lk) in runs.items():
        s = res[key]
        fired = "—" if x is None else "%.0f%% of rounds" % (100 * s["fired"])
        lines.append(f"| {key} | {lab} | **{s['HR']:.3f}** | {s['HR'] - res['L0']['HR']:+.3f} | {s['CS']:.3f} | {s['cut']:.3f} | "
                     f"{P(s['mean'])} | {P(s['worst'])} | {fired} |")
    ok = all(res[k]["HR"] >= res["L0"]["HR"] + MARGIN and res[k]["cut"] >= res["L0"]["cut"] for k in ("S2", "S3", "S5"))
    lines += ["", f"- S2 / S3 / S5 against L0 -> **{'PROPOSE' if ok else 'KEEP THE STRATEGY AS LAUNCHED'}**.", "", f"Tool version: {TOOL}."]
    (OUT / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
