"""Proposed MarketView fields: empty by default (existing models unaffected) and daily_close is point-in-time."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.contracts import MarketView


def view() -> MarketView:
    idx = pd.date_range("2024-01-01 01:00", periods=72, freq="h", tz="UTC")
    close = pd.DataFrame({"AAA": np.arange(72.0), "BBB": np.arange(72.0) * 2, "CCC": 1.0}, index=idx)
    return MarketView(t=idx[-1], close=close, quote_volume=close * 0 + 1, universe=("AAA", "BBB"))


def test_new_fields_default_to_empty():
    v = view()
    assert v.ohlc == {} and v.funding.empty and v.open_interest.empty and v.macro.empty and v.events.empty


def test_daily_close_is_the_16_utc_grid_up_to_t_on_the_universe():
    v = view()
    d = v.daily_close()
    assert list(d.columns) == ["AAA", "BBB"]
    assert list(d.index.hour) == [16, 16, 16] and (d.index <= v.t).all()
    assert d["AAA"].tolist() == [15.0, 39.0, 63.0]     # bars from 01:00: 16:00 is index 15, then every 24
    assert v.daily_close(hour=0).index.hour.tolist() == [0, 0, 0]
