"""Report for research/baitoey/prereg/20261010-e20-coin-shorts.md."""
import sys; sys.path.insert(0, "/home/ubuntu/test/MiniMax/.worktrees/baitoey-mom-ss")
import glob, json, os, importlib.util
import numpy as np, pandas as pd
from backtest.data import load_market
from backtest.scoring.evaluate import simulate
from backtest.scoring.windows import pool_starts
from src.config import load_config
from src.models import get
from src.models.baitoey._btc_short import run_short, switch_down_series
ROOT = "/home/ubuntu/test/MiniMax/"; S2 = ROOT + "results/scoring/score2/603da2948b68ee0f5c8a/"
cfg = load_config(); m = load_market(cfg); s = pool_starts(m, cfg); liq = float(cfg["scoring"]["liquidation_cost"])
cases = pd.read_parquet(ROOT + "results/book/20261009-weak-eval-v2/cases.parquet")
board = pd.read_csv(ROOT + "results/scoring/leaderboard_2.csv").set_index("model")
P = lambda v: f"{100*v:+.2f}%"
NAMES = [("pol_switch_vt_tl_e20v45", "e20v45 (live)"), ("baitoey_e20_btcs_c", "e20v45 + BTC short (C)"), ("baitoey_e20_shortc_eth", "e20v45 + ETH short (C)"),
         ("baitoey_e20_shortc_sol", "e20v45 + SOL short (C)"), ("baitoey_e20_shortc_alts", "e20v45 + 6-altcoin basket shorts (C)")]
R = {}
L = ["# e20v45 plus failed-rally shorts on other coins: results", "", "Pre-registration: `research/baitoey/prereg/20261010-e20-coin-shorts.md` (9dc8849).", "",
     "| Model | Weak 228 h median / p10 / p90 | All rounds median / p10 / p90 | HEADLINE / REL SCREEN / CONFIRM | Gates | Fees per round | Board rank (conservative) |",
     "|---|---|---|---|---|---|---|"]
for n, lab in NAMES:
    sj = json.load(open(max(glob.glob(S2 + n + "/*/score.json"), key=os.path.getmtime)))
    run = simulate(get(n), m, cfg, s, use_cache=True); E, G = run.equity.astype(float), run.gross.astype(float)
    Rw = E[:, -1] * (1 - liq * G[:, -1]) / E[:, 0] - 1
    k = run.windows.index.get_indexer(cases.index[cases.weak_archived]); w = E[k, 228] * (1 - liq * G[k, 228]) / E[k, 0] - 1
    a = sj["activity"]; fails = [g for g, v in sj["gates"].items() if not v["pass"]]
    R[n] = {"run": run, "weak": (np.median(w), np.percentile(w, 10), np.percentile(w, 90)), "scr": sj["period_check"]["SCREEN"], "con": sj["period_check"]["CONFIRM"],
            "hard": [g for g, v in sj["gates"].items() if not v["pass"] and v.get("hard")]}
    L.append(f"| {lab} | {' / '.join(P(q) for q in R[n]['weak'])} | {P(np.median(Rw))} / {P(np.percentile(Rw,10))} / {P(np.percentile(Rw,90))} | "
             f"{sj['primary']['headline']:.3f} / {sj['period_check']['SCREEN']:.3f} / {sj['period_check']['CONFIRM']:.3f} | {'all pass' if not fails else 'FAIL ' + ', '.join(fails)} | "
             f"{P(a['mean_fees_e0'] + a['mean_spread_e0'])} | {board['rank'].get(n, np.nan):.0f} ({P(board['selection_score'].get(n, np.nan))}) |")
b = R["pol_switch_vt_tl_e20v45"]
L += ["", "Better than e20v45 (pre-registered rule): weak median and p10 at least e20v45's, REL SCREEN and CONFIRM each >= e20v45's - 0.05, no hard gate fails.", ""]
for n, lab in NAMES[2:]:
    r = R[n]; ok = r["weak"][0] >= b["weak"][0] and r["weak"][1] >= b["weak"][1] and r["scr"] >= b["scr"] - 0.05 and r["con"] >= b["con"] - 0.05 and not r["hard"]
    L.append(f"- {lab}: {'**better**' if ok else 'not better'}.")
