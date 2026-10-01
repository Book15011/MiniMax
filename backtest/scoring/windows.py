"""Which windows are scored and how they are weighted (docs/EVALUATION.md section 1).

- Pool: the harness's window starts with the holdout sealed (backtest.evaluate.window_starts), thinned by
  scoring.stride_days and anchored on the newest start so the most recent window is always scored.
- LIVE-LIKE weights: validation/live_like_v1.json (PART 0), restricted to the scored windows, renormalized.
- RECENCY weights: 0.5 ** (age / half-life), age = days from a window's end to T*.
- Sets from the validation artifact: LOOKALIKE25, RECENT25, and STRESS (10 drops + 10 rebounds).
- Regimes: the ex-post 3x3 grid written by the validation build (terciles of BTC return x volatility).
"""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd

from backtest.data import Market
from backtest.evaluate import holdout_start, window_starts
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


def scored_starts(market: Market, cfg: dict, stride: int | None = None) -> pd.DatetimeIndex:
    pool = window_starts(market, cfg, holdout=False)
    days = pd.Timedelta(days=cfg["harness"]["window_days"])
    if len(pool) and pool[-1] + days > holdout_start(cfg):
        raise AssertionError("a scored window reaches into the sealed holdout")
    return thin(pool, int(cfg["scoring"]["stride_days"] if stride is None else stride))


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
    sc = cfg["scoring"]
    t_star, hl = ts(sc["t_star"]), float(sc["recency_half_life_days"])
    end = starts + pd.Timedelta(days=cfg["harness"]["window_days"])
    age = (t_star - end) / pd.Timedelta(days=1)
    w = normalized(pd.Series(0.5 ** (np.asarray(age, dtype=float) / hl), index=starts))
    return w, {"t_star": str(t_star), "half_life_days": hl, "min_age_days": float(age.min()),
               "effective_n": effective_n(w)}


def window_sets(cfg: dict) -> dict[str, pd.DatetimeIndex]:
    art = json.loads(resolve(cfg["scoring"]["validation_set"]).read_text())
    stress = [w["start"] for w in art["stress"]["drops"]] + [w["start"] for w in art["stress"]["rebounds"]]
    return {"LOOKALIKE25": pd.DatetimeIndex([ts(w["start"]) for w in art["windows"]]),
            "RECENT25": pd.DatetimeIndex([ts(w["start"]) for w in art["recent"]]),
            "STRESS": pd.DatetimeIndex([ts(s) for s in stress])}


def regimes(starts: pd.DatetimeIndex, cfg: dict) -> pd.Series:
    o = pd.read_parquet(resolve(cfg["scoring"]["regimes"]), columns=["y1_tercile", "y2_tercile"])
    o.index = pd.DatetimeIndex([ts(t) for t in o.index])
    o = o.reindex(starts)
    lab = o["y1_tercile"].astype(str) + "/" + o["y2_tercile"].astype(str)
    return lab.where(o["y1_tercile"].notna() & o["y2_tercile"].notna())
