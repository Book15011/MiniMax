"""Volume-confirmed breakouts.

Enter a coin when its hourly close breaks above its highest close of the previous 72 hours while its last 24 hours of
quote volume are at least 1.5 times a normal day of the last week. Exit when it closes below its lowest close of the
previous 24 hours, or below a trailing stop two daily average true ranges under its highest close of the last 72
hours. Each position takes 1/k of the book; when more coins break out than slots are free, the strongest 7/14-day
risk-adjusted momentum goes first. The book is scaled down to a daily volatility target. Long only.
"""
from __future__ import annotations

import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey._volume_signals import (chandelier_exit, momentum_score, prior_high, prior_low,
                                                scale_to_daily_vol, volume_ratio)


class VolumeBreakout:
    spec = ModelSpec(name="baitoey_breakout", method="momentum", author="baitoey", rebalance_hours=24, band=0.05,
                     description="Volume-confirmed 72h breakouts; exit on a 24h low or a 2-ATR trailing stop; "
                                 "1/k slots, book volatility-capped")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        lbs = [int(d) for d in p["lookback_days"]]
        need = max(max(lbs) * 24, p["vol_days"] * 24, p["volume_long_days"] * 24 + p["volume_short_hours"],
                   (p["atr_days"] + 1) * 24, p["breakout_hours"] + 1) + 1
        close, qv = view.tail(need)
        ok = (close.notna().sum() >= p["min_history_days"] * 24) & close.iloc[-1].notna()
        for d in lbs:
            ok &= close.iloc[-1 - d * 24].notna()
        close, qv = close.loc[:, ok], qv.loc[:, ok]
        if close.shape[1] == 0:
            return pd.Series(dtype=float)

        last = close.iloc[-1]
        ratio = volume_ratio(qv, p["volume_short_hours"], p["volume_long_days"]).iloc[-1]
        entry = (last > prior_high(close, p["breakout_hours"]).iloc[-1]) & (ratio > p["entry_volume_ratio"])
        stop = (last < prior_low(close, p["exit_low_hours"]).iloc[-1]) | chandelier_exit(
            close, p["trail_hours"], p["atr_days"], p["atr_mult"])

        held = [c for c, w in view.prev_targets.items() if w > 0 and c in close.columns and not stop[c]]
        for c in momentum_score(close, lbs).sort_values(ascending=False).index:
            if len(held) >= p["k"]:
                break
            if entry[c] and c not in held:
                held.append(c)
        if not held:
            return pd.Series(dtype=float)
        w = pd.Series(1.0 / p["k"], index=sorted(held))
        return scale_to_daily_vol(w, close, p["vol_days"], p["target_daily_vol"])


MODEL = VolumeBreakout()
