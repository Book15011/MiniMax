"""Hand-built cases for src/models/baitoey/_overlays.py (pre-registration research/baitoey/prereg/20261009-overlays.md)."""
import numpy as np
import pandas as pd

from src.contracts import MarketView, ModelSpec
from src.models.baitoey import _overlays as ov

T0 = pd.Timestamp("2026-01-01 00:00", tz="UTC")


class Fixed:
    """A stand-in base model: fixed weights; records the previous targets it was given."""
    spec = ModelSpec(name="fixed", method="momentum", author="baitoey", rebalance_hours=24, band=0.05,
                     uses_shorts=True, description="test")

    def __init__(self, w):
        self.w, self.seen = pd.Series(w, dtype=float), []

    def targets(self, view):
        self.seen.append(view.prev_targets.copy())
        return self.w.copy()


def view(daily: dict[str, list[float]], t_hour=16, params=None, prev=None):
    """Hourly closes where every hour of day d carries daily[coin][d]; the view ends on the last day at t_hour."""
    n = len(next(iter(daily.values())))
    idx = pd.date_range(T0, T0 + pd.Timedelta(days=n - 1, hours=t_hour), freq="h")
    close = pd.DataFrame({c: np.repeat(v, 24)[:len(idx)] for c, v in daily.items()}, index=idx)
    return MarketView(t=idx[-1], close=close, quote_volume=close * 0 + 1e6, universe=tuple(daily),
                      params={"vt": {}, **(params or {})}, prev_targets=pd.Series(dtype=float) if prev is None else prev)


def test_alts_lagging_btc_move_alt_longs_to_btc_or_cash_and_keep_shorts():
    # over the last 10 days BTC +10%, A 0%, B +5%: the basket (+2.5%) lags BTC
    flat = [100.0] * 20
    d = {"BTCUSDT": flat + [110.0], "AUSDT": flat + [100.0], "BUSDT": flat + [105.0], "CUSDT": flat + [100.0]}
    base = {"AUSDT": 0.4, "BUSDT": 0.3, "BTCUSDT": 0.1, "CUSDT": -0.1}
    to_btc = ov.make(ov.AltBtc, Fixed(base), "t1", "x", "t", TO="btc").targets(view(d, params={"lookback_days": 10}))
    to_cash = ov.make(ov.AltBtc, Fixed(base), "t2", "x", "t", TO="cash").targets(view(d, params={"lookback_days": 10}))
    assert to_btc.round(9).to_dict() == {"BTCUSDT": 0.8, "CUSDT": -0.1}
    assert to_cash.round(9).to_dict() == {"BTCUSDT": 0.1, "CUSDT": -0.1}


def test_alts_beating_btc_leave_the_base_unchanged():
    flat = [100.0] * 20
    d = {"BTCUSDT": flat + [101.0], "AUSDT": flat + [110.0], "BUSDT": flat + [100.0]}
    base = {"AUSDT": 0.5, "BUSDT": 0.5}
    out = ov.make(ov.AltBtc, Fixed(base), "t3", "x", "t", TO="btc").targets(view(d, params={"lookback_days": 10}))
    assert out.to_dict() == base


def test_breakdown_blocks_until_a_close_above_the_20_day_mean_and_ignores_shorts():
    p = {"channel_days": 20, "scan_days": 120}
    base = {"AUSDT": 0.5, "BUSDT": -0.2}
    m = ov.make(ov.Breakdown, Fixed(base), "t4", "x", "t")
    a = [100.0] * 25 + [90.0]                                  # day 25 closes below the 20-day low (100)
    assert m.targets(view({"AUSDT": a, "BUSDT": a}, params=p)).to_dict() == {"BUSDT": -0.2}
    a2 = a + [99.0]                                            # below the 20-day mean (99.5): still out
    assert m.targets(view({"AUSDT": a2, "BUSDT": a2}, params=p)).to_dict() == {"BUSDT": -0.2}
    a3 = a2 + [100.0]                                          # above the mean (99.45): back in
    assert m.targets(view({"AUSDT": a3, "BUSDT": a3}, params=p)).to_dict() == base


def test_event_window_is_12_hours_before_to_6_hours_after_by_fill_time():
    T = pd.Timestamp("2026-03-11 12:30", tz="UTC")
    times = np.array([T.value])
    f = lambda h: ov.event_factor(T + pd.Timedelta(hours=h), times, 12, 6, 0.5)
    assert f(-12.5) == 1.0 and f(-12) == 0.5 and f(-11.5) == 0.5 and f(5.5) == 0.5 and f(6) == 1.0 and f(6.5) == 1.0


def test_event_wrapper_halves_the_standing_book_and_gives_the_base_its_unscaled_book():
    T = pd.Timestamp("2026-01-26 20:00", tz="UTC")            # an event at 20:00 on the last day
    ov._EVENTS[("TEST",)] = np.array([T.value])
    p = {"events": ["TEST"], "before_hours": 12, "after_hours": 6, "scale": 0.5}
    inner = Fixed({"AUSDT": 0.6})
    m = ov.make(ov.EventDerisk, inner, "t5", "x", "t", hourly=True)
    d = {"AUSDT": [100.0] * 26}
    # 16:00 (inside the window, fill 17:00 inside): the base decides with its unscaled previous book; output halved
    out = m.targets(view(d, t_hour=16, params=p, prev=pd.Series({"AUSDT": 0.3})))
    assert inner.seen[-1].to_dict() == {"AUSDT": 0.6} and out.to_dict() == {"AUSDT": 0.3}
    # 07:00 (fill 08:00 = T - 12 h): not yet inside, so the standing book is whole; the base is not asked
    calls = len(inner.seen)
    out = m.targets(view(d, t_hour=7, params=p, prev=pd.Series({"AUSDT": 0.6})))
    assert out.to_dict() == {"AUSDT": 0.3} and len(inner.seen) == calls      # fill at 08:00 is inside: halved
    out = m.targets(view(d, t_hour=6, params=p, prev=pd.Series({"AUSDT": 0.6})))
    assert out.to_dict() == {"AUSDT": 0.6}                                    # fill at 07:00: outside
    del ov._EVENTS[("TEST",)]
