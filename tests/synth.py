"""A small synthetic market for leakage tests (deterministic)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.validation.features import MarketData

START, END = pd.Timestamp("2019-01-01 01:00", tz="UTC"), pd.Timestamp("2021-06-30 00:00", tz="UTC")
# series id -> (listing start, delisting end or None)
COINS = {
    "BTCUSDT": ("2019-01-01", None), "ETHUSDT": ("2019-01-01", None), "AAAUSDT": ("2019-01-01", None),
    "BBBUSDT": ("2019-03-01", None), "CCCUSDT": ("2019-06-01", "2020-11-01"), "DDDUSDT": ("2020-02-15", None),
    "EEEUSDT": ("2020-05-10", None), "FFFUSDT": ("2019-01-01", None), "PAXGUSDT": ("2019-01-01", None),
    "USDCUSDT": ("2019-01-01", None), "GGGUSDT": ("2019-01-01", None), "HHHUSDT": ("2020-08-01", None),
}
LATE_LISTING = ("EEEUSDT", pd.Timestamp("2020-05-10", tz="UTC"))


def make_market(seed: int = 7) -> MarketData:
    rng = np.random.default_rng(seed)
    idx = pd.date_range(START, END, freq="h")
    n = len(idx)
    common = rng.normal(0, 0.006, n)
    close, qv = {}, {}
    for j, (c, (a, b)) in enumerate(COINS.items()):
        r = 0.6 * common + rng.normal(0, 0.008, n)
        p = 100 * (1 + j) * np.exp(np.cumsum(r))
        mask = idx >= pd.Timestamp(a, tz="UTC")
        if b:
            mask &= idx < pd.Timestamp(b, tz="UTC")
        p = np.where(mask, p, np.nan)
        close[c] = p
        qv[c] = np.where(mask, rng.lognormal(10 + (12 - j) * 0.3, 0.5, n), np.nan)
    close_df, qv_df = pd.DataFrame(close, index=idx), pd.DataFrame(qv, index=idx)
    # a few missing hours, as in real archives
    for k in rng.choice(n, 40, replace=False):
        close_df.iloc[k, rng.integers(0, len(COINS))] = np.nan

    ft = pd.date_range(pd.Timestamp("2019-01-01 00:00", tz="UTC"), END, freq="8h")
    funding = pd.Series(rng.normal(1e-4, 5e-5, len(ft)), index=ft)
    ot = pd.date_range(pd.Timestamp("2019-01-01 00:05", tz="UTC"), END, freq="15min")
    oi = pd.Series(50_000 * np.exp(np.cumsum(rng.normal(0, 0.001, len(ot)))), index=ot)

    days = pd.bdate_range("2017-01-02", "2021-07-15")
    def daily(level, vol):
        return pd.Series(level * np.exp(np.cumsum(rng.normal(0, vol, len(days)))), index=days)
    months = pd.date_range("2016-01-01", "2021-06-01", freq="MS")
    fred = {
        "CPIAUCNS": pd.Series(240 * np.exp(np.cumsum(rng.normal(0.002, 0.002, len(months)))), index=months),
        "DFEDTARU": pd.Series(np.repeat([1.0, 1.5, 2.0, 2.5, 1.75, 0.25], len(days) // 6 + 1)[: len(days)], index=days),
        "DGS10": daily(2.0, 0.01), "DTWEXBGS": daily(110, 0.003), "SP500": daily(2500, 0.01),
        "VIXCLS": daily(18, 0.03), "DCOILWTICO": daily(55, 0.02),
    }
    return MarketData(close_df, qv_df, funding, oi, fred)


def cpi_release(month: pd.Timestamp, release_day: int = 16) -> pd.Timestamp:
    return (month + pd.offsets.MonthBegin(1) + pd.Timedelta(days=release_day - 1)).tz_localize("UTC")


def perturb_after(data: MarketData, t: pd.Timestamp, seed: int, release_day: int = 16,
                  lags: dict | None = None) -> MarketData:
    """Randomly alter every piece of data that is NOT usable at t (daily FRED series with a publication
    lag of L days are unusable from date(t - L) on)."""
    lags = lags or {}
    rng = np.random.default_rng(seed)
    close, qv = data.close.copy(), data.quote_volume.copy()
    after = close.index > t
    close.loc[after] = close.loc[after] * rng.uniform(0.5, 2.0, close.loc[after].shape)
    qv.loc[after] = qv.loc[after] * rng.uniform(0.1, 10.0, qv.loc[after].shape)
    f = data.funding.copy()
    f[f.index > t] = rng.normal(0, 1e-3, int((f.index > t).sum()))
    oi = data.oi.copy()
    oi[oi.index > t] = oi[oi.index > t] * rng.uniform(0.5, 2.0, int((oi.index > t).sum()))
    day = t.tz_convert(None).normalize()
    fred = {}
    for k, s in data.fred.items():
        s = s.copy()
        if k == "CPIAUCNS":
            late = np.array([cpi_release(m, release_day) > t for m in s.index])
        else:
            late = s.index >= day - pd.Timedelta(days=lags.get(k, 0))
        s[late] = s[late] * rng.uniform(0.5, 2.0, int(late.sum()))
        fred[k] = s
    return MarketData(close, qv, f, oi, fred)
