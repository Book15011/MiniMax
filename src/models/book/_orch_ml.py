"""book_orch's forecasts, v2 (not a model): the stored out-of-sample forecasts and the live path.

The manifest (validation/book_orch_v2_forecasts.json, written by backtest/orch_train.py) lists the forecasts file with
its sha256, every weekly retrain with its models (L and S per horizon), base rates and class means, and the engine's
half-spreads. book_orch's parameters carry the manifest's sha256, so the run key changes with the forecasts, and a
file whose sha256 differs from the manifest is refused.

- load(manifest, sha) -> Store, read once per process and cached by (path, sha256). The scratch runner loads it
  before the first targets() call, so targets() does no I/O when the leakage gate checks it.
- Store.at(t): the forecasts of hour t (index = coin) with the signals of the pre-registration, section 2.5:
  q = mean over horizons of P(rise) - P(fall); p_rise, p_fall = means over horizons; rise_margin = p_rise -
  pbar_rise and fall_margin = p_fall - pbar_fall (confident when >= 0.15; FS's strong FALL when >= 0.25);
  e8 = the expected 8-hour return.
- live(view, ...): the same columns computed from the view with the models of the latest retrain at or before view.t
  (features_at + predict_proba). It needs scikit-learn; it serves the launch cards and the stored-vs-live test.
"""
from __future__ import annotations

import hashlib
import json
import pickle
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.config import resolve

HORIZONS = (2, 4, 8)
CLASSES = ("fall", "flat", "rise")
SHORT = {"fall": "f", "flat": "n", "rise": "r"}
PROB_COLS = [f"p{SHORT[c]}{h}" for h in HORIZONS for c in CLASSES]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def add_signals(df: pd.DataFrame) -> pd.DataFrame:
    pr = df[[f"pr{h}" for h in HORIZONS]].to_numpy(dtype=float)
    pf = df[[f"pf{h}" for h in HORIZONS]].to_numpy(dtype=float)
    out = df.copy()
    out["q"] = (pr - pf).mean(axis=1)
    out["p_rise"], out["p_fall"] = pr.mean(axis=1), pf.mean(axis=1)
    out["rise_margin"] = out.p_rise - out.pbar_rise
    out["fall_margin"] = out.p_fall - out.pbar_fall
    return out


@dataclass
class Store:
    manifest_sha256: str
    df: pd.DataFrame                 # sorted by t, then coin
    t_ns: np.ndarray
    half_spread: dict[str, float]
    default_half_spread: float
    first: pd.Timestamp

    def at(self, t: pd.Timestamp) -> pd.DataFrame | None:
        """The forecasts of hour t (index = coin); None if there are none (before the first model)."""
        lo, hi = np.searchsorted(self.t_ns, [t.value, t.value + 1])
        if lo == hi:
            return None
        return self.df.iloc[lo:hi].set_index("coin")

    def spread(self, coin: str) -> float:
        return float(self.half_spread.get(coin, self.default_half_spread))


_CACHE: dict[tuple[str, str], Store] = {}
_MANIFESTS: dict[tuple[str, str], dict] = {}
_MODELS: dict[tuple[str, str], object] = {}


def manifest(path: str, manifest_sha256: str) -> dict:
    key = (str(path), str(manifest_sha256))
    if key not in _MANIFESTS:
        raw = resolve(path).read_bytes()
        if sha256(raw) != manifest_sha256:
            raise ValueError(f"{path}: sha256 {sha256(raw)[:12]} differs from the parameters' {manifest_sha256[:12]}")
        _MANIFESTS[key] = json.loads(raw)
    return _MANIFESTS[key]


def load(path: str, manifest_sha256: str) -> Store:
    """The stored forecasts of a manifest, verified and cached by (path, sha256)."""
    key = (str(path), str(manifest_sha256))
    if key in _CACHE:
        return _CACHE[key]
    m = manifest(path, manifest_sha256)
    data = resolve(m["forecasts"]["path"]).read_bytes()
    if sha256(data) != m["forecasts"]["sha256"]:
        raise ValueError(f"{m['forecasts']['path']}: sha256 differs from the manifest")
    df = pd.read_parquet(resolve(m["forecasts"]["path"]))
    df = add_signals(df.sort_values(["t", "coin"], kind="mergesort").reset_index(drop=True))
    st = Store(manifest_sha256, df, df.t.to_numpy(dtype="datetime64[ns]").astype(np.int64), m["half_spread"],
               float(np.median(list(m["half_spread"].values()))) if m["half_spread"] else 0.0005, df.t.min())
    _CACHE[key] = st
    return st


def _model(entry: dict):
    key = (entry["path"], entry["sha256"])
    if key not in _MODELS:
        data = resolve(entry["path"]).read_bytes()
        if sha256(data) != entry["sha256"]:
            raise ValueError(f"{entry['path']}: sha256 differs from the manifest")
        import sklearn  # noqa: F401  (needed to unpickle; imported here so the registry works without it)
        _MODELS[key] = pickle.loads(data)
    return _MODELS[key]


def _proba(m, X: np.ndarray) -> np.ndarray:
    out = np.zeros((len(X), 3))
    if len(X):
        out[:, m.classes_.astype(int)] = m.predict_proba(X)
    return out


def live(view, path: str, manifest_sha256: str, trend: dict) -> pd.DataFrame | None:
    """Forecasts of the liquid coins at view.t from the view itself, with the latest retrain at or before view.t
    (the same columns as Store.at). None before the first retrain."""
    from src.models.book._orch_features import FEATURES, features_at
    m = manifest(path, manifest_sha256)
    Ts = pd.DatetimeIndex([e["retrain"] for e in m["models"]])
    k = int(Ts.searchsorted(view.t, side="right")) - 1
    if k < 0:
        return None
    entry = m["models"][k]
    X = features_at(view, trend)
    A = X[FEATURES].to_numpy(dtype=float)
    out = pd.DataFrame(index=X.index)
    out["retrain"] = Ts[k]
    bars = {}
    for h in HORIZONS:
        e = entry["horizons"][str(h)]
        PL, PS = _proba(_model(e["files"]["L"]), A), _proba(_model(e["files"]["S"]), A)
        P = 0.5 * (PL + PS)
        for j, c in enumerate(CLASSES):
            out[f"p{SHORT[c]}{h}"] = P[:, j]
        bars[h] = e["pbar"]
        if h == 8:
            sig = X["vol_30d"].to_numpy(dtype=float) * np.sqrt(8.0)
            out["e8"] = sig * 0.5 * (PL @ np.asarray(e["mu_L"]) + PS @ np.asarray(e["mu_S"]))
            out["sigma8"] = sig
    out["pbar_fall"] = float(np.mean([bars[h][0] for h in HORIZONS]))
    out["pbar_rise"] = float(np.mean([bars[h][2] for h in HORIZONS]))
    return add_signals(out)
