"""Backtest engine: model decisions -> hourly equity of one 14-day window started from cash.

Timeline (all UTC, bars indexed by close time):
- A decision taken at bar t uses data up to and including bar t, and trades at the close of bar t + lag.
- A window starting at t0 is all cash at the close of t0; its first trade is at t0 + lag.
- Between decisions nothing trades except the activity guard: if an HKT day (24 h from the window start)
  has no trade by `guard_offset_hours` into the day, the engine rebalances exactly to the standing target.
- Gross exposure never exceeds 100% after a trade. A band-limited rebalance can leave drifted holdings
  above target while buying new ones in full; then, as src/execution/planner.py does live, reductions
  happen in full and the increases are scaled down together to fit (fit_gross).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from backtest.data import Market, universe_at
from src.contracts import MarketView, Model, check_targets


@dataclass(frozen=True)
class Costs:
    taker: float = 0.001   # market orders on the long side
    short: float = 0.001   # opening or closing a short (0.1% either way on Roostoo)


@dataclass
class WindowResult:
    equity: np.ndarray       # hourly equity, length hours + 1, starts at 1.0
    active_days: int         # HKT days with at least one trade
    turnover: float          # sum of |weight change| over the window
    fees: float              # fees + spread paid, as a fraction of equity (summed)
    max_orders_day: int      # most coins traded in a single HKT day
    max_gross: float         # largest sum |w| right after a trade
    trace: dict | None = None  # only with run(..., trace=True); see Simulator.run


def fit_gross(w: np.ndarray, new: np.ndarray, cap: float = 1.0) -> np.ndarray:
    """Weights `new`, with the increases scaled down so that sum |weights| <= cap.

    Reductions, exits and the closing leg of a flip are kept in full (they free cash); every increase in |w|
    (new coins, adds, the opening leg of a flip) is scaled by one common factor, like the planner's buys."""
    if np.abs(new).sum() <= cap + 1e-12:
        return new
    same = np.sign(new) == np.sign(w)
    kept = np.where(same, np.where(np.abs(new) < np.abs(w), new, w), 0.0)
    add = new - kept
    need = float(np.abs(add).sum())
    room = max(0.0, cap - float(np.abs(kept).sum()))
    return kept + add * min(1.0, room / need) if need > 0 else kept


