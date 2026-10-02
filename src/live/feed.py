"""Hourly bars for the live bot: the same panel the backtest reads, kept up to date while the bot runs.

- Store: hourly close and quote volume for every panel series (the universe ranks all of them, not only the
  Roostoo-listed ones), indexed by bar CLOSE time (UTC), in <state_dir>/close_1h.parquet and qv_1h.parquet.
- Seed: the last `history_days` of the research panel (data/validation), copied once (`seed`).
- Top-up, in order: Binance REST klines (exact, if reachable: it is blocked on the research server) ->
  the data.binance.vision daily archive (full UTC days, published the next day) -> the Roostoo ticker's last
  price and 24-hour quote volume for the newest bar only (Roostoo-listed coins; see fill_ticker_volume).
- `complete_through` is the newest bar that every source-backed series has; bars after it may be ticker-only.
  The universe is ranked only on complete data, so a ticker-only hour can never change it.
- An archive day counts as published when BTC's file is; another coin without a file that day had no data.
"""
from __future__ import annotations

import io
import json
import logging
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import requests

HOUR = pd.Timedelta(hours=1)
UTC = "UTC"


def _ms_to_ts(x) -> pd.DatetimeIndex:
    """Binance open times: ms, or µs in the spot archive since 2025."""
    a = np.asarray(x, dtype="int64")
    return pd.DatetimeIndex(pd.to_datetime(np.where(a > 10**14, a // 1000, a), unit="ms", utc=True))


def klines_frame(rows: list) -> pd.DataFrame:
    """Binance kline rows (REST JSON or archive CSV) -> close and quote volume, indexed by bar CLOSE time."""
    if not len(rows):
        return pd.DataFrame(columns=["close", "qv"], dtype=float)
    df = pd.DataFrame(rows).iloc[:, :8]
    idx = _ms_to_ts(df.iloc[:, 0]) + HOUR
    return pd.DataFrame({"close": df.iloc[:, 4].astype(float).to_numpy(), "qv": df.iloc[:, 7].astype(float).to_numpy()},
                        index=idx)


class SourceDown(Exception):
    """A source cannot be reached at all (blocked or offline): skip it for the rest of this top-up."""


def rest_fetcher(url: str, timeout: float = 10.0, session: requests.Session | None = None) -> Callable:
    http = session or requests.Session()

    def fetch(symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        """Bars with close time in (start, end]."""
        out = []
        t = start
        while t < end:
            try:
                r = http.get(url, params={"symbol": symbol, "interval": "1h", "limit": 1000,
                                          "startTime": int((t).timestamp() * 1000),
                                          "endTime": int((end - HOUR).timestamp() * 1000)}, timeout=timeout)
            except requests.RequestException as e:
                raise SourceDown(f"Binance REST: {type(e).__name__}") from e
            if r.status_code in (403, 418, 451):
                raise SourceDown(f"Binance REST: HTTP {r.status_code}")
            if r.status_code == 400:                       # unknown symbol (delisted): nothing to add
                return klines_frame([])
            r.raise_for_status()
            rows = r.json()
            if not rows:
                break
            out.extend(rows)
            t = pd.Timestamp(int(rows[-1][0]), unit="ms", tz=UTC) + HOUR
            if len(rows) < 1000:
                break
        f = klines_frame(out)
        return f[(f.index > start) & (f.index <= end)]
    return fetch


def archive_fetcher(base_url: str, timeout: float = 20.0, session: requests.Session | None = None) -> Callable:
    http = session or requests.Session()

    def fetch(symbol: str, day: pd.Timestamp) -> pd.DataFrame | None:
        """One UTC day of 1h bars, or None if the file is not published yet."""
        url = f"{base_url.rstrip('/')}/spot/daily/klines/{symbol}/1h/{symbol}-1h-{day:%Y-%m-%d}.zip"
        try:
            r = http.get(url, timeout=timeout)
        except requests.RequestException as e:
            raise SourceDown(f"archive: {type(e).__name__}") from e
        if r.status_code == 404:
            return None
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            raw = z.read(z.namelist()[0]).decode()
        rows = [ln.split(",") for ln in raw.splitlines() if ln and ln[0].isdigit()]
        return klines_frame(rows)
    return fetch


@dataclass
class Store:
    close: pd.DataFrame
    qv: pd.DataFrame
    complete_through: pd.Timestamp
    ticker_only: set = field(default_factory=set)      # bar times filled from the ticker alone

    @classmethod
    def load(cls, d: Path) -> "Store":
        close, qv = pd.read_parquet(d / "close_1h.parquet"), pd.read_parquet(d / "qv_1h.parquet")
        meta = json.loads((d / "store_meta.json").read_text())
        return cls(close, qv, pd.Timestamp(meta["complete_through"]),
                   {pd.Timestamp(t) for t in meta.get("ticker_only", [])})

    def save(self, d: Path) -> None:
        d.mkdir(parents=True, exist_ok=True)
        for name, df in (("close_1h", self.close), ("qv_1h", self.qv)):
            tmp = d / f"{name}.parquet.tmp"
            df.to_parquet(tmp)
            tmp.replace(d / f"{name}.parquet")
        meta = {"complete_through": str(self.complete_through), "ticker_only": sorted(str(t) for t in self.ticker_only)}
        tmp = d / "store_meta.json.tmp"
        tmp.write_text(json.dumps(meta))
        tmp.replace(d / "store_meta.json")

    def put(self, symbol: str, f: pd.DataFrame) -> int:
        """Write source-backed bars for one series; they replace ticker-only values."""
        if f.empty:
            return 0
        idx = self.close.index.union(f.index)
        self.close, self.qv = self.close.reindex(idx), self.qv.reindex(idx)
        for df in (self.close, self.qv):
            if symbol not in df:
                df[symbol] = np.nan
        self.close.loc[f.index, symbol] = f["close"].to_numpy()
        self.qv.loc[f.index, symbol] = f["qv"].to_numpy()
        return len(f)

    def trim(self, days: int) -> None:
        keep = self.close.index >= self.close.index[-1] - pd.Timedelta(days=days)
        self.close, self.qv = self.close.loc[keep], self.qv.loc[keep]
        self.ticker_only = {t for t in self.ticker_only if t >= self.close.index[0]}


def seed(panel_dir: Path, days: int) -> Store:
    """The last `days` of the research panel, live series only (segments of renamed coins end with '~')."""
    close = pd.read_parquet(panel_dir / "panel_close_1h.parquet")
    qv = pd.read_parquet(panel_dir / "panel_quote_volume_1h.parquet")
    keep = close.index >= close.index[-1] - pd.Timedelta(days=days)
    cols = [c for c in close.columns if "~" not in c and close.loc[keep, c].notna().any()]   # drop delisted series
    return Store(close.loc[keep, cols].copy(), qv.loc[keep, cols].copy(), close.index[-1])


def top_up(store: Store, upto: pd.Timestamp, rest: Callable | None, archive: Callable | None,
           ticker_closes: Callable[[], dict[str, float]] | None, log: logging.Logger,
           ticker_volumes: Callable[[], dict[str, float]] | None = None) -> dict:
    """Bring every series up to bar `upto` (a completed bar close time). Returns what each source added."""
    added = {"rest": 0, "archive": 0, "ticker": 0, "sources_down": []}
    symbols = list(store.close.columns)
    start = store.complete_through
    if upto <= start:
        return added
    done = False
    if rest is not None:
        try:
            for s in symbols:
                added["rest"] += store.put(s, rest(s, start, upto))
            store.complete_through = upto
            done = True
        except SourceDown as e:
            added["sources_down"].append(str(e))
            log.warning("feed: %s; trying the archive", e)
    if not done and archive is not None:
        day = start.floor("D")
        ref = "BTCUSDT" if "BTCUSDT" in symbols else symbols[0]
        try:
            while day + pd.Timedelta(days=1) <= upto:
                f_ref = archive(ref, day)
                if f_ref is None:
                    break                                   # that day is not published yet
                for s in symbols:                           # another coin's missing file: no data that day
                    f = f_ref if s == ref else archive(s, day)
                    if f is not None:
                        added["archive"] += store.put(s, f[(f.index > start) & (f.index <= upto)])
                store.complete_through = day + pd.Timedelta(days=1)
                day += pd.Timedelta(days=1)
        except SourceDown as e:
            added["sources_down"].append(str(e))
            log.warning("feed: %s", e)
    store.ticker_only -= {t for t in store.ticker_only if t <= store.complete_through}
    filled = False
    if store.close.index[-1] < upto or store.close.loc[upto].isna().all():
        if ticker_closes is not None:
            px = ticker_closes()
            idx = store.close.index.union(pd.DatetimeIndex([upto]))
            store.close, store.qv = store.close.reindex(idx), store.qv.reindex(idx)
            for s, p in px.items():
                if s in store.close and p > 0:
                    store.close.loc[upto, s] = p
                    added["ticker"] += 1
            store.ticker_only.add(upto)
            filled = True
    full = pd.date_range(store.close.index[0], store.close.index[-1], freq="h")
    store.close, store.qv = store.close.reindex(full), store.qv.reindex(full)
    if filled and ticker_volumes is not None:
        added["ticker_qv"] = fill_ticker_volume(store, upto, ticker_volumes())
    return added


def fill_ticker_volume(store: Store, upto: pd.Timestamp, v24: dict[str, float]) -> int:
    """Quote volume of the ticker-only bar `upto` from each coin's rolling 24-hour quote volume (the Roostoo ticker's
    UnitTradeValue, which is Binance's own 24 h figure: identical on all 86 shared pairs, checked 2026-10-02).

    The bar gets v24 minus the 23 bars before it, so the 24-hour sum ending at `upto` equals the ticker's figure, which
    is what the 24-hour volume ratios read. With a hole in those 23 bars it gets v24 / 24. Never negative. The archive
    or REST replaces it later, like the ticker's price."""
    n = 0
    prev = store.qv.loc[upto - pd.Timedelta(hours=23):upto - pd.Timedelta(hours=1)]
    for s, v in v24.items():
        if s not in store.qv or not v > 0:
            continue
        before = prev[s]
        est = v - float(before.sum()) if len(before) == 23 and before.notna().all() else v / 24.0
        store.qv.loc[upto, s] = max(est, 0.0)
        n += 1
    return n
