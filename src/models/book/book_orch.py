"""book_orch v3: a daily base strategy with equal-risk sizing (R), staged entries (E), forecast longs (F) and forecast
shorts (FS), the last two from a per-coin 2/4/8-hour forecaster (v2), and a per-coin trailing stop (TS) and a BTC-only
hedge (BH) (v3).

Pre-registered in reports/review/20261003-prereg-orch-v2.md, section 3, and reports/review/20261003-prereg-orch-v3.md,
section 2. Every number lives in config.yaml under `book_orch:`; each layer has an `enabled` switch, and with every
layer off the model is its base, held between decisions (version A, band 0.05; v2's A' used 0.015). v1's layers (ML
weight adjustment, shock, short sleeve, partial moves) are recorded at 183827f.

- Base (default baitoey_vt_mom, unchanged): runs at its decision hour (16:00 UTC) and at any hour with no long
  target, on the current view, with this model's current long targets as its previous holdings (option 2).
- Between base decisions every coin keeps its previous target exactly, except for E's top-up at 00:00 UTC, F's
  exits and entries, and FS's openings and closings.
- B' (the base's target between decisions): the base re-run on the view as of the latest 16:00 decision, with the
  current long targets as its previous holdings. It is memoized per (decision time, held targets, data): a cache of
  a pure function, so the outputs are the same as without it.
- R: at base decisions, weights proportional to 1 / 30-day volatility within the base's coins, at the base's gross.
- E: at base decisions a new coin enters in full if its trend score is 1 and its volatility is below the median of
  the base's coins, else at half; the half is completed at 00:00 UTC if the coin is still in B' and not broken down
  (vt_mom's early-exit signal), else at the next decision. A coin staged at another hour (a window's first hour) is
  completed at the next 16:00 UTC decision. Optional gate (H1 / H2, reports/review/20261004-prereg-hybrids.md), read
  at the decision only: stage only while breadth < 0.60 (`gate: breadth`) or while Pol's e20 BTC switch reads down
  (`gate: btc_down`); otherwise every new coin enters in full.
- F: a confident FALL exits a held coin or holds back a new one; a size multiplier clip(1 + q, 0.5, 1.5) applies at
  base decisions only where the expected 8-hour return clears 2 round trips; between decisions a coin of B' that
  is not held enters when q >= 0 and there is no confident FALL.
- FS: shorts of 2% (5% on a strong FALL) on liquid coins not held long, with a confident FALL and an expected
  8-hour drop of at least 2 short round trips; at most 4, and at most min(20%, 1 - long gross); closed when P(fall)
  drops below its base rate. Its 2% / 5% shorts need a band below 5% (v2 ran at 0.015); at v3's 0.05 FS opens none.
- TS (hourly): a held long exits when its close falls below its highest close of the last 7 days x (1 - k sigma_d),
  sigma_d = 30-day hourly volatility x sqrt(24). A coin with that condition at any of the last 48 hours is never
  targeted and is left out of the base's universe (read from the view alone, like the shock rule). Removed weight
  stays in cash until the next decision; a book emptied by stops stays in cash until then.
- BH (hourly): short BTC at min(20%, 1 - long gross) while BTC is in Pol's 20-day trend switch DOWN state
  (src/models/pol/_combo.btc_state, imported) and breadth is below 0.3; never when BTC is held long; longs are never
  cut; closed as soon as either condition ends.
Forecasts are the stored out-of-sample forecasts of backtest/orch_train.py (src/models/book/_orch_ml.py), read once
per process; F and FS do nothing to a coin without one (outside the liquid 20, or before the first model).
`explain(view)` returns the targets and a per-coin record of each decision and its reason (the shadow log). A held
coin that drops out of the point-in-time universe is recorded as an exit (a short as a close) with that reason.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import numpy as np
import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey._volume_signals import breakdown_blocked
from src.models.baitoey.baitoey_vt_mom import MODEL as VT_MOM
from src.models.book._trend import breadth, hourly_vol, trend_scores

HOUR, DAY = pd.Timedelta(hours=1), pd.Timedelta(days=1)
CARRY_ROWS = 48                                   # as the engine and the live store: carry a price at most 48 hours
_BASES = {VT_MOM.spec.name: VT_MOM}
_B_CACHE: dict = {}
_M_CACHE: dict = {}                               # TS and BH market signals (see _memo)
_B_CACHE_MAX = 50_000
LEFT_UNIVERSE = "left the point-in-time universe"   # the shadow-log reason when a held coin drops out of it


def _clean(w: pd.Series) -> pd.Series:
    w = w.astype(float)
    return w[w != 0.0]


def base_model(name: str):
    if name not in _BASES:
        from src.models import get                # deferred: src.models imports every model module
        _BASES[name] = get(name)
    return _BASES[name]


def cap_gross(w: pd.Series) -> pd.Series:
    g = float(w.abs().sum())
    return w / g if g > 1.0 else w


def last_decision(t: pd.Timestamp, hour: int) -> pd.Timestamp:
    d = t.floor("D") + hour * HOUR
    return d if d <= t else d - DAY


def view_at(view: MarketView, t: pd.Timestamp) -> MarketView:
    """The view as it was at an earlier hour t: bars up to t, padded to t as the harness pads (view_frames)."""
    c, q = view.close.loc[:t], view.quote_volume.loc[:t]
    if len(c) and c.index[-1] < t:
        extra = pd.date_range(c.index[-1] + HOUR, t, freq="h")
        last = c.iloc[-CARRY_ROWS:].ffill().iloc[-1].to_numpy()
        c = pd.concat([c, pd.DataFrame(np.tile(last, (len(extra), 1)), index=extra, columns=c.columns)])
        q = pd.concat([q, pd.DataFrame(np.nan, index=extra, columns=q.columns)])
    return replace(view, t=t, close=c, quote_volume=q)


class Trace:
    """Per-coin decisions and reasons of one targets() call (the shadow log); a no-op when not requested."""

    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    def set(self, coin: str, decision: str, reason: str) -> None:
        self.rows[coin] = {"decision": decision, "reason": reason}


class _NoTrace(Trace):
    def set(self, coin: str, decision: str, reason: str) -> None:
        pass


# ------------------------------------------------------------------ the base ------------------------------------------

def run_base(view: MarketView, held: pd.Series, p: dict, stops: bool = True) -> pd.Series:
    """The base's long targets on this view, given our long targets as its previous holdings (option 2). With TS on,
    the coins in TS's cool-down at view.t are left out of its universe (the next-ranked coin takes the slot)."""
    if stops and p["trailing_stop"]["enabled"]:
        out = cooled(view, list(view.universe), p)
        if out:
            view = replace(view, universe=tuple(c for c in view.universe if c not in out))
    w = _clean(base_model(p["base"]).targets(replace(view, params=p["base_params"], prev_targets=held)))
    return w[w > 0]


