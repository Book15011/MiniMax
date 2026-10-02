"""Download data.binance.vision archives (spot klines, futures funding/metrics), sha256-verified.

Run from the repo root:  python -m src.data.binance_downloader [--job NAME ...]
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import logging
import os
import random
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests

from src.config import binance_symbol, load_config, resolve, universe

log = logging.getLogger("binance_downloader")

MAX_WORKERS_CAP = 8
MAX_ATTEMPTS = 5
TIMEOUT_S = 60
RETRY_STATUS = {408, 429, 500, 502, 503, 504}
# A daily file that 404s this close to the newest published day may simply not be published yet.
RECENT_RETRY_DAYS = 7


class AlreadyRunning(RuntimeError):
    pass


class NotFound(Exception):
    pass


@dataclass(frozen=True)
class Task:
    market: str  # "spot" | "futures/um"
    dataset: str  # "klines" | "fundingRate" | "metrics"
    symbol: str
    granularity: str  # "monthly" | "daily"
    period: str  # "YYYY-MM" | "YYYY-MM-DD"
    interval: str | None = None  # klines only

    @property
    def filename(self) -> str:
        tag = self.interval if self.dataset == "klines" else self.dataset
        return f"{self.symbol}-{tag}-{self.period}.zip"

    @property
    def key(self) -> str:
        return f"{self.symbol}/{self.filename}"

    def url(self, base_url: str) -> str:
        sub = f"{self.symbol}/{self.interval}" if self.dataset == "klines" else self.symbol
        return f"{base_url}/{self.market}/{self.granularity}/{self.dataset}/{sub}/{self.filename}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_checksum(text: str) -> tuple[str, str]:
    """`.CHECKSUM` files are `<sha256>  <filename>`."""
    parts = text.strip().split()
    if len(parts) != 2 or len(parts[0]) != 64:
        raise ValueError(f"unexpected .CHECKSUM content: {text[:120]!r}")
    return parts[0].lower(), parts[1]


def verify_checksum(path: Path, checksum_text: str) -> tuple[bool, str, str]:
    """Return (matches, expected_sha, actual_sha); also requires the filename to match."""
    expected, name = parse_checksum(checksum_text)
    actual = sha256_file(path)
    return (expected == actual and name == path.name.removesuffix(".part")), expected, actual


class Manifest:
    """Append-only JSONL log. It is only ever opened in 'a' mode and never rewritten."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def append(self, record: dict) -> None:
        line = json.dumps(record, sort_keys=True)
        with self._lock, open(self.path, "a") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())

    def iter_records(self):
        if not self.path.exists():
            return
        with open(self.path) as f:
            for n, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    log.warning("manifest line %d is not valid JSON; ignored (left in place)", n)

    def latest(self) -> dict[str, dict]:
        return {rec["file"]: rec for rec in self.iter_records()}


class SingleInstanceLock:
    """flock-based; a second process fails immediately. The lock file itself is never deleted."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._fd = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = open(self.path, "a+")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            fd.seek(0)
            holder = fd.read().strip()
            fd.close()
            raise AlreadyRunning(f"another downloader holds {self.path} (pid {holder or '?'})")
        fd.seek(0)
        fd.truncate()
        fd.write(str(os.getpid()))
        fd.flush()
        self._fd = fd
        return self

    def __exit__(self, *exc):
        fcntl.flock(self._fd, fcntl.LOCK_UN)
        self._fd.close()


_thread_local = threading.local()


def _session() -> requests.Session:
    if not hasattr(_thread_local, "session"):
        _thread_local.session = requests.Session()
    return _thread_local.session


def http_get(url: str, method: str = "GET") -> requests.Response:
    """GET/HEAD with retry + exponential backoff. Raises NotFound on 404 (not retried)."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            r = _session().request(method, url, timeout=TIMEOUT_S)
            if r.status_code == 404:
                raise NotFound(url)
            if r.status_code in RETRY_STATUS:
                raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
            r.raise_for_status()
            return r
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            if attempt == MAX_ATTEMPTS:
                raise
            delay = min(60.0, 2.0**attempt) + random.uniform(0, 1)
            log.warning("attempt %d/%d failed for %s: %s; retrying in %.1fs", attempt, MAX_ATTEMPTS, url, e, delay)
            time.sleep(delay)
    raise AssertionError("unreachable")


