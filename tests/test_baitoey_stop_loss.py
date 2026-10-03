import numpy as np
import pandas as pd

from src.contracts import MarketView
from src.models.baitoey._stop_loss import StopLoss

IDX = pd.date_range("2026-01-01 00:00", periods=48, freq="h", tz="UTC")


def view(px: dict, end: int, prev: dict) -> MarketView:
    close = pd.DataFrame(px, index=IDX).iloc[: end + 1]
    return MarketView(t=close.index[-1], close=close, quote_volume=close * 0 + 1e6, universe=tuple(px),
                      params={"vt": {}, "stop": 0.05}, prev_targets=pd.Series(prev, dtype=float))


def falling(at: int, drop: float) -> np.ndarray:
    px = np.full(len(IDX), 100.0)
    px[at:] = 100.0 * (1 - drop)
    return px


def test_a_long_past_the_stop_since_16_utc_is_closed_and_the_rest_kept():
    px = {"AUSDT": falling(20, 0.06), "BUSDT": falling(20, 0.03), "CUSDT": np.full(len(IDX), 100.0)}
    w = StopLoss().targets(view(px, 22, {"AUSDT": 0.3, "BUSDT": 0.3, "CUSDT": 0.3}))   # 16:00 is hour 16
    assert set(w.index) == {"BUSDT", "CUSDT"}


def test_a_short_is_stopped_when_the_price_rises():
    px = {"AUSDT": falling(20, -0.06), "BUSDT": falling(20, 0.06)}
    w = StopLoss().targets(view(px, 22, {"AUSDT": -0.2, "BUSDT": -0.2}))
    assert list(w.index) == ["BUSDT"]


def test_a_move_before_16_utc_does_not_count():
    px = {"AUSDT": falling(10, 0.20)}                                 # fell at 10:00, flat since 16:00
    w = StopLoss().targets(view(px, 22, {"AUSDT": 0.5}))
    assert list(w.index) == ["AUSDT"]
