"""Open every downloaded kline zip and check it; write a JSON report.

Run from the repo root:  python -m src.data.integrity
"""
from __future__ import annotations

import calendar
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from src.config import binance_symbol, load_config, resolve, universe
from src.data.binance_spot_downloader import Manifest, sha256_file
from src.data.loader import PRICE_COLS, read_kline_zip

MINUTE_MS = 60_000
PERIOD_RE = re.compile(r"-(\d{4}-\d{2}(?:-\d{2})?)\.zip$")


def period_bounds(period: str) -> tuple[int, int]:
    """[start, end) of a YYYY-MM or YYYY-MM-DD period, in UTC epoch ms."""
    if len(period) == 7:
        y, m = map(int, period.split("-"))
        start = datetime(y, m, 1, tzinfo=timezone.utc)
        days = calendar.monthrange(y, m)[1]
    else:
        start = datetime.fromisoformat(period).replace(tzinfo=timezone.utc)
        days = 1
    s = int(start.timestamp() * 1000)
    return s, s + days * 1440 * MINUTE_MS


def _ms_to_str(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def missing_runs(present: np.ndarray, start: int, end: int) -> list[dict]:
    grid = np.arange(start, end, MINUTE_MS)
    missing = grid[~np.isin(grid, present)]
    if missing.size == 0:
        return []
    breaks = np.where(np.diff(missing) != MINUTE_MS)[0]
    starts = np.r_[missing[0], missing[breaks + 1]]
    ends = np.r_[missing[breaks], missing[-1]]
    return [{"from": _ms_to_str(a), "to": _ms_to_str(b), "minutes": int((b - a) // MINUTE_MS + 1)}
            for a, b in zip(starts, ends)]


def check_file(path: Path, expected_sha: str | None) -> dict:
    period = PERIOD_RE.search(path.name).group(1)
    start, end = period_bounds(period)
    res = {"file": path.name, "period": period, "expected_rows": (end - start) // MINUTE_MS}
    if expected_sha is not None:
        res["sha256_matches_manifest"] = sha256_file(path) == expected_sha
    df = read_kline_zip(path)
    t = df["open_time"].to_numpy()
    diffs = np.diff(t)
    res.update(
        rows=len(df),
        duplicate_ts=int(df["open_time"].duplicated().sum()),
        non_increasing=int((diffs <= 0).sum()),
        off_grid_ts=int((t % MINUTE_MS != 0).sum()),
        outside_period=int(((t < start) | (t >= end)).sum()),
        nonpositive_price_rows=int((df[PRICE_COLS] <= 0).any(axis=1).sum()),
        gaps=missing_runs(t, start, end),
        first=_ms_to_str(int(t.min())) if len(t) else None,
        last=_ms_to_str(int(t.max())) if len(t) else None,
    )
    res["intact"] = (res["rows"] == res["expected_rows"] and not res["gaps"] and res["duplicate_ts"] == 0
                     and res["non_increasing"] == 0 and res["off_grid_ts"] == 0 and res["outside_period"] == 0
                     and res["nonpositive_price_rows"] == 0 and res.get("sha256_matches_manifest", True))
    return res


def sweep(cfg: dict) -> dict:
    dcfg = cfg["data"]["binance_spot"]
    raw_dir = resolve(dcfg["raw_dir"])
    latest = Manifest(resolve(dcfg["manifest"])).latest()
    report = {}
    for sym in (binance_symbol(p) for p in universe(cfg)):
        files = sorted((raw_dir / sym).glob("*.zip"))
        checks = []
        for f in files:
            rec = latest.get(f"{sym}/{f.name}")
            try:
                checks.append(check_file(f, rec["sha256"] if rec and rec["status"] == "ok" else None))
            except Exception as e:  # noqa: BLE001 -- an unreadable file is a finding, not a crash
                checks.append({"file": f.name, "intact": False, "error": f"{type(e).__name__}: {e}"})
        mf = {k: v for k, v in latest.items() if k.startswith(f"{sym}/")}
        on_disk = {f.name for f in files}
        report[sym] = {
            "files": len(files),
            "first": min((c["first"] for c in checks if c.get("first")), default=None),
            "last": max((c["last"] for c in checks if c.get("last")), default=None),
            "rows": sum(c.get("rows", 0) for c in checks),
            "gaps": [dict(g, file=c["file"]) for c in checks for g in c.get("gaps", [])],
            "not_intact": [c for c in checks if not c["intact"]],
            "manifest_failed": sorted(k for k, v in mf.items() if v["status"] == "failed"),
            "manifest_not_listed": sorted(k for k, v in mf.items() if v["status"] == "not_listed"),
            "manifest_ok_missing_on_disk": sorted(k for k, v in mf.items()
                                                  if v["status"] == "ok" and k.split("/")[1] not in on_disk),
        }
    return report


def main() -> int:
    cfg = load_config()
    report = sweep(cfg)
    out = resolve(cfg["data"]["binance_spot"]["raw_dir"]).parent / "integrity_report.json"
    out.write_text(json.dumps(report, indent=1))
    print("| Symbol | Files | First | Last | Rows | Gaps (count: min) | Not intact | Failed |")
    print("|---|---|---|---|---|---|---|---|")
    for sym, r in report.items():
        gap_min = sum(g["minutes"] for g in r["gaps"])
        print(f"| {sym} | {r['files']} | {r['first']} | {r['last']} | {r['rows']:,} | "
              f"{len(r['gaps'])}: {gap_min} | {len(r['not_intact'])} | {len(r['manifest_failed'])} |")
    print(f"\nreport: {out}")
    bad = any(r["not_intact"] or r["manifest_failed"] or r["manifest_ok_missing_on_disk"] for r in report.values())
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
