"""Exploratory (2026-10-10, thresholds fixed before results): which models make money steadily in 14-day rounds.
Steady positive round: final return (liquidated) > 0, never more than 3% below its running peak (hourly), and at
least 8 of the 14 daily returns (24 h steps from the start) positive. Other positive rounds: bounce / burst."""
import numpy as np, pandas as pd
from backtest.data import load_market
from backtest.scoring.evaluate import simulate
from backtest.scoring.windows import pool_starts
from src.config import load_config
from src.models import get
cfg = load_config(); m = load_market(cfg); s = pool_starts(m, cfg); liq = float(cfg["scoring"]["liquidation_cost"])
board = pd.read_csv("/home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.csv")
cases = pd.read_parquet("/home/ubuntu/test/MiniMax/results/book/20261009-weak-eval-v2/cases.parquet")
weak = cases.index[cases.weak_archived | cases.weak_fresh_btc]
rows = []
for n in board.model:
    try:
        r = simulate(get(n), m, cfg, s, use_cache=True)
    except (Exception, SystemExit):
        continue
    E, G = r.equity.astype(float), r.gross.astype(float)
    R = E[:, -1] * (1 - liq * G[:, -1]) / E[:, 0] - 1
    mdd = 1 - (E / np.maximum.accumulate(E, axis=1)).min(axis=1)
    d = E[:, ::24]; dr = d[:, 1:] / d[:, :-1] - 1
    up = (dr > 0).sum(axis=1)
    steady = (R > 0) & (mdd <= 0.03) & (up >= 8)
    burst = (R > 0) & ~steady
    wk = r.windows.index.isin(weak)
    rows.append({"model": n, "steady": steady.mean(), "burst": burst.mean(), "neg": (R <= 0).mean(),
                 "steady_med": np.median(R[steady]) if steady.any() else np.nan, "burst_med": np.median(R[burst]) if burst.any() else np.nan,
                 "median": np.median(R), "p10": np.percentile(R, 10), "mdd_med": np.median(mdd),
                 "steady_weak": steady[wk].mean() if wk.any() else np.nan, "neg_weak": (R[wk] <= 0).mean() if wk.any() else np.nan})
    print(n, flush=True)
X = pd.DataFrame(rows).set_index("model"); X.to_csv("/home/ubuntu/test/MiniMax/results/baitoey/20261010-steady/steady.csv")
P = lambda v: f"{100*v:+.1f}%" if pd.notna(v) else "-"
def table(Y, title):
    print(f"\n{title}")
    print(f"{'model':30s} {'steady +':>8s} {'bounce +':>8s} {'negative':>8s} {'steady med':>10s} {'bounce med':>10s} {'all med':>8s} {'p10':>7s} {'typ. MDD':>8s} {'steady in weak':>14s}")
    for n, r in Y.iterrows():
        print(f"{n:30s} {100*r.steady:7.0f}% {100*r.burst:7.0f}% {100*r.neg:7.0f}% {P(r.steady_med):>10s} {P(r.burst_med):>10s} {P(r['median']):>8s} {P(r.p10):>7s} {100*r.mdd_med:7.1f}% {100*r.steady_weak:13.0f}%")
table(X.sort_values("steady", ascending=False).head(20), "TOP 20 by share of rounds that were steady and positive")
keep = ["pol_switch_vt_tl_e20v45", "baitoey_vt_dual", "baitoey_vt_mom", "book_orch", "baitoey_mr_4h", "pol_mr_cap", "pol_trend_ls", "team_btc_hold", "team_cash", "baitoey_mjt_24_96_d"]
table(X.loc[[k for k in keep if k in X.index]], "Reference models")
