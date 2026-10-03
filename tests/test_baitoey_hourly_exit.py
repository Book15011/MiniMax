import numpy as np
import pandas as pd

from src.contracts import MarketView
from src.models.baitoey._hourly_exit import HourlyExit

IDX = pd.date_range("2026-01-01 00:00", periods=10 * 24, freq="h", tz="UTC")
Q = {"exit_low_hours": 24, "exit_volume_ratio": 1.5, "volume_short_hours": 24, "volume_long_days": 7}


def view(px: dict, vol: dict, end: int, prev: dict, hourly_exit: bool = True) -> MarketView:
    close = pd.DataFrame(px, index=IDX).iloc[: end + 1]
    qv = pd.DataFrame(vol, index=IDX).iloc[: end + 1]
    return MarketView(t=close.index[-1], close=close, quote_volume=qv, universe=tuple(px),
                      params={"vt": {}, "exit": Q, "hourly_exit": hourly_exit}, prev_targets=pd.Series(prev, dtype=float))


def drop_at(k: int) -> np.ndarray:
    px = 100 + np.sin(np.arange(len(IDX)) / 5)
    px[k:] = 90.0                                                    # a new 24 h low from hour k on
    return px


def volume(spike_from: int | None) -> np.ndarray:
    v = np.full(len(IDX), 1e6)
    if spike_from is not None:
        v[spike_from:] = 5e6                                          # several times normal from then on
    return v


END = 9 * 24 + 3                                                      # 03:00 UTC, not a decision hour


def test_a_breakdown_on_heavy_volume_is_sold_at_once():
    px = {"AUSDT": drop_at(END), "BUSDT": 100 + np.sin(np.arange(len(IDX)) / 5)}
    vol = {"AUSDT": volume(END - 10), "BUSDT": volume(None)}
    w = HourlyExit().targets(view(px, vol, END, {"AUSDT": 0.4, "BUSDT": 0.4}))
    assert list(w.index) == ["BUSDT"]


def test_a_breakdown_on_normal_volume_is_kept():
    px = {"AUSDT": drop_at(END)}
    w = HourlyExit().targets(view(px, {"AUSDT": volume(None)}, END, {"AUSDT": 0.4}))
    assert list(w.index) == ["AUSDT"]


def test_shorts_and_the_control_are_untouched():
    px = {"AUSDT": drop_at(END)}
    vol = {"AUSDT": volume(END - 10)}
    assert list(HourlyExit().targets(view(px, vol, END, {"AUSDT": -0.4})).index) == ["AUSDT"]
    assert list(HourlyExit().targets(view(px, vol, END, {"AUSDT": 0.4}, hourly_exit=False)).index) == ["AUSDT"]
