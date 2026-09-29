import zipfile

import pandas as pd
import pytest

from src.data.integrity import check_file
from src.data.loader import load_symbol, normalize_time_units, read_kline_zip

T0_MS = 1_735_689_600_000  # 2025-01-01 00:00 UTC


def _rows(start_ms: int, n: int, scale: int) -> str:
    lines = []
    for i in range(n):
        o = (start_ms + i * 60_000) * scale
        c = (start_ms + i * 60_000 + 59_999) * scale + (scale - 1)
        lines.append(f"{o},100.0,101.0,99.0,100.5,1.5,{c},150.0,10,0.7,70.0,0")
    return "\n".join(lines) + "\n"


def _write_zip(path, csv_text: str):
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(path.name.replace(".zip", ".csv"), csv_text)
    return path


@pytest.fixture
def mixed_symbol_dir(tmp_path):
    d = tmp_path / "raw" / "TESTUSDT"
    d.mkdir(parents=True)
    _write_zip(d / "TESTUSDT-1m-2024-12-31.zip", _rows(T0_MS - 3 * 60_000, 3, 1))  # ms
    _write_zip(d / "TESTUSDT-1m-2025-01-01.zip", _rows(T0_MS, 3, 1000))  # µs
    return tmp_path


def test_microseconds_are_normalized_to_ms(mixed_symbol_dir):
    df = read_kline_zip(mixed_symbol_dir / "raw" / "TESTUSDT" / "TESTUSDT-1m-2025-01-01.zip")
    assert df["open_time"].tolist() == [T0_MS, T0_MS + 60_000, T0_MS + 120_000]
    assert df["close_time"].iloc[0] == T0_MS + 59_999


def test_milliseconds_are_left_unchanged(mixed_symbol_dir):
    df = read_kline_zip(mixed_symbol_dir / "raw" / "TESTUSDT" / "TESTUSDT-1m-2024-12-31.zip")
    assert df["open_time"].iloc[-1] == T0_MS - 60_000


def test_load_symbol_mixed_units_gives_one_continuous_ms_series(mixed_symbol_dir):
    df = load_symbol("TESTUSDT", mixed_symbol_dir / "raw", mixed_symbol_dir / "pq")
    assert len(df) == 6
    assert (df["open_time"].diff().dropna() == 60_000).all()
    assert df["timestamp"].iloc[3] == pd.Timestamp("2025-01-01 00:00", tz="UTC")
    assert (mixed_symbol_dir / "pq" / "TESTUSDT.parquet").exists()
    cached = load_symbol("TESTUSDT", mixed_symbol_dir / "raw", mixed_symbol_dir / "pq")
    assert cached["open_time"].tolist() == df["open_time"].tolist()


def test_file_mixing_units_is_rejected():
    df = pd.DataFrame({"open_time": [T0_MS, T0_MS * 1000], "close_time": [T0_MS, T0_MS * 1000]})
    with pytest.raises(ValueError):
        normalize_time_units(df)


def test_exact_duplicate_block_is_dropped(tmp_path):
    d = tmp_path / "raw" / "TESTUSDT"
    d.mkdir(parents=True)
    _write_zip(d / "TESTUSDT-1m-2025-01-01.zip", _rows(T0_MS, 3, 1000) + _rows(T0_MS, 2, 1000))
    df = load_symbol("TESTUSDT", tmp_path / "raw", tmp_path / "pq")
    assert df["open_time"].tolist() == [T0_MS, T0_MS + 60_000, T0_MS + 120_000]


def test_conflicting_duplicate_timestamps_raise(tmp_path):
    d = tmp_path / "raw" / "TESTUSDT"
    d.mkdir(parents=True)
    conflicting = _rows(T0_MS, 1, 1000).replace("100.5", "105.0")
    _write_zip(d / "TESTUSDT-1m-2025-01-01.zip", _rows(T0_MS, 2, 1000) + conflicting)
    with pytest.raises(ValueError, match="conflicting"):
        load_symbol("TESTUSDT", tmp_path / "raw", tmp_path / "pq")


def test_header_row_is_tolerated(tmp_path):
    header = "open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore\n"
    p = _write_zip(tmp_path / "TESTUSDT-1m-2025-01-01.zip", header + _rows(T0_MS, 2, 1000))
    assert read_kline_zip(p)["open_time"].tolist() == [T0_MS, T0_MS + 60_000]


def test_integrity_flags_short_day_with_gap(tmp_path):
    p = _write_zip(tmp_path / "TESTUSDT-1m-2025-01-01.zip", _rows(T0_MS, 3, 1000))
    res = check_file(p, None)
    assert res["rows"] == 3 and res["expected_rows"] == 1440
    assert not res["intact"]
    assert res["gaps"][0]["minutes"] == 1437
