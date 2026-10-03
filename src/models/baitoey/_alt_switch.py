"""Research only (not a registered model): pol_switch_vt_tl_e20v45 with its up/down switch read from altcoins.

The switch is team_trend_2's rule exactly as btc_state applies it (EMA of hourly closes over `ema_days`, +-hysteresis,
replayed at every 6-hour point of the last `state_days`, out of trend when undecided), but on an equal-weight index
of the universe's coins other than BTC and ETH (mean hourly return across the coins with a price, compounded) instead
of BTC. `market: alts` uses that index alone; `market: both` is up only when BTC and the altcoin index are both up.
`market: momentum` reads the same rule on a momentum basket: each day at 16:00 UTC the universe's top 6 by the 7/14-day
momentum score (data up to that hour), held in equal weights for the next 24 hours, compounded; its trend says
whether the coins we would hold have been rising. Everything else is e20v45 unchanged. Pre-registration: research/baitoey/prereg/20261004-alt-switch.md.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from src.contracts import MarketView
from src.models.baselines import team_trend_2
from src.models.baitoey._volume_signals import momentum_score
from src.models.pol._combo import btc_state
from src.models.pol.pol_switch_vt_tl_e20v45 import SwitchVtTlE20V45

EXCLUDE = ("BTCUSDT", "ETHUSDT")
GRID_HOUR, K, LOOKBACKS = 16, 6, (7, 14)
_PICKS: dict = {}                              # (selection hour, coins) -> the top K then; prices up to that hour only


def alt_index(view: MarketView, hours: int) -> pd.Series:
    close, _ = view.tail(hours)
    alts = close[[c for c in close.columns if c not in EXCLUDE]]
    r = alts.pct_change(fill_method=None).mean(axis=1, skipna=True).fillna(0.0)
    return (1.0 + r).cumprod()


def momentum_index(view: MarketView, hours: int) -> pd.Series:
    """The momentum basket over the last `hours` hours: top K picked daily at GRID_HOUR, held for the next 24 hours."""
    need = max(LOOKBACKS) * 24 + 1
    close, _ = view.tail(hours + need + 24)
    if close.shape[1] == 0:                                            # no coins yet: a flat index (no trend)
        return pd.Series(1.0, index=close.index).iloc[-hours:]
    cols = tuple(close.columns)
    grid = [t for t in close.index[close.index.hour == GRID_HOUR] if close.index.get_loc(t) >= need]
    picks = np.full((len(grid), K), -1)
    for i, g in enumerate(grid):
        key = (g, cols)
        if key not in _PICKS:
            hist = close.loc[:g].iloc[-need:]
            s = momentum_score(hist, list(LOOKBACKS)).sort_values(ascending=False)
            _PICKS[key] = tuple(cols.index(c) for c in s.index[:K])
        row = _PICKS[key]
        picks[i, :len(row)] = row
    rets = close.pct_change(fill_method=None).to_numpy()
    held_from = close.index.get_indexer(grid) + 1                      # held from the hour after the pick
    day = np.searchsorted(held_from, np.arange(len(close)), side="right") - 1
    r = np.zeros(len(close))
    ok = day >= 0
    sel = picks[day[ok]]
    vals = np.take_along_axis(rets[ok], np.where(sel >= 0, sel, 0), axis=1)
    vals = np.where(sel >= 0, vals, np.nan)
    with np.errstate(invalid="ignore"):
        r[ok] = np.nan_to_num(np.nanmean(vals, axis=1))
    return pd.Series(np.cumprod(1.0 + r), index=close.index).iloc[-hours:]


def alt_state(view: MarketView, p: dict, index=alt_index) -> str:
    """'up' or 'down': team_trend_2's trend state of an index (default the altcoin index) at view.t."""
    span = int(p["ema_days"]) * 24
    px = index(view, (int(p["state_days"]) + 3 * int(p["ema_days"])) * 24 + 1)
    if len(px) < span:
        return "down"
    ema = px.ewm(span=span, adjust=False).mean()
    step = (px.index.hour - px.index[-1].hour) % team_trend_2.MODEL.spec.rebalance_hours == 0
    pts = (px.index > px.index[-1] - pd.Timedelta(days=int(p["state_days"]))) & step
    return "up" if team_trend_2.in_trend(px[pts], ema[pts], p["hysteresis"]) else "down"


class AltSwitch(SwitchVtTlE20V45):
    spec = replace(SwitchVtTlE20V45.spec, name="baitoey_altswitch_e20v45", author="baitoey",
                   description="research only: e20v45 with the up/down switch read from an altcoin index")

    @staticmethod
    def state(view: MarketView, p: dict) -> str | None:
        if not p.get("switch"):
            return None
        if p.get("market", "alts") == "momentum":
            return alt_state(view, p["switch"], momentum_index)
        alts = alt_state(view, p["switch"])
        if p.get("market", "alts") == "both":
            return "up" if alts == "up" and btc_state(view, p["switch"]) == "up" else "down"
        return alts


MODEL = AltSwitch()
