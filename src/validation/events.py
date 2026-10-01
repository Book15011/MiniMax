"""Scheduled US CPI and FOMC-minutes release times (2020-2026) from published calendars.

FOMC minutes (all from the Federal Reserve Board): release dates from the FOMC meeting calendars'
  "Minutes (Released <date>)" notes; the time from each minutes press release ("For release at 2:00 p.m. EST");
  minutes not yet released from the monthly event calendars (federalreserve.gov/newsevents/<year>-<month>.htm),
  which are also cross-checked against the press-release times where both exist.
CPI: bls.gov refuses this server (HTTP 403), so the BLS release list is kept as a file,
  validation/cpi_release_times_2020_2026.csv (dates from the BLS news-release archive, one link per row; 8:30 a.m.
  ET). Every row is re-checked here (UTC recomputed with daylight saving, weekday, after its reference month, no
  missing month). The October 2025 CPI was never published (government shutdown) and stays a 'not_published'
  row with no time. The St. Louis Fed FRED release calendar (release 10, US Central Time) is used to cross-check
  2025-2026 and only adds scheduled releases after the file's last date.
Every row keeps its source URL. Nothing is approximated: what cannot be read is reported, not filled in.

    python -m src.validation.events          -> validation/event_calendar_v1.csv
"""
from __future__ import annotations

import calendar
import hashlib
import json
import logging
import re
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from src.config import REPO_ROOT

log = logging.getLogger("events")
OUT = REPO_ROOT / "validation" / "event_calendar_v1.csv"
STATUS = REPO_ROOT / "validation" / "event_calendar_v1.status.json"
BLS_CSV = REPO_ROOT / "validation" / "cpi_release_times_2020_2026.csv"
YEARS = range(2020, 2027)
FRED_YEARS = (2025, 2026)  # the FRED calendar only lists recent years; used to cross-check and extend BLS
ET, CT = ZoneInfo("America/New_York"), ZoneInfo("America/Chicago")
BLS_URL = "https://www.bls.gov/schedule/news_release/cpi.htm"
FED_MONTH = "https://www.federalreserve.gov/newsevents/{year}-{month}.htm"
FED_FOMC = ["https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
            "https://www.federalreserve.gov/monetarypolicy/fomchistorical2020.htm"]
FRED_CAL = "https://fred.stlouisfed.org/releases/calendar?rid=10&y={year}"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) MiniMax-research/1.0"}
CHECKS = [("CPI", "2026-10-14 12:30"), ("FOMC_MINUTES", "2026-10-07 18:00")]


def _get(url: str, attempts: int = 3) -> requests.Response:
    for a in range(1, attempts + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=45)
            return r
        except requests.RequestException:
            if a == attempts:
                raise
            time.sleep(2 * a)
    raise AssertionError("unreachable")


def _to_utc(day: datetime, hhmm: str, tz: ZoneInfo) -> pd.Timestamp:
    m = re.fullmatch(r"(\d{1,2}):(\d{2})\s*([ap])\.?m\.?", hhmm.strip().lower())
    if not m:
        raise ValueError(f"unparseable time {hhmm!r}")
    h = int(m.group(1)) % 12 + (12 if m.group(3) == "p" else 0)
    local = datetime(day.year, day.month, day.day, h, int(m.group(2)), tzinfo=tz)
    return pd.Timestamp(local).tz_convert("UTC")


def fomc_minutes() -> tuple[list[dict], list[str]]:
    rows, problems = [], []
    for y in YEARS:
        for mi in range(1, 13):
            url = FED_MONTH.format(year=y, month=calendar.month_name[mi].lower())
            try:
                r = _get(url)
            except requests.RequestException as e:
                problems.append(f"{url}: {type(e).__name__}")
                continue
            if r.status_code != 200:
                problems.append(f"{url}: HTTP {r.status_code}")
                continue
            html = r.text
            for m in re.finditer(r"<p>\s*FOMC Minutes\s*</p>", html):
                before, after = html[max(0, m.start() - 500):m.start()], html[m.end():m.end() + 700]
                tm = re.findall(r"<p>\s*(\d{1,2}:\d{2}\s*[ap]\.m\.)\s*</p>", before)
                dy = re.search(r'<div class="col-xs-3">\s*<p>\s*(\d{1,2})\s*</p>', after)
                meeting = re.search(r"Meeting of ([^<]+)</p>", after)
                if not tm or not dy:
                    problems.append(f"{url}: an 'FOMC Minutes' entry without a readable time/day")
                    continue
                day = datetime(y, mi, int(dy.group(1)))
                rows.append({"event": "FOMC_MINUTES", "time_utc": _to_utc(day, tm[-1], ET),
                             "local": f"{day:%Y-%m-%d} {tm[-1]} ET",
                             "detail": f"Meeting of {meeting.group(1).strip()}" if meeting else "",
                             "source": url})
            time.sleep(0.3)
    return rows, problems


