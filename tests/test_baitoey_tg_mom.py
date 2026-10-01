import numpy as np
import pandas as pd
import pytest

from src.config import load_config
from src.contracts import MarketView, check_targets
from src.models.baitoey.baitoey_tg_mom import MODEL

COINS = ["BTCUSDT", "ETHUSDT"] + [f"C{i}USDT" for i in range(10)]


def make_view(btc_drift: float, seed: int = 1, **overrides) -> MarketView:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01 01:00", periods=45 * 24, freq="h", tz="UTC")
    drifts = {c: (btc_drift if c == "BTCUSDT" else rng.normal(0, 0.0008)) for c in COINS}
    close = pd.DataFrame({c: 100 * np.exp(np.cumsum(rng.normal(drifts[c], 0.006, len(idx)))) for c in COINS},
                         index=idx)
    qv = pd.DataFrame({c: rng.lognormal(12, 0.3, len(idx)) for c in COINS}, index=idx)
    qv.iloc[-24:] *= 1.5  # above-normal volume today, so the volume filter lets coins through
    params = {**load_config()["models"]["baitoey_tg_mom"], **overrides}
    return MarketView(t=idx[-1], close=close, quote_volume=qv, universe=tuple(COINS), params=params)


def test_gate_follows_btc_trend():
    assert MODEL.gate(make_view(+0.002)) == pytest.approx(1.0)
    assert MODEL.gate(make_view(-0.002)) == pytest.approx(0.0)


def test_risk_on_holds_capped_longs_within_contract():
    view = make_view(+0.002)
    w = check_targets(MODEL.targets(view), view, MODEL.spec)
    longs = w[w > 0]
    assert 0 < len(longs) <= view.params["k"]
    assert (longs <= view.params["max_weight"] + 1e-12).all()
    assert w.abs().sum() <= 1.0


def test_risk_off_only_shorts_falling_coins():
    view = make_view(-0.002)
    w = check_targets(MODEL.targets(view), view, MODEL.spec)
    assert (w < 0).all() and len(w) <= view.params["short_k"]
    assert w.abs().sum() == pytest.approx(view.params["short_gross"])
    last = view.close.iloc[-1]
    mom = sum(last / view.close.iloc[-1 - h] - 1 for h in view.params["lookback_hours"])
    assert (mom[w.index] < 0).all()


def test_long_only_fallback_never_shorts_and_keeps_btc():
    view = make_view(-0.002, long_only=True)
    w = check_targets(MODEL.targets(view), view, MODEL.spec)
    assert (w >= 0).all()
    assert w["BTCUSDT"] == pytest.approx(view.params["btc_floor"])


def test_deterministic():
    view = make_view(+0.001, seed=3)
    pd.testing.assert_series_equal(MODEL.targets(view), MODEL.targets(view))