def base_between(view: MarketView, held: pd.Series, p: dict) -> tuple[pd.Series, MarketView]:
    """B': the base re-run as of the latest decision hour, with the current long targets as its previous holdings."""
    t_d = last_decision(view.t, int(p["decision_hour_utc"]))
    v = view_at(view, t_d)
    tail_c, tail_q = v.close.iloc[-CARRY_ROWS:], v.quote_volume.iloc[-CARRY_ROWS:]
    fp = hashlib.blake2b(np.ascontiguousarray(tail_c.to_numpy(dtype=float)).tobytes()
                         + np.ascontiguousarray(tail_q.to_numpy(dtype=float)).tobytes()
                         + "|".join(map(str, tail_c.columns)).encode()
                         + json.dumps([p["base_params"], p["trailing_stop"]], sort_keys=True, default=str).encode(),
                         digest_size=16).hexdigest()
    key = (p["base"], t_d.value, tuple(sorted(held.round(15).items())), tuple(view.universe), fp)
    if key not in _B_CACHE:
        if len(_B_CACHE) >= _B_CACHE_MAX:
            _B_CACHE.clear()
        _B_CACHE[key] = run_base(v, held, p)
    return _B_CACHE[key].copy(), v


# ------------------------------------------------------------------ layers --------------------------------------------

