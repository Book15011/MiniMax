"""Trend-gated momentum.

A BTC trend gate sets how much of the book is "risk on": exposure ramps smoothly with BTC's distance
above its slow moving average and with the fast/slow average spread, instead of switching all-or-nothing,
so choppy markets don't whipsaw the whole book. The risk-on part holds the few liquid coins with the best
risk-adjusted 1-3 day momentum whose trading volume is above normal, weighted by inverse volatility,
capped per coin and scaled to a daily volatility target. The risk-off part runs a small short sleeve on
the weakest falling coins (or, long-only, a small BTC position), so the bot keeps trading every day.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.contracts import MarketView, ModelSpec

HOURS_PER_YEAR = 24 * 365
BTC = "BTCUSDT"


def _ramp(x: float, width: float) -> float:
    return float(np.clip(x / width + 0.5, 0.0, 1.0))


class TrendGatedMomentum:
    spec = ModelSpec(name="baitoey_tg_mom", method="momentum", author="baitoey", rebalance_hours=24, band=0.03,
                     uses_shorts=True,
                     description="BTC-trend-gated top-k momentum with a volume filter, inverse-vol weights, "
                                 "vol target; risk-off slice goes to a small short sleeve")

    def gate(self, view: MarketView) -> float:
        p = view.params
        if BTC not in view.close.columns:
            return 0.0
        btc = view.close[BTC].iloc[-p["gate_slow_hours"]:].dropna()
        if len(btc) < p["gate_slow_hours"] * 0.9:
            return 0.0
        slow, fast, last = btc.mean(), btc.iloc[-p["gate_fast_hours"]:].mean(), btc.iloc[-1]
        return 0.5 * _ramp(last / slow - 1, p["gate_ramp"]) + 0.5 * _ramp(fast / slow - 1, p["gate_ramp"])

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        lbs = [int(h) for h in p["lookback_hours"]]
        vol_h = p["vol_days"] * 24
        close, qv = view.tail(max(max(lbs), vol_h) + 1)
        ok = close.notna().sum() >= p["min_history_days"] * 24
        close, qv = close.loc[:, ok], qv.loc[:, ok]
        if close.shape[1] < p["min_coins"]:
            return pd.Series(dtype=float)
        liquid = qv.iloc[-vol_h:].sum().sort_values(ascending=False).index[: p["top_n"]]
        close, qv = close[liquid], qv[liquid]
        rets = close.pct_change(fill_method=None).iloc[-vol_h:]
        vol = rets.std() * np.sqrt(HOURS_PER_YEAR)
        last = close.iloc[-1]
        mom = sum(last / close.iloc[-1 - h] - 1 for h in lbs) / len(lbs)
        score = (mom / vol).replace([np.inf, -np.inf], np.nan).dropna()
        if score.empty:
            return pd.Series(dtype=float)
        vol_ratio = qv.iloc[-24:].sum() / (qv.iloc[-vol_h:].sum() / p["vol_days"])

        g = self.gate(view)
        rank = score.rank(ascending=False)
        prev_long = [c for c, w in view.prev_targets.items() if w > 0]
        held = [c for c in prev_long if c in rank.index and rank[c] <= p["keep_rank"] and score[c] > 0]
        for c in rank.sort_values().index:
            if len(held) >= p["k"]:
                break
            if c not in held and score[c] > 0 and vol_ratio.get(c, 0.0) >= p["min_volume_ratio"]:
                held.append(c)

        w = pd.Series(0.0, index=score.index)
        if held and g > 0:
            iv = 1.0 / vol[held]
            lw = (iv / iv.sum()).clip(upper=p["max_weight"])
            cov = rets[held].fillna(0.0).cov().to_numpy() * HOURS_PER_YEAR
            port_vol = float(np.sqrt(max(lw.to_numpy() @ cov @ lw.to_numpy(), 1e-12)))
            target_vol = p["target_daily_vol"] * np.sqrt(365)
            w[held] = lw * min(1.0, target_vol / port_vol) * g

        off = 1.0 - g
        if off > 0:
            if p["long_only"]:
                if BTC in w.index:
                    w[BTC] += p["btc_floor"] * off
            else:
                losers = [c for c in score[score < 0].sort_values().index if c not in held][: p["short_k"]]
                if losers:
                    iv = 1.0 / vol[losers]
                    w[losers] = -(iv / iv.sum()) * p["short_gross"] * off
        return w[w != 0.0]


MODEL = TrendGatedMomentum()
