"""Mean reversion on Bollinger Bands and RSI, long only.

On bars of bar_hours: buy a coin whose close is below its lower Bollinger band (20-bar mean minus 2 standard
deviations) while its 14-bar RSI is below 30, betting that it returns to the mean. Sell when the close is back at or
above the 20-bar mean, or when no buy signal has occurred for max_hold_hours (the bounce did not come). Each position
takes 1/k of the book; when more coins qualify than slots are free, the most oversold (lowest RSI) goes first. The
book is scaled down to a daily volatility target.
"""
from __future__ import annotations

import math

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey._bar_signals import bollinger, rsi, sample_bars
from src.models.baitoey._volume_signals import scale_to_daily_vol


class BollingerRsiReversion:
    spec = ModelSpec(name="baitoey_mr_bbrsi", method="trend", author="baitoey", rebalance_hours=24, band=0.05,
                     description="Long-only mean reversion: buy below the lower Bollinger band with RSI < 30, sell "
                                 "at the 20-bar mean or after a time stop; 1/k slots, book volatility-capped")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        bh = int(p["bar_hours"])
        hold_bars = math.ceil(p["max_hold_hours"] / bh)
        n_bars = max(p["bb_bars"], p["rsi_bars"] + 1) + hold_bars + 1
        close, _ = view.tail(max((n_bars - 1) * bh + 1, p["vol_days"] * 24 + 1))
        ok = (close.notna().sum() >= p["min_history_days"] * 24) & close.iloc[-1].notna()
        close = close.loc[:, ok]
        if close.shape[1] == 0:
            return pd.Series(dtype=float)

        bars = sample_bars(close, bh, n_bars)
        mid, lower = bollinger(bars, p["bb_bars"], p["bb_k"])
        r = rsi(bars, p["rsi_bars"])
        signal = (bars < lower) & (r < p["rsi_entry"])
        recent = signal.iloc[-(hold_bars + 1):].any()
        done = (bars.iloc[-1] >= mid.iloc[-1]) | ~recent

        held = [c for c, w in view.prev_targets.items() if w > 0 and c in bars.columns and not done[c]]
        now = signal.iloc[-1]
        for c in r.iloc[-1][now[now].index].sort_values().index:
            if len(held) >= p["k"]:
                break
            if c not in held:
                held.append(c)
        if not held:
            return pd.Series(dtype=float)
        w = pd.Series(1.0 / p["k"], index=sorted(held))
        return scale_to_daily_vol(w, close, p["vol_days"], p["target_daily_vol"])


MODEL = BollingerRsiReversion()