def fomc_released_dates() -> tuple[set[str], list[str]]:
    """Minutes release dates from the FOMC meeting calendars: '(Released <Month DD, YYYY>)' notes whose
    nearest preceding label is 'Minutes' (the 2020 page also has 'Statement (Released ...)' notes)."""
    dates, problems = set(), []
    for url in FED_FOMC:
        try:
            r = _get(url)
        except requests.RequestException as e:
            problems.append(f"{url}: {type(e).__name__}")
            continue
        if r.status_code != 200:
            problems.append(f"{url}: HTTP {r.status_code}")
            continue
        html = r.text
        for m in re.finditer(r"\(Released ([A-Z][a-z]+ \d{1,2}, \d{4})\)", html):
            ctx = html[max(0, m.start() - 600):m.start()]
            if ctx.rfind("Minutes") > ctx.rfind("Statement"):
                dates.add(datetime.strptime(m.group(1), "%B %d, %Y").strftime("%Y-%m-%d"))
    return dates, problems


def fomc_press_release(day: str) -> tuple[dict | None, str | None]:
    """The minutes press release of that day, which states 'For release at H:MM p.m. EST|EDT'."""
    ymd = day.replace("-", "")
    for sfx in "abc":
        url = f"https://www.federalreserve.gov/newsevents/pressreleases/monetary{ymd}{sfx}.htm"
        try:
            r = _get(url)
        except requests.RequestException as e:
            return None, f"{url}: {type(e).__name__}"
        if r.status_code != 200 or "Minutes of the Federal Open Market Committee" not in r.text:
            continue
        m = re.search(r"For release at\s+(\d{1,2}:\d{2}\s*[ap]\.m\.)\s+(EST|EDT)", r.text)
        if not m:
            return None, f"{url}: no 'For release at' time"
        ts = _to_utc(datetime.strptime(day, "%Y-%m-%d"), m.group(1), ET)
        expected = "EDT" if ts.tz_convert(ET).dst() else "EST"
        if m.group(2) != expected:
            return None, f"{url}: stated {m.group(2)} but the date is in {expected}"
        return {"event": "FOMC_MINUTES", "time_utc": ts, "local": f"{day} {m.group(1)} {m.group(2)}",
                "detail": "press release", "source": url}, None
    return None, f"no minutes press release found for {day}"


def cpi_releases() -> tuple[list[dict], list[str]]:
    rows, problems = [], []
    for y in FRED_YEARS:
        url = FRED_CAL.format(year=y)
        try:
            r = _get(url)
        except requests.RequestException as e:
            problems.append(f"{url}: {type(e).__name__}")
            continue
        if r.status_code != 200 or "All times are US Central Time" not in r.text:
            problems.append(f"{url}: HTTP {r.status_code} or no Central-Time statement")
            continue
        pat = (r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) ([A-Z][a-z]+ \d{1,2}, \d{4})</span>"
               r".{0,400}?<td[^>]*>\s*(\d{1,2}:\d{2}\s*[ap]m)\s*</td>\s*<td[^>]*>\s*<a href=\"/release\?rid=10\">")
        found = 0
        for d, tm in re.findall(pat, r.text, flags=re.S):
            day = datetime.strptime(d, "%B %d, %Y")
            if day.year != y:
                continue
            rows.append({"event": "CPI", "time_utc": _to_utc(day, tm.replace("am", "a.m.").replace("pm", "p.m."), CT),
                         "local": f"{day:%Y-%m-%d} {tm} CT", "detail": "Consumer Price Index (FRED release 10)",
                         "source": url})
            found += 1
        if found == 0:
            problems.append(f"{url}: no CPI rows for {y} (the FRED calendar only lists recent years)")
        time.sleep(0.3)
    return rows, problems


