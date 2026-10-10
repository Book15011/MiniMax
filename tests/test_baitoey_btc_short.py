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


def test_a2_uses_the_20_day_ema_and_a_1_percent_band():
    c = path([100.0] * 150 + [98.5, 98.5, 100.5])                 # -1.5%: below EMA20 x 0.99, not below EMA40 x 0.97
    a = bs.run_short(c, P, start(100))
    a2 = bs.run_short(c, {**P, "variant": "a2", "ema_days": 20, "entry_below": 0.01, "cover_above": 0.01, "ret_days": 7}, start(100))
    assert a == [] and a2[0]["i"] == bar(c, 150, 16)


def test_b2_breaks_the_10_day_low_and_covers_above_the_5_day_high():
    c = path([100.0] * 140 + [98.0] * 10 + [97.5, 98.2, 98.2])     # day 140 breaks the 10-day low (a first short),
    b2 = bs.run_short(c, {**P, "variant": "b2", "low_days": 10, "high_days": 5}, start(100))   # day 150 breaks it again
    assert b2[0]["i"] == bar(c, 140, 16) and b2[0]["reason"] == "time"
    assert b2[-1]["i"] == bar(c, 150, 16) and b2[-1]["reason"] == "cover" and b2[-1]["x"] == bar(c, 151, 16)


def test_an_ungated_add_on_shorts_whatever_the_switch_reads():
    m = bs.make(bs.E20BtcShort, "t3", "t")
    params = {"vt": {"switch": {"ema_days": 20, "hysteresis": 0.03}}, "short": {**P, "gate": "none"}}
    held = m.targets(view(path([100.0] * 150 + [95.0, 100.0], end_day=150, end_hour=20), {"BTCUSDT": -0.4}, params))
    assert held.to_dict() == {"BTCUSDT": -0.4}


def coin_view(paths: dict, t_day, t_hour, prev=None, params=None, qv=None):
    n_end = T0 + pd.Timedelta(days=t_day, hours=t_hour)
    close = pd.DataFrame({k: v.loc[:n_end] for k, v in paths.items()})
    q = close * 0 + 1e6 if qv is None else pd.DataFrame({k: close[k] * 0 + qv[k] for k in close})
    return MarketView(t=close.index[-1], close=close, quote_volume=q, universe=tuple(paths), params=params,
                      prev_targets=pd.Series(dtype=float) if prev is None else pd.Series(prev, dtype=float))


def test_the_basket_takes_the_most_traded_altcoins_but_never_btc_or_eth():
    paths = {k: path([100.0] * 40) for k in ("BTCUSDT", "ETHUSDT", "AUSDT", "BUSDT", "CUSDT")}
    p = {"coins": "top_alts", "n_coins": 2}
    v = coin_view(paths, 39, 20, params=p, qv={"BTCUSDT": 9e9, "ETHUSDT": 8e9, "AUSDT": 1e6, "BUSDT": 3e6, "CUSDT": 2e6})
    assert bs.E20CoinShort.candidates(v, p) == ["BUSDT", "CUSDT"]


def test_a_coin_short_between_decisions_keeps_the_book_and_drops_only_its_stopped_short():
    paths = {"BTCUSDT": path([100.0] * 152), "ETHUSDT": path([100.0] * 150 + [95.0, 100.0])}
    params = {"vt": {"switch": {"ema_days": 20, "hysteresis": 0.03}}, "short": P, "coins": ["ETHUSDT"], "size_each": 0.4, "max_open": 1}
    m = bs.make(bs.E20CoinShort, "t4", "t")
    prev = {"ETHUSDT": -0.4, "AUSDT": 0.3}
    held = m.targets(coin_view(paths, 150, 20, prev, params))
    stopped = m.targets(coin_view(paths, 151, 0, prev, params))
    assert held.to_dict() == prev and stopped.round(9).to_dict() == {"AUSDT": 0.3}


def test_at_a_decision_open_shorts_are_added_and_e20_is_scaled_to_make_room(monkeypatch):
    class Stub:
        spec = bs.E20V45.spec
        def targets(self, view):
            return pd.Series({"AUSDT": 0.6, "BUSDT": 0.4})
    monkeypatch.setattr(bs, "E20V45", Stub())
    paths = {"BTCUSDT": path([100.0] * 151), "XUSDT": path([100.0] * 150 + [95.0]), "YUSDT": path([100.0] * 150 + [95.0])}
    params = {"vt": {"switch": {"ema_days": 20, "hysteresis": 0.03}}, "short": P, "coins": ["XUSDT", "YUSDT"], "size_each": 0.1, "max_open": 4}
    w = bs.make(bs.E20CoinShort, "t5", "t").targets(coin_view(paths, 150, 16, None, params))
    assert w.round(9).to_dict() == {"AUSDT": 0.48, "BUSDT": 0.32, "XUSDT": -0.1, "YUSDT": -0.1}
