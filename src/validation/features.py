"""Point-in-time market-state features on the 16:00-UTC daily grid.

Every value at grid time t uses only bars that CLOSED at or before t (hourly bars are indexed by
close time), funding/OI stamped at or before t, FRED daily observations dated before t's UTC date,
and CPI months whose assumed release (16th of the next month, 00:00 UTC) is at or before t.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

GROUPS: dict[str, list[str]] = {
    "TREND": ["T1", "T2", "T3", "T4"],
    "CYCLE": ["C1", "C2"],
    "VOL": ["V1", "V2"],
    "STRUCTURE": ["M1", "M2", "M3", "M4"],
    "POSITIONING": ["P1", "P2"],
    "MACRO": ["X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8"],
    "CALENDAR": ["E1"],
}
CORE_GROUPS = ["TREND", "CYCLE", "VOL", "STRUCTURE"]
FEATURES = [f for g in GROUPS.values() for f in g]
BTC = "BTCUSDT"


@dataclass
class MarketData:
    close: pd.DataFrame  # hourly closes, index = bar CLOSE time (UTC), columns = series ids
    quote_volume: pd.DataFrame
    funding: pd.Series | None = None  # index = funding time (UTC)
    oi: pd.Series | None = None  # index = snapshot time (UTC)
    fred: dict[str, pd.Series] | None = None  # index = observation date (naive)


def grid_labels(index: pd.DatetimeIndex, hour: int) -> pd.DatetimeIndex:
    """Map a bar close time to the daily-grid time t whose bar (t-24h, t] contains it."""
    off = pd.Timedelta(hours=hour)
    return (index - off).ceil("D") + off


def base_symbol(series_id: str) -> str:
    return series_id.split("~", 1)[0]


def is_allowed(series_id: str, ucfg: dict) -> bool:
    sym = base_symbol(series_id)
    return (sym not in set(ucfg["exclude"]) and sym not in set(ucfg["stablecoins"])
            and not re.match(ucfg["leveraged_regex"], sym))


def daily_bars(close_h: pd.DataFrame, qv_h: pd.DataFrame, hour: int):
    lab = grid_labels(close_h.index, hour)
    close_d = close_h.groupby(lab).last()
    qv_d = qv_h.groupby(lab).sum(min_count=1)
    exists = close_h.notna().groupby(lab).sum() > 0
    full = pd.date_range(close_d.index[0], close_d.index[-1], freq="D")
    return close_d.reindex(full), qv_d.reindex(full), exists.reindex(full, fill_value=False)


def _value_before_day(s: pd.Series, t: pd.Timestamp) -> float:
    """Last observation dated strictly before t's UTC date (previous business day, ffilled)."""
    day = t.tz_convert(None).normalize()
    pos = s.index.searchsorted(day, side="left") - 1
    return float(s.iloc[pos]) if pos >= 0 else np.nan


