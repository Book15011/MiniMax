"""Report for research/baitoey/prereg/20261010-majors-trend.md."""
import sys; sys.path.insert(0, "/home/ubuntu/test/MiniMax/.worktrees/baitoey-mom-ss")
import glob, json, os, importlib.util
import numpy as np, pandas as pd
from backtest.data import load_market
from backtest.scoring.evaluate import simulate
from backtest.scoring.windows import pool_starts
from src.config import load_config
from src.models import get
ROOT = "/home/ubuntu/test/MiniMax/"; S2 = ROOT + "results/scoring/score2/603da2948b68ee0f5c8a/"
cfg = load_config(); m = load_market(cfg); s = pool_starts(m, cfg); liq = float(cfg["scoring"]["liquidation_cost"])
cases = pd.read_parquet(ROOT + "results/book/20261009-weak-eval-v2/cases.parquet")
board = pd.read_csv(ROOT + "results/scoring/leaderboard_2.csv").set_index("model")
P = lambda v: f"{100*v:+.2f}%"
VAR = [f"baitoey_mjt_{a}_{b}_{c}" for a, b in (("06", "24"), ("12", "48"), ("24", "96")) for c in ("d", "6h")]
lab = lambda n: ("EMA " + n.split("_")[2].lstrip("0") + "/" + n.split("_")[3] + (" daily" if n.endswith("_d") else " 6-hourly")) if "mjt" in n else "e20v45 (live)"
R = {}
for n in ["pol_switch_vt_tl_e20v45"] + VAR:
    sj = json.load(open(max(glob.glob(S2 + n + "/*/score.json"), key=os.path.getmtime)))
    run = simulate(get(n), m, cfg, s, use_cache=True); E, G = run.equity.astype(float), run.gross.astype(float)
    Rw = E[:, -1] * (1 - liq * G[:, -1]) / E[:, 0] - 1
    k = run.windows.index.get_indexer(cases.index[cases.weak_archived]); w = E[k, 228] * (1 - liq * G[k, 228]) / E[k, 0] - 1
    a = sj["activity"]
    R[n] = {"run": run, "head": sj["primary"]["headline"], "scr": sj["period_check"]["SCREEN"], "con": sj["period_check"]["CONFIRM"],
            "hard": [g for g, v in sj["gates"].items() if not v["pass"] and v.get("hard")], "fails": [g for g, v in sj["gates"].items() if not v["pass"]],
            "fees": a["mean_fees_e0"] + a["mean_spread_e0"], "turn": a["mean_turnover"], "weak": (np.median(w), np.percentile(w, 10), np.percentile(w, 90)),
            "all": (np.median(Rw), np.percentile(Rw, 10), np.percentile(Rw, 90)), "rank": board["rank"].get(n, np.nan), "cons": board["selection_score"].get(n, np.nan)}
L = ["# Fast large-cap trend long/short: results", "", "Pre-registration: `research/baitoey/prereg/20261010-majors-trend.md` (df48129). "
     f"Public reference: Pol's EMA 8/24 version scored 0.304 (reports/review/20261003-ext-baselines.md). Board: {int(board['rank'].max())} models.", "",
     "| Model | Weak 228 h median / p10 / p90 | All rounds median / p10 / p90 | HEADLINE / REL SCREEN / CONFIRM | Gates | Turnover / fees per round | Board rank (conservative) |",
     "|---|---|---|---|---|---|---|"]
for n in ["pol_switch_vt_tl_e20v45"] + VAR:
    r = R[n]
    L.append(f"| {lab(n)} | {' / '.join(P(q) for q in r['weak'])} | {' / '.join(P(q) for q in r['all'])} | {r['head']:.3f} / {r['scr']:.3f} / {r['con']:.3f} | "
             f"{'all pass' if not r['fails'] else 'FAIL ' + ', '.join(r['fails'])} | {r['turn']:.2f} / {P(r['fees'])} | {r['rank']:.0f} ({P(r['cons'])}) |")
