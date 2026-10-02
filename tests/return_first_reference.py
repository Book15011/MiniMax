"""PART 6.2: independent recomputation of w', the three HITs, HEADLINE_RET and CS_HIT from the saved per-window outputs.

Imports nothing from backtest/ or src/: it reads the registry (JSONL), each run's score.json, the live-like v2 file
and the panel's BTC closes, and applies the pre-registered rules (reports/review/20261002-prereg-return-first.md)
with its own code (the pre-registration's PART 6.2). Run from the worktree root:
    python tests/return_first_reference.py <tool version> <model> [<model> ...]
"""
import json
import sys

import numpy as np
import pandas as pd

LENIENT_DOWN, LENIENT_UP, MIDDLE, STRICT_FLOOR = -0.014965215, 0.0, 0.0, 0.0      # pre-registered, PART 3.2
HALF_LIFE, SPLIT_LL, SPLIT_REC = 60.0, 0.7, 0.3                                       # PART 2.3, 2.4
HOLDOUT_FROM = pd.Timestamp("2026-08-08 16:00", tz="UTC")
FIELD = ["team_btc_hold", "team_ew_daily", "team_rot_ew", "team_rot_iv", "team_trend_2", "team_mom_ss25"]
TOOL = sys.argv[1]
MODELS = sys.argv[2:]

reg = [json.loads(line) for line in open("results/scoring/registry.jsonl")]
latest = {}
for e in reg:
    if e.get("full") and e["tool_version"] == TOOL:
        latest[e["model"]] = e


def per_window(name):
    s = json.load(open(latest[name]["score_json"]))
    pw = s["per_window"]
    df = pd.DataFrame(pw)
    df.index = pd.to_datetime(df.pop("start"), utc=True)
    return s, df[df.scored.astype(bool)]


ll_file = json.load(open("validation/live_like_v2_prelim.json"))
LL = pd.Series(ll_file["weights"]["all"], dtype=float)
LL.index = pd.to_datetime(LL.index, utc=True)
btc = pd.read_parquet("data/validation/panel_close_1h.parquet", columns=["BTCUSDT"])["BTCUSDT"].dropna()
field = {n: per_window(n)[1] for n in FIELD}

worst = 0.0
for name in MODELS:
    s, pw = per_window(name)
    starts = pw.index
    for pool, sel in (("full", np.ones(len(starts), bool)),
                      ("in_sample", np.asarray(starts + pd.Timedelta(days=14) <= HOLDOUT_FROM))):
        idx = starts[sel]
        ll = LL.reindex(idx)
        assert ll.notna().all()
        age = np.asarray((idx.max() - idx) / pd.Timedelta(days=1), dtype=float)
        rec = pd.Series(0.5 ** (age / HALF_LIFE), index=idx)
        w = SPLIT_LL * ll / ll.sum() + SPLIT_REC * rec / rec.sum()
        # UP: BTC's close at the end >= at the start (the last close at or before each hour)
        at = lambda ts: np.array([btc.iloc[btc.index.searchsorted(t, side="right") - 1] for t in ts])
        up = at(idx + pd.Timedelta(days=14)) >= at(idx)
        pi_up = up.mean()
        wf = w.copy()
        wf[up] = w[up] * pi_up / w[up].sum()
        wf[~up] = w[~up] * (1 - pi_up) / w[~up].sum()
        Rl = pw.loc[idx, "R_liq"].to_numpy(dtype=float)
        fmed = np.median(np.column_stack([field[n].loc[idx, "R_liq"].to_numpy(dtype=float) for n in FIELD]), axis=1)
        bars = {"LENIENT": np.where(up, LENIENT_UP, LENIENT_DOWN), "MIDDLE": np.full(len(idx), MIDDLE),
                "STRICT": np.maximum(STRICT_FLOOR, fmed)}
        hit = {b: float((wf.to_numpy() * (Rl >= v)).sum()) for b, v in bars.items()}
        head = (hit["LENIENT"] + hit["MIDDLE"] + hit["STRICT"]) / 3
        ok = Rl >= bars["LENIENT"]
        comp = pw.loc[idx, "FLOORED.V1.composite"].to_numpy(dtype=float)
        cs = float((wf.to_numpy()[ok] * comp[ok]).sum() / wf.to_numpy()[ok].sum()) if ok.any() else 0.0
        got = s["return_first"][pool]
        col = "w_final" if pool == "full" else "w_final_in_sample"
        d = {"pi_up": abs(pi_up - got["pi_up"]), "w'": float(np.abs(wf.to_numpy() - pw.loc[idx, col].to_numpy(dtype=float)).max()),
             **{f"HIT_{b}": abs(hit[b] - got["hit"][b]) for b in hit},
             "HEADLINE_RET": abs(head - got["headline_ret"]), "CS_HIT": abs(cs - got["cs_hit"])}
        worst = max(worst, max(d.values()))
        print(f"| {name} | {pool} ({len(idx)}) | {pi_up:.6f} | {hit['LENIENT']:.12f} | {hit['MIDDLE']:.12f} | {hit['STRICT']:.12f} | "
              f"{head:.12f} | {cs:.12f} | {max(d.values()):.1e} ({max(d, key=d.get)}) |")
print(f"\nlargest difference vs score.json: {worst:.2e} -> {'PASS' if worst <= 1e-12 else 'FAIL'} (limit 1e-12)")
