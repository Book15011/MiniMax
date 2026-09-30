"""Outcomes over (t0, t0 + horizon]: for EVALUATION only. Selection code may never read them."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.validation.features import BTC, StateEngine
from src.validation.guard import OUTCOME_COLUMNS, check_outcome_access

HOURS_PER_YEAR = 24 * 365


def compute_outcomes(engine: StateEngine, t0s: pd.DatetimeIndex, horizon_days: int) -> pd.DataFrame:
    h = pd.Timedelta(days=horizon_days)
    close_h = engine.data.close
    hidx = close_h.index
    H = close_h.to_numpy()
    cols = list(close_h.columns)
    col_pos = {c: j for j, c in enumerate(cols)}
    btc_h = col_pos[BTC]
    cd = engine.close_d
    rows = []
    for t0 in t0s:
        t1 = t0 + h
        u = engine.universe(t0)
        daily = cd.loc[t0:t1, BTC]
        p0, p1 = daily.iloc[0], daily.iloc[-1]
        y1 = np.log(p1 / p0)
        dr = np.diff(np.log(daily.to_numpy()))
        y4 = abs(y1) / np.abs(dr).sum() if np.abs(dr).sum() > 0 else np.nan

        lo, hi = hidx.searchsorted(t0, side="left"), hidx.searchsorted(t1, side="right")
        path = H[lo:hi, btc_h]
        path = path[~np.isnan(path)]
        hr = np.diff(np.log(path))
        y2 = hr.std(ddof=1) * np.sqrt(HOURS_PER_YEAR)
        y3 = float(np.max(1 - path / np.maximum.accumulate(path)))
        y8 = float(np.max(path / np.minimum.accumulate(path) - 1))

        ret = np.log(cd.loc[t1, u] / cd.loc[t0, u]).dropna()
        y5 = ret.std(ddof=1) if len(ret) >= 3 else np.nan
        alts = ret.drop(BTC, errors="ignore")
        y7 = alts.median() - ret[BTC] if BTC in ret and len(alts) else np.nan

        block = np.log(H[lo:hi][:, [col_pos[c] for c in u]])
        hrets = pd.DataFrame(np.diff(block, axis=0))
        keep = hrets.notna().mean() >= 0.95
        y6 = np.nan
        if keep.sum() >= 3:
            cm = hrets.loc[:, keep].corr().to_numpy()
            n = cm.shape[0]
            off = cm[~np.eye(n, dtype=bool)]
            y6 = float(np.nanmean(off)) if np.isfinite(off).any() else np.nan
        rows.append((y1, y2, y3, y4, y5, y6, y7, y8))
    return pd.DataFrame(rows, index=t0s, columns=list(OUTCOME_COLUMNS))


def regime_labels(outcomes: pd.DataFrame) -> pd.DataFrame:
    """Ex-post 3x3 regime grid: terciles of Y1 (return) x terciles of Y2 (volatility). For a LATER task."""
    names = ["low", "mid", "high"]
    r = pd.qcut(outcomes["Y1"], 3, labels=["down", "flat", "up"])
    v = pd.qcut(outcomes["Y2"], 3, labels=[f"{n}vol" for n in names])
    return pd.DataFrame({"y1_tercile": r.astype(str), "y2_tercile": v.astype(str),
                         "regime": r.astype(str) + "/" + v.astype(str)}, index=outcomes.index)


def save_outcomes(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path)


def load_outcomes(path: Path) -> pd.DataFrame:
    check_outcome_access()
    return pd.read_parquet(path)