e = R["pol_switch_vt_tl_e20v45"]
L += ["", "Worth a forward paper test (pre-registered): conservative score above e20v45's, REL SCREEN and CONFIRM >= 1.0, no hard gate fails.", ""]
for n in VAR:
    r = R[n]; ok = r["cons"] > e["cons"] and r["scr"] >= 1.0 and r["con"] >= 1.0 and not r["hard"]
    L.append(f"- {lab(n)}: {'**worth a paper test**' if ok else 'no'}.")
# this round on live prices
os.chdir(ROOT)
spec = importlib.util.spec_from_file_location("pl", ROOT + "results/book/paper-live/paper_live.py"); pl = importlib.util.module_from_spec(spec); spec.loader.exec_module(pl)
mk = pl.load_market(cfg)
L += ["", "## This round on live prices (Book's replay engine, from cash at 4 Oct 12:00 UTC)", "", "| Model | This round | Holdings now |", "|---|---|---|"]
for n in ["pol_switch_vt_tl_e20v45"] + VAR:
    r = pl.run_model(n, mk, cfg)
    held = ", ".join(f"{k.replace('USDT','')} {100*v:+.0f}%" for k, v in sorted(r["w_end"].items(), key=lambda z: -abs(z[1]))) or "cash"
    L.append(f"| {lab(n)} | {P(r['E'][-1]/r['E'][0]-1)} (as of {pl.hk(r['at'][-1])} HKT) | {held} |")
# recovery from day 6
D6, H = 144, 336
E0, G0, st = e["run"].equity.astype(float), e["run"].gross.astype(float), e["run"].windows.index
later = st + pd.Timedelta(hours=D6); ok = later.isin(st); j = st.get_indexer(later)
r6 = E0[:, D6] / E0[:, 0] - 1; btc = m.close.BTCUSDT
b6 = btc.reindex(later).to_numpy() / btc.reindex(st).to_numpy() - 1
for Lstart in (-0.084, -0.116):
    B = ok & (np.abs(r6 - Lstart) <= 0.03) & (b6 >= -0.06) & (b6 <= 0)
    L += ["", f"## Recovery for the rest of the round, starting at {100*Lstart:+.1f}% on day 6 ({B.sum()} past rounds within 3 points, BTC 0 to -6%; last 8 days)", "",
          "| Last 8 days with | Bad (p10) | Median | Good (p90) | Finish >= +1% | Finish <= -15% |", "|---|---|---|---|---|---|"]
    rest_e = E0[B, H] * (1 - liq * G0[B, H]) / E0[B, D6] - 1
    def put(name, rest):
        tot = (1 + Lstart) * (1 + rest) - 1; q = np.percentile(tot, [10, 50, 90])
        L.append(f"| {name} | {P(q[0])} | {P(q[1])} | {P(q[2])} | {100*(tot>=0.01).mean():.0f}% | {100*(tot<=-0.15).mean():.0f}% |")
    put("stay with e20v45", rest_e)
    re_e = E0[B, D6:H + 1]; ge = G0[B, H]
    for n in VAR:
        E, G = R[n]["run"].equity.astype(float), R[n]["run"].gross.astype(float); jj = j[B]
        put(f"switch to {lab(n)}", (1 - G0[B, D6] * 0.0015) * (E[jj, H - D6] * (1 - liq * G[jj, H - D6]) / E[jj, 0]) - 1)
        rv = E[jj, :H - D6 + 1]
        mix = 0.7 * (re_e[:, 1:] / re_e[:, :-1] - 1) + 0.3 * (rv[:, 1:] / rv[:, :-1] - 1)
        put(f"70% e20v45 + 30% {lab(n)}", np.prod(1 + mix, axis=1) * (1 - liq * (0.7 * ge + 0.3 * G[jj, H - D6])) * (1 - 0.3 * G0[B, D6] * 0.0015) - 1)
out = ROOT + "results/baitoey/20261010-majors-trend/report.md"; open(out, "w").write("\n".join(L) + "\n"); print("\n".join(L))
