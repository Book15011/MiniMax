"""Research only: three overlays on a daily base model (pre-registration research/baitoey/prereg/20261009-overlays.md).

The base model's parameters sit under "vt" (as in pol_abl_shock). The registered models baitoey_ovl_* pick a base
and an overlay; each overlay only removes, moves or scales the base model's weights and never opens a short.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from src.config import REPO_ROOT
from src.contracts import MarketView, ModelSpec

GRID_HOUR = 16
BTC = "BTCUSDT"
CALENDAR = REPO_ROOT / "validation" / "event_calendar_v1.csv"


def _clean(w: pd.Series) -> pd.Series:
    return w[w != 0].astype(float)


def daily_closes(view: MarketView, coins: list[str], days: int) -> pd.DataFrame:
    """The last `days` 16:00 UTC closes at or before view.t."""
    grid = view.close.index[view.close.index.hour == GRID_HOUR]
    return view.close.loc[grid[-days:], coins]


def alts_lag_btc(view: MarketView, lookback_hours: int) -> bool:
    """True when the equal-weight alt basket's return over lookback_hours is below BTC's."""
    c = view.close
    k = c.index.searchsorted(view.t - pd.Timedelta(hours=lookback_hours), side="right") - 1   # last bar at or before
    if BTC not in c.columns or k < 0:
        return False
    now, then = c.iloc[-1], c.iloc[k]
    r = now / then - 1.0
    alts = [x for x in view.universe if x != BTC and np.isfinite(r.get(x, np.nan))]
    if not alts or not np.isfinite(r[BTC]):
        return False
    return float(r[alts].mean()) < float(r[BTC])


def blocked(view: MarketView, coins: list[str], channel: int, scan: int) -> set[str]:
    """Coins whose latest daily close below their previous-`channel`-day low has had no later daily close above
    their previous-`channel`-day mean (within the last `scan` days)."""
    if not coins:
        return set()
    d = daily_closes(view, coins, scan + channel)
    prev = d.shift(1)
    low, mean = prev.rolling(channel).min(), prev.rolling(channel).mean()
    brk, up = (d < low).to_numpy(), (d > mean).to_numpy()
    pos = np.arange(len(d))[:, None]
    last_brk = np.where(brk, pos, -1).max(axis=0) if len(d) else np.full(len(coins), -1)
    last_up = np.where(up, pos, -1).max(axis=0) if len(d) else np.full(len(coins), -1)
    return {c for c, b, u in zip(coins, last_brk, last_up) if b >= 0 and b > u}


def load_events(kinds: tuple[str, ...]) -> np.ndarray:
    ev = pd.read_csv(CALENDAR)
    t = pd.to_datetime(ev.loc[ev.event.isin(kinds), "time_utc"], utc=True)
    return np.sort(t.to_numpy(dtype="datetime64[ns]").astype("int64"))


_EVENTS: dict[tuple[str, ...], np.ndarray] = {}


def event_factor(fill: pd.Timestamp, times: np.ndarray, before_h: float, after_h: float, scale: float) -> float:
    """scale when fill lies in [T - before_h, T + after_h) for some event time T, else 1."""
    x = pd.Timestamp(fill).value
    lo = np.searchsorted(times, x - int(after_h * 3.6e12), side="right")     # T > fill - after
    hi = np.searchsorted(times, x + int(before_h * 3.6e12), side="right")    # T <= fill + before
    return scale if hi > lo else 1.0


class _Overlay:
    INNER = None                                   # the base model
    BASE = ""                                      # short base label for names/descriptions

    def base(self, view: MarketView, prev: pd.Series | None = None) -> pd.Series:
        v = replace(view, params=view.params["vt"]) if prev is None else \
            replace(view, params=view.params["vt"], prev_targets=prev)
        return _clean(self.INNER.targets(v))


class AltBtc(_Overlay):
    TO = "btc"

    def targets(self, view: MarketView) -> pd.Series:
        w = self.base(view)
        p = view.params
        if not alts_lag_btc(view, int(p["lookback_days"]) * 24):
            return w
        alt_long = w[(w > 0) & (w.index != BTC)]
        out = w.drop(alt_long.index)
        if self.TO == "btc" and BTC in view.universe:
            out[BTC] = float(out.get(BTC, 0.0)) + float(alt_long.sum())
        return _clean(out)


class Breakdown(_Overlay):
    def targets(self, view: MarketView) -> pd.Series:
        w = self.base(view)
        p = view.params
        longs = [c for c in w.index[w > 0] if c in view.close.columns]
        out = w.copy()
        for c in blocked(view, longs, int(p["channel_days"]), int(p["scan_days"])):
            out[c] = 0.0
        return _clean(out)


class EventDerisk(_Overlay):
    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        kinds = tuple(p["events"])
        if kinds not in _EVENTS:
            _EVENTS[kinds] = load_events(kinds)
        times, b, a, s = _EVENTS[kinds], float(p["before_hours"]), float(p["after_hours"]), float(p["scale"])
        f_now = event_factor(view.t, times, b, a, s)                 # factor applied to the book now held
        prev = _clean(view.prev_targets) / f_now if len(view.prev_targets) else pd.Series(dtype=float)
        if view.t.hour == GRID_HOUR or prev.empty:
            book = self.base(view, prev)
        else:
            book = prev[prev.index.isin(list(view.universe))]
        return _clean(book * event_factor(view.t + pd.Timedelta(hours=1), times, b, a, s))


def make(kind: type, inner, name: str, base_label: str, description: str, hourly: bool = False, **attrs):
    """A registered overlay model on `inner` (band and shorts as the base; hourly decisions for event_derisk)."""
    cls = type(name, (kind,), {"INNER": inner, "BASE": base_label, **attrs})
    cls.spec = ModelSpec(name=name, method=inner.spec.method, author="baitoey",
                         rebalance_hours=1 if hourly else inner.spec.rebalance_hours, band=inner.spec.band,
                         uses_shorts=inner.spec.uses_shorts, description=description)
    return cls()
