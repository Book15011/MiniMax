import hashlib
import json

import pytest

from datetime import date

from src.data import binance_downloader as dl
from src.data.binance_downloader import (
    AlreadyRunning, Manifest, NotFound, SingleInstanceLock, Task, month_range, should_skip, verify_checksum,
)

BASE = "https://example.invalid/data"


def K(symbol, granularity, period, interval="1m"):
    return Task("spot", "klines", symbol, granularity, period, interval)


def test_urls_match_archive_layout():
    assert K("BTCUSDT", "monthly", "2025-09", "1h").url(BASE) == \
        f"{BASE}/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2025-09.zip"
    assert Task("futures/um", "fundingRate", "BTCUSDT", "monthly", "2026-08").url(BASE) == \
        f"{BASE}/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2026-08.zip"
    assert Task("futures/um", "metrics", "BTCUSDT", "daily", "2026-08-12").url(BASE) == \
        f"{BASE}/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-2026-08-12.zip"


def test_recent_daily_not_listed_is_retried(tmp_path):
    old, recent = K("XUSDT", "daily", "2026-09-01"), K("XUSDT", "daily", "2026-09-27")
    cutoff = date(2026, 9, 22)
    assert should_skip(old, {"status": "not_listed"}, tmp_path, False, cutoff)
    assert not should_skip(recent, {"status": "not_listed"}, tmp_path, False, cutoff)


def _checksum_line(payload: bytes, name: str) -> str:
    return f"{hashlib.sha256(payload).hexdigest()}  {name}\n"


def test_verify_checksum_accepts_matching_file(tmp_path):
    p = tmp_path / "BTCUSDT-1m-2026-09-01.zip"
    p.write_bytes(b"payload")
    ok, expected, actual = verify_checksum(p, _checksum_line(b"payload", p.name))
    assert ok and expected == actual


def test_verify_checksum_rejects_tampered_file(tmp_path):
    p = tmp_path / "BTCUSDT-1m-2026-09-01.zip"
    p.write_bytes(b"payload-tampered")
    ok, _, _ = verify_checksum(p, _checksum_line(b"payload", p.name))
    assert not ok


def test_verify_checksum_rejects_wrong_filename(tmp_path):
    p = tmp_path / "BTCUSDT-1m-2026-09-01.zip"
    p.write_bytes(b"payload")
    ok, _, _ = verify_checksum(p, _checksum_line(b"payload", "ETHUSDT-1m-2026-09-01.zip"))
    assert not ok


def test_verify_checksum_rejects_garbage_checksum_file(tmp_path):
    p = tmp_path / "x.zip"
    p.write_bytes(b"payload")
    with pytest.raises(ValueError):
        verify_checksum(p, "<html>error</html>")


def test_manifest_is_append_only(tmp_path):
    m = Manifest(tmp_path / "_manifest.jsonl")
    m.append({"file": "A/a.zip", "status": "failed", "reason": "boom"})
    before = m.path.read_bytes()
    m.append({"file": "A/a.zip", "status": "ok", "reason": ""})
    after = m.path.read_bytes()
    assert after.startswith(before)
    lines = [json.loads(line) for line in after.splitlines()]
    assert [r["status"] for r in lines] == ["failed", "ok"]
    assert m.latest()["A/a.zip"]["status"] == "ok"


def _fake_http(files: dict[str, bytes]):
    def fake(url, method="GET"):
        if url not in files:
            raise NotFound(url)

        class R:
            content = files[url]
            text = files[url].decode("latin-1")
        return R()
    return fake


def test_run_preserves_existing_failed_history(tmp_path, monkeypatch):
    t = K("BTCUSDT", "daily", "2026-09-01")
    payload = b"zipbytes"
    monkeypatch.setattr(dl, "http_get", _fake_http({
        t.url(BASE): payload,
        t.url(BASE) + ".CHECKSUM": _checksum_line(payload, t.filename).encode(),
    }))
    m = Manifest(tmp_path / "_manifest.jsonl")
    m.append({"file": t.key, "status": "failed", "reason": "earlier network error"})
    history = m.path.read_bytes()

    rec = dl.process(t, BASE, tmp_path / "raw", m)

    assert rec["status"] == "ok"
    assert m.path.read_bytes().startswith(history)
    assert (tmp_path / "raw" / "BTCUSDT" / t.filename).read_bytes() == payload
    assert not list((tmp_path / "raw").rglob("*.part"))


def test_404_is_recorded_as_not_listed(tmp_path, monkeypatch):
    monkeypatch.setattr(dl, "http_get", _fake_http({}))
    m = Manifest(tmp_path / "_manifest.jsonl")
    rec = dl.process(K("PUMPUSDT", "monthly", "2025-08"), BASE, tmp_path, m)
    assert rec["status"] == "not_listed"
    assert m.latest()["PUMPUSDT/PUMPUSDT-1m-2025-08.zip"]["status"] == "not_listed"


def test_checksum_mismatch_is_failed_and_leaves_no_file(tmp_path, monkeypatch):
    t = K("BTCUSDT", "daily", "2026-09-01")
    monkeypatch.setattr(dl, "http_get", _fake_http({
        t.url(BASE): b"corrupted",
        t.url(BASE) + ".CHECKSUM": _checksum_line(b"original", t.filename).encode(),
    }))
    rec = dl.process(t, BASE, tmp_path, Manifest(tmp_path / "_manifest.jsonl"))
    assert rec["status"] == "failed" and "checksum mismatch" in rec["reason"]
    assert not list(tmp_path.rglob("*.zip*"))


def test_skip_logic(tmp_path):
    t = K("BTCUSDT", "daily", "2026-09-01")
    dest = tmp_path / "BTCUSDT" / t.filename
    dest.parent.mkdir()
    dest.write_bytes(b"12345")
    assert should_skip(t, {"status": "ok", "bytes": 5}, tmp_path, False)
    assert not should_skip(t, {"status": "ok", "bytes": 6}, tmp_path, False)
    assert not should_skip(t, {"status": "failed"}, tmp_path, False)
    assert should_skip(t, {"status": "not_listed"}, tmp_path, False)
    assert not should_skip(t, {"status": "not_listed"}, tmp_path, True)
    assert not should_skip(t, None, tmp_path, False)


def test_second_instance_refuses_to_start(tmp_path):
    lock = tmp_path / ".downloader.lock"
    with SingleInstanceLock(lock):
        with pytest.raises(AlreadyRunning):
            with SingleInstanceLock(lock):
                pass
    with SingleInstanceLock(lock):
        pass


def test_month_range():
    assert month_range("2025-11", "2026-02") == ["2025-11", "2025-12", "2026-01", "2026-02"]