def decision_times(index: pd.DatetimeIndex, every_h: int, anchor_hour: int,
                   start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    sel = index[(index >= start) & (index <= end)]
    return sel[((sel.hour - anchor_hour) % every_h) == 0]


def compute_targets(model: Model, market: Market, times: pd.DatetimeIndex, params: dict) -> pd.DataFrame:
    """Run the model at every decision time on a view truncated at that time. Rows = times, cols = all series."""
    close, qv = market.close, market.quote_volume
    pos = close.index.get_indexer(times)
    if (pos < 0).any():
        raise ValueError("decision times must be bar close times present in the panel")
    rows, prev = [], pd.Series(dtype=float)
    for t, i in zip(times, pos):
        view = MarketView(t=t, close=close.iloc[: i + 1], quote_volume=qv.iloc[: i + 1],
                          universe=universe_at(market, t), params=params, prev_targets=prev)
        w = check_targets(model.targets(view), view, model.spec)
        rows.append(w)
        prev = w
    out = pd.DataFrame(rows, index=times, dtype=float)
    return out.reindex(columns=close.columns).fillna(0.0)


class Simulator:
    """Numpy views of prices and standing targets, for fast repeated window runs."""

    def __init__(self, market: Market, targets: pd.DataFrame, band: float, costs: Costs,
                 lag_hours: int = 1, anchor_hour: int = 16, guard_offset_hours: int = 20):
        active = targets.columns[(targets != 0).any()]
        self.cols = list(active) if len(active) else [market.close.columns[0]]
        idx = market.close.index
        self.index = idx
        px = market.close[self.cols].ffill()
        self.R = px.pct_change(fill_method=None).fillna(0.0).to_numpy()
        tg = targets[self.cols]
        dec = idx.get_indexer(tg.index)
        if (dec < 0).any():
            raise ValueError("target times must be panel bar times")
        self.is_dec = np.zeros(len(idx), dtype=bool)
        self.is_dec[dec] = True
        standing = np.full((len(idx), len(self.cols)), np.nan)
        standing[dec] = tg.to_numpy()
        standing = pd.DataFrame(standing).ffill().fillna(0.0).to_numpy()
        self.T = standing
        self.half = market.half_spread.reindex(self.cols).fillna(float(market.half_spread.median())).to_numpy()
        self.band, self.costs, self.lag = band, costs, lag_hours
        self.guard = guard_offset_hours

    def _trade(self, w: np.ndarray, tgt: np.ndarray, exact: bool) -> tuple[np.ndarray, float, float, int]:
        d = tgt - w
        if not exact:
            keep = (np.abs(d) > self.band) | ((tgt == 0.0) & (w != 0.0))
            d = np.where(keep, d, 0.0)
        new = fit_gross(w, w + d)
        d = new - w
        moved = np.abs(d) > 1e-12
        if not moved.any():
            return w, 0.0, 0.0, 0
        long_vol = np.abs(np.maximum(new, 0.0) - np.maximum(w, 0.0))
        short_vol = np.abs(np.minimum(new, 0.0) - np.minimum(w, 0.0))
        cost = float(long_vol.sum() * self.costs.taker + short_vol.sum() * self.costs.short
                     + np.abs(d) @ self.half)
        # fees are taken from the book pro rata, so weights relative to the new equity equal `new` (gross stays <= 1)
        return new, float(np.abs(d).sum()), cost, int(moved.sum())

    def run(self, i0: int, hours: int, trace: bool = False) -> WindowResult:
        """trace=True also returns, for the scoring layer (backtest/scoring), the hourly gross and net exposure,
        every trade (hour, kind, weights before and after, equity before, cost), which days had a strategy trade
        and which had a guard trade. It never changes the result. A guard hour that is also a decision hour
        counts as a strategy trade if the decision alone would have traded."""
        if i0 + hours >= len(self.index):
            raise ValueError("window runs past the end of the data")
        n_days = hours // 24
        w = np.zeros(len(self.cols))
        eq = 1.0
        E = np.empty(hours + 1)
        E[0] = 1.0
        traded = np.zeros(n_days, dtype=bool)
        orders = np.zeros(n_days, dtype=int)
        turnover = fees = max_gross = 0.0
        tr = None
        if trace:
            tr = {"cols": self.cols, "gross": np.zeros(hours + 1), "net": np.zeros(hours + 1), "trades": [],
                  "strategy_day": np.zeros(n_days, dtype=bool), "guard_day": np.zeros(n_days, dtype=bool)}
        for h in range(1, hours + 1):
            i = i0 + h
            r = self.R[i]
            pr = float(w @ r)
            if pr != 0.0:
                eq *= 1.0 + pr
                w = w * (1.0 + r) / (1.0 + pr)
            j = i - self.lag
            day = min((h - 1) // 24, n_days - 1)
            first = h == 1
            guard = (not traded[day]) and ((h - 1) % 24 == self.guard)
            if first or guard or self.is_dec[j]:
                w0 = w
                w, tv, cost, n = self._trade(w, self.T[j], exact=first or guard)
                if n:
                    if tr is not None:
                        by_guard = guard and not (self.is_dec[j] and self._trade(w0, self.T[j], exact=False)[3])
                        tr["trades"].append((h, "entry" if first else "guard" if by_guard else "decision",
                                             w0, w, eq, cost))
                        tr["guard_day" if by_guard else "strategy_day"][day] = True
                    eq *= 1.0 - cost
                    turnover += tv
                    fees += cost
                    traded[day] = True
                    orders[day] += n
                    max_gross = max(max_gross, float(np.abs(w).sum()))
            E[h] = eq
            if tr is not None:
                tr["gross"][h], tr["net"][h] = float(np.abs(w).sum()), float(w.sum())
        if tr is not None:
            tr["w_end"] = w
        return WindowResult(E, int(traded.sum()), turnover, fees, int(orders.max()), max_gross, tr)
