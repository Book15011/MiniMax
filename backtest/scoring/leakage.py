"""Gate G5, the leakage check (docs/EVALUATION.md section 3.5).

The harness builds each view from bars up to t, so the view's own API cannot reach the future. Pol's
lookahead_check (backtest/evaluate.py) re-runs decisions on those same views: it proves determinism, but a model
that reaches past t some other way would pass it. G5 therefore runs three checks at the same decision times:
1. determinism: Pol's lookahead_check, reused as is;
2. future noise: every price and volume after t is replaced by a random walk in a fresh copy of the panel, the
   view is rebuilt from that copy, and targets(view) must not change. This catches a model that reads past t
   through the arrays behind the view (e.g. ndarray.base) or through any object shared with the harness;
3. no I/O: opening files, reading data files or connecting a socket inside targets() fails the check (the
   contract forbids it, and a model that reads the panel from disk would see the future).
"""
from __future__ import annotations

import builtins
import contextlib
import io
import socket

import numpy as np
import pandas as pd

from backtest.data import Market, universe_at
from backtest.engine import view_frames
from backtest.evaluate import lookahead_check
from src.contracts import MarketView, Model

GUARDED = ((builtins, "open"), (io, "open"), (socket.socket, "connect"), (pd, "read_parquet"), (pd, "read_csv"),
           (pd, "read_json"), (pd, "read_pickle"), (np, "load"), (np, "loadtxt"), (np, "fromfile"))


@contextlib.contextmanager
def no_io():
    """Record (and refuse) file and network access while the block runs."""
    attempts: list[str] = []
    saved = [(obj, name, getattr(obj, name)) for obj, name in GUARDED]

    def deny(label):
        def refuse(*a, **k):
            attempts.append(f"{label}({a[0] if a else ''!r})")
            raise PermissionError(f"I/O is not allowed inside targets(): {label}")
        return refuse

    try:
        for obj, name, _ in saved:
            setattr(obj, name, deny(name))
        yield attempts
    finally:
        for obj, name, orig in saved:
            setattr(obj, name, orig)


def _prev(targets: pd.DataFrame, k: int) -> pd.Series:
    prev = targets.iloc[k - 1] if k > 0 else pd.Series(dtype=float)
    return prev[prev != 0.0]


def future_noise_check(model: Model, market: Market, targets: pd.DataFrame, params: dict, picks: list[int],
                       seed: int, sigma: float) -> list[str]:
    rng = np.random.default_rng(seed)
    idx = market.close.index
    fails = []
    for k in picks:
        t = targets.index[k]
        i = int(idx.searchsorted(t, side="right")) - 1     # last bar at or before t (t may be a gap hour)
        close, qv = market.close.copy(), market.quote_volume.copy()
        n_after = len(idx) - i - 1
        if n_after:
            last = close.iloc[: i + 1].ffill().iloc[-1].fillna(1.0).to_numpy()
            close.iloc[i + 1:] = last * np.exp(np.cumsum(rng.normal(0.0, sigma, (n_after, close.shape[1])), axis=0))
            qv.iloc[i + 1:] = rng.lognormal(10.0, 1.0, (n_after, qv.shape[1]))
        c, q = view_frames(close, qv, t)
        view = MarketView(t=t, close=c, quote_volume=q, universe=universe_at(market, t), params=params,
                          prev_targets=_prev(targets, k))
        w = model.targets(view).astype(float)
        w = w[w != 0.0].reindex(targets.columns).fillna(0.0)
        if not np.allclose(w.to_numpy(), targets.iloc[k].to_numpy(), rtol=0.0, atol=1e-12):
            fails.append(f"decision at {t} changed when the data after t was replaced by noise")
    return fails


def leakage_gate(model: Model, market: Market, targets: pd.DataFrame, params: dict, g: dict) -> dict:
    n, seed = int(g["decisions"]), int(g["seed"])
    picks = sorted(np.random.default_rng(seed).choice(len(targets), size=min(n, len(targets)), replace=False).tolist())
    out = {"decisions": len(picks), "determinism": [], "future_noise": [], "io": [], "errors": []}
    with no_io() as attempts:
        try:
            out["determinism"] = lookahead_check(model, market, targets, params, n=n, seed=seed)
            out["future_noise"] = future_noise_check(model, market, targets, params, picks, seed, float(g["noise_sigma"]))
        except Exception as e:                       # noqa: BLE001 - any crash fails the gate, with its reason
            out["errors"].append(f"{type(e).__name__}: {e}")
    out["io"] = sorted(set(attempts))
    out["pass"] = not (out["determinism"] or out["future_noise"] or out["io"] or out["errors"])
    return out