def size_r(view: MarketView, B: pd.Series, p: dict) -> pd.Series:
    """R: within the base's coins, weights proportional to 1 / sigma (30-day hourly), at the base's gross. A coin with
    no sigma keeps its base weight and the others share the rest."""
    if B.empty:
        return B
    sig = hourly_vol(view.close, view.t, list(B.index), float(p["size"]["vol_days"])).reindex(B.index)
    ok = sig[np.isfinite(sig) & (sig > 0)]
    if ok.empty:
        return B
    keep = B.drop(ok.index)
    inv = 1.0 / ok
    out = pd.concat([keep, (float(B.sum()) - float(keep.sum())) * inv / float(inv.sum())])
    return out.reindex(B.index)


def stage_factor(view: MarketView, L: pd.Series, held: pd.Series, p: dict) -> pd.Series:
    """E at a base decision: 1 for a held coin and for a new coin with trend score 1 and volatility below the median
    of L's coins; `fraction` (0.5) for any other new coin."""
    e = p["stage"]
    fac = pd.Series(1.0, index=L.index)
    new = [c for c in L.index if c not in held.index]
    if not new:
        return fac
    sig = hourly_vol(view.close, view.t, list(L.index), float(e["vol_days"])).reindex(L.index)
    med = float(sig.median())
    s = trend_scores(view.close, view.t, new, p["trend"])
    for c in new:
        full = s.get(c, 0.0) == 1.0 and np.isfinite(sig[c]) and np.isfinite(med) and sig[c] < med
        fac[c] = 1.0 if full else float(e["fraction"])
    return fac


def stage_reason(hour: int, p: dict) -> str:
    """E's shadow-log reason for a staged coin, with the time the half is actually completed. Staged at the base
    decision: at the top-up hour (00:00 UTC), or at the next decision if it has broken down by then. Staged at any
    other hour (a window's first hour, or an empty book): at the next base decision, where it is a held coin."""
    dh = int(p["decision_hour_utc"])
    if hour == dh:
        top = (dh + int(p["stage"]["topup_hours"])) % 24
        return (f"new coin: half now, the rest at {top:02d}:00 UTC (at the next {dh:02d}:00 UTC decision "
                "if it has broken down by then)")
    return f"new coin: half now, the rest at the next {dh:02d}:00 UTC decision"


def multiplier(c: str, fc: pd.DataFrame | None, p: dict, spread) -> float:
    """F's size multiplier: clip(1 + q, m_min, m_max), only where the expected 8-hour return clears filter_mult round
    trips in the direction of the change; else 1. 1 without a forecast."""
    if fc is None or c not in fc.index:
        return 1.0
    f, g = p["forecast_longs"], p["forecasts"]
    m = float(np.clip(1.0 + fc.at[c, "q"], float(f["m_min"]), float(f["m_max"])))
    cost = 2.0 * (float(g["fee"]) + spread(c))
    e8 = fc.at[c, "e8"]
    bar = float(g["filter_mult"]) * cost
    if m > 1.0 and e8 >= bar:
        return m
    if m < 1.0 and e8 <= -bar:
        return m
    return 1.0


def confident_fall(c: str, fc: pd.DataFrame | None, p: dict) -> bool:
    return fc is not None and c in fc.index and bool(fc.at[c, "fall_margin"] >= float(p["forecasts"]["confident"]))


def f_full(L: pd.Series, fc: pd.DataFrame | None, p: dict, spread) -> tuple[pd.Series, set[str], pd.Series]:
    """F at a base decision: (full targets of the coins it lets in, the coins it holds out, multipliers). If the sum
    exceeds L's gross, the coins with a multiplier above 1 are scaled down by one factor to fit."""
    out = set(c for c in L.index if confident_fall(c, fc, p))
    m = pd.Series({c: multiplier(c, fc, p, spread) for c in L.index if c not in out}, dtype=float)
    full = L.reindex(m.index) * m
    G = float(L.sum())
    up = m.index[m > 1.0]
    if float(full.sum()) > G + 1e-15 and len(up):
        rest = float(full.drop(up).sum())
        full[up] = full[up] * max(0.0, G - rest) / float(full[up].sum())
    return full, out, m


