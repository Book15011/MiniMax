"""Walk-forward training of book_orch's per-coin forecasters, v2 (reports/review/20261003-prereg-orch-v2.md, section 2).

    export PYTHONPATH=.:results/book/20261003-book-orch/pylib OMP_NUM_THREADS=1
    python -m backtest.orch_train rows  --out results/book/20261003-book-orch-v2/ml
    python -m backtest.orch_train time  --out results/book/20261003-book-orch-v2/ml --workers 6
    python -m backtest.orch_train train --out results/book/20261003-book-orch-v2/ml --kind real --workers 6 \
        --manifest validation/book_orch_v2_forecasts.json

rows:  the features (src/models/book/_orch_features.py) of the liquid coins at every hour from the universe's first
       day, with labels for h = 2, 4, 8 hours: entry at t + 1 h (the engine's lag), exit h hours later, both bars
       stamped exactly then (a data gap drops the label); c = 2 x (0.10% + the engine's half-spread); class FALL (0)
       if r < -c, RISE (2) if r > c, else FLAT (1). Hours with no bar (outages) are recomputed through the live path
       on the harness's padded view, as the live bot would see them.
time:  fits the largest L model once, single-threaded, and estimates the total for the three label sets.
train: per horizon, every Monday 16:00 UTC from the first with 365 days of rows: L (all purged rows, weights halving
       every 365 days of age) and S (purged rows of the last 180 days), HistGradientBoostingClassifier as
       pre-registered, training rows every 4th hour (0, 4, ..., 20 UTC), purged (label known before the retrain:
       t + 1 h + h < T). Every hour until the next retrain is predicted by both; the forecast is their average.
       --kind shuffled permutes the labels (all horizons together, by row) across every training row of the whole
       period; shuffled_hour permutes them across coins within each hour; numpy default_rng(0).
Writes the forecasts (and for `real` the pickled models) under --out/<kind>/ (not committed) and the manifest, whose
sha256 goes into book_orch's parameters.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import multiprocessing as mp
import os
import pickle
import platform
import time

import numpy as np
import pandas as pd

from backtest.data import load_market, universe_at
from backtest.engine import view_frames
from src.config import REPO_ROOT, load_config, resolve
from src.contracts import MarketView
from src.models.book._orch_features import FEATURES, feature_frame, features_at

log = logging.getLogger("orch_train")
HOUR, DAY = pd.Timedelta(hours=1), pd.Timedelta(days=1)
HORIZONS = (2, 4, 8)
LAG_HOURS = 1
FEE = 0.001
TRAIN_HOURS = (0, 4, 8, 12, 16, 20)
HALF_LIFE_DAYS, S_DAYS, FIRST_AFTER_DAYS = 365.0, 180, 365
RETRAIN_WEEKDAY, RETRAIN_HOUR = 0, 16          # Monday 16:00 UTC: the first 16:00 decision of each ISO week
HGB = dict(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=500, l2_regularization=1.0,
           random_state=0, early_stopping=False)
CLASSES = ("fall", "flat", "rise")              # label codes 0, 1, 2
SHORT = {"fall": "f", "flat": "n", "rise": "r"}  # forecast columns: pf8 = P(fall) at 8 h, pn = flat, pr = rise
KINDS = ("real", "shuffled", "shuffled_hour")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def file_sha(path) -> str:
    return sha(resolve(path).read_bytes())


def rel(path) -> str:
    """A path as recorded in the manifest: relative to the repository when it is inside it."""
    path = resolve(path)
    return str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT) else str(path)


# ---------------------------------------------------------------- rows -----------------------------------------------

def add_labels(df: pd.DataFrame, close: pd.DataFrame, half_spread: pd.Series) -> pd.DataFrame:
    """r_h, y_h (0 fall, 1 flat, 2 rise, -1 missing) and the round trip c for every (t, coin) row."""
    grid = pd.date_range(close.index[0], close.index[-1] + 10 * HOUR, freq="h")
    C = close.reindex(grid)                        # bars only: a gap is missing, never carried
    cols = {c: j for j, c in enumerate(C.columns)}
    A = C.to_numpy(dtype=float)
    ci = df.coin.map(cols).to_numpy(dtype=int)
    tp = grid.get_indexer(pd.DatetimeIndex(df.t))
    out = df.copy()
    hs = half_spread.reindex(df.coin).to_numpy(dtype=float)
    out["c"] = 2.0 * (FEE + hs)
    for h in HORIZONS:
        e, x = tp + LAG_HOURS, tp + LAG_HOURS + h
        ok = (x < len(grid))
        r = np.full(len(df), np.nan)
        r[ok] = A[x[ok], ci[ok]] / A[e[ok], ci[ok]] - 1.0
        y = np.where(r > out.c, 2, np.where(r < -out.c, 0, 1)).astype(np.int8)
        y[~np.isfinite(r)] = -1
        out[f"r{h}"], out[f"y{h}"] = r, y
    return out


def build_rows(market, cfg: dict) -> pd.DataFrame:
    trend = cfg["models"]["book_orch"]["trend"]
    first = market.universe_by_day.index[0]
    times = pd.date_range(first, market.close.index[-1], freq="h")
    t0 = time.time()
    df = feature_frame(market.close, market.quote_volume, times, lambda t: universe_at(market, t), trend)
    log.info("features: %d rows, %d hours in %.0f s", len(df), df.t.nunique(), time.time() - t0)
    gaps = times[~times.isin(market.close.index)]
    fixed = []
    for t in gaps:                                   # outage hours: the padded view the harness and the live bot see
        c, q = view_frames(market.close, market.quote_volume, t)
        f = features_at(MarketView(t=t, close=c, quote_volume=q, universe=universe_at(market, t)), trend)
        fixed.append(f.reset_index().assign(t=t)[["t", "coin"] + FEATURES])
    if fixed:
        df = pd.concat([df[~df.t.isin(gaps)]] + fixed, ignore_index=True).sort_values(["t", "coin"], kind="mergesort")
        df = df.reset_index(drop=True)
    log.info("outage hours recomputed through the live path: %d", len(gaps))
    df = add_labels(df, market.close, market.half_spread)
    df["sigma8"] = df["vol_30d"] * np.sqrt(8.0)
    return df


# ---------------------------------------------------------------- walk-forward ---------------------------------------

def retrain_times(first_row: pd.Timestamp, last_row: pd.Timestamp, every_weeks: int = 1) -> pd.DatetimeIndex:
    start = first_row + FIRST_AFTER_DAYS * DAY
    T = start.normalize() + RETRAIN_HOUR * HOUR
    while T < start or T.weekday() != RETRAIN_WEEKDAY:
        T += DAY
    return pd.date_range(T, last_row, freq=f"{7 * every_weeks}D")


def shuffled_labels(df: pd.DataFrame, kind: str, train: np.ndarray, seed: int = 0) -> dict[str, np.ndarray]:
    """Label arrays (y_h, r_h for every h) for a label set: unchanged for `real`; permuted by row for the controls."""
    cols = [f"y{h}" for h in HORIZONS] + [f"r{h}" for h in HORIZONS]
    lab = {c: df[c].to_numpy().copy() for c in cols}
    if kind == "real":
        return lab
    rng = np.random.default_rng(seed)
    idx = np.flatnonzero(train)
    if kind == "shuffled":
        src = idx[rng.permutation(len(idx))]
        dst = idx
    elif kind == "shuffled_hour":
        groups = pd.Series(idx).groupby(df.t.to_numpy()[idx]).indices
        keys = sorted(groups)
        dst = np.concatenate([idx[groups[g]] for g in keys])
        src = np.concatenate([idx[groups[g]][rng.permutation(len(groups[g]))] for g in keys])
    else:
        raise ValueError(f"unknown label set {kind!r}")
    for c in cols:
        lab[c][dst] = df[c].to_numpy()[src]
    return lab


# Worker state, set in the parent before the pool forks (copy-on-write, never written by workers).
G: dict = {}


def _init_globals(df: pd.DataFrame, kind: str, Ts: pd.DatetimeIndex, out_dir, save_models: bool) -> None:
    t_ns = df.t.to_numpy(dtype="datetime64[ns]").astype(np.int64)
    train = np.isin(df.t.dt.hour.to_numpy(), TRAIN_HOURS)
    G.update(X=df[FEATURES].to_numpy(dtype=np.float64), t=t_ns, train=train, lab=shuffled_labels(df, kind, train),
             sigma8=df.sigma8.to_numpy(dtype=float), Ts=Ts.asi8, end=int(df.t.max().value) + int(HOUR.value),
             out=out_dir, save=save_models, kind=kind)


def training_index(T_ns: int, h: int) -> tuple[np.ndarray, np.ndarray]:
    """Rows L and S may learn from at retrain T: training hours, label present, label known before T (purge)."""
    t, y = G["t"], G["lab"][f"y{h}"]
    known = t + (LAG_HOURS + h) * int(HOUR.value) < T_ns
    iL = np.flatnonzero(G["train"] & (y >= 0) & known)
    iS = iL[t[iL] > T_ns - S_DAYS * int(DAY.value)]
    return iL, iS


def _fit(X, y, w=None):
    from sklearn.ensemble import HistGradientBoostingClassifier
    from threadpoolctl import threadpool_limits
    with threadpool_limits(1):
        return HistGradientBoostingClassifier(**HGB).fit(X, y, sample_weight=w)


def _proba(m, X) -> np.ndarray:
    out = np.zeros((len(X), 3))
    if len(X):
        out[:, m.classes_.astype(int)] = m.predict_proba(X)
    return out


def _shares(y: np.ndarray, w: np.ndarray | None) -> list[float]:
    w = np.ones(len(y)) if w is None else w
    s = np.bincount(y, weights=w, minlength=3)
    return (s / s.sum()).tolist()


def _mu(y: np.ndarray, z: np.ndarray, w: np.ndarray | None) -> list[float]:
    """Mean of r_8 / sigma_8 per class (weighted), finite rows only; 0 for an empty class."""
    w = np.ones(len(y)) if w is None else w
    ok = np.isfinite(z)
    num = np.bincount(y[ok], weights=(w * z)[ok], minlength=3)
    den = np.bincount(y[ok], weights=w[ok], minlength=3)
    return np.where(den > 0, num / np.where(den > 0, den, 1.0), 0.0).tolist()


def fit_task(task: tuple[int, int]) -> dict:
    k, h = task
    T = int(G["Ts"][k])
    T_next = int(G["Ts"][k + 1]) if k + 1 < len(G["Ts"]) else G["end"]
    iL, iS = training_index(T, h)
    y = G["lab"][f"y{h}"]
    age = (T - G["t"][iL]) / float(DAY.value)
    wL = 0.5 ** (age / HALF_LIFE_DAYS)
    t0 = time.time()
    mL = _fit(G["X"][iL], y[iL].astype(int), wL)
    mS = _fit(G["X"][iS], y[iS].astype(int))
    secs = time.time() - t0
    pred = np.flatnonzero((G["t"] >= T) & (G["t"] < T_next))
    res = {"k": k, "h": h, "T": pd.Timestamp(T, tz="UTC").isoformat(), "n_L": int(len(iL)), "n_S": int(len(iS)),
           "last_label_known_L": pd.Timestamp(int(G["t"][iL].max()) + (LAG_HOURS + h) * int(HOUR.value),
                                              tz="UTC").isoformat() if len(iL) else None,
           "pbar_L": _shares(y[iL].astype(int), wL), "pbar_S": _shares(y[iS].astype(int), None),
           "pred": pred, "PL": _proba(mL, G["X"][pred]), "PS": _proba(mS, G["X"][pred]), "fit_s": secs, "files": {}}
    if h == 8:
        z = G["lab"]["r8"] / G["sigma8"]
        res["mu_L"], res["mu_S"] = _mu(y[iL].astype(int), z[iL], wL), _mu(y[iS].astype(int), z[iS], None)
    if G["save"]:
        for name, m in (("L", mL), ("S", mS)):
            blob = pickle.dumps(m, protocol=4)
            path = resolve(G["out"]) / "models" / f"{pd.Timestamp(T, tz='UTC'):%Y%m%d}_h{h}_{name}.pkl"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)
            res["files"][name] = {"path": rel(path), "sha256": sha(blob)}
    return res


def load_rows(out: str) -> pd.DataFrame:
    return pd.read_parquet(resolve(out) / "rows.parquet")


def time_one_fit(out: str, workers: int, every_weeks: int = 1) -> dict:
    df = load_rows(out)
    Ts = retrain_times(df.t.min(), df.t.max(), every_weeks)
    _init_globals(df, "real", Ts, resolve(out) / "timing", False)
    k = len(Ts) - 1
    iL, iS = training_index(int(Ts.asi8[k]), 8)
    y = G["lab"]["y8"]
    t0 = time.time()
    _fit(G["X"][iL], y[iL].astype(int), np.ones(len(iL)))
    big = time.time() - t0
    t0 = time.time()
    _fit(G["X"][iS], y[iS].astype(int))
    small = time.time() - t0
    rate = (big + small) / (len(iL) + len(iS))       # seconds per training row, single-threaded
    rows = sum(len(a) + len(b) for kk in range(len(Ts)) for a, b in [training_index(int(Ts.asi8[kk]), h)
                                                                      for h in HORIZONS])
    cpu = rate * rows
    est = {"largest_L_rows": int(len(iL)), "largest_L_s": round(big, 1), "S_rows": int(len(iS)), "S_s": round(small, 1),
           "retrains": len(Ts), "fits_per_label_set": 2 * len(HORIZONS) * len(Ts), "training_rows_total": int(rows),
           "cpu_hours_per_label_set": round(cpu / 3600, 2), "workers": workers,
           "wall_hours_all_three_sets": round(3 * cpu / workers / 3600, 2)}
    (resolve(out) / "timing.json").write_text(json.dumps(est, indent=1))
    return est


def train(out: str, kind: str, workers: int, manifest_path: str | None, every_weeks: int = 1) -> dict:
    from sklearn import __version__ as skv
    t_start = time.time()
    cfg = load_config()
    df = load_rows(out)
    rows_sha = file_sha(resolve(out) / "rows.parquet")
    Ts = retrain_times(df.t.min(), df.t.max(), every_weeks)
    odir = resolve(out) / kind
    odir.mkdir(parents=True, exist_ok=True)
    _init_globals(df, kind, Ts, odir, kind == "real")
    tasks = sorted([(k, h) for k in range(len(Ts)) for h in HORIZONS], key=lambda x: (-x[0], -x[1]))
    results = {}
    with mp.get_context("fork").Pool(workers) as pool:
        for n, r in enumerate(pool.imap_unordered(fit_task, tasks, chunksize=1)):
            results[(r["k"], r["h"])] = r
            if n % 50 == 0:
                log.info("%s: %d / %d fits, %.0f s", kind, n + 1, len(tasks), time.time() - t_start)
    pred_all = np.flatnonzero(df.t.to_numpy(dtype="datetime64[ns]").astype(np.int64) >= Ts.asi8[0])
    fc = pd.DataFrame({"t": df.t.to_numpy()[pred_all], "coin": df.coin.to_numpy()[pred_all]})
    pos = pd.Series(np.arange(len(pred_all)), index=pred_all)
    ens = {f"p{SHORT[c]}{h}{s}": np.full(len(pred_all), np.nan) for h in HORIZONS for c in CLASSES
           for s in ("", "_L", "_S")}
    pbar = {f"pbar_{c}{h}": np.full(len(pred_all), np.nan) for h in HORIZONS for c in CLASSES}
    e8 = np.full(len(pred_all), np.nan)
    retr = np.full(len(pred_all), np.datetime64("NaT"), dtype="datetime64[ns]")
    sig = df.sigma8.to_numpy()[pred_all]
    models, fit_s = [], {}
    for k, T in enumerate(Ts):
        entry = {"retrain": T.isoformat(), "horizons": {}}
        for h in HORIZONS:
            r = results[(k, h)]
            p = pos.reindex(r["pred"]).to_numpy(dtype=int)
            retr[p] = np.datetime64(T.tz_convert(None))
            P = 0.5 * (r["PL"] + r["PS"])
            bar = 0.5 * (np.asarray(r["pbar_L"]) + np.asarray(r["pbar_S"]))
            for j, c in enumerate(CLASSES):
                ens[f"p{SHORT[c]}{h}"][p] = P[:, j]
                ens[f"p{SHORT[c]}{h}_L"][p], ens[f"p{SHORT[c]}{h}_S"][p] = r["PL"][:, j], r["PS"][:, j]
                pbar[f"pbar_{c}{h}"][p] = bar[j]
            if h == 8:
                eL = r["PL"] @ np.asarray(r["mu_L"])
                eS = r["PS"] @ np.asarray(r["mu_S"])
                e8[p] = sig[p] * 0.5 * (eL + eS)
            entry["horizons"][str(h)] = {kk: r[kk] for kk in ("n_L", "n_S", "last_label_known_L", "pbar_L", "pbar_S",
                                                               "files") + (("mu_L", "mu_S") if h == 8 else ())}
            fit_s[f"{T:%Y-%m-%d}_h{h}"] = round(r["fit_s"], 2)
            entry["horizons"][str(h)]["pbar"] = bar.tolist()
            entry["horizons"][str(h)]["n_pred"] = int(len(p))
        models.append(entry)
    fc["retrain"] = pd.DatetimeIndex(retr).tz_localize("UTC")
    for kk, v in {**ens, **pbar}.items():
        fc[kk] = v
    fc["pbar_fall"] = fc[[f"pbar_fall{h}" for h in HORIZONS]].mean(axis=1)
    fc["pbar_rise"] = fc[[f"pbar_rise{h}" for h in HORIZONS]].mean(axis=1)
    fc["e8"] = e8
    fc["sigma8"] = sig
    lean = (["t", "coin", "retrain"] + [f"p{SHORT[c]}{h}" for h in HORIZONS for c in CLASSES]
            + ["pbar_fall", "pbar_rise", "e8", "sigma8"])
    fpath, dpath = odir / "forecasts.parquet", odir / "forecasts_detail.parquet"
    fc[lean].to_parquet(fpath, index=False)
    fc.to_parquet(dpath, index=False)
    market = load_market(cfg)
    market_notes, half = market.notes, market.half_spread
    man = {"version": "book_orch_v2", "kind": kind, "features": FEATURES, "horizons_hours": list(HORIZONS),
           "lag_hours": LAG_HOURS, "fee": FEE, "classes": list(CLASSES), "estimator": "HistGradientBoostingClassifier",
           "hyperparams": HGB, "train_hours_utc": list(TRAIN_HOURS), "half_life_days": HALF_LIFE_DAYS,
           "s_days": S_DAYS, "first_after_days": FIRST_AFTER_DAYS, "retrain": f"every {every_weeks} week(s), Monday 16:00 UTC",
           "shuffle": None if kind == "real" else {"how": kind, "seed": 0},
           "libraries": {"scikit-learn": skv, "numpy": np.__version__, "pandas": pd.__version__,
                         "python": platform.python_version()},
           "threads_per_fit": 1, "data": market_notes,
           "rows": {"path": rel(resolve(out) / "rows.parquet"), "sha256": rows_sha,
                    "n": int(len(df)), "first": df.t.min().isoformat(), "last": df.t.max().isoformat()},
           "forecasts": {"path": rel(fpath), "sha256": file_sha(fpath), "n": int(len(fc))},
           "forecasts_detail": {"path": rel(dpath), "sha256": file_sha(dpath)},
           "half_spread": {k: float(v) for k, v in half.items()}, "models": models}
    raw = (json.dumps(man, indent=1, sort_keys=True) + "\n").encode()
    mpath = resolve(manifest_path) if manifest_path else odir / "manifest.json"
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_bytes(raw)
    runtime = round(time.time() - t_start)
    (odir / "timings.json").write_text(json.dumps({"runtime_s": runtime, "workers": workers, "fit_s": fit_s}, indent=1))
    log.info("%s: manifest %s sha256 %s, %d retrains, %.0f s", kind, mpath, sha(raw), len(Ts), time.time() - t_start)
    return {"manifest": rel(mpath), "manifest_sha256": sha(raw), "runtime_s": runtime}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=("rows", "time", "train"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--kind", choices=KINDS, default="real")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--every-weeks", type=int, default=1)
    ap.add_argument("--manifest", default=None, help="where to write the manifest (default <out>/<kind>/manifest.json)")
    a = ap.parse_args(argv)
    if a.workers > 8:
        raise SystemExit("at most 8 workers (AGENTS.md)")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if a.step == "rows":
        cfg = load_config()
        df = build_rows(load_market(cfg), cfg)
        path = resolve(a.out) / "rows.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, index=False)
        print(json.dumps({"rows": len(df), "hours": int(df.t.nunique()), "sha256": file_sha(path)}))
    elif a.step == "time":
        print(json.dumps(time_one_fit(a.out, a.workers, a.every_weeks), indent=1))
    else:
        print(json.dumps(train(a.out, a.kind, a.workers, a.manifest, a.every_weeks)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
