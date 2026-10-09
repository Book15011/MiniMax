"""Research only (research/baitoey/prereg/20261009-btc-short.md): a BTC-only short sleeve (variants A-D) and its
add-on to pol_switch_vt_tl_e20v45.

The book is cash or BTC short at 40% of equity, never long. Entries and signal covers are decided at the 16:00 UTC
close; the hard stop (entry x 1.045), C's bounce stop and the 168-hour time stop act on any hourly close. The state
is rebuilt at every call by `run_short` from the last `replay_days` days of hourly closes, starting flat, so the
model stays a function of its view. `run_short` also lists the trades for the report.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from src.config import REPO_ROOT
from src.contracts import MarketView, ModelSpec
from src.models.pol.pol_switch_vt_tl_e20v45 import MODEL as E20V45

BTC = "BTCUSDT"
GRID = 16
SIZE = 0.40
TAIL_H = 260 * 24                                   # EMA40 warm-up (3 spans) + 90 days + 20 daily closes
H_NS = 3_600_000_000_000
MAIN = REPO_ROOT.parents[1] if REPO_ROOT.parent.name == ".worktrees" else REPO_ROOT
CALENDAR = REPO_ROOT / "validation" / "event_calendar_v1.csv"
FUNDING = MAIN / "data" / "external" / "binance_futures_ext" / "funding8h_mean72.parquet"   # read-only (Pol's table)
_CACHE: dict = {}


def events(kinds: tuple[str, ...]) -> np.ndarray:
    if ("ev", kinds) not in _CACHE:
        ev = pd.read_csv(CALENDAR)
        t = pd.to_datetime(ev.loc[ev.event.isin(kinds), "time_utc"], utc=True)
        _CACHE[("ev", kinds)] = np.sort(t.to_numpy(dtype="datetime64[ns]").astype("int64"))
    return _CACHE[("ev", kinds)]


def funding_daily() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(times, BTC 72-hour mean funding at 16:00 UTC, its trailing 365-day 10th percentile), causal."""
    if "fund" not in _CACHE:
        f = pd.read_parquet(FUNDING)[BTC].dropna()
        f = f[f.index.hour == GRID]
        q = f.rolling(365, min_periods=180).quantile(0.10)
        _CACHE["fund"] = (f.index.asi8, f.to_numpy(float), q.to_numpy(float))
    return _CACHE["fund"]


def switch_down_series(c: pd.Series, ema_days: int, hysteresis: float) -> np.ndarray:
    """e20v45's BTC switch read on the 6-hourly points of the 16:00 grid: down unless the last close outside the
    +-hysteresis band around the EMA was above it (team_trend_2's rule, on this series' own EMA)."""
    ema = c.ewm(span=int(ema_days) * 24, adjust=False).mean()
    pts = (c.index.hour % 6) == (GRID % 6)
    r = (c / ema)[pts]
    side = pd.Series(np.where(r > 1 + hysteresis, 1.0, np.where(r < 1 - hysteresis, -1.0, np.nan)), index=r.index).ffill()
    return (side.reindex(c.index, method="ffill") != 1.0).to_numpy()


