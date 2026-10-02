"""Copy BTCUSDT funding / open-interest parquet files out of lob-execution-hma (read-only source).

Each copy is verified three ways: source sha256 == the old project's manifest sha256 (status ok),
and destination sha256 == source sha256. Results go to an append-only manifest.
Run from the repo root:  python -m src.data.external_copy
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.config import load_config, resolve
from src.data.binance_downloader import Manifest, sha256_file

log = logging.getLogger("external_copy")


def _old_manifest(path: Path) -> dict[str, dict]:
    """The old project's manifest, keyed by period (last record wins)."""
    out: dict[str, dict] = {}
    with open(path) as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                out[rec["period"]] = rec
    return out


def copy_dataset(src_dir: Path, dst_dir: Path, manifest: Manifest) -> Counter:
    old = _old_manifest(src_dir / "_manifest.jsonl")
    state = manifest.latest()
    dst_dir.mkdir(parents=True, exist_ok=True)
    counts: Counter = Counter()
    for src in sorted(src_dir.glob("*.parquet")):
        key = f"{src_dir.name}/{src.name}"
        dst = dst_dir / src.name
        last = state.get(key)
        if last and last["status"] == "ok" and dst.exists() and sha256_file(dst) == last["sha256"]:
            counts["skipped"] += 1
            continue
        rec ={"file": key, "source": str(src), "sha256": None, "bytes": None, "reason": ""}
        src_sha = sha256_file(src)
        ref = old.get(_period_of(src.name))
        if ref is None or ref.get("status") != "ok":
            rec.update(status="failed", reason="no ok record in the source project's manifest")
        elif ref["sha256"] != src_sha:
            rec.update(status="failed", reason=f"source sha256 {src_sha} != source manifest {ref['sha256']}")
        else:
            tmp = dst.with_name(dst.name + ".part")
            shutil.copyfile(src, tmp)
            if sha256_file(tmp) != src_sha:
                tmp.unlink()
                rec.update(status="failed", reason="copy sha256 differs from source")
            else:
                os.replace(tmp, dst)
                rec.update(status="ok", sha256=src_sha, bytes=dst.stat().st_size)
        rec["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        manifest.append(rec)
        counts[rec["status"]] += 1
        if rec["status"] == "failed":
            log.error("FAILED %s: %s", key, rec["reason"])
    return counts


def _period_of(name: str) -> str:
    """BTCUSDT-funding_rate-2026-07.parquet -> 2026-07 ; BTCUSDT-open_interest-2026-08-11.parquet -> 2026-08-11"""
    return "-".join(name.removesuffix(".parquet").split("-")[2:])


def run(cfg: dict) -> dict[str, Counter]:
    ecfg = cfg["data"]["external_copy"]
    src_root = Path(ecfg["source"])
    dst_root = resolve(ecfg["dest"])
    manifest = Manifest(dst_root / "_manifest.jsonl")
    return {ds: copy_dataset(src_root / ds, dst_root / ds, manifest) for ds in ecfg["datasets"]}


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    res = run(load_config())
    for ds, c in res.items():
        log.info("%s: %s", ds, dict(c))
    return 1 if any(c.get("failed") for c in res.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
