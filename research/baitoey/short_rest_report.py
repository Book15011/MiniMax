"""Report for research/baitoey/prereg/20261012-short-models-rest-of-round.md (independent rest-of-round test)."""
import sys; sys.path.insert(0, "/home/ubuntu/test/MiniMax/.worktrees/baitoey-mom-ss")
import json, os
import numpy as np, pandas as pd
from backtest.data import load_market
from src.config import load_config

ROOT = "/home/ubuntu/test/MiniMax/"; CACHE = ROOT + "results/scoring/cache/"
OUT = ROOT + ".worktrees/baitoey-mom-ss/research/baitoey/results/20261012-short-rest-of-round/"
LIVE, CASH, BTCH = "pol_switch_vt_tl_e20v45", "team_cash", "team_btc_hold"
D0, HE, L0, BTC0, BAND, COST, SEED, NB = 186, 336, -0.0284, -0.0153, 0.03, 0.002, 20261012, 10000
RANKED = ["book_short_shock_fade", "book_short_volume_fade", "book_short_range_fail", "book_short_ridge6", "book_bear_pullback",
          "book_short_analogue12", "book_bear_breakdown", "book_short_analogue6", "book_bear_cost_guard", "book_bear_guard",
          "book_bear_trend_control", "book_bear_trail_exit", "book_bear_fast_exit"]
EXCLUDED = lambda n: (n.startswith(("book_pooled_", "book_cloneall_", "book_e20clone_")) or n in ("book_daily_channel", "book_clone_ourcoins"))

cfg = load_config(); m = load_market(cfg); liq = float(cfg["scoring"]["liquidation_cost"])
board = pd.read_csv(ROOT + "results/scoring/leaderboard_2.csv").set_index("model")
names = [n for n in board.index if not EXCLUDED(n)]
excluded = [n for n in board.index if EXCLUDED(n)]

def load(n):
    k = board.loc[n, "run_key"]; meta = json.load(open(f"{CACHE}{n}/{k}.json"))
    z = np.load(f"{CACHE}{n}/{k}.arrays.npz"); st = pd.DatetimeIndex(pd.read_parquet(f"{CACHE}{n}/{k}.windows.parquet").index)
    return meta, z["equity"].astype(float), z["gross"].astype(float), z["net"].astype(float), st

meta, E0, G0, _, st = load(LIVE)
btc = m.close["BTCUSDT"]; b = lambda h: btc.reindex(st + pd.Timedelta(hours=h)).to_numpy()
r_live = E0[:, D0] / E0[:, 0] - 1; b_d0 = b(D0) / b(0) - 1; b_rest = b(HE) / b(D0) - 1
similar = (np.abs(r_live - L0) <= BAND) & (np.abs(b_d0 - BTC0) <= BAND)
cases = pd.read_parquet(ROOT + "results/book/20261009-weak-eval-v2/cases.parquet")
cp = pd.DatetimeIndex(cases.index[cases.weak_archived | cases.weak_fresh_btc])
rest0, rest1 = st + pd.Timedelta(hours=D0), st + pd.Timedelta(hours=HE)
overlap = np.zeros(len(st), bool)
for c in cp:
    overlap |= (rest0 < c + pd.Timedelta(hours=228)) & (rest1 > c)
primary = similar & ~overlap
fallback = primary.sum() < 40
if fallback:
    primary = similar.copy()

R, info = {}, {}
for n in names:
    try:
        mt, E, G, N, s = load(n)
    except Exception as e:
        info[n] = {"skip": f"cache unreadable: {e}"}; continue
    if mt.get("tool_version") != "3036a0d8bfdaa6a0" or len(s) != len(st) or not (s == st).all():
        info[n] = {"skip": "different windows or tool version"}; continue
    r = E[:, HE] * (1 - liq * G[:, HE]) / E[:, D0] - 1
    R[n] = r if n == LIVE else (1 + r) * (1 - COST) - 1
    R[n + "|nocost"] = r
    info[n] = {"shorts": bool((N < -1e-3).any())}

def group(n):
    if n in (LIVE, CASH, BTCH): return "reference"
    if n in RANKED: return "A ranked short"
    if "e20" in n: return "C e20v45 + add-on"
    return "B short or long/short" if info[n].get("shorts") else "D other"

tested = [n for n in names if n in R and n != LIVE]
k = len(tested)
rng = np.random.default_rng(SEED)

