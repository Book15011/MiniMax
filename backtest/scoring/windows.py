"""Which windows are scored and how they are weighted (docs/EVALUATION.md section 1).

- Pool: a start every day at scoring.window_hour_utc (12:00 UTC, the round's start time) from harness.first_window,
  up to the last start whose window and execution lag end by the panel's last bar; a start needs a bar. With
  scoring.include_spent_holdout false, windows ending after harness.holdout_from are left out. Thinned by
  scoring.stride_days, anchored on the newest start so the most recent window is always scored.
- LIVE-LIKE weights: scoring.live_like (PART 0's method), restricted to the scored windows, renormalized.
- RECENCY weights: 0.5 ** (age / half-life), age = days from a window's start to the latest start scored.
- Final weights: w = 0.7 LL / sum LL + 0.3 REC / sum REC, then rebalanced so that UP windows (BTC's close at the
  end >= its close at the start) carry pi_up, the unweighted share of UP windows, and DOWN windows the rest.
- Sets from the validation artifact: LOOKALIKE25, RECENT25, and STRESS (10 drops + 10 rebounds).
- Regimes: the ex-post 3x3 grid written by the validation build (terciles of BTC return x volatility).
"""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd

from backtest.data import Market
from backtest.evaluate import holdout_start
from src.config import resolve


def ts(s) -> pd.Timestamp:
    t = pd.Timestamp(s)
    return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")


def sha256(path) -> str:
    return hashlib.sha256(resolve(path).read_bytes()).hexdigest()


def thin(pool: pd.DatetimeIndex, stride: int) -> pd.DatetimeIndex:
    """Every stride-th start, counted back from the newest one."""
    if stride < 1:
        raise ValueError("scoring.stride_days must be >= 1")
    return pool[::-1][::stride][::-1]


def pool_starts(market: Market, cfg: dict, include_spent_holdout: bool | None = None) -> pd.DatetimeIndex:
    """Every scoring window start (see the module docstring)."""
    h, sc = cfg["harness"], cfg["scoring"]
    hour = int(sc.get("window_hour_utc", h["grid_hour_utc"]))
    inc = bool(sc.get("include_spent_holdout", False)) if include_spent_holdout is None else include_spent_holdout
    days, lag = pd.Timedelta(days=h["window_days"]), pd.Timedelta(hours=h["execution_lag_hours"])
    first = ts(h["first_window"]) + pd.Timedelta(hours=hour)
    end = market.close.index[-1] - days - lag
    if not inc:
        end = min(end, holdout_start(cfg) - days)
    starts = pd.date_range(first, end, freq="1D")
    return starts[starts.isin(market.close.index)]


def post_holdout(starts: pd.DatetimeIndex, cfg: dict) -> np.ndarray:
    """Windows ending after harness.holdout_from: opened once on 2026-10-01, spent, and in the pool only with
    scoring.include_spent_holdout."""
    return np.asarray(starts + pd.Timedelta(days=cfg["harness"]["window_days"]) > holdout_start(cfg))


def scored_starts(market: Market, cfg: dict, stride: int | None = None) -> pd.DatetimeIndex:
    pool = pool_starts(market, cfg)
    if post_holdout(pool, cfg).any() and not cfg["scoring"].get("include_spent_holdout", False):
        raise AssertionError("a scored window reaches into the holdout")
    return thin(pool, int(cfg["scoring"]["stride_days"] if stride is None else stride))


def btc_up(market: Market, starts: pd.DatetimeIndex, cfg: dict, coin: str = "BTCUSDT") -> pd.Series:
    """True if the coin's close at the window's end (t0 + 14 days) is >= its close at the start; each close is the
    last one at or before that hour, as the engine reads equity."""
    px = market.close[coin].dropna()
    days = pd.Timedelta(days=cfg["harness"]["window_days"])
    a = px.reindex(px.index.union(starts)).ffill().reindex(starts).to_numpy()
    ends = starts + days
    b = px.reindex(px.index.union(ends)).ffill().reindex(ends).to_numpy()
    if not (np.isfinite(a).all() and np.isfinite(b).all()):
        raise ValueError(f"{coin} has no close at or before some window start or end")
    return pd.Series(b >= a, index=starts)


