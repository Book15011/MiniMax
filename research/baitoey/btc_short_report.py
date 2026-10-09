"""Report for research/baitoey/prereg/20261009-btc-short.md (reads published score2 artifacts and cached runs)."""
import glob, json, os
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
VAR = {"a": "A trend", "b": "B breakdown", "c": "C failed rally", "d": "D trend + funding"}
c = m.close["BTCUSDT"].dropna(); x = c.to_numpy(float)
sw = cfg["models"]["pol_switch_vt_tl_e20v45"]["switch"]
down = switch_down_series(c, sw["ema_days"], float(sw["hysteresis"]))
def row(name):
    f = max(glob.glob(S2 + name + "/*/score.json"), key=os.path.getmtime); sj = json.load(open(f))
    run = simulate(get(name), m, cfg, s, use_cache=True); E, G = run.equity.astype(float), run.gross.astype(float)
    R = E[:, -1] * (1 - liq * G[:, -1]) / E[:, 0] - 1
    k = run.windows.index.get_indexer(cases.index[cases.weak_archived]); w = E[k, 228] * (1 - liq * G[k, 228]) / E[k, 0] - 1
    a = sj["activity"]; fails = [g for g, v in sj["gates"].items() if not v["pass"]]
    return {"run": run, "head": sj["primary"]["headline"], "scr": sj["period_check"]["SCREEN"], "con": sj["period_check"]["CONFIRM"],
            "hard": [g for g, v in sj["gates"].items() if not v["pass"] and v.get("hard")], "fails": fails,
            "turn": a["mean_turnover"], "fees": a["mean_fees_e0"] + a["mean_spread_e0"],
            "weak": (np.median(w), np.percentile(w, 10), np.percentile(w, 90)), "all": (np.median(R), np.percentile(R, 10), np.percentile(R, 90)),
            "rank": board["rank"].get(name, np.nan), "cons": board["selection_score"].get(name, np.nan)}
def trades(p, switch):
    tr = run_short(c, p, int(pd.Timestamp("2020-06-01", tz="UTC").value), switch)
    out = []
    for t in tr:
        if t["x"] is None or t["f"] is None: continue
        e = t["entry"]; ex = x[min(t["x"] + 1, len(x) - 1)]
        out.append({"ret": (e - ex) / e - 0.003, "hours": t["x"] - t["f"], "squeeze": bool(np.max(x[t["f"] + 1:t["f"] + 73]) >= e * 1.05), "why": t["reason"]})
    return pd.DataFrame(out)
L = ["# BTC-only short sleeve and e20v45 add-ons: results", "", "Pre-registration: `research/baitoey/prereg/20261009-btc-short.md` (bc348ed).", "",
     "## Standalone (BTC short 40% or cash)", "",
     "| Variant | Weak 228 h median / p10 / p90 | All windows median / p10 / p90 | HEADLINE / REL SCREEN / CONFIRM | Gates | Fees per round | Board rank |",
     "|---|---|---|---|---|---|---|"]
R = {}
for v, lab in VAR.items():
    n = f"baitoey_btc_short_{v}"; r = R[n] = row(n)
    L.append(f"| {lab} | {' / '.join(P(q) for q in r['weak'])} | {' / '.join(P(q) for q in r['all'])} | {r['head']:.3f} / {r['scr']:.3f} / {r['con']:.3f} | "
             f"{'all pass' if not r['fails'] else 'FAIL ' + ', '.join(r['fails'])} | {P(r['fees'])} | {r['rank']:.0f} ({P(r['cons'])}) |")
L += ["", "Trades 2020-06 to 2026-09 (model's own replay; after 0.3% round-trip costs):", "",
      "| Variant | Trades | Hit rate | Average | Worst trade | Squeeze rate (BTC +5% within 72 h) | Average hours held | Exits (stop / time / cover) |", "|---|---|---|---|---|---|---|---|"]
p0 = cfg["models"]["baitoey_btc_short_a"]
for v, lab in VAR.items():
    T = trades({**p0, "variant": v}, None); wc = T.why.value_counts()
    L.append(f"| {lab} | {len(T)} | {100*(T.ret>0).mean():.0f}% | {P(T.ret.mean())} | {P(T.ret.min())} | {100*T['squeeze'].mean():.0f}% | {T.hours.mean():.0f} | "
             f"{wc.get('stop',0)} / {wc.get('time',0)} / {wc.get('cover',0)} |")
