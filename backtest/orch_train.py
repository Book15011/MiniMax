"""Walk-forward training of book_orch's forecasters (reports/review/20261003-prereg-orch.md, section 3.2).

    PYTHONPATH=.:<pylib> python -m backtest.orch_train --kind real     --out results/book/20261003-book-orch/ml
    PYTHONPATH=.:<pylib> python -m backtest.orch_train --kind shuffled --out results/book/20261003-book-orch/ml

- Rows: every coin of the day's universe at every 16:00 UTC decision, features from the same code the model runs
  (src/models/book/_orch_features.py) on the same view the harness builds, the base's weight from the base's own
  decision history.
- Labels: y_H = close(t + 1 h + H) / close(t + 1 h) - 1 (entry after the engine's 1-hour lag), H = 24 h (mu1) and
  72 h (mu3); a close is the last one at or before the time, at most 24 h old. Rows with a missing label or feature
  are dropped.
- Walk-forward: a model per horizon at 00:00 UTC on the 1st of each month from the first row + 365 days, expanding,
  purged (t + 1 h + H <= the retrain time), HistGradientBoostingRegressor as pre-registered, single-threaded.
  q = the 90th percentile of |mu3| among the model's in-sample predictions.
- --kind shuffled: labels permuted within each calendar month of t (numpy default_rng(0), the same permutation for
  y1 and y3), everything else equal: the control of the ML gate.
Writes the pickled models (not committed), the out-of-sample predictions, and the manifest whose sha256 goes into
book_orch's parameters (validation/book_orch_ml_v1.json for --kind real).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import pickle
import platform
import time

import numpy as np
import pandas as pd

from backtest.data import load_market, universe_at
from backtest.engine import compute_targets, decision_times, view_frames
from src.config import REPO_ROOT, load_config, resolve
from src.contracts import MarketView
from src.models import get
from src.models.book._orch_features import FEATURES, coin_features, market_features

log = logging.getLogger("orch_train")
HOUR, DAY = pd.Timedelta(hours=1), pd.Timedelta(days=1)
HORIZONS = {"mu1": 24, "mu3": 72}
LAG_HOURS = 1
HGB = dict(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=200, l2_regularization=1.0, random_state=0,
           early_stopping=False)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def label_prices(close: pd.DataFrame, times: pd.DatetimeIndex, stale_h: int = 24) -> pd.DataFrame:
    """Last close at or before each time, at most stale_h hours old (rows = times)."""
    grid = pd.date_range(close.index[0], close.index[-1], freq="h")
    px = close.reindex(grid).ffill(limit=stale_h)
    return px.reindex(times)


def build_rows(market, cfg: dict, end: pd.Timestamp) -> pd.DataFrame:
    p = cfg["models"]["book_orch"]
    base = get(p["base"])
    first = pd.Timestamp(cfg["harness"]["first_window"], tz="UTC") + pd.Timedelta(hours=int(p["decision_hour_utc"]))
    times = decision_times(market.close.index, 24, int(p["decision_hour_utc"]), first, end)
    _, chain = compute_targets(base, market, times, p["base_params"], keep_raw=True)
    rows = []
    for t, b in zip(times, chain):
        c, q = view_frames(market.close, market.quote_volume, t)
        view = MarketView(t=t, close=c, quote_volume=q, universe=universe_at(market, t), params=p)
        coins = [x for x in view.universe if x in c.columns]
        if not coins:
            continue
        f = coin_features(view, coins, b, p["trend"], market_features(view, p["trend"]))
        f.insert(0, "coin", f.index)
        f.insert(0, "t", t)
        rows.append(f.reset_index(drop=True))
    df = pd.concat(rows, ignore_index=True)
    ts = pd.DatetimeIndex(sorted(df.t.unique()))
    for name, h in HORIZONS.items():
        e = label_prices(market.close, ts + LAG_HOURS * HOUR)
        x = label_prices(market.close, ts + (LAG_HOURS + h) * HOUR)
        e.index = x.index = ts
        y = (x / e - 1.0).stack(future_stack=True).rename(f"y_{name}")
        y.index.names = ["t", "coin"]
        df = df.join(y, on=["t", "coin"])
    return df


def shuffle_within_month(df: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    out = df.copy()
    rng = np.random.default_rng(seed)
    month = out.t.dt.year * 12 + out.t.dt.month
    cols = [f"y_{n}" for n in HORIZONS]
    for m in sorted(month.unique()):
        idx = np.flatnonzero((month == m).to_numpy())
        perm = rng.permutation(idx)
        out.loc[out.index[idx], cols] = out.loc[out.index[perm], cols].to_numpy()
    return out


def training_rows(df: pd.DataFrame, complete: pd.Series, R: pd.Timestamp, name: str) -> pd.DataFrame:
    """Rows a model retrained at R may learn from: features and label present, and the label ended by R (purge)."""
    h = HORIZONS[name]
    return df[complete & df[f"y_{name}"].notna() & (df.t + (LAG_HOURS + h) * HOUR <= R)]


def fit(X: np.ndarray, y: np.ndarray):
    from sklearn.ensemble import HistGradientBoostingRegressor
    return HistGradientBoostingRegressor(**HGB).fit(X, y)


def retrain_times(df: pd.DataFrame, end: pd.Timestamp) -> pd.DatetimeIndex:
    start = (df.t.min() + 365 * DAY)
    first = pd.Timestamp(year=start.year, month=start.month, day=1, tz="UTC")
    if first < start:
        first = first + pd.offsets.MonthBegin(1)
    return pd.date_range(first, end, freq="MS", tz="UTC")


def train(kind: str, out: str, manifest_path: str | None) -> dict:
    from sklearn import __version__ as skv
    cfg = load_config()
    market = load_market(cfg)
    end = market.close.index[-1] - (LAG_HOURS + max(HORIZONS.values())) * HOUR
    t0 = time.time()
    df = build_rows(market, cfg, end)
    log.info("rows %d (%d decisions) in %.0f s", len(df), df.t.nunique(), time.time() - t0)
    if kind == "shuffled":
        df = shuffle_within_month(df, 0)
    complete = df[FEATURES].notna().all(axis=1)
    odir = resolve(out) / kind
    odir.mkdir(parents=True, exist_ok=True)
    models, oos = [], []
    Rs = retrain_times(df, df.t.max())
    for k, R in enumerate(Rs):
        nxt = Rs[k + 1] if k + 1 < len(Rs) else df.t.max() + DAY
        entry, files, preds = {"retrain": R.isoformat(), "files": {}}, {}, {}
        for name, h in HORIZONS.items():
            y = f"y_{name}"
            tr = training_rows(df, complete, R, name)
            assert (tr.t + (LAG_HOURS + h) * HOUR <= R).all()
            m = fit(tr[FEATURES].to_numpy(dtype=float), tr[y].to_numpy(dtype=float))
            blob = pickle.dumps(m, protocol=4)
            path = odir / f"{R:%Y%m}_{name}.pkl"
            path.write_bytes(blob)
            files[name] = {"path": str(path.relative_to(REPO_ROOT)), "sha256": sha(blob)}
            entry[f"n_rows_{name}"] = int(len(tr))
            entry[f"last_label_end_{name}"] = (tr.t.max() + (LAG_HOURS + h) * HOUR).isoformat()
            if name == "mu3":
                entry["q"] = float(np.quantile(np.abs(m.predict(tr[FEATURES].to_numpy(dtype=float))), 0.9))
            te = df[complete & (df.t >= R) & (df.t < nxt)]
            preds[name] = pd.Series(m.predict(te[FEATURES].to_numpy(dtype=float)), index=te.index) if len(te) else None
        entry["files"] = files
        models.append(entry)
        if preds["mu3"] is not None:
            te = df.loc[preds["mu3"].index, ["t", "coin", "base_w", "y_mu1", "y_mu3"]].copy()
            te["mu1"], te["mu3"], te["q"], te["retrain"] = preds["mu1"], preds["mu3"], entry["q"], R
            oos.append(te)
        log.info("%s %s: rows %d / %d, q %.5f", kind, f"{R:%Y-%m}", entry["n_rows_mu1"], entry["n_rows_mu3"], entry["q"])
    oos_df = pd.concat(oos, ignore_index=True)
    oos_df.to_parquet(resolve(out) / f"oos_{kind}.parquet")
    df.to_parquet(resolve(out) / f"rows_{kind}.parquet")
    h = cfg["harness"]
    man = {"version": "book_orch_ml_v1", "kind": kind, "features": FEATURES, "horizons_hours": HORIZONS,
           "lag_hours": LAG_HOURS, "estimator": "HistGradientBoostingRegressor", "hyperparams": HGB,
           "shuffle": {"within": "calendar month of t", "seed": 0} if kind == "shuffled" else None,
           "libraries": {"scikit-learn": skv, "numpy": np.__version__, "pandas": pd.__version__,
                         "python": platform.python_version()},
           "threads": os.environ.get("OMP_NUM_THREADS"), "data": market.notes,
           "rows": int(len(df)), "rows_complete": int(complete.sum()), "first_row": df.t.min().isoformat(),
           "half_spread": {k: float(v) for k, v in market.half_spread.items()},
           "default_half_spread": float(h["default_half_spread_bps"]) / 1e4, "models": models}
    raw = (json.dumps(man, indent=1, sort_keys=True) + "\n").encode()
    mpath = resolve(manifest_path) if manifest_path else resolve(out) / f"manifest_{kind}.json"
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_bytes(raw)
    log.info("manifest %s sha256 %s; %d models in %.0f s", mpath, sha(raw), len(models), time.time() - t0)
    return {"manifest": str(mpath.relative_to(REPO_ROOT)), "manifest_sha256": sha(raw)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kind", choices=("real", "shuffled"), required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--manifest", default=None, help="where to write the manifest (default <out>/manifest_<kind>.json)")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ref = train(a.kind, a.out, a.manifest)
    print(json.dumps(ref))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
