"""Per-coin attribution of a scored run (reports/review/20261003-prereg-orch-v2.md: K8 in section 4, and section 5.1).

From a run's trade log (window_start, hour, series, w_before, w_after, fee_usd, spread_usd) and the hourly closes,
each window is replayed as the engine runs it: every hour the book earns w . r on the clock grid (a gap hour earns
0 and its move lands on the next bar), weights drift, and then the hour's trades set the traded coins' weights and
cost their fees and spread. So each coin's contribution is Σ equity x weight x the coin's hourly return minus the
costs of its trades, in units of E0, and the contributions add up to the window's R (checked).

Positions: a coin's position opens when its weight leaves 0 (or changes sign) and closes when it returns to 0 or
flips; one still open at the window's end closes there. Per position: side, hours held and P&L after costs.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def returns_grid(close: pd.DataFrame) -> tuple[pd.DatetimeIndex, list[str], np.ndarray]:
    """The engine's hourly returns: every clock hour, prices carried over gaps, 0 in a gap hour."""
    idx = pd.date_range(close.index[0], close.index[-1], freq="h")
    px = close.reindex(idx).ffill()
    return idx, list(close.columns), px.pct_change(fill_method=None).fillna(0.0).to_numpy()


def attribute(trades: pd.DataFrame, starts, close: pd.DataFrame, hours: int = 336, e0: float = 1e5):
    """(contributions, positions, check): per (window, coin) P&L in E0 units; one row per position; per window the
    replayed R. Only coins that trade in a window can hold a weight in it (every window starts from cash)."""
    idx, cols, R = returns_grid(close)
    col = {c: j for j, c in enumerate(cols)}
    tr = trades.copy()
    tr["window_start"] = pd.to_datetime(tr.window_start, utc=True)
    by_w = dict(tuple(tr.groupby("window_start")))
    contrib, positions, check = [], [], []
    for s in pd.DatetimeIndex(starts):
        t = by_w.get(s)
        i0 = idx.get_loc(s)
        if t is None or t.empty:
            check.append({"window_start": s, "R_replay": 0.0})
            continue
        coins = sorted(t.series.unique())
        J = np.array([col[c] for c in coins])
        w = np.zeros(len(coins))
        pnl = np.zeros(len(coins))
        eq = 1.0
        pos_c = {c: k for k, c in enumerate(coins)}
        by_h = {h: g for h, g in t.groupby("hour")}
        open_ = {}                                              # coin -> [side, open hour, pnl at open]
        for h in range(1, hours + 1):
            r = R[i0 + h, J]
            pr = float(w @ r)
            pnl += eq * w * r
            if pr != 0.0:
                eq *= 1.0 + pr
                w = w * (1.0 + r) / (1.0 + pr)
            g = by_h.get(h)
            if g is None:
                continue
            cost = 0.0
            for row in g.itertuples(index=False):
                k = pos_c[row.series]
                c_usd = (row.fee_usd + row.spread_usd) / e0
                pnl[k] -= c_usd
                cost += c_usd
                before, after = w[k], float(row.w_after)
                w[k] = after
                side_b, side_a = np.sign(before), np.sign(after)
                if row.series in open_ and side_a != open_[row.series][0]:
                    sd, oh, p0 = open_.pop(row.series)
                    positions.append({"window_start": s, "coin": row.series, "side": int(sd), "open_hour": oh,
                                      "close_hour": h, "pnl": float(pnl[k] - p0)})
                if side_a != 0 and row.series not in open_:
                    open_[row.series] = [side_a, h, float(pnl[k] + (c_usd if side_b != side_a else 0.0))]
            eq -= cost
        for c, (sd, oh, p0) in open_.items():
            positions.append({"window_start": s, "coin": c, "side": int(sd), "open_hour": oh, "close_hour": hours,
                              "pnl": float(pnl[pos_c[c]] - p0)})
        contrib += [{"window_start": s, "coin": c, "pnl": float(pnl[k])} for c, k in pos_c.items()]
        check.append({"window_start": s, "R_replay": eq - 1.0})
    pos = pd.DataFrame(positions)
    if len(pos):
        pos["hours"] = pos.close_hour - pos.open_hour
    return pd.DataFrame(contrib), pos, pd.DataFrame(check).set_index("window_start")


def single_coin_loss(contrib: pd.DataFrame, R: pd.Series, share: float = 0.4) -> pd.Series:
    """K8, per window: True when R < 0 and the worst coin's loss exceeds `share` of the summed losses of all coins
    that lost in that window."""
    c = contrib.pivot_table(index="window_start", columns="coin", values="pnl", aggfunc="sum").reindex(R.index)
    losses = (-c.clip(upper=0.0)).fillna(0.0)
    tot = losses.sum(axis=1)
    worst = losses.max(axis=1)
    return (R < 0) & (tot > 0) & (worst > share * tot)
