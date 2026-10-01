"""Fetch FRED series as CSV snapshots (no API key) and load the newest snapshot of each.

Run from the repo root:  python -m src.data.fred
"""
from __future__ import annotations

import hashlib
import io
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from src.config import load_config, resolve
from src.data.binance_downloader import Manifest

log = logging.getLogger("fred")


class FredUnavailable(RuntimeError):
    pass


def parse_fred_csv(text: str, series: str) -> pd.Series:
    df = pd.read_csv(io.StringIO(text))
    date_col = df.columns[0]
    if series not in df.columns:
        raise ValueError(f"{series}: column missing in FRED CSV (got {list(df.columns)})")
    s = pd.to_numeric(df[series].replace(".", None), errors="coerce")
    s.index = pd.to_datetime(df[date_col])
    s.name = series
    return s.dropna().sort_index()


def fetch(cfg: dict, attempts: int = 3) -> dict[str, str]:
    """Download every configured series; returns {series: status}. Raises FredUnavailable if none succeed."""
    fcfg = cfg["data"]["fred"]
    out_dir = resolve(fcfg["dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = Manifest(out_dir / "_manifest.jsonl")
    status = {}
    for sid in fcfg["series"]:
        url = fcfg["url"].format(series=sid)
        rec = {"file": None, "series": sid, "url": url, "sha256": None, "bytes": None, "reason": ""}
        for a in range(1, attempts + 1):
            try:
                r = requests.get(url, timeout=60)
                r.raise_for_status()
                s = parse_fred_csv(r.text, sid)
                if s.empty:
                    raise ValueError("no observations")
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                path = out_dir / f"{sid}__{stamp}.csv"
                path.write_bytes(r.content)
                rec.update(status="ok", file=path.name, sha256=hashlib.sha256(r.content).hexdigest(),
                           bytes=len(r.content), rows=int(len(s)), first=str(s.index[0].date()),
                           last=str(s.index[-1].date()))
                break
            except Exception as e:  # noqa: BLE001 -- recorded, then retried or reported
                rec.update(status="failed", reason=f"{type(e).__name__}: {e}"[:300])
                time.sleep(3 * a)
        rec["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        manifest.append(rec)
        status[sid] = rec["status"]
        log.info("%s: %s %s", sid, rec["status"], rec.get("last") or rec["reason"])
    if not any(v == "ok" for v in status.values()):
        raise FredUnavailable(f"FRED unreachable: {status}")
    return status


def load(cfg: dict, pins: dict[str, dict] | None = None) -> tuple[dict[str, pd.Series], dict[str, dict]]:
    """One snapshot per series and the manifest record it came from: the pinned file when `pins`
    ({series: {"file", "sha256"}}) is given, else the newest ok snapshot."""
    fcfg = cfg["data"]["fred"]
    out_dir = resolve(fcfg["dir"])
    latest: dict[str, dict] = {}
    for rec in Manifest(out_dir / "_manifest.jsonl").iter_records():
        if rec.get("status") != "ok":
            continue
        if pins is None or pins.get(rec["series"], {}).get("file") == rec["file"]:
            latest[rec["series"]] = rec
    if pins is not None and set(pins) - set(latest):
        raise FileNotFoundError(f"pinned FRED snapshots not found in the manifest: {sorted(set(pins) - set(latest))}")
    series = {}
    for sid, rec in latest.items():
        raw = (out_dir / rec["file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != rec["sha256"]:
            raise ValueError(f"{rec['file']}: sha256 differs from manifest")
        series[sid] = parse_fred_csv(raw.decode(), sid)
    return series, latest


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    try:
        st = fetch(load_config())
    except FredUnavailable as e:
        log.error("%s", e)
        return 2
    return 0 if all(v == "ok" for v in st.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
