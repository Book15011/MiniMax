"""Hand-built BTC paths for src/models/baitoey/_btc_short.py (research/baitoey/prereg/20261009-btc-short.md)."""
import numpy as np
import pandas as pd

from src.contracts import MarketView
from src.models.baitoey import _btc_short as bs

T0 = pd.Timestamp("2026-01-01 00:00", tz="UTC")
P = {"variant": "a", "replay_days": 90, "hard_stop": 0.045, "time_stop_hours": 168, "event_block_hours": 12,
     "events": ["CPI", "FOMC_MINUTES"]}


def path(days: list[float], overrides: dict | None = None, end_day: int | None = None, end_hour: int = 23) -> pd.Series:
    """Hourly closes: every hour of day d is days[d]; overrides {(day, hour): value}; the path ends at end_day/end_hour."""
    end_day = len(days) - 1 if end_day is None else end_day
    idx = pd.date_range(T0, T0 + pd.Timedelta(days=end_day, hours=end_hour), freq="h")
    c = pd.Series(np.repeat(np.asarray(days, float), 24)[:len(idx)], index=idx)
    for (d, h), v in (overrides or {}).items():
        c.loc[T0 + pd.Timedelta(days=d, hours=h)] = v
    return c


def bar(c, day, hour):
    return int(c.index.get_loc(T0 + pd.Timedelta(days=day, hours=hour)))


def start(day):
    return int((T0 + pd.Timedelta(days=day)).value)


def test_a_enters_below_the_ema_and_the_hard_stop_closes_it_on_the_next_hourly_close():
    c = path([100.0] * 150 + [95.0, 100.0, 100.0])
    tr = bs.run_short(c, {**P, "variant": "a"}, start(100))
    assert tr[0]["i"] == bar(c, 150, 16) and tr[0]["entry"] == 95.0 and np.isclose(tr[0]["stop"], 95 * 1.045)
    assert tr[0]["reason"] == "stop" and tr[0]["x"] == bar(c, 151, 0)


def test_a_time_stop_then_no_reentry_until_the_condition_has_lapsed():
    c = path([100.0] * 150 + [95.0] * 25 + [88.0] * 5)
    tr = bs.run_short(c, {**P, "variant": "a"}, start(100))
    assert tr[0]["reason"] == "time" and tr[0]["x"] == tr[0]["f"] + 168
    assert len(tr) == 2 and tr[1]["i"] == bar(c, 175, 16)          # re-armed while flat at 95, re-entered at 88


def test_b_breakdown_entry_and_cover_above_the_10_day_high():
    c = path([100.0] * 150 + [99.0, 100.5, 100.5])
    tr = bs.run_short(c, {**P, "variant": "b"}, start(100))
    assert tr[0]["i"] == bar(c, 150, 16) and tr[0]["reason"] == "cover" and tr[0]["x"] == bar(c, 151, 16)


def test_c_failed_rally_uses_the_bounce_high_for_its_stop():
    over = {(176, h): 91.0 for h in range(11)}                     # a touch of the 20-day mean (90) ...
    over[(177, 0)] = 92.0                                          # ... a close back below it, then a squeeze
    c = path([100.0] * 150 + [90.0] * 26 + [89.0, 89.0], over)
    tr = bs.run_short(c, {**P, "variant": "c"}, start(100))
    last = tr[-1]
    assert last["i"] == bar(c, 176, 16) and np.isclose(last["stop"], 91.0 * 1.005)
    assert last["reason"] == "stop" and last["x"] == bar(c, 177, 0)


def test_no_new_short_within_12_hours_before_an_event():
    bs._CACHE[("ev", ("TEST",))] = np.array([(T0 + pd.Timedelta(days=151, hours=2)).value])
    try:
        c = path([100.0] * 150 + [95.0] * 3)
        tr = bs.run_short(c, {**P, "variant": "a", "events": ["TEST"]}, start(100))
        assert tr[0]["i"] == bar(c, 151, 16)                       # day 150 blocked (event 10 h later); day 151 not
    finally:
        del bs._CACHE[("ev", ("TEST",))]


def test_the_add_on_shorts_only_while_the_switch_reads_down():
    c = path([100.0] * 150 + [95.0] * 3)
    assert bs.run_short(c, P, start(100), switch_down=np.zeros(len(c), bool)) == []
    assert bs.run_short(c, P, start(100), switch_down=np.ones(len(c), bool))[0]["i"] == bar(c, 150, 16)


def view(c, prev=None, params=None):
    return MarketView(t=c.index[-1], close=c.to_frame("BTCUSDT"), quote_volume=c.to_frame("BTCUSDT") * 0 + 1e6,
                      universe=("BTCUSDT", "AUSDT"), params=params or P,
                      prev_targets=pd.Series(dtype=float) if prev is None else pd.Series(prev, dtype=float))


def test_the_standalone_model_is_short_or_cash_never_long():
    m = bs.make(bs.BtcShort, "t1", "t")
    on = m.targets(view(path([100.0] * 150 + [95.0, 100.0], end_day=150, end_hour=20)))
    off = m.targets(view(path([100.0] * 150 + [95.0, 100.0], end_day=151, end_hour=0)))
    assert on.to_dict() == {"BTCUSDT": -0.4} and off.empty


def test_the_add_on_between_decisions_keeps_the_book_and_drops_only_a_stopped_short():
    m = bs.make(bs.E20BtcShort, "t2", "t")
    params = {"vt": {"switch": {"ema_days": 20, "hysteresis": 0.03}}, "short": P}
    prev = {"BTCUSDT": -0.4, "AUSDT": 0.3}
    held = m.targets(view(path([100.0] * 150 + [95.0, 100.0], end_day=150, end_hour=20), prev, params))
    stopped = m.targets(view(path([100.0] * 150 + [95.0, 100.0], end_day=151, end_hour=0), prev, params))
    assert held.to_dict() == prev and stopped.round(9).to_dict() == {"AUSDT": 0.3}
