"""Hourly close / quote-volume panel for every downloaded spot symbol.

Bars are indexed by CLOSE time (open_time + 1h, UTC). Symbols with 1m data use resampled 1m bars
from `validation.hourly_from_1m` on; earlier bars come from the 1h archive.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import binance_symbol, resolve, universe
from src.data.loader import concat_klines, load_symbol

log = logging.getLogger(__name__)
HOUR_MS = 3_600_000


@dataclass
class HourlyPanel:
    close: pd.DataFrame
    quote_volume: pd.DataFrame
    notes: dict = field(default_factory=dict)

    def save(self, out_dir: Path) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        self.close.to_parquet(out_dir / "panel_close_1h.parquet")
        self.quote_volume.to_parquet(out_dir / "panel_quote_volume_1h.parquet")
        (out_dir / "panel_notes.json").write_text(json.dumps(self.notes, indent=1, default=str))

    @classmethod
    def load(cls, out_dir: Path) -> "HourlyPanel":
        return cls(pd.read_parquet(out_dir / "panel_close_1h.parquet"),
                   pd.read_parquet(out_dir / "panel_quote_volume_1h.parquet"),
                   json.loads((out_dir / "panel_notes.json").read_text()))


def resample_1m_to_1h(df: pd.DataFrame) -> pd.DataFrame:
    """Hourly bars from 1m bars: close = last 1m close in the hour, quote_volume = sum."""
    df = df.sort_values("open_time")
    g = df.groupby((df["open_time"] // HOUR_MS) * HOUR_MS, sort=True)
    return pd.DataFrame({"open_time": g.size().index.to_numpy(),
                         "close": g["close"].last().to_numpy(),
                         "quote_volume": g["quote_volume"].sum().to_numpy()})


def _indexed(df: pd.DataFrame) -> pd.DataFrame:
    out = df[["close", "quote_volume"]].copy()
    out.index = pd.to_datetime(df["open_time"].to_numpy() + HOUR_MS, unit="ms", utc=True)
    out.index.name = "close_time"
    return out


def overlap_check(h1: pd.DataFrame, m1_hourly: pd.DataFrame, month: str) -> dict:
    """Assert resampled-1m closes equal archived-1h closes for every hour of `month`."""
    start = pd.Timestamp(month + "-01", tz="UTC")
    end = start + pd.offsets.MonthBegin(1)
    lo, hi = int(start.timestamp() * 1000), int(end.timestamp() * 1000)
    a = h1[(h1.open_time >= lo) & (h1.open_time < hi)].set_index("open_time")["close"]
    b = m1_hourly[(m1_hourly.open_time >= lo) & (m1_hourly.open_time < hi)].set_index("open_time")["close"]
    expected = (hi - lo) // HOUR_MS
    res = {"month": month, "hours_expected": int(expected), "hours_1h": int(len(a)), "hours_1m": int(len(b)),
           "mismatches": int((a.reindex(b.index) != b).sum()) if len(a) == len(b) else None,
           "max_abs_diff": float((a.reindex(b.index) - b).abs().max()) if len(a) else None}
    assert len(a) == len(b) == expected, f"overlap check {month}: hour counts differ {res}"
    assert a.index.equals(b.index) and (a == b).all(), f"overlap check {month}: closes differ {res}"
    return res


def check_rename(old: pd.Series, new: pd.Series, rc: dict) -> dict:
    old, new = old.dropna(), new.dropna()
    both = old.index.intersection(new.index)
    res = {"old_last": str(old.index[-1]), "new_first": str(new.index[0]), "overlap_hours": int(len(both))}
    if len(both) >= rc["min_overlap_hours"]:
        d = np.abs(np.log(new[both] / old[both]))
        res.update(median_abs_log_diff=float(d.median()), max_abs_log_diff=float(d.max()),
                   clean=bool(d.median() <= rc["max_median_abs_log_diff"] and d.max() <= rc["max_abs_log_diff"]))
    else:
        gap_h = (new.index[0] - old.index[-1]) / pd.Timedelta(hours=1)
        jump = float(abs(np.log(new.iloc[0] / old.iloc[-1])))
        res.update(gap_hours=float(gap_h), jump_abs_log=jump,
                   clean=bool(gap_h <= rc["max_gap_hours"] and jump <= rc["max_gap_abs_log_diff"]))
    return res


def split_segments(s: pd.DataFrame, name: str, gap_days: int) -> dict[str, pd.DataFrame]:
    """Split at holes longer than gap_days. The newest segment keeps `name`; older ones get `name~until-DATE`."""
    idx = s.dropna(subset=["close"]).index
    if len(idx) == 0:
        return {}
    gaps = np.where(np.diff(idx.asi8) > gap_days * 86_400 * 10**9)[0]
    bounds = [0, *(gaps + 1), len(idx)]
    segs = {}
    for i in range(len(bounds) - 1):
        seg = s.loc[idx[bounds[i]]:idx[bounds[i + 1] - 1]]
        last = i == len(bounds) - 2
        segs[name if last else f"{name}~until-{idx[bounds[i + 1] - 1].date()}"] = seg
    return segs


def build_hourly_panel(cfg: dict) -> HourlyPanel:
    vcfg = cfg["validation"]
    jobs = cfg["data"]["jobs"]
    dir_1h = resolve(jobs["spot_klines_1h"]["raw_dir"])
    one_m_syms = {binance_symbol(p) for p in universe(cfg)}
    cut = int(pd.Timestamp(vcfg["hourly_from_1m"], tz="UTC").timestamp() * 1000)
    oc = vcfg["overlap_check"]
    symbols = sorted({p.name for p in dir_1h.iterdir() if p.is_dir()} | one_m_syms)

    notes: dict = {"sources": {}, "renames": [], "segments": {}}
    series: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        files = sorted((dir_1h / sym).glob("*.zip")) if (dir_1h / sym).exists() else []
        h1 = concat_klines(files, sym) if files else None
        parts = []
        if sym in one_m_syms:
            m1 = resample_1m_to_1h(load_symbol(sym))
            if sym == oc["symbol"]:
                notes["overlap_check"] = overlap_check(h1, m1, oc["month"])
            if h1 is not None:
                parts.append(h1[h1.open_time < cut])
            parts.append(m1[m1.open_time >= cut])
            notes["sources"][sym] = "1h archive < %s, resampled 1m after" % vcfg["hourly_from_1m"]
        elif h1 is not None:
            parts.append(h1)
            notes["sources"][sym] = "1h archive"
        else:
            continue
        df = pd.concat([p[["open_time", "close", "quote_volume"]] for p in parts], ignore_index=True)
        if df.open_time.duplicated().any():
            raise ValueError(f"{sym}: duplicate hourly bars after combining sources")
        series[sym] = _indexed(df.sort_values("open_time"))

    for r in vcfg["renames"]:
        old, new = r["old"], r["new"]
        if old not in series or new not in series:
            notes["renames"].append({**r, "clean": False, "reason": "one side has no data", "stitched": False})
            continue
        chk = check_rename(series[old]["close"], series[new]["close"], vcfg["rename_checks"])
        chk.update(r, stitched=chk["clean"])
        if chk["clean"]:
            first_new = series[new].dropna(subset=["close"]).index[0]
            series[new] = pd.concat([series[old][series[old].index < first_new], series[new]])
            del series[old]
        notes["renames"].append(chk)

    out: dict[str, pd.DataFrame] = {}
    for sym, df in series.items():
        segs = split_segments(df, sym, vcfg["segment_gap_days"])
        if len(segs) > 1:
            notes["segments"][sym] = {k: [str(v.index[0]), str(v.index[-1])] for k, v in segs.items()}
        out.update(segs)
    if "BTCUSDT" not in out or len(notes["segments"].get("BTCUSDT", {})) > 1:
        raise ValueError("BTCUSDT must be one continuous series")

    close = pd.concat({k: v["close"] for k, v in out.items()}, axis=1).sort_index()
    qv = pd.concat({k: v["quote_volume"] for k, v in out.items()}, axis=1).sort_index()
    notes["n_series"] = close.shape[1]
    notes["first"], notes["last"] = str(close.index[0]), str(close.index[-1])
    return HourlyPanel(close, qv, notes)
