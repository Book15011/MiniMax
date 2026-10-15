"""EXPERIMENTAL / report-only: which book gives the best chance of a large 72 h gain (the top-20 gate push).

Each candidate runs as one continuous hourly path on the harness panel (2022 -> 2026-09-30), long only, cost 0.15%
per unit of weight traded (fee plus about half a spread). Every 72 h window, starting every 6 h, is scored by its
compounded return. Reported: P(>= +16%), P(>= +20%), P(>= +25%), P(<= -10%), median, worst; on 2022-2024 (where the
settings are chosen), on 2025-2026 (the check), and on the weak-market cases like now
(results/book/20261009-weak-eval-v2/cases.parquet).

Candidates:
  mom  L k R      top k coins by L-hour return, equal weight, rebalanced every R hours (16:00 UTC grid)
  brk  N t h k    breakout: a coin closing above its N-hour high with 24 h volume above its 7-day average is bought
                  (strongest first, at most k coins, 1/k each); sold on a t trailing stop or after h hours
  beta            top 5 by 30-day hourly volatility, daily
  rebound         the 3 biggest 7-day losers, daily
  btc             BTC only
  live            book_e20combo_brk_cash's own daily targets (results/book/cloneall/paths), held between decisions

    PYTHONPATH=. python research/book/gate/gate_odds.py
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from backtest.data import load_market
from src.config import REPO_ROOT, load_config

MAIN = REPO_ROOT.parents[1] if REPO_ROOT.parent.name == ".worktrees" else REPO_ROOT
COST, H, STEP = 0.0015, 72, 6
START = pd.Timestamp("2022-01-01", tz="UTC")
SPLIT = pd.Timestamp("2025-01-01", tz="UTC")

cfg = load_config()
mk = load_market(cfg)
close = mk.close.loc[START - pd.Timedelta(days=40):]
qv = mk.quote_volume.reindex_like(close)
idx = close.index
coins = list(close.columns)
ret = (close / close.shift(1) - 1).fillna(0.0).clip(-0.5, 1.0).to_numpy()
# universe membership by hour (the harness's daily point-in-time universe, carried forward)
ub = mk.universe_by_day
U = np.zeros(close.shape, dtype=bool)
pos = ub.index.searchsorted(idx, side="right") - 1
col = {c: j for j, c in enumerate(coins)}
for i, p in enumerate(pos):
    if p >= 0:
        for c in ub.iloc[p]:
            if c in col:
                U[i, col[c]] = True
U &= close.notna().to_numpy()


def run_weights(W: np.ndarray) -> np.ndarray:
    """Hourly portfolio returns for target weights W (set at each hour, NaN = keep), costs on changes."""
    out = np.zeros(len(idx))
    w = np.zeros(len(coins))
    for i in range(1, len(idx)):
        out[i] = float(w @ ret[i])
        if out[i] != 0.0:                                        # drift: weights move with prices
            g = w * (1 + ret[i])
            s = 1 + out[i]
            w = g / s
        tgt = W[i]
        if not np.isnan(tgt).all():
            out[i] -= COST * float(np.abs(tgt - w).sum())
            w = tgt
    return out


def grid_hours(every: int) -> np.ndarray:
    return ((idx.hour - 16) % 24 % every == 0) if every < 24 else (idx.hour == 16)


def ranked(score: pd.DataFrame, k: int, every: int, largest: bool = True) -> np.ndarray:
    S = score.to_numpy()
    W = np.full(close.shape, np.nan)
    for i in np.flatnonzero(grid_hours(every)):
        s = np.where(U[i] & np.isfinite(S[i]), S[i], np.nan)
        ok = np.flatnonzero(np.isfinite(s))
        W[i] = 0.0
        if len(ok) >= k:
            pick = ok[np.argsort(-s[ok] if largest else s[ok])[:k]]
            W[i, pick] = 1.0 / k
    return run_weights(W)


def breakout(n: int, trail: float, hold: int, k: int) -> np.ndarray:
    hi = close.shift(1).rolling(n, min_periods=n).max().to_numpy()
    c = close.to_numpy()
    v24 = qv.rolling(24, min_periods=24).sum().to_numpy()
    v7 = (qv.rolling(168, min_periods=168).sum() / 7).to_numpy()
    sig = U & (c > hi) & (v24 > v7)
    strength = np.where(sig, c / hi - 1, np.nan)
    out = np.zeros(len(idx))
    held: dict[int, list] = {}                                   # coin -> [entry hour, peak]
    for i in range(1, len(idx)):
        r = sum(ret[i, j] for j in held) / k if held else 0.0
        out[i] = r
        cost = 0.0
        for j in list(held):
            held[j][1] = max(held[j][1], c[i, j]) if np.isfinite(c[i, j]) else held[j][1]
            if (np.isfinite(c[i, j]) and c[i, j] <= held[j][1] * (1 - trail)) or i - held[j][0] >= hold:
                del held[j]
                cost += COST / k
        free = k - len(held)
        if free > 0:
            s = strength[i]
            cand = [j for j in np.argsort(-np.nan_to_num(s, nan=-1.0)) if np.isfinite(s[j]) and j not in held][:free]
            for j in cand:
                held[j] = [i, c[i, j]]
                cost += COST / k
        out[i] -= cost
    return out


def live_book() -> np.ndarray:
    tg = pd.read_parquet(MAIN / "results/book/cloneall/paths/book_e20combo_brk_cash.parquet")
    tg = tg.reindex(columns=coins).fillna(0.0)
    W = np.full(close.shape, np.nan)
    at = idx.get_indexer(tg.index)
    for i, row in zip(at, tg.to_numpy()):
        if i >= 0:
            W[i] = np.clip(row, 0.0, None)
    return run_weights(W)


def windows(r: np.ndarray) -> pd.Series:
    lg = np.log1p(np.clip(r, -0.99, None)).cumsum()
    s = pd.Series(lg, index=idx)
    starts = s.index[(s.index >= START) & (s.index.hour % STEP == 0)]
    starts = starts[starts <= s.index[-1] - pd.Timedelta(hours=H)]
    end = s.reindex(starts + pd.Timedelta(hours=H)).to_numpy()
    return pd.Series(np.expm1(end - s.reindex(starts).to_numpy()), index=starts)


def stats(w: pd.Series) -> dict:
    return {"n": len(w), "p16": (w >= 0.16).mean(), "p20": (w >= 0.20).mean(), "p25": (w >= 0.25).mean(),
            "p_m10": (w <= -0.10).mean(), "median": w.median(), "worst": w.min()}


cases = pd.read_parquet(MAIN / "results/book/20261009-weak-eval-v2/cases.parquet")
like_now = cases.index[cases.weak_archived | cases.weak_fresh_btc]

def btc_only() -> np.ndarray:
    W = np.full(close.shape, np.nan)
    W[1] = 0.0
    W[1, coins.index("BTCUSDT")] = 1.0
    return run_weights(W)


cands: dict[str, callable] = {"btc": btc_only}
cands["live"] = live_book
for L, k, R in itertools.product([24, 72, 168], [1, 2, 3], [4, 24]):
    cands[f"mom L{L} k{k} R{R}"] = (lambda L=L, k=k, R=R: ranked(close / close.shift(L) - 1, k, R))
vol30 = (close / close.shift(1)).apply(np.log).rolling(720, min_periods=600).std()
cands["beta top5"] = lambda: ranked(vol30, 5, 24)
cands["rebound 3"] = lambda: ranked(close / close.shift(168) - 1, 3, 24, largest=False)
for n, t, h, k in itertools.product([24, 72], [0.04, 0.08], [24, 48], [1, 3]):
    cands[f"brk N{n} t{int(t * 100)} h{h} k{k}"] = (lambda n=n, t=t, h=h, k=k: breakout(n, t, h, k))

rows = []
for name, f in cands.items():
    w = windows(f())
    tr, te = w[w.index < SPLIT], w[w.index >= SPLIT]
    ln = w.reindex(like_now).dropna()
    rows.append({"candidate": name, **{f"train_{a}": b for a, b in stats(tr).items()},
                 **{f"test_{a}": b for a, b in stats(te).items()}, **{f"now_{a}": b for a, b in stats(ln).items()}})
    print("done", name, flush=True)
d = pd.DataFrame(rows).set_index("candidate")
out = MAIN / "results/book/gate"
out.mkdir(parents=True, exist_ok=True)
d.to_csv(out / "gate_odds.csv")
pct = lambda x: f"{100 * x:.0f}%"
d = d.sort_values("train_p20", ascending=False)
print("\n| Candidate | Train P(>=+20%) | Test P(>=+16%) | Test P(>=+20%) | Test P(>=+25%) | Test P(<=-10%) | Test median | Test worst | Like-now P(>=+16%) (n) | Like-now median |")
print("|---|---|---|---|---|---|---|---|---|---|")
for name, r in list(d.iterrows())[:15] + [(n, d.loc[n]) for n in ("live", "btc") if n in d.index]:
    print(f"| {name} | {pct(r.train_p20)} | {pct(r.test_p16)} | {pct(r.test_p20)} | {pct(r.test_p25)} | {pct(r.test_p_m10)} | "
          f"{100 * r.test_median:+.1f}% | {100 * r.test_worst:+.1f}% | {pct(r.now_p16)} ({int(r.now_n)}) | {100 * r.now_median:+.1f}% |")
