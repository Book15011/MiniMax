"""Volume readings shared by the pol volume models (reports/review/20261002-volume.md). Views only: rows up to view.t."""
from __future__ import annotations

from src.contracts import MarketView


def market_volume_ratio(view: MarketView, short_h: int, long_days: int, min_coins: int) -> float | None:
    """Total quote volume of the universe over the last short_h hours, over its average for the same length across the
    last long_days. Coins with any missing hour in the window are left out; None if fewer than min_coins remain
    (then the caller does not act on it)."""
    _, qv = view.tail(long_days * 24)
    if len(qv) < long_days * 24:
        return None
    full = qv.columns[qv.notna().all().to_numpy()]
    if len(full) < min_coins:
        return None
    total = qv[full].sum(axis=1)
    base = float(total.sum()) * short_h / len(total)
    return float(total.iloc[-short_h:].sum()) / base if base > 0 else None