def fs_layer(view: MarketView, longs: pd.Series, prev_shorts: pd.Series, fc: pd.DataFrame | None, p: dict, spread,
             band: float, tr: Trace) -> pd.Series:
    """FS: the short targets (negative) this hour, given the final long targets."""
    s = p["forecast_shorts"]
    S = prev_shorts[prev_shorts.index.isin(list(view.universe))].copy()
    for c in prev_shorts.index.difference(S.index):
        tr.set(c, "close_short", LEFT_UNIVERSE)
    if fc is None:
        for c in S.index:
            tr.set(c, "close_short", "no forecast")
        return pd.Series(dtype=float)
    for c in list(S.index):
        why = ("no forecast" if c not in fc.index else "in the long target" if c in longs.index
               else "P(fall) below its base rate" if fc.at[c, "fall_margin"] < 0.0 else None)
        if why:
            S = S.drop(c)
            tr.set(c, "close_short", why)
    room = min(float(s["max_gross"]), 1.0 - float(longs.sum()))
    while not S.empty and float(-S.sum()) > room + 1e-12:
        weakest = sorted(S.index, key=lambda c: (fc.at[c, "fall_margin"], c))[0]
        S = S.drop(weakest)
        tr.set(weakest, "close_short", "no room: the long book grew")
    for c in S.index:
        tr.set(c, "hold_short", "confident fall persists or not yet below base rate")
    cand = fc[(fc.fall_margin >= float(p["forecasts"]["confident"])) & ~fc.index.isin(longs.index)
              & ~fc.index.isin(S.index) & fc.index.isin(list(view.universe))]
    cost = pd.Series({c: float(s["fee_open"]) + float(s["fee_close"]) + 2.0 * spread(c) for c in cand.index},
                     dtype=float)
    ok = cand.e8 <= -float(p["forecasts"]["filter_mult"]) * cost.reindex(cand.index)
    for c in cand.index[~ok.to_numpy(dtype=bool)]:
        tr.set(c, "no_short", "confident fall, but the expected drop is below 2 short round trips")
    ranked = sorted(cand.index[ok.to_numpy(dtype=bool)], key=lambda c: (-cand.at[c, "fall_margin"], c))
    for c in ranked:
        left = room - float(-S.sum())
        if len(S) >= int(s["max_coins"]) or left <= band:
            tr.set(c, "no_short", "no slot or no room")
            continue
        strong = cand.at[c, "fall_margin"] >= float(p["forecasts"]["strong"])
        size = min(float(s["large"] if strong else s["small"]), left)
        if size <= band:
            tr.set(c, "no_short", "remaining room below the band")
            continue
        S[c] = -size
        tr.set(c, "open_short", f"{'strong' if strong else 'confident'} fall, expected 8 h drop clears the cost")
    return S


# ------------------------------------------------------------------ TS and BH (v3) ------------------------------------

def stop_panel(close: pd.DataFrame, t: pd.Timestamp, coins, ts: dict, hours: int) -> pd.DataFrame:
    """TS's stop condition at each of the last `hours` hourly closes up to t (rows: hours, columns: coins): close <
    (highest close over the last `high_hours` hours, this one included) x (1 - k sigma_d), with sigma_d = the
    `vol_days`-day hourly volatility (as _trend.hourly_vol, on the clock grid) x sqrt(24). False where the close, the
    high or sigma is missing."""
    cols = [c for c in coins if c in close.columns]
    vol_h, hi_h = int(ts["vol_days"]) * 24, int(ts["high_hours"])
    grid = pd.date_range(t - (hours - 1 + max(vol_h, hi_h)) * HOUR, t, freq="h")
    c = close.loc[grid[0]: t, cols].reindex(grid)
    sig = c.pct_change(fill_method=None).rolling(vol_h, min_periods=2).std(ddof=1) * np.sqrt(24.0)
    hi = c.rolling(hi_h, min_periods=1).max()
    return (c < hi * (1.0 - float(ts["k"]) * sig)).iloc[-hours:]


