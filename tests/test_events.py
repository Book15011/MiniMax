import pandas as pd

from src.validation.events import BLS_CSV, cross_check_cpi, load_bls_cpi


def test_bls_cpi_file_passes_every_check():
    rows, problems, info = load_bls_cpi()
    assert problems == []
    assert info["reference_months"] == "2019-12 .. 2026-09"
    assert info["not_published"] == ["2025-10"]
    assert info["released"] + info["scheduled"] + len(info["not_published"]) == info["rows"]


def test_october_2025_stays_not_published_without_a_time():
    rows, _, _ = load_bls_cpi()
    missing = [r for r in rows if r["status"] == "not_published"]
    assert len(missing) == 1 and pd.isna(missing[0]["time_utc"]) and "2025-10" in missing[0]["detail"]


def test_daylight_saving_conversion():
    rows, _, _ = load_bls_cpi()
    by_ref = {r["detail"].split()[-1]: r["time_utc"] for r in rows if pd.notna(r["time_utc"])}
    assert by_ref["2020-01"] == pd.Timestamp("2020-02-13 13:30", tz="UTC")   # EST, UTC-5
    assert by_ref["2020-02"] == pd.Timestamp("2020-03-11 12:30", tz="UTC")   # EDT from 2020-03-08, UTC-4
    assert by_ref["2020-10"] == pd.Timestamp("2020-11-12 13:30", tz="UTC")   # back to EST on 2020-11-01
    assert by_ref["2026-09"] == pd.Timestamp("2026-10-14 12:30", tz="UTC")


def test_a_wrong_utc_value_is_reported(tmp_path):
    text = BLS_CSV.read_text().replace("2020-02-13T13:30Z", "2020-02-13T12:30Z")
    p = tmp_path / "cpi.csv"
    p.write_text(text)
    _, problems, _ = load_bls_cpi(p)
    assert any("2020-01" in s and "13:30Z" in s for s in problems)


def test_cross_check_reports_one_sided_dates():
    t = lambda s: pd.Timestamp(s, tz="UTC")
    bls = [{"time_utc": t("2025-01-15 13:30")}, {"time_utc": t("2025-02-12 13:30")}, {"time_utc": pd.NaT}]
    fred = [{"time_utc": t("2025-01-15 13:30")}, {"time_utc": t("2025-02-13 13:30")}]
    c = cross_check_cpi(bls, fred)
    assert c["matching"] == 1 and c["fred_only"] == ["2025-02-13 13:30"] and c["bls_only"] == ["2025-02-12 13:30"]
