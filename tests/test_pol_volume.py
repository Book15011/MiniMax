"""pol volume models: market-volume gate (pol_vt_mvr) and capitulation-volume mean reversion (pol_mr_cap)."""
import numpy as np
import pandas as pd
import pytest

from src.config import load_config
from src.contracts import MarketView, check_targets
from src.models.baitoey.baitoey_vt_mom import MODEL as VT_MOM
from src.models.pol._volume import market_volume_ratio
from src.models.pol.pol_mr_cap import MODEL as MR_CAP
from src.models.pol.pol_vt_mvr import MODEL as VT_MVR

MODELS = load_config()["models"]
COINS = ["BTCUSDT", "ETHUSDT"] + [f"C{i}USDT" for i in range(10)]
N = 45 * 24


def market():
    idx = pd.date_range("2024-01-01 01:00", periods=N, freq="h", tz="UTC")
    k = np.arange(N)
    close = pd.DataFrame({c: 100 * (1 + 0.004 * np.sin(k / (5 + j)) + 0.0004 * j * k / N) for j, c in enumerate(COINS)},
                         index=idx)
    return close, pd.DataFrame(1e6, index=idx, columns=COINS)


def view(close, qv, params, prev=None):
    return MarketView(t=close.index[-1], close=close, quote_volume=qv, universe=tuple(COINS), params=params,
                      prev_targets=pd.Series(prev or {}, dtype=float))


def test_market_volume_ratio_reads_the_last_day_and_skips_gappy_coins():
    close, qv = market()
    assert market_volume_ratio(view(close, qv, {}), 24, 30, 10) == pytest.approx(1.0)
    qv.iloc[-24:] *= 0.5
    assert market_volume_ratio(view(close, qv, {}), 24, 30, 10) == pytest.approx(12 / ((720 - 24 + 12) / 30))
    qv.iloc[-3, :3] = np.nan                                 # 9 complete coins left: below min_coins
    assert market_volume_ratio(view(close, qv, {}), 24, 30, 10) is None


def test_quiet_market_halves_the_book_with_the_same_coins():
    close, qv = market()
    p = MODELS["pol_vt_mvr"]
    base = VT_MOM.targets(view(close, qv, p))
    pd.testing.assert_series_equal(VT_MVR.targets(view(close, qv, p)), base)
    qv.iloc[-24:] *= 0.5
    w = check_targets(VT_MVR.targets(view(close, qv, p)), view(close, qv, p), VT_MVR.spec)
    pd.testing.assert_series_equal(w, base * p["mvr_low_scale"])


def oversold(close, c):
    j = close.columns.get_loc(c)
    close.iloc[-12:, j] = close.iloc[-12:, j].to_numpy() * np.linspace(0.97, 0.80, 12)
    return close


def test_mean_reversion_enters_only_on_heavy_volume_but_keeps_holdings():
    close, qv = market()
    c = "C4USDT"
    close = oversold(close, c)
    p = MODELS["pol_mr_cap"]
    assert MR_CAP.targets(view(close, qv, p)).empty                       # normal volume: no entry
    qv.iloc[-24:, qv.columns.get_loc(c)] *= 2.0
    w = check_targets(MR_CAP.targets(view(close, qv, p)), view(close, qv, p), MR_CAP.spec)
    assert list(w.index) == [c]
    qv.iloc[-24:, qv.columns.get_loc(c)] /= 2.0                           # held already: volume no longer matters
    assert c in MR_CAP.targets(view(close, qv, p, {c: 0.1})).index
    qv.iloc[-2, qv.columns.get_loc(c)] = np.nan
    assert MR_CAP.targets(view(close, qv, p)).empty                       # missing volume: no new entry
