"""BTCUSDT perpetual funding rate and open interest: lob-execution-hma copy + newer archive zips."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

from src.config import resolve


def _read_zip_csv(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as zf:
        (name,) = [n for n in zf.namelist() if n.endswith(".csv")]
        return pd.read_csv(io.BytesIO(zf.read(name)))


def _merge(frames: list[pd.DataFrame], key: str, value: str, label: str) -> pd.Series:
    df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=[key, value])
    if df[key].duplicated().any():
        raise ValueError(f"{label}: {int(df[key].duplicated().sum())} timestamps with conflicting values")
    return df.set_index(key)[value].sort_index()


def load_funding(cfg: dict, symbol: str = "BTCUSDT") -> pd.Series:
    """Funding prints indexed by funding time (UTC); value = last_funding_rate."""
    frames = [pd.read_parquet(p) for p in sorted((resolve(cfg["data"]["external_copy"]["dest"]) / "funding_rate")
                                                  .glob(f"{symbol}-funding_rate-*.parquet"))]
    frames += [_read_zip_csv(p) for p in sorted((resolve(cfg["data"]["jobs"]["futures_funding"]["raw_dir"]) / symbol)
                                                 .glob("*.zip"))]
    frames = [f[["calc_time", "last_funding_rate"]].astype({"calc_time": "int64", "last_funding_rate": "float64"})
              for f in frames]
    s = _merge(frames, "calc_time", "last_funding_rate", f"{symbol} funding")
    s.index = pd.to_datetime(s.index, unit="ms", utc=True)
    s.name = "funding_rate"
    return s


def load_open_interest(cfg: dict, symbol: str = "BTCUSDT") -> pd.Series:
    """Open-interest snapshots indexed by create_time (UTC); value = sum_open_interest (in BTC)."""
    frames = [pd.read_parquet(p) for p in sorted((resolve(cfg["data"]["external_copy"]["dest"]) / "open_interest")
                                                  .glob(f"{symbol}-open_interest-*.parquet"))]
    frames += [_read_zip_csv(p) for p in sorted((resolve(cfg["data"]["jobs"]["futures_metrics"]["raw_dir"]) / symbol)
                                                 .glob("*.zip"))]
    frames = [pd.DataFrame({"t": pd.to_datetime(f["create_time"], utc=True),
                            "oi": f["sum_open_interest"].astype("float64")}) for f in frames]
    s = _merge(frames, "t", "oi", f"{symbol} open interest")
    s.name = "open_interest"
    return s