def load_bls_cpi(path=None) -> tuple[list[dict], list[str], dict]:
    """The BLS CPI release list (validation/cpi_release_times_2020_2026.csv), checked row by row:
    UTC recomputed from the ET date and time with daylight saving; weekday; after the reference month;
    one row per reference month with no gaps. A 'not_published' row is kept with no time."""
    df = pd.read_csv(path or BLS_CSV, dtype=str, keep_default_na=False)
    rows, problems = [], []
    months = pd.PeriodIndex(df["reference_month"], freq="M")
    expected = pd.period_range(months.min(), months.max(), freq="M")
    if list(months) != list(expected):
        problems.append(f"reference months are not one per month without gaps: {sorted(set(expected) - set(months))}")
    for r in df.itertuples():
        ref = pd.Period(r.reference_month, freq="M")
        if r.status.startswith("not_published"):
            if r.release_date_et or r.release_time_et or r.release_utc:
                problems.append(f"{r.reference_month}: 'not published' row has a date or time")
            rows.append({"event": "CPI", "time_utc": pd.NaT, "local": "", "status": "not_published",
                         "detail": f"reference month {r.reference_month}: not published ({r.status})",
                         "source": r.source, "sort_key": (ref + 1).start_time.tz_localize("UTC") + pd.Timedelta(days=14)})
            continue
        if r.status not in ("released", "scheduled"):
            problems.append(f"{r.reference_month}: unknown status {r.status!r}")
            continue
        day = datetime.strptime(r.release_date_et, "%Y-%m-%d")
        hh, mm = map(int, r.release_time_et.split(":"))
        ts = pd.Timestamp(datetime(day.year, day.month, day.day, hh, mm, tzinfo=ET)).tz_convert("UTC")
        stated = pd.Timestamp(r.release_utc.replace("Z", "+00:00"))
        if ts != stated:
            problems.append(f"{r.reference_month}: {r.release_date_et} {r.release_time_et} ET is {ts:%Y-%m-%dT%H:%MZ}, "
                            f"file says {r.release_utc}")
        if day.weekday() >= 5:
            problems.append(f"{r.reference_month}: release on a weekend ({r.release_date_et})")
        if pd.Timestamp(day) <= ref.end_time:
            problems.append(f"{r.reference_month}: released before its reference month ended")
        rows.append({"event": "CPI", "time_utc": ts, "local": f"{r.release_date_et} {r.release_time_et} ET",
                     "status": r.status, "detail": f"reference month {r.reference_month}", "source": r.source,
                     "sort_key": ts})
    info = {"rows": int(len(df)), "released": int((df.status == "released").sum()),
            "scheduled": int((df.status == "scheduled").sum()),
            "not_published": [m for m, s in zip(df.reference_month, df.status) if s.startswith("not_published")],
            "reference_months": f"{months.min()} .. {months.max()}"}
    return rows, problems, info


def cross_check_cpi(bls_rows: list[dict], fred_rows: list[dict]) -> dict:
    """Compare FRED CPI release times with the BLS list over the release months both cover."""
    b = {r["time_utc"] for r in bls_rows if pd.notna(r["time_utc"])}
    f = {r["time_utc"] for r in fred_rows}
    month = lambda t: t.strftime("%Y-%m")
    lo = max(min(map(month, b)), min(map(month, f)))
    hi = min(max(map(month, b)), max(map(month, f)))
    b_in, f_in = {t for t in b if lo <= month(t) <= hi}, {t for t in f if lo <= month(t) <= hi}
    fmt = lambda s: sorted(t.strftime("%Y-%m-%d %H:%M") for t in s)
    return {"overlap_release_months": f"{lo} .. {hi}", "matching": len(b_in & f_in),
            "fred_only": fmt(f_in - b_in), "bls_only": fmt(b_in - f_in)}


