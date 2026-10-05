"""A daily take-profit on e20v45 (research/baitoey/prereg/20261005-daily-tp.md).

    python -m research.baitoey.daily_tp
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
OUT = ROOT / "results" / "baitoey" / "20261005-daily-tp"
TOOL = "3036a0d8bfdaa6a0"
H, EXIT, LOCK, DAY = 336, 0.0013, 0.03, 10
NOISE, MARGIN, CS_GAIN, WORST_GAIN = 0.01, 0.03, 0.02, 0.02
CYCLES = [0] + list(range(4, H, 24)) + [H]                               # 12:00 UTC start, then every 16:00 UTC


def take_profit(Em: np.ndarray, Gm: np.ndarray, x: float | None):
    """Account path with the daily take-profit at +x (None: off) and the live lock-in. Returns E, G, exits per window.

    Hour by hour: apply the model's return while invested; carry out an exit or lock decided at the previous hour (at
    0.13% on the gross held); at a cycle start (16:00 UTC) set the base and, if in cash, buy the model's book back
    (0.13% on its gross); then decide: a take-profit exit once the account is x above the base (at most once a cycle,
    never at a cycle start) and the lock-in once the account is +3% on the round start from day 10.
    """
    n = len(Em)
    starts = set(CYCLES[1:-1])
    E, G, exits = np.empty_like(Em), np.empty_like(Gm), np.zeros(n)
    for i in range(n):
        acc, inv, locked, base, armed, want_exit, want_lock = 1.0, True, False, 1.0, True, False, False
        E[i, 0], G[i, 0] = 1.0, Gm[i, 0]
        for t in range(1, H + 1):
            if locked:
                E[i, t], G[i, t] = acc, 0.0
                continue
            if inv:
                acc *= Em[i, t] / Em[i, t - 1]
            if want_lock:
                if inv:
                    acc *= 1 - EXIT * Gm[i, t]
                inv, locked = False, True
                E[i, t], G[i, t] = acc, 0.0
                continue
            if want_exit and t not in starts and inv:
                acc *= 1 - EXIT * Gm[i, t]; inv = False; exits[i] += 1
            want_exit = False
            if t in starts:
                if not inv:
                    acc *= 1 - EXIT * Gm[i, t]; inv = True
                base, armed = acc, True
            E[i, t], G[i, t] = acc, (Gm[i, t] if inv else 0.0)
            if t < H and inv and x is not None and armed and acc >= base * (1 + x):
                want_exit, armed = True, False
            if t < H and t >= DAY * 24 and acc - 1.0 >= LOCK:
                want_lock = True
    return E, G, exits


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
    r = simulate(get(NAME), market, cfg, starts, use_cache=True); k = r.windows.index.get_indexer(starts)
    Em, Gm = r.equity[k].astype(float), r.gross[k].astype(float)
    Em = Em / Em[:, :1]

    def score(E, G):
        R = E[:, -1] * (1 - liq * G[:, -1]) / E[:, 0] - 1
        comp = window_metrics(E, G[:, -1], sc, points=points)["FLOORED.V1.composite"].to_numpy()
        ind = (R[:, None] >= bars).astype(float); ok = ind[:, 0] > 0
        return {"HR": float((w[:, None] * ind).sum(0).mean()), "CS": float((w[ok] * comp[ok]).sum() / w[ok].sum()),
                "cut": float((w * (R >= cut)).sum()), "mean": float((w * R).sum()), "worst": float(R.min())}

    R_raw = Em[:, -1] * (1 - liq * Gm[:, -1]) - 1
    raw_hr = float((w[:, None] * (R_raw[:, None] >= bars)).sum(0).mean())
    runs = {"L0": None, "TP05": 0.005, "TP10": 0.01, "TP20": 0.02}
    res, ex = {}, {}
    for key, x in runs.items():
        E, G, exits = take_profit(Em, Gm, x)
        res[key] = score(E, G); ex[key] = float((w * exits).sum())
    labels = {"L0": "e20v45 + lock-in (as launched)", "TP05": "daily take-profit +0.5%, plus lock-in", "TP10": "daily take-profit +1%, plus lock-in", "TP20": "daily take-profit +2%, plus lock-in"}
    P = lambda v: f"{100 * v:+.2f}%"
    lines = ["# A daily take-profit on e20v45 (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261005-daily-tp.md`. e20v45's cached paths, method of Pol's endgame2.py.",
             f"Check: e20v45 without the lock gives HEADLINE_RET {raw_hr:.4f} (registered 0.5682).", "",
             "| Run | Rule | HEADLINE_RET | vs L0 | CS_HIT | Top-20 proxy | Mean R | Worst R | Take-profit exits per round |", "|---|---|---|---|---|---|---|---|---|"]
    for key, lab in labels.items():
        s = res[key]
        lines.append(f"| {key} | {lab} | **{s['HR']:.3f}** | {s['HR'] - res['L0']['HR']:+.3f} | {s['CS']:.3f} | {s['cut']:.3f} | {P(s['mean'])} | {P(s['worst'])} | "
                     f"{'—' if key == 'L0' else f'{ex[key]:.1f}'} |")
    l0 = res["L0"]
    good = lambda s: (s["HR"] >= l0["HR"] + MARGIN or (s["HR"] >= l0["HR"] - NOISE and (s["CS"] - l0["CS"] >= CS_GAIN or s["worst"] - l0["worst"] >= WORST_GAIN))) and s["cut"] >= l0["cut"]
    ok = good(res["TP05"]) and good(res["TP10"])
    lines += ["", f"- TP05 {'better' if good(res['TP05']) else 'not better'}, TP10 {'better' if good(res['TP10']) else 'not better'} -> **{'PROPOSE' if ok else 'KEEP THE STRATEGY AS LAUNCHED'}**.", "", f"Tool version: {TOOL}."]
    (OUT / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