btc = m.close["BTCUSDT"].dropna(); sw = cfg["models"]["pol_switch_vt_tl_e20v45"]["switch"]
down = pd.Series(switch_down_series(btc, sw["ema_days"], float(sw["hysteresis"])), index=btc.index)
p = cfg["models"]["baitoey_e20_shortc_eth"]["short"]
L += ["", "Short trades while the switch reads down (2020-06 to 2026-09, after 0.3% round-trip costs):", "",
      "| Coin | Trades | Hit rate | Average | Worst | Squeeze +5% / +10% within 72 h |", "|---|---|---|---|---|---|"]
for coin in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
    c = m.close[coin].dropna(); x = c.to_numpy(float); d = down.reindex(c.index, method="ffill").fillna(True).to_numpy(bool)
    st = max(pd.Timestamp("2020-06-01", tz="UTC"), c.index[0] + pd.Timedelta(days=260))
    tr = [t for t in run_short(c, p, int(st.value), d) if t["x"] is not None and t["f"] is not None]
    ret = np.array([(t["entry"] - x[min(t["x"] + 1, len(x) - 1)]) / t["entry"] - 0.003 for t in tr])
    mx = np.array([np.max(x[t["f"] + 1:t["f"] + 73]) / t["entry"] - 1 for t in tr])
    L.append(f"| {coin.replace('USDT','')} | {len(tr)} | {100*(ret>0).mean():.0f}% | {P(ret.mean())} | {P(ret.min())} | {100*(mx>=0.05).mean():.0f}% / {100*(mx>=0.10).mean():.0f}% |")
os.chdir(ROOT)
spec = importlib.util.spec_from_file_location("pl", ROOT + "results/book/paper-live/paper_live.py"); pl = importlib.util.module_from_spec(spec); spec.loader.exec_module(pl)
mk = pl.load_market(cfg)
L += ["", "## This round on live prices (Book's replay engine, from cash at 4 Oct 12:00 UTC)", "", "| Model | This round | Shorts now |", "|---|---|---|"]
for n, lab in NAMES:
    r = pl.run_model(n, mk, cfg)
    sh = ", ".join(f"{k.replace('USDT','')} {100*v:+.0f}%" for k, v in r["w_end"].items() if v < 0) or "none"
    L.append(f"| {lab} | {P(r['E'][-1]/r['E'][0]-1)} (as of {pl.hk(r['at'][-1])} HKT) | {sh} |")
E0, G0 = b["run"].equity.astype(float), b["run"].gross.astype(float); st = b["run"].windows.index
D6, H = 144, 336; r6 = E0[:, D6] / E0[:, 0] - 1
b6 = m.close.BTCUSDT.reindex(st + pd.Timedelta(hours=D6)).to_numpy() / m.close.BTCUSDT.reindex(st).to_numpy() - 1
for L0 in (-0.066, -0.084):
    B = (np.abs(r6 - L0) <= 0.03) & (b6 >= -0.06) & (b6 <= 0)
    L += ["", f"## Recovery from {100*L0:+.1f}% on day 6 ({B.sum()} rounds like ours; the model's own last 8 days)", "",
          "| Last 8 days with | Bad (p10) | Median | Good (p90) | Finish >= 0% | Finish >= +1% | Finish <= -10% |", "|---|---|---|---|---|---|---|"]
    for n, lab in NAMES:
        E, G = R[n]["run"].equity.astype(float), R[n]["run"].gross.astype(float)
        tot = (1 + L0) * (E[B, H] * (1 - liq * G[B, H]) / E[B, D6]) - 1; q = np.percentile(tot, [10, 50, 90])
        L.append(f"| {lab} | {P(q[0])} | {P(q[1])} | {P(q[2])} | {100*(tot>=0).mean():.0f}% | {100*(tot>=0.01).mean():.0f}% | {100*(tot<=-0.10).mean():.0f}% |")
open(ROOT + "results/baitoey/20261010-coin-shorts/report.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))
