"""Report for research/baitoey/prereg/20261009-overlays.md: reads the published score2 artifacts and cached runs."""
import glob, json, os, sys
import numpy as np, pandas as pd
from backtest.data import load_market
from backtest.scoring.evaluate import simulate
from backtest.scoring.windows import pool_starts
from src.config import load_config
from src.models import get

ROOT = "/home/ubuntu/test/MiniMax/"
S2 = ROOT + "results/scoring/score2/603da2948b68ee0f5c8a/"
OUT = ROOT + "results/baitoey/20261009-overlays/"
BASES = {"e20": "pol_switch_vt_tl_e20v45", "dual": "baitoey_vt_dual"}
OVL = [("altbtc_a", "1a alts to BTC"), ("altbtc_b", "1b alts to cash"), ("brk", "2 breakdown exit"), ("evt", "3 event de-risk"), ("evtctl", "3 control (hourly, factor 1)")]
cfg = load_config(); m = load_market(cfg); pool = pool_starts(m, cfg); liq = float(cfg["scoring"]["liquidation_cost"])
cases = pd.read_parquet(ROOT + "results/book/20261009-weak-eval-v2/cases.parquet")
board = pd.read_csv(ROOT + "results/scoring/leaderboard_2.csv").set_index("model")
P = lambda v: f"{100 * v:+.2f}%"

def row(name):
    f = max(glob.glob(S2 + name + "/*/score.json"), key=os.path.getmtime)
    s = json.load(open(f)); a = s["activity"]
    run = simulate(get(name), m, cfg, pool, use_cache=True)
    r = {"name": name, "tool": s["tool_version"], "head": s["primary"]["headline"], "scr": s["period_check"]["SCREEN"],
         "con": s["period_check"]["CONFIRM"], "elig": s["eligible"],
         "gates": {k: (v["pass"], v.get("hard", False)) for k, v in s["gates"].items()},
         "turn": a["mean_turnover"], "fees": a["mean_fees_e0"] + a["mean_spread_e0"],
         "rank": board.loc[name, "rank"] if name in board.index else np.nan,
         "cons": board.loc[name, "selection_score"] if name in board.index else np.nan}
    for prof in ("weak_archived", "weak_fresh_btc"):
        st = cases.index[cases[prof]]; k = run.windows.index.get_indexer(st)
        E, G = run.equity[k].astype(float), run.gross[k].astype(float)
        for h in (216, 228, 240):
            x = E[:, h] * (1 - liq * G[:, h]) / E[:, 0] - 1
            r[(prof, h)] = (np.median(x), np.percentile(x, 10), np.percentile(x, 90))
    return r

names = list(BASES.values()) + [f"baitoey_ovl_{k}_{b}" for k, _ in OVL for b in BASES]
done = [n for n in names if glob.glob(S2 + n + "/*/score.json")]
R = {n: row(n) for n in done}
L = ["# Three overlays on e20v45 and vt_dual: results", "",
     "Pre-registration: `research/baitoey/prereg/20261009-overlays.md` (c35047e). Book's weak-market board, protocol "
     f"603da2948b68ee0f5c8a; tool version {R[BASES['e20']]['tool']} for every row. Rank = the board's experimental rank "
     f"among {int(board['rank'].max())} models (lower is better); conservative = the board's joint lower bound.", ""]
for b, bn in BASES.items():
    L += [f"## Base: {bn}", "",
          "| Model | Archived 228 h median / p10 / p90 | Fresh 228 h median / p10 / p90 | HEADLINE_RET | REL SCREEN / CONFIRM | Gates G1-G6 | Turnover / fees per round | Board rank (conservative) |",
          "|---|---|---|---|---|---|---|---|"]
    for n, lab in [(bn, "base")] + [(f"baitoey_ovl_{k}_{b}", l) for k, l in OVL]:
        if n not in R: L.append(f"| {lab} | not run yet | | | | | | |"); continue
        r = R[n]; g = r["gates"]; fails = [k for k, (ok, _) in g.items() if not ok]
        q = lambda prof: " / ".join(P(v) for v in r[(prof, 228)])
        L.append(f"| {lab} (`{n}`) | {q('weak_archived')} | {q('weak_fresh_btc')} | {r['head']:.3f} | {r['scr']:.3f} / {r['con']:.3f} | "
                 f"{'all pass' if not fails else 'FAIL ' + ', '.join(fails)} | {r['turn']:.2f} / {P(r['fees'])} | {r['rank']:.0f} ({P(r['cons'])}) |")
    L += ["", "9- and 10-day horizons (archived profile, median / p10 / p90):", "",
          "| Model | 216 h | 240 h |", "|---|---|---|"]
    for n, lab in [(bn, "base")] + [(f"baitoey_ovl_{k}_{b}", l) for k, l in OVL]:
        if n in R:
            L.append(f"| {lab} | {' / '.join(P(v) for v in R[n][('weak_archived', 216)])} | {' / '.join(P(v) for v in R[n][('weak_archived', 240)])} |")
    L += ["", "Reading rule (pre-registered): better than the base if archived 228 h median and p10 are both at least the base's, "
          "REL SCREEN and CONFIRM each at least the base's minus 0.05, and no hard gate fails that the base passes.", ""]
    base = R[bn]
    for k, lab in OVL:
        n = f"baitoey_ovl_{k}_{b}"
        if n not in R: continue
        def better(r, ref):
            ok = (r[("weak_archived", 228)][0] >= ref[("weak_archived", 228)][0] and r[("weak_archived", 228)][1] >= ref[("weak_archived", 228)][1]
                  and r["scr"] >= ref["scr"] - 0.05 and r["con"] >= ref["con"] - 0.05
                  and not any(h and not ok_ and ref["gates"].get(g, (False,))[0] for g, (ok_, h) in r["gates"].items()))
            return "**better**" if ok else "not better"
        line = f"- {lab}: {better(R[n], base)} than the base"
        ctl = f"baitoey_ovl_evtctl_{b}"
        if k == "evt" and ctl in R:
            line += f"; {better(R[n], R[ctl])} than its control"
        L.append(line + ".")
    L.append("")
open(OUT + "report.md", "w").write("\n".join(L) + "\n")
print("\n".join(L))
