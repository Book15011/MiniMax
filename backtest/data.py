"""Market data for the harness: the hourly panel and point-in-time universe written by src.validation.build."""
from __future__ import annotations

import glob
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import binance_symbol, resolve, universe
from src.data.panel import HourlyPanel


@dataclass
class Market:
    close: pd.DataFrame          # hourly closes, index = bar close time (UTC), columns = series ids
    quote_volume: pd.DataFrame
    universe_by_day: pd.Series   # index = daily grid time (UTC), value = tuple of series ids tradable from then on
    half_spread: pd.Series       # fraction of price paid on each trade (half the bid-ask spread), by series id
    notes: dict = field(default_factory=dict)


def universe_at(market: Market, t: pd.Timestamp) -> tuple[str, ...]:
    """Universe of the latest grid time at or before t (empty before the first grid time)."""
    idx = market.universe_by_day.index
    pos = idx.searchsorted(t, side="right") - 1
    return market.universe_by_day.iloc[pos] if pos >= 0 else ()


def spreads_from_snapshot(pattern: str, default_bps: float) -> tuple[pd.Series, str]:
    """Half-spreads by series id from the newest saved Roostoo ticker; unknown ids get the default later."""
    files = sorted(glob.glob(str(resolve(pattern))))
    if not files:
        return pd.Series(dtype=float), "none (default for every coin)"
    data = json.loads(Path(files[-1]).read_text())
    data = data.get("Data", data)
    out = {}
    for pair, q in data.items():
        bid, ask = q.get("MaxBid") or 0.0, q.get("MinAsk") or 0.0
        if bid > 0 and ask > bid:
            out[binance_symbol(pair)] = (ask - bid) / ((ask + bid) / 2) / 2
    return pd.Series(out, dtype=float), Path(files[-1]).name


def universe_from_panel(close: pd.DataFrame, qv: pd.DataFrame, top_n: int = 30, min_history_days: int = 90,
                        volume_days: int = 30, hour: int = 16) -> pd.Series:
    """Point-in-time top-N by trailing quote volume. Used for synthetic test data; production uses the
    universe written by src.validation.build."""
    grid = close.index[close.index.hour == hour]
    exists = close.notna()
    hist = exists.cumsum()
    vol = qv.fillna(0.0).rolling(volume_days * 24, min_periods=1).sum()
    out = {}
    for t in grid:
        ok = (hist.loc[t] >= min_history_days * 24) & exists.loc[t]
        ranked = vol.loc[t][ok].sort_values(ascending=False)
        out[t] = tuple(sorted(ranked.index[:top_n]))
    return pd.Series(out)


def load_market(cfg: dict) -> Market:
    h = cfg["harness"]
    pdir = resolve(h["panel_dir"])
    panel = HourlyPanel.load(pdir)
    uni = pd.read_parquet(pdir / "universe.parquet")
    by_day = uni.groupby("t")["series"].apply(lambda s: tuple(sorted(s)))
    mode = h["universe"]
    if mode == "roostoo":
        allowed = {binance_symbol(p) for p in universe(cfg)}
        by_day = by_day.apply(lambda ids: tuple(i for i in ids if i in allowed))
    elif mode != "broad":
        raise ValueError("harness.universe must be 'roostoo' or 'broad'")
    spreads, source = spreads_from_snapshot(h["spreads_snapshot_glob"], h["default_half_spread_bps"])
    half = pd.Series(h["default_half_spread_bps"] / 1e4, index=panel.close.columns)
    half.update(spreads.reindex(half.index).dropna())
    notes = {"panel_first": str(panel.close.index[0]), "panel_last": str(panel.close.index[-1]),
             "n_series": int(panel.close.shape[1]), "universe_mode": mode, "spreads_source": source,
             "median_half_spread_bps": float(np.median(half.to_numpy()) * 1e4),
             "universe_first_day": str(by_day.index[0]), "universe_last_day": str(by_day.index[-1])}
    return Market(panel.close, panel.quote_volume, by_day, half, notes)
