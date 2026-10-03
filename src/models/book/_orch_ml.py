"""book_orch's fitted forecasters: load once per process, verified against the manifest (not a model).

The manifest (validation/book_orch_ml_v1.json, written by backtest/orch_train.py) lists, for every monthly retrain,
the pickled mu1 and mu3 models with their sha256, q (the 90th percentile of |mu3| among that model's in-sample
predictions) and the engine's half-spreads. book_orch's parameters carry the manifest's sha256, so the run key
changes when the artifacts change, and a model file whose sha256 differs from the manifest is refused.
scikit-learn is imported only here, when a manifest is loaded: the model registry and the tests work without it.
"""
from __future__ import annotations

import hashlib
import json
import pickle
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.config import resolve


@dataclass
class Forecaster:
    retrain: pd.Timestamp
    mu1: object
    mu3: object
    q: float


@dataclass
class Bundle:
    manifest_sha256: str
    features: list[str]
    forecasters: list[Forecaster]               # sorted by retrain time
    retrains: pd.DatetimeIndex
    half_spread: dict[str, float]
    default_half_spread: float

    def at(self, t: pd.Timestamp) -> Forecaster | None:
        """The latest model retrained at or before t (None before the first one)."""
        k = int(self.retrains.searchsorted(t, side="right")) - 1
        return self.forecasters[k] if k >= 0 else None

    def spread(self, coin: str) -> float:
        return float(self.half_spread.get(coin, self.default_half_spread))

    def predict(self, t: pd.Timestamp, X: pd.DataFrame) -> pd.DataFrame | None:
        """mu1 and mu3 per row of X (columns = features), and q; None before the first model or for an empty X."""
        f = self.at(t)
        if f is None or X.empty:
            return None
        A = X[self.features].to_numpy(dtype=float)
        return pd.DataFrame({"mu1": f.mu1.predict(A), "mu3": f.mu3.predict(A), "q": f.q}, index=X.index)


_CACHE: dict[tuple[str, str], Bundle] = {}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(manifest: str, manifest_sha256: str) -> Bundle:
    """The bundle of a manifest, read once per process and cached by (path, sha256)."""
    key = (str(manifest), str(manifest_sha256))
    if key in _CACHE:
        return _CACHE[key]
    raw = resolve(manifest).read_bytes()
    if sha256(raw) != manifest_sha256:
        raise ValueError(f"{manifest}: sha256 {sha256(raw)[:12]} differs from the parameters' {manifest_sha256[:12]}")
    m = json.loads(raw)
    import sklearn  # noqa: F401  (needed to unpickle; imported here so the registry works without it)
    fs = []
    for e in m["models"]:
        est = {}
        for h in ("mu1", "mu3"):
            data = resolve(e["files"][h]["path"]).read_bytes()
            if sha256(data) != e["files"][h]["sha256"]:
                raise ValueError(f"{e['files'][h]['path']}: sha256 differs from the manifest")
            est[h] = pickle.loads(data)
        fs.append(Forecaster(pd.Timestamp(e["retrain"]), est["mu1"], est["mu3"], float(e["q"])))
    fs.sort(key=lambda f: f.retrain)
    b = Bundle(manifest_sha256, list(m["features"]), fs, pd.DatetimeIndex([f.retrain for f in fs]),
               {k: float(v) for k, v in m["half_spread"].items()}, float(m["default_half_spread"]))
    _CACHE[key] = b
    return b


def adjust(b: pd.Series, pred: pd.DataFrame, half_spread, p: dict) -> tuple[pd.Series, pd.DataFrame]:
    """Layer T on the base's longs b (> 0): returns the new longs and, per coin, the numbers behind them.
    z = mu3 / q; adj = clip(k z, -cap, +cap), 0 if mu1 and mu3 disagree in sign; aim = b (1 + adj); the cost filter
    keeps aim = b unless |mu3| >= filter_mult x 2 x (fee + half-spread). If the total then exceeds the base's, the
    upward tilts are shrunk by one common factor until it does not (DEVIATION D1 of the pre-registration: scaling every
    adjusted coin could push a down-tilted coin below 0.5 b), so every coin stays within [0.5 b, 1.5 b] and the gross
    never exceeds the base's."""
    pr = pred.reindex(b.index)
    mu1, mu3, q = pr["mu1"], pr["mu3"], pr["q"]
    adj = (float(p["k"]) * mu3 / q).clip(-float(p["cap"]), float(p["cap"]))
    adj = adj.where(np.sign(mu1) == np.sign(mu3), 0.0).fillna(0.0)
    rtc = pd.Series({c: 2.0 * (float(p["fee"]) + float(half_spread(c))) for c in b.index})
    passed = (mu3.abs() >= float(p["filter_mult"]) * rtc) & mu3.notna()
    adj = adj.where(passed, 0.0)
    excess = float((b * adj).sum())                   # the total above the base's (negative: below it)
    up = adj > 0
    if excess > 0:
        s = 1.0 - excess / float((b[up] * adj[up]).sum())
        adj = adj.where(~up, adj * max(0.0, s))
    out = b * (1.0 + adj)
    info = pd.DataFrame({"b": b, "mu1": mu1, "mu3": mu3, "q": q, "adj": adj, "rtc": rtc, "passed": passed, "w": out})
    return out, info
