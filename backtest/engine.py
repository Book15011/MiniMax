"""Backtest engine: model decisions -> hourly equity of one 14-day window started from cash.

Timeline (all UTC, bars indexed by close time):
- A decision taken at bar t uses data up to and including bar t, and trades at the close of bar t + lag.
- A window starting at t0 is all cash at the close of t0; its first trade is at t0 + lag.
- Between decisions nothing trades except the activity guard: if an HKT day (24 h from the window start)
  has no trade by `guard_offset_hours` into the day, the engine rebalances exactly to the standing target.
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
        moved = np.abs(d) > 1e-12
        if not moved.any():
            return w, 0.0, 0.0, 0
        new = w + d
        long_vol = np.abs(np.maximum(new, 0.0) - np.maximum(w, 0.0))
        short_vol = np.abs(np.minimum(new, 0.0) - np.minimum(w, 0.0))
        cost = float(long_vol.sum() * self.costs.taker + short_vol.sum() * self.costs.short
                     + np.abs(d) @ self.half)
        # fees are taken from the book pro rata, so weights relative to the new equity equal `new` (gross stays <= 1)
        return new, float(np.abs(d).sum()), cost, int(moved.sum())

    def run(self, i0: int, hours: int) -> WindowResult:
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
                w, tv, cost, n = self._trade(w, self.T[j], exact=first or guard)
                if n:
                    eq *= 1.0 - cost
                    turnover += tv
                    fees += cost
                    traded[day] = True
                    orders[day] += n
                    max_gross = max(max_gross, float(np.abs(w).sum()))
            E[h] = eq
        return WindowResult(E, int(traded.sum()), turnover, fees, int(orders.max()), max_gross)