def _memo(key: tuple, frames: list[pd.DataFrame], fn):
    """A cache of a pure function of the view (TS's and BH's market signals; the engine asks for the same hour once
    per window's first decisions and once in the shared history). The key holds the hour, the coins and parameters,
    and a hash of every bar the function reads, so a cached value is the value."""
    h = hashlib.blake2b(digest_size=16)
    for f in frames:
        h.update(np.ascontiguousarray(f.to_numpy(dtype=float)).tobytes())
        h.update(np.ascontiguousarray(f.index.asi8).tobytes())
        h.update("|".join(map(str, f.columns)).encode())
    k = key + (h.hexdigest(),)
    if k not in _M_CACHE:
        if len(_M_CACHE) >= _B_CACHE_MAX:
            _M_CACHE.clear()
        _M_CACHE[k] = fn()
    return _M_CACHE[k]


def stop48(view: MarketView, p: dict) -> pd.DataFrame:
    """TS's stop condition for every universe coin over the last `cooldown_hours` hours (memoized; read-only)."""
    ts = p["trailing_stop"]
    n = int(ts["cooldown_hours"])
    cols = [c for c in view.universe if c in view.close.columns]
    t0 = view.t - (n - 1 + max(int(ts["vol_days"]) * 24, int(ts["high_hours"]))) * HOUR
    return _memo(("stop", view.t.value, tuple(cols), json.dumps(ts, sort_keys=True, default=str)),
                 [view.close.loc[t0: view.t, cols]], lambda: stop_panel(view.close, view.t, cols, ts, n))


def cooled(view: MarketView, coins, p: dict) -> set[str]:
    """TS's cool-down C(t): the coins (of the universe) with the stop condition at any of the last `cooldown_hours`
    hourly closes, whether or not they were held (the view is all the model keeps)."""
    if not coins:
        return set()
    s = stop48(view, p)
    s = s[[c for c in coins if c in s.columns]]
    return set(s.columns[s.any(axis=0).to_numpy()])


def stop_wait(view: MarketView, p: dict) -> list[str]:
    """TS with an empty book at a non-decision hour: the coins the base would pick on the full universe (from an empty
    book) that had the stop condition at any hour since the latest decision, that hour included. If there are any,
    the book stays in cash until the next decision: stops emptied it, which the view cannot tell from a window's first
    hour otherwise."""
    B = run_base(view, pd.Series(dtype=float), p, stops=False)
    if B.empty:
        return []
    n = int((view.t - last_decision(view.t, int(p["decision_hour_utc"]))) / HOUR) + 1
    s = stop48(view, p)
    s = s.iloc[-n:] if n <= len(s) else stop_panel(view.close, view.t, list(B.index), p["trailing_stop"], n)
    return [c for c in B.index if c in s.columns and bool(s[c].any())]


def btc_state_at(view: MarketView, st: dict, coin: str = "BTCUSDT") -> str:
    """Pol's switch state of `coin` at view.t (team_trend_2's rule with the parameters `st`). Memoized."""
    from src.models.pol._combo import btc_state      # Pol's switch state, imported, not copied
    call = (lambda: btc_state(view, st)) if coin == "BTCUSDT" else (lambda: btc_state(view, st, coin))   # its default coin
    if coin not in view.close.columns:
        return call()
    need = (int(st["state_days"]) + 3 * int(st["ema_days"])) * 24 + 1
    return _memo(("btc_state", view.t.value, coin, json.dumps(st, sort_keys=True, default=str)),
                 [view.close[[coin]].iloc[-need:]], call)


def breadth_at(view: MarketView, tp: dict) -> float:
    """_trend.breadth at view.t (the share of the liquid universe in an up-trend). Memoized."""
    lb = max(int(L) for L in tp["lookback_days"]) * DAY + pd.Timedelta(hours=float(tp["max_stale_hours"]))
    cols = [x for x in view.universe if x in view.close.columns]
    qcols = [x for x in view.universe if x in view.quote_volume.columns]
    return _memo(("breadth", view.t.value, tuple(view.universe), json.dumps(tp, sort_keys=True, default=str)),
                 [view.close.loc[view.t - lb: view.t, cols],
                  view.quote_volume.loc[view.t - float(tp["volume_days"]) * DAY: view.t, qcols]],
                 lambda: breadth(view, tp))


