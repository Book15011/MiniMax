"""Report for research/baitoey/prereg/20261009-faster-down-switch.md."""
import sys; sys.path.insert(0, "/home/ubuntu/test/MiniMax/.worktrees/baitoey-mom-ss")
import glob, json, os, importlib.util
import numpy as np, pandas as pd
from backtest.data import load_market
from backtest.scoring.evaluate import simulate
from backtest.scoring.windows import pool_starts
from src.config import load_config
from src.models import get
ROOT = "/home/ubuntu/test/MiniMax/"; S2 = ROOT + "results/scoring/score2/603da2948b68ee0f5c8a/"
NAMES = [("pol_switch_vt_tl_e20v45", "e20 (down at -3%)"), ("baitoey_e20_out15", "down at -1.5%"), ("baitoey_e20_out10", "down at -1%")]
cfg = load_config(); m = load_market(cfg); s = pool_starts(m, cfg); liq = float(cfg["scoring"]["liquidation_cost"])
cases = pd.read_parquet(ROOT + "results/book/20261009-weak-eval-v2/cases.parquet")
board = pd.read_csv(ROOT + "results/scoring/leaderboard_2.csv").set_index("model")
P = lambda v: f"{100*v:+.2f}%"
runs = {n: simulate(get(n), m, cfg, s, use_cache=True) for n, _ in NAMES}
st = runs["pol_switch_vt_tl_e20v45"].windows.index
L = ["# Faster down switch for e20v45: results", "", "Pre-registration: `research/baitoey/prereg/20261009-faster-down-switch.md`.", "",
     "| Model | Archived 228 h median / p10 / p90 | Fresh 228 h median / p10 / p90 | HEADLINE_RET | REL SCREEN / CONFIRM | Gates | Turnover / fees | Board rank (conservative) |",
     "|---|---|---|---|---|---|---|---|"]
R = {}
for n, lab in NAMES:
    sj = json.load(open(max(glob.glob(S2 + n + "/*/score.json"), key=os.path.getmtime)))
    E, G = runs[n].equity.astype(float), runs[n].gross.astype(float)
    q = {}
    for prof in ("weak_archived", "weak_fresh_btc"):
        k = runs[n].windows.index.get_indexer(cases.index[cases[prof]])
        x = E[k, 228] * (1 - liq * G[k, 228]) / E[k, 0] - 1; q[prof] = (np.median(x), np.percentile(x, 10), np.percentile(x, 90))
    a = sj["activity"]; fails = [g for g, v in sj["gates"].items() if not v["pass"]]
    hard_fail = [g for g, v in sj["gates"].items() if not v["pass"] and v.get("hard")]
    R[n] = {"q": q, "scr": sj["period_check"]["SCREEN"], "con": sj["period_check"]["CONFIRM"], "hard": hard_fail}
    L.append(f"| {lab} (`{n}`) | {' / '.join(P(v) for v in q['weak_archived'])} | {' / '.join(P(v) for v in q['weak_fresh_btc'])} | "
             f"{sj['primary']['headline']:.3f} | {sj['period_check']['SCREEN']:.3f} / {sj['period_check']['CONFIRM']:.3f} | "
             f"{'all pass' if not fails else 'FAIL ' + ', '.join(fails)} | {a['mean_turnover']:.2f} / {P(a['mean_fees_e0'] + a['mean_spread_e0'])} | "
             f"{board.loc[n, 'rank']:.0f} ({P(board.loc[n, 'selection_score'])}) |")
b = R["pol_switch_vt_tl_e20v45"]
L += ["", "Reading rule (pre-registered): better if archived 228 h median and p10 both at least e20's, REL SCREEN and CONFIRM each at least e20's minus 0.05, and no hard gate fails.", ""]
for n, lab in NAMES[1:]:
    r = R[n]
    ok = (r["q"]["weak_archived"][0] >= b["q"]["weak_archived"][0] and r["q"]["weak_archived"][1] >= b["q"]["weak_archived"][1]
          and r["scr"] >= b["scr"] - 0.05 and r["con"] >= b["con"] - 0.05 and not r["hard"])
    L.append(f"- {lab}: {'**better**' if ok else 'not better'} than e20.")
D, H, SELL = 120, 336, 0.0015
E0, G0 = runs["pol_switch_vt_tl_e20v45"].equity.astype(float), runs["pol_switch_vt_tl_e20v45"].gross.astype(float)
later = st + pd.Timedelta(hours=D); ok = later.isin(st); j = st.get_indexer(later)
r5 = E0[:, D] / E0[:, 0] - 1; btc = m.close.BTCUSDT; b5 = btc.reindex(later).to_numpy() / btc.reindex(st).to_numpy() - 1
B = ok & (r5 <= -0.054) & (r5 >= -0.114) & (b5 >= -0.06) & (b5 <= 0)
L += ["", f"## From our situation ({B.sum()} past rounds: e20 down 5.4-11.4% on day 5, BTC 0 to -6%; our -8.4% applied)", "",
      "| Last 9 days with | Bad (p10) | Median | Good (p90) | Finish >= +1% | Finish <= -15% |", "|---|---|---|---|---|---|"]
for n, lab in NAMES:
    if n == "pol_switch_vt_tl_e20v45":
        rest = E0[B, H] * (1 - liq * G0[B, H]) / E0[B, D] - 1
    else:
        E, G = runs[n].equity.astype(float), runs[n].gross.astype(float); jj = j[B]
        rest = (1 - G0[B, D] * SELL) * (E[jj, H - D] * (1 - liq * G[jj, H - D]) / E[jj, 0]) - 1
    tot = 0.916 * (1 + rest) - 1; qq = np.percentile(tot, [10, 50, 90])
    L.append(f"| {lab} | {P(qq[0])} | {P(qq[1])} | {P(qq[2])} | {100*(tot>=0.01).mean():.0f}% | {100*(tot<=-0.15).mean():.0f}% |")
os.chdir(ROOT)
spec = importlib.util.spec_from_file_location("pl", ROOT + "results/book/paper-live/paper_live.py"); pl = importlib.util.module_from_spec(spec); spec.loader.exec_module(pl)
mk = pl.load_market(cfg)
L += ["", "## This round on live prices (Book's replay engine, from cash at 4 Oct 12:00 UTC)", "", "| Model | This round | Holdings now |", "|---|---|---|"]
for n, lab in NAMES:
    r = pl.run_model(n, mk, cfg)
    held = ", ".join(f"{k.replace('USDT','')} {100*v:+.0f}%" for k, v in sorted(r["w_end"].items(), key=lambda x: -abs(x[1])))
    L.append(f"| {lab} | {P(r['E'][-1]/r['E'][0]-1)} (as of {pl.hk(r['at'][-1])} HKT) | {held} |")
out = ROOT + "results/baitoey/20261009-fast-down/report.md"
open(out, "w").write("\n".join(L) + "\n"); print("\n".join(L))