def evaluate(mask):
    mon = st[mask].strftime("%Y-%m"); um, mi = np.unique(mon, return_inverse=True)
    cnt = np.bincount(mi, minlength=len(um)).astype(float)
    idx = rng.integers(0, len(um), size=(NB, len(um))); W = np.zeros((NB, len(um)))
    np.add.at(W, (np.arange(NB)[:, None], idx), 1.0)
    base = R[LIVE][mask]; rows = []
    for n in [LIVE] + tested:
        x = R[n][mask]; d = x - base
        S = np.bincount(mi, weights=d, minlength=len(um)); boot = (W @ S) / (W @ cnt)
        fin = (1 + L0) * (1 + x) - 1; br = b_rest[mask]
        rows.append({"model": n, "group": group(n), "headline": board.loc[n, "original_headline_ret"],
                     "hard_fail": str(board.loc[n, "failed_hard_gates"]) not in ("", "nan", "[]", "None"),
                     "mean_R": x.mean(), "median_R": np.median(x), "p10_R": np.percentile(x, 10), "p90_R": np.percentile(x, 90),
                     "mean_d": d.mean(), "median_d": np.median(d), "d_lo90": np.percentile(boot, 10), "p_one_sided": float((boot <= 0).mean()),
                     "mean_d_nocost": (R[n + "|nocost"][mask] - base).mean(),
                     "finish_ge0": (fin >= 0).mean(), "finish_med": np.median(fin), "finish_le_m10": (fin <= -0.10).mean(),
                     "R_btc_down": np.median(x[br <= -0.02]) if (br <= -0.02).any() else np.nan,
                     "R_btc_flat": np.median(x[np.abs(br) < 0.02]) if (np.abs(br) < 0.02).any() else np.nan,
                     "R_btc_up": np.median(x[br >= 0.02]) if (br >= 0.02).any() else np.nan})
    T = pd.DataFrame(rows).set_index("model"); p10_live = T.loc[LIVE, "p10_R"]
    ok = (T.median_d >= 0) & (T.p10_R >= p10_live - 0.01) & ~T.hard_fail
    T["better"] = ok & (T.p_one_sided <= 0.10 / k); T["promising"] = ok & (T.p_one_sided <= 0.10) & ~T.better
    T.loc[LIVE, ["better", "promising"]] = False
    return T, len(um)

P, nm_p = evaluate(primary); S2, nm_s = evaluate(similar)
os.makedirs(OUT, exist_ok=True)
P.to_csv(OUT + "primary.csv", float_format="%.6f"); S2.to_csv(OUT + "all_similar.csv", float_format="%.6f")

pc = lambda v: "-" if pd.isna(v) else f"{100*v:+.2f}%"
pp = lambda v: f"{100*v:.0f}%"
def table(T, rows, extra_sec=None):
    L = ["| Model | Group | Rest of round: mean / median / p10 | vs e20v45: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for n in rows:
        r = T.loc[n]; v = "current" if n == LIVE else ("**better**" if r.better else ("promising" if r.promising else "no"))
        L.append(f"| {n} | {r.group} | {pc(r.mean_R)} / {pc(r.median_R)} / {pc(r.p10_R)} | {pc(r.mean_d)} ({pc(r.d_lo90)}) | {r.p_one_sided:.3f} | "
                 f"{pp(r.finish_ge0)} | {pc(r.finish_med)} | {pc(r.R_btc_down)} / {pc(r.R_btc_flat)} / {pc(r.R_btc_up)} | {r.headline:.3f} | {v} |")
    return L

L = ["# Short models against e20v45 over the rest of this round: independent test", "",
     f"Pre-registration: `research/baitoey/prereg/20261012-short-models-rest-of-round.md` (3c5bdd8). Start: round hour {D0} (2026-10-12 06:00 UTC), "
     f"e20v45 at {pc(L0)} on Book's live-price replay (EC2 account UNVERIFIED), BTC {pc(BTC0)} since the round start, 150 hours left.", "",
     f"- Similar past rounds: **{int(similar.sum())}** of {len(st)}, in {nm_s} calendar months.",
     f"- Primary sample (rest of round does not overlap Book's 50 weak-market cases): **{int(primary.sum())}** rounds in {nm_p} months"
     + (" (fewer than 40, so the pre-registered fallback to all similar rounds applies)" if fallback else "") + ".",
     f"- Models tested against e20v45: **{k}**; Bonferroni threshold p <= {0.10/k:.4f}. Excluded (reference log, AGENTS rule 7 question): {len(excluded)}.",
     f"- Switching cost 0.20% for every model except e20v45. Final account = (1 {pc(L0)})(1 + R) - 1.", ""]
better = [n for n in P.index if P.loc[n, "better"]]; prom = [n for n in P.index if P.loc[n, "promising"]]
L += ["## Verdict (primary sample)", "", f"- Better than e20v45: **{', '.join(better) if better else 'none'}**.",
      f"- Promising, not proven: {', '.join(prom) if prom else 'none'}.", ""]
L += ["## A. Book's 13 ranked short models", ""] + table(P, [LIVE] + [n for n in RANKED if n in P.index]) + [""]
for g in ["C e20v45 + add-on", "B short or long/short", "D other"]:
    rows = P[P.group == g].sort_values("mean_d", ascending=False)
    L += [f"## {g} (top 10 of {len(rows)} by mean d)", ""] + table(P, [LIVE] + list(rows.index[:10])) + [""]
L += ["## References", ""] + table(P, [LIVE, CASH, BTCH]) + [""]
L += ["## Top 10 overall by mean d", ""] + table(P, [LIVE] + list(P.drop(LIVE).sort_values("mean_d", ascending=False).index[:10])) + [""]
L += ["## Context: all similar rounds (secondary sample)", "",
      f"Better: {', '.join(n for n in S2.index if S2.loc[n, 'better']) or 'none'}. Promising: {', '.join(n for n in S2.index if S2.loc[n, 'promising']) or 'none'}.", ""]
L += table(S2, [LIVE] + [n for n in RANKED if n in S2.index] + list(S2.drop([LIVE] + RANKED, errors='ignore').sort_values('mean_d', ascending=False).index[:5])) + [""]
skips = {n: v["skip"] for n, v in info.items() if "skip" in v}
L += ["## Notes", "", f"- Skipped: {skips if skips else 'none'}.",
      "- Rounds that start on consecutive days overlap, so the effective sample is far smaller than the round count; the bootstrap resamples whole calendar months for that reason.",
      "- Full tables: `primary.csv`, `all_similar.csv` in this folder.", ""]
open(OUT + "report.md", "w").write("\n".join(L)); print("\n".join(L))