def bh_signals(view: MarketView, p: dict) -> tuple[str, float | None]:
    """BH's two conditions at view.t: Pol's switch state of BTC, and (only when it is 'down') the breadth. Memoized."""
    h = p["btc_hedge"]
    state = btc_state_at(view, h["state"], h["coin"])
    if state != "down":
        return state, None
    return state, breadth_at(view, p["trend"])


def stage_gate(view: MarketView, p: dict) -> tuple[bool, str]:
    """H1 / H2: whether E stages at this base decision, read from the decision's view only. `stage.gate`: none (plain
    E), breadth (stage only while breadth < gate_breadth_max) or btc_down (only while Pol's e20 switch reads down)."""
    e = p["stage"]
    g = e.get("gate", "none")
    if g == "none":
        return True, ""
    if g == "breadth":
        b, lim = breadth_at(view, p["trend"]), float(e["gate_breadth_max"])
        return b < lim, f"breadth {b:.2f} {'<' if b < lim else '>='} {lim:.2f}"
    if g == "btc_down":
        st = btc_state_at(view, e["gate_state"])
        return st == "down", f"BTC switch {st}"
    raise ValueError(f"unknown stage gate {g!r}")


def bh_layer(view: MarketView, longs: pd.Series, shorts: pd.Series, prev_shorts: pd.Series, p: dict,
             tr: Trace) -> pd.Series:
    """BH: short BTC at min(size, 1 - long gross) while BTC is in the switch's DOWN state and breadth < breadth_max;
    not while BTC is held long (longs are never cut); target 0 as soon as either condition ends."""
    h = p["btc_hedge"]
    c = h["coin"]
    had = c in prev_shorts.index

    def off(why: str) -> pd.Series:
        if had:
            tr.set(c, "close_hedge", why)
        return pd.Series(dtype=float)

    if c not in view.universe:
        return off("BTC not in the universe")
    if c in shorts.index:
        return off("BTC already shorted by FS")
    state, b = bh_signals(view, p)
    if state != "down":
        return off("BTC left the DOWN state")
    if b >= float(h["breadth_max"]):
        return off(f"breadth {b:.2f} >= {float(h['breadth_max']):.2f}")
    if longs.get(c, 0.0) > 0.0:
        if not had:
            tr.set(c, "no_hedge", "BTC held long")
        return off("BTC held long")
    size = min(float(h["size"]), 1.0 - float(longs[longs > 0].sum()))
    if size <= 0.0:
        return off("no cash left by the longs")
    tr.set(c, "hold_hedge" if had else "hedge",
           f"BTC in the DOWN state, breadth {b:.2f} < {float(h['breadth_max']):.2f}: short {size:.3f}")
    return pd.Series({c: -size})


# ------------------------------------------------------------------ the model -----------------------------------------