def remote_today(base_url: str) -> date:
    """Today's UTC date from the archive server's Date header (the local clock is not trusted)."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            r = _session().head(base_url.rsplit("/data", 1)[0] + "/", timeout=TIMEOUT_S)
            return parsedate_to_datetime(r.headers["Date"]).astimezone(timezone.utc).date()
        except (requests.ConnectionError, requests.Timeout, KeyError):
            if attempt == MAX_ATTEMPTS:
                raise
            time.sleep(2.0**attempt)
    raise AssertionError("unreachable")


def month_range(start: str, end: str) -> list[str]:
    y, m = map(int, start.split("-"))
    ey, em = map(int, end.split("-"))
    out = []
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def day_range(start: date, end: date) -> list[str]:
    return [(start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]


def _exists(task: Task, base_url: str) -> bool:
    try:
        http_get(task.url(base_url), method="HEAD")
        return True
    except NotFound:
        return False


def latest_daily(probe: Task, base_url: str, earliest: date, today: date) -> date | None:
    d = today
    while d >= earliest:
        if _exists(Task(probe.market, probe.dataset, probe.symbol, "daily", d.isoformat(), probe.interval), base_url):
            return d
        d -= timedelta(days=1)
    return None


def latest_monthly(probe: Task, base_url: str, earliest: str, today: date) -> str | None:
    for p in reversed(month_range(earliest, f"{today.year:04d}-{today.month:02d}")):
        if _exists(Task(probe.market, probe.dataset, probe.symbol, "monthly", p, probe.interval), base_url):
            return p
    return None


def group_symbols(cfg: dict, group: dict) -> list[str]:
    syms = group["symbols"]
    syms = [binance_symbol(p) for p in universe(cfg)] if syms == "universe" else list(syms)
    excl = set(group.get("exclude", []))
    return [s for s in syms if s not in excl]


def plan_job(cfg: dict, jcfg: dict, base_url: str, today: date) -> tuple[list[Task], date | None]:
    """All tasks for one job, plus the earliest 'latest daily' date found (for retry decisions)."""
    tasks: list[Task] = []
    seen: set[str] = set()
    newest_daily: date | None = None
    for g in jcfg["groups"]:
        syms = group_symbols(cfg, g)
        probe = Task(jcfg["market"], jcfg["dataset"], syms[0], "monthly", "", jcfg.get("interval"))
        periods: list[tuple[str, str]] = []
        if "monthly" in g:
            start, end = g["monthly"]
            if end == "latest":
                end = latest_monthly(probe, base_url, start, today)
            if end:
                periods += [("monthly", p) for p in month_range(start, end)]
        if "daily_from" in g:
            start = date.fromisoformat(g["daily_from"])
            end = latest_daily(probe, base_url, start, today)
            if end:
                periods += [("daily", d) for d in day_range(start, end)]
                newest_daily = end if newest_daily is None else min(newest_daily, end)
        log.info("group %s..: %d symbols, %d periods (%s..%s)", syms[0], len(syms), len(periods),
                 periods[0][1] if periods else "-", periods[-1][1] if periods else "-")
        for s in syms:
            for gran, p in periods:
                t = Task(jcfg["market"], jcfg["dataset"], s, gran, p, jcfg.get("interval"))
                if t.key not in seen:
                    seen.add(t.key)
                    tasks.append(t)
    return tasks, newest_daily


def should_skip(task: Task, last: dict | None, raw_dir: Path, retry_not_listed: bool,
                recent_cutoff: date | None = None) -> bool:
    if last is None:
        return False
    if last["status"] == "ok":
        dest = raw_dir / task.symbol / task.filename
        return dest.exists() and dest.stat().st_size == last.get("bytes")
    if last["status"] == "not_listed":
        if retry_not_listed:
            return False
        recent = (task.granularity == "daily" and recent_cutoff is not None
                  and date.fromisoformat(task.period) >= recent_cutoff)
        return not recent
    return False  # failed -> retry


def process(task: Task, base_url: str, raw_dir: Path, manifest: Manifest) -> dict:
    url = task.url(base_url)
    dest = raw_dir / task.symbol / task.filename
    tmp = dest.with_name(dest.name + ".part")
    rec = {"file": task.key, "symbol": task.symbol, "granularity": task.granularity,
           "period": task.period, "url": url, "sha256": None, "bytes": None, "reason": ""}
    try:
        try:
            z = http_get(url)
        except NotFound:
            rec.update(status="not_listed", reason="HTTP 404: no archive for this period")
            return rec
        try:
            ck = http_get(url + ".CHECKSUM")
        except NotFound:
            rec.update(status="failed", reason="zip exists but .CHECKSUM returned 404")
            return rec
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(z.content)
        ok, expected, actual = verify_checksum(tmp, ck.text)
        if not ok:
            tmp.unlink(missing_ok=True)
            rec.update(status="failed", reason=f"checksum mismatch: expected {expected}, got {actual}")
            return rec
        os.replace(tmp, dest)
        rec.update(status="ok", sha256=actual, bytes=dest.stat().st_size)
        return rec
    except Exception as e:  # noqa: BLE001 -- every outcome must land in the manifest
        tmp.unlink(missing_ok=True)
        rec.update(status="failed", reason=f"{type(e).__name__}: {e}"[:500])
        return rec
    finally:
        rec["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        manifest.append(rec)


def run_job(cfg: dict, name: str, retry_not_listed: bool = False, dry_run: bool = False) -> Counter:
    dcfg = cfg["data"]
    jcfg = dcfg["jobs"][name]
    base_url = dcfg["base_url"].rstrip("/")
    raw_dir = resolve(jcfg["raw_dir"])
    manifest = Manifest(resolve(jcfg["manifest"]))
    workers = min(int(dcfg.get("max_workers", MAX_WORKERS_CAP)), MAX_WORKERS_CAP)
    today = remote_today(base_url)

    tasks, newest_daily = plan_job(cfg, jcfg, base_url, today)
    cutoff = newest_daily - timedelta(days=RECENT_RETRY_DAYS) if newest_daily else None
    state = manifest.latest()
    todo = [t for t in tasks if not should_skip(t, state.get(t.key), raw_dir, retry_not_listed, cutoff)]
    log.info("[%s] remote_today=%s planned=%d already_done=%d to_fetch=%d workers=%d",
             name, today, len(tasks), len(tasks) - len(todo), len(todo), workers)
    counts: Counter = Counter()
    if dry_run:
        return counts

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(process, t, base_url, raw_dir, manifest) for t in todo]
        for i, fut in enumerate(as_completed(futures), 1):
            rec = fut.result()
            counts[rec["status"]] += 1
            if rec["status"] == "failed":
                log.error("FAILED %s: %s", rec["file"], rec["reason"])
            if i % 200 == 0 or i == len(futures):
                log.info("[%s] progress %d/%d %s", name, i, len(futures), dict(counts))
    log.info("[%s] run done: %s", name, dict(counts))
    return counts


def run_all(cfg: dict, jobs: list[str] | None = None, retry_not_listed: bool = False,
            dry_run: bool = False) -> dict[str, Counter]:
    names = jobs or list(cfg["data"]["jobs"])
    with SingleInstanceLock(resolve(cfg["data"]["lock_file"])):
        log.info("lock acquired (pid %d)", os.getpid())
        return {n: run_job(cfg, n, retry_not_listed, dry_run) for n in names}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=None)
    ap.add_argument("--job", action="append", help="job name from config data.jobs (default: all)")
    ap.add_argument("--retry-not-listed", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    cfg = load_config(args.config) if args.config else load_config()
    try:
        results = run_all(cfg, args.job, args.retry_not_listed, args.dry_run)
    except AlreadyRunning as e:
        log.error("refusing to start: %s", e)
        return 2
    return 1 if any(c.get("failed") for c in results.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