def build() -> dict:
    status = {}
    try:
        status["bls"] = f"HTTP {_get(BLS_URL).status_code}"
    except requests.RequestException as e:
        status["bls"] = f"{type(e).__name__}"
    monthly, p1 = fomc_minutes()
    released, p2 = fomc_released_dates()
    released = {d for d in released if int(d[:4]) in YEARS}
    pr_rows, p4 = [], []
    for d in sorted(released):
        row, err = fomc_press_release(d)
        (pr_rows.append(row) if row else p4.append(err))
        time.sleep(0.3)
    for r in pr_rows:
        r.update(status="released", sort_key=r["time_utc"])
    last_released = max(released) if released else ""
    pr_days = {r["time_utc"].strftime("%Y-%m-%d"): r for r in pr_rows}
    mon_days = {r["time_utc"].strftime("%Y-%m-%d"): r for r in monthly}
    time_mismatch = sorted(d for d in set(pr_days) & set(mon_days) if pr_days[d]["time_utc"] != mon_days[d]["time_utc"])
    monthly_only = [dict(r, status="scheduled" if d > last_released else "released", sort_key=r["time_utc"])
                    for d, r in mon_days.items() if d not in released]

    bls, p5, bls_info = load_bls_cpi()
    fred, p3 = cpi_releases()
    cpi_check = cross_check_cpi(bls, fred)
    last_bls = max(r["time_utc"] for r in bls if pd.notna(r["time_utc"]))
    fred_after = [dict(r, status="scheduled", sort_key=r["time_utc"]) for r in fred if r["time_utc"] > last_bls]

    df = pd.DataFrame(pr_rows + monthly_only + bls + fred_after)
    df = df.drop_duplicates(subset=["event", "time_utc", "detail"]).sort_values(["sort_key", "event"])
    timed = df[df.time_utc.notna()]
    status.update(
        problems=p1 + p2 + p4 + p3 + p5,
        fomc_cross_check={"released_notes": len(released), "press_release_times": len(pr_rows),
                          "monthly_calendar_rows": len(monthly),
                          "released_but_not_in_monthly_calendar": sorted(set(released) - set(mon_days)),
                          "time_mismatch_press_release_vs_monthly": time_mismatch,
                          "monthly_calendar_only (upcoming, or before the notes range)": sorted(d for d in mon_days if d not in released)},
        cpi_bls_file={**bls_info, "sha256": hashlib.sha256(BLS_CSV.read_bytes()).hexdigest(),
                      "checks": "UTC recomputed from 08:30 ET with DST; weekdays; after the reference month; "
                                "one row per month", "problems": p5},
        cpi_cross_check_fred_vs_bls=cpi_check,
        cpi_coverage=(f"BLS release list for reference months {bls_info['reference_months']} (dates from the BLS "
                      "news-release archive, supplied as a file because bls.gov refuses this server); "
                      f"not published: {bls_info['not_published']}; later scheduled releases from the FRED calendar: "
                      f"{[r['time_utc'].strftime('%Y-%m-%d %H:%M') for r in fred_after]}"),
        counts={e: {int(y): int(n) for y, n in g.time_utc.dt.year.value_counts().sort_index().items()}
                for e, g in timed.groupby("event")},
        checks={f"{e} {t} UTC": bool((df.event.eq(e) & df.time_utc.eq(pd.Timestamp(t, tz="UTC"))).any())
                for e, t in CHECKS},
    )
    out = df.drop(columns="sort_key")
    out = out.assign(time_utc=out.time_utc.map(lambda t: t.strftime("%Y-%m-%d %H:%M") if pd.notna(t) else ""))
    OUT.write_text(out[["event", "time_utc", "local", "status", "detail", "source"]].to_csv(index=False))
    status["sha256"] = hashlib.sha256(OUT.read_bytes()).hexdigest()
    status["rows"] = int(len(out))
    STATUS.write_text(json.dumps(status, indent=1, default=str) + "\n")
    return status


def load() -> pd.DataFrame:
    """All calendar rows; time_utc is NaT for releases that never happened (status 'not_published')."""
    df = pd.read_csv(OUT, keep_default_na=False)
    df["time_utc"] = pd.to_datetime(df["time_utc"].replace("", None), utc=True)
    return df


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    st = build()
    for k, v in st.items():
        log.info("%s: %s", k, v)
    ok = (all(st["checks"].values()) and not st["fomc_cross_check"]["time_mismatch_press_release_vs_monthly"]
          and not st["cpi_bls_file"]["problems"] and not st["cpi_cross_check_fred_vs_bls"]["fred_only"]
          and not st["cpi_cross_check_fred_vs_bls"]["bls_only"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