class BookOrch:
    spec = ModelSpec(name="book_orch", method="momentum", author="book", rebalance_hours=1, band=0.05,
                     uses_shorts=True,
                     description="baitoey_vt_mom daily with equal-risk sizing, staged entries, longs and shorts "
                                 "steered by a per-coin 2/4/8-hour forecaster, a per-coin trailing stop and a BTC "
                                 "hedge (each layer switchable)")

    def targets(self, view: MarketView) -> pd.Series:
        return self._run(view, _NoTrace())[0]

    def explain(self, view: MarketView) -> tuple[pd.Series, dict[str, dict]]:
        """The targets and, per coin, the decision and its reason (the shadow-log records)."""
        tr = Trace()
        w, _ = self._run(view, tr)
        return w, tr.rows

    def _forecasts(self, view: MarketView, p: dict):
        if not (p["forecast_longs"]["enabled"] or p["forecast_shorts"]["enabled"]):
            return None, None
        from src.models.book import _orch_ml
        st = _orch_ml.load(p["forecasts"]["manifest"], p["forecasts"]["manifest_sha256"])
        return st, st.at(view.t)

    def _run(self, view: MarketView, tr: Trace) -> tuple[pd.Series, pd.DataFrame | None]:
        p = view.params
        prev = _clean(view.prev_targets)
        gone = prev[~prev.index.isin(list(view.universe))]
        for c, x in gone.items():
            tr.set(c, "exit" if x > 0 else "close_short", LEFT_UNIVERSE)
        prev = prev.drop(gone.index)
        held, prev_shorts = prev[prev > 0], prev[prev < 0]
        ts_on = bool(p["trailing_stop"]["enabled"])
        if ts_on and not held.empty:
            held = self._stops(view, held, p, tr)
        st, fc = self._forecasts(view, p)
        spread = st.spread if st is not None else (lambda c: 0.0)
        F = bool(p["forecast_longs"]["enabled"])
        fcF = fc if F else None
        if view.t.hour == int(p["decision_hour_utc"]):
            longs = self._decide(view, held, p, fcF, spread, tr)
        elif held.empty:
            wait = stop_wait(view, p) if ts_on else []
            for c in wait:
                tr.set(c, "wait", "trailing stop since the last decision: cash until the next decision")
            longs = pd.Series(dtype=float) if wait else self._decide(view, held, p, fcF, spread, tr)
        else:
            longs = self._between(view, held, p, fcF, spread, st, tr)
        shorts = pd.Series(dtype=float)
        if p["forecast_shorts"]["enabled"]:
            shorts = fs_layer(view, longs, prev_shorts, fc, p, spread, self.spec.band, tr)
        if p["btc_hedge"]["enabled"]:
            shorts = pd.concat([shorts, bh_layer(view, longs, shorts, prev_shorts, p, tr)])
        return _clean(cap_gross(pd.concat([longs, shorts]))), fc

    def _stops(self, view, held, p, tr: Trace) -> pd.Series:
        """TS on the held longs: exit every held coin in the cool-down (its stop condition now or in the last 48 h)."""
        ts = p["trailing_stop"]
        s = stop48(view, p)                                            # held coins are in the universe (see _run)
        out = [c for c in held.index if c in s.columns and bool(s[c].any())]
        for c in out:
            tr.set(c, "exit", f"trailing stop: close below the 7-day high x (1 - {float(ts['k']):g} x daily vol)"
                   if bool(s[c].iloc[-1]) else "trailing-stop cool-down")
        return held.drop(out)

    def _decide(self, view, held, p, fc, spread, tr: Trace) -> pd.Series:
        B = run_base(view, held, p)
        L = size_r(view, B, p) if p["size"]["enabled"] else B
        if fc is not None:
            full, out, m = f_full(L, fc, p, spread)
        else:
            full, out, m = L.copy(), set(), pd.Series(1.0, index=L.index)
        on, gate_why = stage_gate(view, p) if p["stage"]["enabled"] else (False, "")
        fac = stage_factor(view, L, held, p) if on else pd.Series(1.0, index=L.index)
        w = full * fac.reindex(full.index)
        for c in held.index.difference(B.index):
            tr.set(c, "exit", "the base dropped it")
        for c in L.index:
            new = c not in held.index
            if c in out:
                tr.set(c, "wait" if new else "exit", "confident fall")
            elif fac[c] < 1.0:
                tr.set(c, "stage", stage_reason(view.t.hour, p))
            else:
                why = "base decision" + (f", multiplier {m[c]:.2f}" if m.get(c, 1.0) != 1.0 else "")
                if new and p["stage"]["enabled"] and not on:
                    why += f" (staging off: {gate_why})"
                tr.set(c, "enter" if new else "hold", why)
        return w

    def _between(self, view, held, p, fc, spread, st, tr: Trace) -> pd.Series:
        L = held.copy()
        for c in L.index:
            tr.set(c, "hold", "between decisions")
        if fc is not None:
            for c in list(L.index):
                if confident_fall(c, fc, p):
                    L = L.drop(c)
                    tr.set(c, "exit", "confident fall")
        dh = int(p["decision_hour_utc"])
        topup = p["stage"]["enabled"] and view.t.hour == (dh + int(p["stage"]["topup_hours"])) % 24
        if not (topup or fc is not None):
            return L
        Bp, v_d = base_between(view, L, p)
        Lp = size_r(v_d, Bp, p) if p["size"]["enabled"] else Bp
        if topup:
            fc_d = st.at(v_d.t) if (fc is not None and st is not None) else None
            full_d = f_full(Lp, fc_d, p, spread)[0] if fc_d is not None else Lp
            vp = p["base_params"]
            need = (vp["volume_long_days"] * 24 + max(vp["volume_short_hours"], vp["chase_return_hours"])
                    + max(vp["exit_cooldown_hours"] + vp["exit_low_hours"], vp["chase_window_hours"]) + 1)
            broken = breakdown_blocked(*view.tail(need), vp)
            frac = float(p["stage"]["fraction"])
            for c in L.index:
                if c in full_d.index and abs(L[c] - frac * full_d[c]) <= 1e-9 * full_d[c]:
                    if c in broken:
                        tr.set(c, "hold", "staged half kept: broken down")
                    else:
                        L[c] = full_d[c]
                        tr.set(c, "top_up", "staged coin completed at 00:00 UTC")
        if fc is not None:
            room = float(Bp.sum()) - float(L.sum())
            cand = [c for c in Lp.index if c not in L.index]
            ok = [c for c in cand if c not in fc.index or (fc.at[c, "q"] >= 0.0 and not confident_fall(c, fc, p))]
            for c in set(cand) - set(ok):
                tr.set(c, "wait", "q below 0 or confident fall")
            ok.sort(key=lambda c: (-(fc.at[c, "q"] if c in fc.index else 0.0), c))
            for c in ok:
                size = min(float(Lp[c]) * multiplier(c, fc, p, spread), room)
                if size <= 0.0:
                    tr.set(c, "wait", "no room under the base's gross")
                    continue
                L[c] = size
                room -= size
                tr.set(c, "enter", "base coin, signal clear (q >= 0, no confident fall)")
        return L