class StateEngine:
    def __init__(self, data: MarketData, vcfg: dict):
        self.data, self.v = data, vcfg
        self.hour = vcfg["grid_hour_utc"]
        ucfg = vcfg["universe"]
        self.close_d, self.qv_d, self.exists_d = daily_bars(data.close, data.quote_volume, self.hour)
        self.cols = np.array(self.close_d.columns)
        allowed = np.array([is_allowed(c, ucfg) for c in self.cols])
        hist_before = self.exists_d.cumsum().shift(1, fill_value=0)
        self.eligible = self.exists_d & (hist_before >= ucfg["min_history_days"]) & allowed
        self.qv30 = self.qv_d.rolling(ucfg["volume_days"], min_periods=1).sum()
        logc = np.log(self.close_d)
        self.r_d = logc.diff()
        self.ret30 = logc - logc.shift(30)
        self.ma50 = self.close_d.rolling(50, min_periods=45).mean()
        self.btc_j = int(np.where(self.cols == BTC)[0][0])

    # --- universe -------------------------------------------------------------------------
    def universe_idx(self, i: int) -> np.ndarray:
        """Top-N eligible series by trailing quote volume at grid row i (ties broken by name)."""
        self._prepare()
        el = np.where(self._E[i])[0]
        return el[np.lexsort((self.cols[el], -self._Q[i, el]))][: self.v["universe"]["top_n"]]

    def universe(self, t: pd.Timestamp) -> list[str]:
        self._prepare()
        return list(self.cols[self.universe_idx(self.close_d.index.get_loc(t))])

    def _prepare(self):
        if not hasattr(self, "_E"):
            self._E = self.eligible.to_numpy()
            self._Q = self.qv30.to_numpy()
            self._C = self.close_d.to_numpy()
            self._MA = self.ma50.to_numpy()
            self._R = self.r_d.to_numpy()
            self._R30 = self.ret30.to_numpy()

    # --- features -------------------------------------------------------------------------
    def btc_features(self) -> pd.DataFrame:
        p = self.close_d[BTC]
        lp = np.log(p)
        r = lp.diff()
        t1 = lp - lp.shift(30)
        return pd.DataFrame({
            "T1": t1,
            "T2": lp - lp.shift(90),
            "T3": p / p.rolling(200).mean() - 1,
            "T4": t1.abs() / r.abs().rolling(30).sum(),
            "C1": p / p.rolling(365).max() - 1,
            "C2": p / p.rolling(90).min() - 1,
            "V1": r.rolling(30).std() * np.sqrt(365),
            "V2": r.rolling(7).std() / r.rolling(90).std(),
        })

    def structure_features(self, times: pd.DatetimeIndex) -> pd.DataFrame:
        self._prepare()
        rows = []
        for t in times:
            i = self.close_d.index.get_loc(t)
            u = self.universe_idx(i)
            m1 = m2 = m3 = m4 = np.nan
            if len(u):
                c, ma = self._C[i, u], self._MA[i, u]
                ok = ~np.isnan(ma) & ~np.isnan(c)
                if ok.any():
                    m1 = float(np.mean(c[ok] > ma[ok]))
                if i >= 29:
                    rw = self._R[i - 29:i + 1][:, u]
                    full = ~np.isnan(rw).any(axis=0)
                    n = int(full.sum())
                    if n >= 3:
                        with np.errstate(invalid="ignore", divide="ignore"):
                            cm = np.corrcoef(rw[:, full].T)
                        off = cm[~np.eye(n, dtype=bool)]
                        m2 = float(np.nanmean(off)) if np.isfinite(off).any() else np.nan
                x = self._R30[i, u]
                ok = ~np.isnan(x)
                if ok.sum() >= 3:
                    m3 = float(np.std(x[ok], ddof=1))
                alt = ok & (u != self.btc_j)
                btc30 = self._R30[i, self.btc_j]
                if alt.any() and not np.isnan(btc30):
                    m4 = float(np.median(x[alt]) - btc30)
            rows.append((m1, m2, m3, m4))
        return pd.DataFrame(rows, index=times, columns=["M1", "M2", "M3", "M4"])

    def positioning_features(self, times: pd.DatetimeIndex) -> pd.DataFrame:
        out = pd.DataFrame(np.nan, index=times, columns=["P1", "P2"])
        f, oi = self.data.funding, self.data.oi
        if f is not None and len(f):
            ft, fv = f.index, f.to_numpy()
            need = self.v["funding_min_coverage"] * 7 * self.v["funding_prints_per_day"]
            for t in times:
                lo = ft.searchsorted(t - pd.Timedelta(days=7), side="right")
                hi = ft.searchsorted(t, side="right")
                if hi - lo >= need:
                    out.at[t, "P1"] = float(fv[lo:hi].mean())
        if oi is not None and len(oi):
            ot, ov = oi.index, oi.to_numpy()
            stale = pd.Timedelta(hours=self.v["oi_max_staleness_hours"])

            def oi_at(t):
                j = ot.searchsorted(t, side="right") - 1
                return ov[j] if j >= 0 and ot[j] >= t - stale else np.nan

            for t in times:
                a, b = oi_at(t), oi_at(t - pd.Timedelta(days=30))
                out.at[t, "P2"] = float(np.log(a / b)) if a > 0 and b > 0 else np.nan
        return out

    def macro_features(self, times: pd.DatetimeIndex) -> pd.DataFrame:
        cols = GROUPS["MACRO"]
        out = pd.DataFrame(np.nan, index=times, columns=cols)
        fred = self.data.fred or {}
        need = {"CPIAUCNS", "DFEDTARU", "DGS10", "DTWEXBGS", "SP500", "VIXCLS", "DCOILWTICO"}
        if not need <= set(fred):
            return out
        cpi = fred["CPIAUCNS"]
        rel_day = self.v["cpi_release_day"]
        release = pd.DatetimeIndex([(m + pd.offsets.MonthBegin(1)) + pd.Timedelta(days=rel_day - 1)
                                    for m in cpi.index]).tz_localize("UTC")
        order = np.argsort(release.asi8, kind="stable")
        release, cpi_sorted = release[order], cpi.iloc[order]

        def yoy(month: pd.Timestamp) -> float:
            prev = month - pd.DateOffset(years=1)
            return float(cpi[month] / cpi[prev] - 1) if prev in cpi.index else np.nan

        d30, d180 = pd.Timedelta(days=30), pd.Timedelta(days=180)
        sp = fred["SP500"]
        # extra publication lags (e.g. DTWEXBGS is published weekly, so its latest days are not yet out)
        lags = {k: pd.Timedelta(days=d) for k, d in (self.v.get("macro_lag_days") or {}).items()}

        def val(s: str, when: pd.Timestamp) -> float:
            return _value_before_day(fred[s], when - lags.get(s, pd.Timedelta(0)))

        for t in times:
            k = release.searchsorted(t, side="right")  # months released at or before t
            if k >= 4:
                released = cpi_sorted.index[:k]
                out.at[t, "X1"] = yoy(released[-1])
                out.at[t, "X2"] = yoy(released[-1]) - yoy(released[-4])
            v = {s: val(s, t) for s in ("DFEDTARU", "DGS10", "DTWEXBGS", "VIXCLS", "DCOILWTICO")}
            out.at[t, "X3"] = float(np.sign(v["DFEDTARU"] - val("DFEDTARU", t - d180)))
            out.at[t, "X4"] = v["DGS10"] - val("DGS10", t - d30)
            out.at[t, "X5"] = v["DTWEXBGS"] / val("DTWEXBGS", t - d30) - 1
            day = t.tz_convert(None).normalize()
            hist = sp.iloc[: sp.index.searchsorted(day, side="left")]
            if len(hist) >= 200:
                out.at[t, "X6"] = float(hist.iloc[-1] / hist.iloc[-200:].mean() - 1)
            out.at[t, "X7"] = v["VIXCLS"]
            out.at[t, "X8"] = v["DCOILWTICO"] / val("DCOILWTICO", t - d30) - 1
        return out

    def calendar_features(self, times: pd.DatetimeIndex) -> pd.DataFrame:
        h = pd.Timedelta(days=self.v["horizon_days"])
        vals = []
        for t in times:
            first = pd.Timestamp(year=t.year, month=t.month, day=12, hour=12, minute=30, tz="UTC")
            cands = [first, first + pd.DateOffset(months=1)]
            vals.append(float(any(t < c <= t + h for c in cands)))
        return pd.DataFrame({"E1": vals}, index=times)

    def features(self, times: pd.DatetimeIndex | None = None) -> pd.DataFrame:
        times = self.close_d.index if times is None else pd.DatetimeIndex(times)
        parts = [self.btc_features().reindex(times), self.structure_features(times),
                 self.positioning_features(times), self.macro_features(times), self.calendar_features(times)]
        return pd.concat(parts, axis=1)[FEATURES]


def available_groups(data: MarketData) -> dict[str, bool]:
    fred_ok = data.fred is not None and {"CPIAUCNS", "DFEDTARU", "DGS10", "DTWEXBGS", "SP500", "VIXCLS",
                                         "DCOILWTICO"} <= set(data.fred)
    return {**{g: True for g in CORE_GROUPS}, "POSITIONING": data.funding is not None and data.oi is not None,
            "MACRO": fred_ok, "CALENDAR": True}
