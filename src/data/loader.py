from __future__ import annotations

import io
import logging
import os
import zipfile
from pathlib import Path

import pandas as pd

from src.config import load_config, resolve

log = logging.getLogger(__name__)

COLUMNS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume",
           "trades", "taker_buy_base", "taker_buy_quote", "ignore"]
PRICE_COLS = ["open", "high", "low", "close"]
# Epoch in ms is ~1.7e12 and in µs ~1.7e15; anything >= 1e14 is µs.
MICROSECOND_THRESHOLD = 10**14


def _default_dirs() -> tuple[Path, Path]:
    jcfg = load_config()["data"]["jobs"]["spot_klines_1m"]
    return resolve(jcfg["raw_dir"]), resolve(jcfg["parquet_dir"])


def normalize_time_units(df: pd.DataFrame) -> pd.DataFrame:
    """Convert one file's open_time/close_time to ms, detecting µs vs ms by magnitude."""
    is_us = df["open_time"] >= MICROSECOND_THRESHOLD
    if is_us.any() and not is_us.all():
        raise ValueError("file mixes millisecond and microsecond timestamps")
    if is_us.all():
        df = df.copy()
        df["open_time"] = df["open_time"] // 1000
        df["close_time"] = df["close_time"] // 1000
    return df


def read_kline_zip(path: str | Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as zf:
        csvs = [n for n in zf.namelist() if n.endswith(".csv")]
        if len(csvs) != 1:
            raise ValueError(f"{path}: expected exactly one CSV, found {csvs}")
        raw = zf.read(csvs[0])
    has_header = not raw[:1].isdigit()
    df = pd.read_csv(io.BytesIO(raw), header=0 if has_header else None, names=COLUMNS)
    df = df.drop(columns="ignore").astype({"open_time": "int64", "close_time": "int64", "trades": "int64"})
    return normalize_time_units(df)


def concat_klines(files: list[Path], label: str) -> pd.DataFrame:
    df = pd.concat([read_kline_zip(f) for f in files], ignore_index=True)
    df = df.sort_values("open_time", kind="stable")
    # Binance archives occasionally repeat a block of identical rows (e.g. VIRTUALUSDT 2026-07-16).
    n_before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    if len(df) < n_before:
        log.warning("%s: dropped %d exact duplicate rows", label, n_before - len(df))
    dups = df["open_time"].duplicated()
    if dups.any():
        raise ValueError(f"{label}: {int(dups.sum())} open_time values with conflicting rows")
    df.insert(0, "timestamp", pd.to_datetime(df["open_time"], unit="ms", utc=True))
    return df


def load_symbol(symbol: str, raw_dir: str | Path | None = None, parquet_dir: str | Path | None = None,
                use_cache: bool = True) -> pd.DataFrame:
    """All downloaded klines for one Binance symbol; `open_time`/`close_time` are UTC epoch ms."""
    d_raw, d_pq = _default_dirs() if raw_dir is None or parquet_dir is None else (None, None)
    raw_dir = Path(raw_dir or d_raw)
    parquet_dir = Path(parquet_dir or d_pq)
    files = sorted((raw_dir / symbol).glob("*.zip"))
    if not files:
        raise FileNotFoundError(f"no zips for {symbol} in {raw_dir / symbol}")

    cache = parquet_dir / f"{symbol}.parquet"
    newest = max(f.stat().st_mtime for f in files)
    if use_cache and cache.exists() and cache.stat().st_mtime >= newest:
        return pd.read_parquet(cache)

    df = concat_klines(files, symbol)
    parquet_dir.mkdir(parents=True, exist_ok=True)
    tmp = cache.with_name(cache.name + ".tmp")
    df.to_parquet(tmp, index=False)
    os.replace(tmp, cache)
    return df