def _num(x) -> float | None:
    x = float(x)
    return x if np.isfinite(x) else None


def coin_log(view: MarketView, w: pd.Series, records: dict[str, dict], fc: pd.DataFrame | None, p: dict) -> list[dict]:
    """The shadow-mode log (pre-registration v2, section 5.4): one record per coin at view.t, for every coin that is
    held, targeted, forecast or decided on: coin, hour, signals, probabilities, decision, reason and size. Pure: the
    caller writes the records (one JSON line each); nothing here starts shadow mode."""
    prev = _clean(view.prev_targets)
    coins = sorted(set(records) | set(w.index) | set(prev.index) | (set(fc.index) if fc is not None else set()))
    cols = [c for c in coins if c in view.close.columns]
    sig = hourly_vol(view.close, view.t, cols, 30.0) if cols else pd.Series(dtype=float)
    s = trend_scores(view.close, view.t, cols, p["trend"]) if cols else pd.Series(dtype=float)
    vp = p["base_params"]
    need = (vp["volume_long_days"] * 24 + max(vp["volume_short_hours"], vp["chase_return_hours"])
            + max(vp["exit_cooldown_hours"] + vp["exit_low_hours"], vp["chase_window_hours"]) + 1)
    broken = breakdown_blocked(*view.tail(need), vp) if view.universe else set()
    out = []
    for c in coins:
        probs = None
        if fc is not None and c in fc.index:
            r = fc.loc[c]
            probs = {f"h{h}": {k: _num(r[f"p{x}{h}"]) for k, x in (("rise", "r"), ("flat", "n"), ("fall", "f"))}
                     for h in (2, 4, 8)}
            probs.update({k: _num(r[k]) for k in ("q", "p_rise", "p_fall", "pbar_rise", "pbar_fall", "e8")})
            probs["confident_rise"] = bool(r["rise_margin"] >= float(p["forecasts"]["confident"]))
            probs["confident_fall"] = bool(r["fall_margin"] >= float(p["forecasts"]["confident"]))
        rec = records.get(c, {})
        out.append({"coin": c, "hour": view.t.isoformat(),
                    "signals": {"trend_score": _num(s.get(c, np.nan)), "sigma30": _num(sig.get(c, np.nan)),
                                "broken_down": c in broken, "in_universe": c in view.universe,
                                "liquid": fc is not None and c in fc.index, "previous_target": _num(prev.get(c, 0.0))},
                    "probabilities": probs, "decision": rec.get("decision", "none"), "reason": rec.get("reason", ""),
                    "size": _num(w.get(c, 0.0))})
    return out


MODEL = BookOrch()
