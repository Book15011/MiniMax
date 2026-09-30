"""Scheduled US CPI and FOMC-minutes release times (2020-2026) from published calendars.

FOMC minutes (all from the Federal Reserve Board): release dates from the FOMC meeting calendars'
  "Minutes (Released <date>)" notes; the time from each minutes press release ("For release at 2:00 p.m. EST");
  minutes not yet released from the monthly event calendars (federalreserve.gov/newsevents/<year>-<month>.htm),
  which are also cross-checked against the press-release times where both exist.
CPI: the official BLS schedule is unreachable from this server (HTTP 403), so CPI dates and times come from the
  Federal Reserve Bank of St. Louis FRED release calendar for release 10 ("Consumer Price Index"; the page states
  "All times are US Central Time"). That calendar only lists recent years, so 2020-2024 CPI is missing.
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
YEARS = range(2020, 2027)
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
    for y in YEARS:
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
    pr_days = {r["time_utc"].strftime("%Y-%m-%d"): r for r in pr_rows}
    mon_days = {r["time_utc"].strftime("%Y-%m-%d"): r for r in monthly}
    time_mismatch = sorted(d for d in set(pr_days) & set(mon_days) if pr_days[d]["time_utc"] != mon_days[d]["time_utc"])
    upcoming = [r for d, r in mon_days.items() if d not in released]   # scheduled, not yet released
    cpi, p3 = cpi_releases()
    df = pd.DataFrame(pr_rows + upcoming + cpi).drop_duplicates(subset=["event", "time_utc"]) \
        .sort_values(["time_utc", "event"])
    status.update(
        problems=p1 + p2 + p4 + p3,
        fomc_cross_check={"released_notes": len(released), "press_release_times": len(pr_rows),
                          "monthly_calendar_rows": len(monthly),
                          "released_but_not_in_monthly_calendar": sorted(set(released) - set(mon_days)),
                          "time_mismatch_press_release_vs_monthly": time_mismatch,
                          "monthly_calendar_only (upcoming, or before the notes range)": sorted(d for d in mon_days if d not in released)},
        cpi_coverage="2025-2026 only: bls.gov refuses this server and the FRED calendar lists only recent "
                     "years, so 2020-2024 CPI release times are NOT in the calendar (not approximated)",
        counts={e: {int(y): int(n) for y, n in g.time_utc.dt.year.value_counts().sort_index().items()}
                for e, g in df.groupby("event")},
        checks={f"{e} {t} UTC": bool((df.event.eq(e) & df.time_utc.eq(pd.Timestamp(t, tz="UTC"))).any())
                for e, t in CHECKS},
    )
    out = df.assign(time_utc=df.time_utc.dt.strftime("%Y-%m-%d %H:%M"))
    OUT.write_text(out.to_csv(index=False))
    status["sha256"] = hashlib.sha256(OUT.read_bytes()).hexdigest()
    status["rows"] = int(len(out))
    STATUS.write_text(json.dumps(status, indent=1, default=str) + "\n")
    return status


def load() -> pd.DataFrame:
    df = pd.read_csv(OUT)
    df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True)
    return df


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    st = build()
    for k, v in st.items():
        log.info("%s: %s", k, v)
    return 0 if all(st["checks"].values()) and not st["fomc_cross_check"]["time_mismatch_press_release_vs_monthly"] else 1


if __name__ == "__main__":
    sys.exit(main())