L += ["", "## Add-on to e20v45 (short only while its switch reads down)", "",
      "| Model | Weak 228 h median / p10 / p90 | All windows median / p10 / p90 | HEADLINE / REL SCREEN / CONFIRM | Gates | Fees per round | Board rank |", "|---|---|---|---|---|---|---|"]
for n, lab in [("pol_switch_vt_tl_e20v45", "e20v45 (base)"), ("baitoey_ovl_evtctl_e20", "e20v45 decided hourly (context: the hourly-wrapper effect)")] + [(f"baitoey_e20_btcs_{v}", f"e20v45 + {VAR[v]}") for v in VAR]:
    r = R[n] = row(n)
    L.append(f"| {lab} | {' / '.join(P(q) for q in r['weak'])} | {' / '.join(P(q) for q in r['all'])} | {r['head']:.3f} / {r['scr']:.3f} / {r['con']:.3f} | "
             f"{'all pass' if not r['fails'] else 'FAIL ' + ', '.join(r['fails'])} | {P(r['fees'])} | {r['rank']:.0f} ({P(r['cons'])}) |")
L += ["", "Add-on trades (2020-06 to 2026-09):", "", "| Add-on | Trades | Hit rate | Worst trade | Squeeze rate |", "|---|---|---|---|---|"]
for v, lab in VAR.items():
    T = trades({**p0, "variant": v}, down)
    L.append(f"| e20v45 + {lab} | {len(T)} | {100*(T.ret>0).mean():.0f}% | {P(T.ret.min()) if len(T) else '-'} | {100*T['squeeze'].mean():.0f}% |" if len(T) else f"| e20v45 + {lab} | 0 | - | - | - |")
b = R["pol_switch_vt_tl_e20v45"]
L += ["", "Reading rule (pre-registered): an add-on is better if its weak 228 h median and p10 are both at least e20v45's, REL SCREEN and CONFIRM each at least e20v45's minus 0.05, and no hard gate fails.", ""]
for v, lab in VAR.items():
    r = R[f"baitoey_e20_btcs_{v}"]
    ok = r["weak"][0] >= b["weak"][0] and r["weak"][1] >= b["weak"][1] and r["scr"] >= b["scr"] - 0.05 and r["con"] >= b["con"] - 0.05 and not r["hard"]
    L.append(f"- e20v45 + {lab}: {'**better**' if ok else 'not better'} than e20v45.")
# from our situation: e20 for 5 days, then the add-on (same holdings path, e20 until day 5 is identical except when the add-on's short was already on)
D, H = 120, 336
E0, G0, st = b["run"].equity.astype(float), b["run"].gross.astype(float), b["run"].windows.index
r5 = E0[:, D] / E0[:, 0] - 1; btc = m.close.BTCUSDT
b5 = btc.reindex(st + pd.Timedelta(hours=D)).to_numpy() / btc.reindex(st).to_numpy() - 1
B = (r5 <= -0.054) & (r5 >= -0.114) & (b5 >= -0.06) & (b5 <= 0)
L += ["", f"## From our situation ({B.sum()} rounds: e20v45 down 5.4-11.4% on day 5, BTC 0 to -6%; the add-on's last 9 days of the same round; our -8.4% applied)", "",
      "| Last 9 days with | Bad (p10) | Median | Good (p90) | Finish >= +1% | Finish <= -15% |", "|---|---|---|---|---|---|"]
for n, lab in [("pol_switch_vt_tl_e20v45", "e20v45")] + [(f"baitoey_e20_btcs_{v}", f"e20v45 + {VAR[v]}") for v in VAR]:
    E, G = R[n]["run"].equity.astype(float), R[n]["run"].gross.astype(float)
    rest = E[B, H] * (1 - liq * G[B, H]) / E[B, D] - 1
    tot = 0.916 * (1 + rest) - 1; q = np.percentile(tot, [10, 50, 90])
    L.append(f"| {lab} | {P(q[0])} | {P(q[1])} | {P(q[2])} | {100*(tot>=0.01).mean():.0f}% | {100*(tot<=-0.15).mean():.0f}% |")
out = ROOT + "results/baitoey/20261009-btc-short/report.md"; open(out, "w").write("\n".join(L) + "\n"); print("\n".join(L))