def run_short(c: pd.Series, p: dict, start_ns: int, switch_down: np.ndarray | None = None) -> list[dict]:
    """The short's trades from start_ns (flat there) to the last bar of c (hourly BTC closes, no gaps assumed):
    dicts with i (decision bar), f (fill bar), x (exit decision bar, None while open), reason, entry, stop."""
    v = p["variant"]
    hard, tstop = float(p["hard_stop"]), int(p["time_stop_hours"])
    blk = int(p["event_block_hours"]) * H_NS
    x = c.to_numpy(float)
    tn = c.index.asi8
    n = len(x)
    ema40 = c.ewm(span=40 * 24, adjust=False).mean().to_numpy()
    dpos = np.flatnonzero(c.index.hour == GRID)
    d = pd.Series(x[dpos])
    low20 = d.shift(1).rolling(20).min().to_numpy()
    mean20 = d.shift(1).rolling(20).mean().to_numpy()
    high10 = d.shift(1).rolling(10).max().to_numpy()
    ret20 = (d / d.shift(20) - 1).to_numpy()
    ev = events(tuple(p["events"]))
    fund = funding_daily() if v == "d" else None

    def blocked(i):
        return np.searchsorted(ev, tn[i] + blk, side="right") > np.searchsorted(ev, tn[i], side="right")

    def funding_ok(i):
        if fund is None:
            return True
        j = np.searchsorted(fund[0], tn[i], side="right") - 1
        return j < 0 or not (fund[1][j] < fund[2][j])          # NaN percentile: no filter yet

    def entry(k, i, last_exit):
        if v in "ad":
            return bool(x[i] < ema40[i] * 0.97 and ret20[k] < 0), None
        if v == "b":
            return bool(x[i] < low20[k]), None
        lo = max(i - 72, last_exit + 1)                          # C: the touch must come after the last exit
        if lo >= i or not np.isfinite(mean20[k]):
            return False, None
        bh = float(np.max(x[lo:i]))
        return bool(x[i] < ema40[i] and x[i] < mean20[k] and bh >= mean20[k]), bh

    def cover(kk, j):
        if switch_down is not None and not switch_down[j]:
            return True                                         # add-on: the switch reads up
        if v in "ad":
            return bool(x[j] > ema40[j] * 1.03)
        if v == "b":
            return bool(x[j] > high10[kk])
        return False

    trades, last_exit, armed = [], -1, True
    k = int(np.searchsorted(tn[dpos], start_ns))
    while k < len(dpos):
        i = dpos[k]
        cond, bh = entry(k, i, last_exit)
        if v in "ad" and not armed:                             # a fresh signal needs one close outside the condition
            armed = not cond
            k += 1
            continue
        if not (cond and not blocked(i) and funding_ok(i) and (switch_down is None or switch_down[i])):
            k += 1
            continue
        f = i + 1
        if f >= n:
            trades.append({"i": i, "f": None, "x": None, "reason": "open", "entry": None, "stop": None})
            break
        e = x[f]
        stop = e * (1 + hard) if bh is None else min(e * (1 + hard), bh * 1.005)
        cands = []
        hit = np.flatnonzero(x[f + 1:] >= stop)
        if hit.size:
            cands.append((f + 1 + int(hit[0]), "stop"))
        if f + tstop < n:
            cands.append((f + tstop, "time"))
        for kk in range(k + 1, len(dpos)):
            j = dpos[kk]
            if cands and j >= min(cands)[0]:
                break
            if cover(kk, j):
                cands.append((j, "cover"))
                break
        if not cands:
            trades.append({"i": i, "f": f, "x": None, "reason": "open", "entry": e, "stop": stop})
            break
        xe, why = min(cands)
        trades.append({"i": i, "f": f, "x": xe, "reason": why, "entry": e, "stop": stop})
        last_exit = xe
        armed = v not in "ad"
        k = int(np.searchsorted(dpos, xe, side="left" if v in "ad" else "right"))
    return trades


def short_on(c: pd.Series, p: dict, switch_down: np.ndarray | None = None) -> tuple[bool, bool]:
    """(short at the last bar of c, short at the bar before), from the last replay_days days."""
    if len(c) < 3:
        return False, False
    tr = run_short(c, p, int(c.index.asi8[-1] - int(p["replay_days"]) * 24 * H_NS), switch_down)
    n = len(c)

    def on(b):
        return any(t["i"] <= b and (t["x"] is None or b < t["x"]) for t in tr)
    return on(n - 1), on(n - 2)


def _clean(w: pd.Series) -> pd.Series:
    return w[w.abs() > 1e-12].astype(float)


class BtcShort:
    spec = ModelSpec(name="baitoey_btc_short", method="trend", author="baitoey", rebalance_hours=1, band=0.10,
                     uses_shorts=True, description="research only: BTC short or cash")

    def targets(self, view: MarketView) -> pd.Series:
        if BTC not in view.universe or BTC not in view.close:
            return pd.Series(dtype=float)
        c = view.close[BTC].iloc[-TAIL_H:].dropna()
        now, _ = short_on(c, view.params)
        return pd.Series({BTC: -SIZE}) if now else pd.Series(dtype=float)


class E20BtcShort:
    """pol_switch_vt_tl_e20v45 plus the short while e20v45's switch reads down (e20v45's book <= 60% gross then)."""
    spec = ModelSpec(name="baitoey_e20_btcs", method="selector", author="baitoey", rebalance_hours=1,
                     band=E20V45.spec.band, uses_shorts=True, description="research only: e20v45 + BTC short")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params
        prev = _clean(view.prev_targets)
        now = had = False
        if BTC in view.universe and BTC in view.close:
            c = view.close[BTC].iloc[-TAIL_H:].dropna()
            sw = p["vt"]["switch"]
            now, had = short_on(c, p["short"], switch_down_series(c, sw["ema_days"], float(sw["hysteresis"])))
        had = had and float(prev.get(BTC, 0.0)) <= -SIZE + 1e-9     # the short is in the previous book
        base_prev = _clean(prev.add(pd.Series({BTC: SIZE}), fill_value=0.0)) if had else prev
        if view.t.hour == GRID or prev.empty:                        # e20v45's decision (or a window's first)
            w = _clean(E20V45.targets(replace(view, params=p["vt"], prev_targets=base_prev)))
            if now:
                g = float(w.abs().sum())
                if g > 1 - SIZE:
                    w = w * ((1 - SIZE) / g)
                w = w.add(pd.Series({BTC: -SIZE}), fill_value=0.0)
            return _clean(w)
        if had and not now:                                          # a stop between decisions: only the short goes
            return base_prev
        return prev


def make(kind: type, name: str, description: str):
    cls = type(name, (kind,), {})
    cls.spec = replace(kind.spec, name=name, description=description)
    return cls()