def final_weights(w_live: pd.Series, w_rec: pd.Series, up: pd.Series, split: dict) -> tuple[pd.Series, pd.Series, float]:
    """(w, w', pi_up). w = live_like share x LL / sum LL + recency share x REC / sum REC; pi_up = the unweighted
    share of UP windows; w' = w x pi_up / sum over UP of w for UP windows, w x (1 - pi_up) / sum over DOWN of w
    for DOWN windows, so sum w' = 1 and the UP windows carry exactly pi_up."""
    idx = up.index
    wl, wr = w_live.reindex(idx), w_rec.reindex(idx)
    if wl.isna().any() or wr.isna().any():
        raise ValueError("a window has no live-like or recency weight")
    w = split["live_like"] * wl / wl.sum() + split["recency"] * wr / wr.sum()
    u = up.to_numpy(dtype=bool)
    pi_up = float(u.mean())
    wf = w.copy()
    if u.any():
        wf[u] = w[u] * pi_up / w[u].sum()
    if (~u).any():
        wf[~u] = w[~u] * (1.0 - pi_up) / w[~u].sum()
    return w, wf, pi_up


def normalized(w: pd.Series) -> pd.Series:
    return w / float(w.sum())


def effective_n(w: pd.Series) -> float:
    w = normalized(w)
    return float(1.0 / (w ** 2).sum())


def live_like_weights(starts: pd.DatetimeIndex, cfg: dict, pool: pd.DatetimeIndex | None = None) -> tuple[pd.Series, dict]:
    """Weights of the scored windows, renormalized. File windows the harness cannot run (no bar at the start, e.g.
    an exchange outage) are listed; with a stride, the thinned-out ones are counted."""
    path = cfg["scoring"]["live_like"]
    art = json.loads(resolve(path).read_text())
    if art["weights"].get("direction_factor_applied"):
        raise ValueError(f"{path}: weights include a direction factor; PART 0 decided against it")
    w = pd.Series(art["weights"]["all"], dtype=float)
    w.index = pd.DatetimeIndex([ts(s) for s in w.index])
    missing = starts.difference(w.index)
    if len(missing):
        raise ValueError(f"{path} has no weight for {len(missing)} scored windows, e.g. {missing[:3].tolist()}; "
                         "rebuild it for the same pool")
    used = normalized(w.reindex(starts))
    not_in_pool = w.index[:0] if pool is None else w.index.difference(pool)
    info = {"source": path, "file_sha256": sha256(path), "artifact_sha256": art.get("sha256"),
            "asof": art.get("asof"), "n_in_file": int(len(w)), "n_used": int(len(used)),
            "not_in_harness_pool": [str(t) for t in not_in_pool],
            "mass_not_in_harness_pool": float(w.reindex(not_in_pool).sum() / w.sum()),
            "dropped_by_stride": int(len(w.index.difference(starts).difference(not_in_pool))),
            "mass_dropped": float(1.0 - w.reindex(starts).sum() / w.sum()),
            "effective_n": effective_n(used), "events_used_in_weights": art.get("events", {}).get("used_in_weights")}
    return used, info


def recency_weights(starts: pd.DatetimeIndex, cfg: dict) -> tuple[pd.Series, dict]:
    """0.5 ** (age / half-life), age = days from each window's start to the latest start given."""
    hl = float(cfg["scoring"]["recency_half_life_days"])
    ref = starts.max()
    age = (ref - starts) / pd.Timedelta(days=1)
    w = normalized(pd.Series(0.5 ** (np.asarray(age, dtype=float) / hl), index=starts))
    return w, {"age_from": str(ref), "half_life_days": hl, "max_age_days": float(age.max()),
               "effective_n": effective_n(w)}


def window_sets(cfg: dict) -> dict[str, pd.DatetimeIndex]:
    art = json.loads(resolve(cfg["scoring"]["validation_set"]).read_text())
    drops = [ts(w["start"]) for w in art["stress"]["drops"]]
    rebounds = [ts(w["start"]) for w in art["stress"]["rebounds"]]
    return {"LOOKALIKE25": pd.DatetimeIndex([ts(w["start"]) for w in art["windows"]]),
            "RECENT25": pd.DatetimeIndex([ts(w["start"]) for w in art["recent"]]),
            "STRESS": pd.DatetimeIndex(drops + rebounds),
            "STRESS_DROPS": pd.DatetimeIndex(drops), "STRESS_REBOUNDS": pd.DatetimeIndex(rebounds)}


def regimes(starts: pd.DatetimeIndex, cfg: dict) -> pd.Series:
    o = pd.read_parquet(resolve(cfg["scoring"]["regimes"]), columns=["y1_tercile", "y2_tercile"])
    o.index = pd.DatetimeIndex([ts(t) for t in o.index])
    o = o.reindex(starts)
    lab = o["y1_tercile"].astype(str) + "/" + o["y2_tercile"].astype(str)
    return lab.where(o["y1_tercile"].notna() & o["y2_tercile"].notna())
