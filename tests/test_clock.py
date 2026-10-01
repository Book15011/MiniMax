"""Windows, days and the activity guard follow clock time, not bar counts (panel gaps: outages, maintenance)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest.data import Market
from backtest.engine import Costs, Simulator, compute_targets, decision_times, view_frames
from backtest.scoring.metrics import clock_series
from src.contracts import MarketView, ModelSpec

H = pd.Timedelta(hours=1)
T0 = pd.Timestamp("2024-01-10 16:00", tz="UTC")          # a window start (00:00 HKT)
FEE = 0.001


def market(drop=(), start="2024-01-01 00:00", hours=24 * 30) -> Market:
    """One coin rising 0.1% an hour; `drop` removes those bar times (a gap in the exchange's data)."""
    idx = pd.date_range(start, periods=hours, freq="h", tz="UTC")
    close = pd.DataFrame({"BTCUSDT": 100.0 * 1.001 ** np.arange(hours)}, index=idx).drop(index=list(drop))
    qv = close * 0 + 1e6
    uni = pd.Series({t: ("BTCUSDT",) for t in idx[idx.hour == 16]})
    return Market(close, qv, uni, pd.Series(0.0, index=close.columns), {})


class Hold:
    spec = ModelSpec(name="book_hold", method="momentum", author="book", band=0.0)

    def targets(self, view: MarketView) -> pd.Series:
        return pd.Series({"BTCUSDT": 1.0})


class Cash:
    spec = ModelSpec(name="book_cash", method="momentum", author="book", band=0.0)

    def targets(self, view: MarketView) -> pd.Series:
        return pd.Series(dtype=float)


class EvenDay:
    """100% BTC when the decision falls on an even UTC day, cash otherwise: a trade at every daily decision."""
    spec = ModelSpec(name="book_even", method="momentum", author="book", band=0.0)

    def targets(self, view: MarketView) -> pd.Series:
        assert view.close.index[-1] == view.t                 # the view always ends at the decision time
        return pd.Series({"BTCUSDT": 1.0}) if int(view.t.timestamp() // 86400) % 2 == 0 else pd.Series(dtype=float)


def run(mk: Market, model, keep_alive: float = 0.0, guard: int = 20):
    times = decision_times(mk.close.index, 24, 16, T0, T0 + pd.Timedelta(days=14))
    tg = compute_targets(model, mk, times, {})
    sim = Simulator(mk, tg, model.spec.band, Costs(FEE, FEE), 1, 16, guard, keep_alive)
    i0 = sim.index.get_loc(T0)
    res = sim.run(i0, 336, trace=True)
    fills = [(sim.index[i0 + h], kind) for h, kind, *_ in res.trace["trades"]]
    return sim, res, fills


def price(t: pd.Timestamp) -> float:
    return 100.0 * 1.001 ** int((t - pd.Timestamp("2024-01-01 00:00", tz="UTC")) / H)


def test_decisions_are_clock_hours_even_without_a_bar():
    mk = market(drop=[T0 + pd.Timedelta(days=2)])
    times = decision_times(mk.close.index, 24, 16, T0, T0 + pd.Timedelta(days=4))
    assert list(times) == [T0 + pd.Timedelta(days=d) for d in range(5)]
    c, q = view_frames(mk.close, mk.quote_volume, T0 + pd.Timedelta(days=2))
    assert c.index[-1] == T0 + pd.Timedelta(days=2) and c.iloc[-1, 0] == c.iloc[-2, 0]   # last price carried
    assert np.isnan(q.iloc[-1, 0])                                                        # no volume invented


def test_missing_single_bar_keeps_a_14_day_clock_window():
    gap = T0 + pd.Timedelta(days=3, hours=5)                    # 21:00 UTC: nothing is due then
    _, full, f_full = run(market(), Hold())
    sim, res, fills = run(market(drop=[gap]), Hold())
    assert len(res.equity) == 337 and sim.index[sim.index.get_loc(T0) + 336] == T0 + pd.Timedelta(days=14)
    assert fills == f_full == [(T0 + H, "entry")]
    # the window ends at t0 + 14 days: entry at the close of t0 + 1 h, exit price at t0 + 336 h
    assert res.equity[-1] - 1 == pytest.approx((1 - FEE) * price(T0 + 336 * H) / price(T0 + H) - 1, rel=1e-12)
    k = 3 * 24 + 5
    assert res.equity[k] == res.equity[k - 1]                   # no price in the gap hour: equity carries
    assert res.equity[k + 1] == pytest.approx(full.equity[k + 1], rel=1e-12)   # the move lands on the next bar
    assert np.allclose(np.delete(res.equity, k), np.delete(full.equity, k), rtol=1e-12)


def test_three_hour_maintenance_gap_defers_the_fill_to_the_next_bar():
    d2 = T0 + pd.Timedelta(days=2)
    gap = [d2 + H, d2 + 2 * H, d2 + 3 * H]                      # 17:00-19:00 UTC: the fill hour of the 16:00 decision
    _, res, fills = run(market(drop=gap), EvenDay())
    times = [t for t, _ in fills]
    assert d2 + 4 * H in times and d2 + H not in times          # filled at 20:00, the first bar after the gap
    others = [t for t in times if t != d2 + 4 * H]
    assert all((t - T0) % pd.Timedelta(days=1) == H for t in others)   # every other day still fills at 17:00
    assert res.active_days == 14 and len(times) == 14


def test_gap_over_the_decision_hour_still_decides_at_16_utc():
    d5 = T0 + pd.Timedelta(days=5)
    _, res, fills = run(market(drop=[d5 - H, d5, d5 + H]), EvenDay())   # 15:00-17:00 missing
    assert (d5 + 2 * H, "decision") in fills                    # the 16:00 decision (made on carried prices) fills at 18:00
    assert res.active_days == 14


def test_gap_across_the_day_boundary_moves_the_fill_into_the_new_day_only():
    d4 = T0 + pd.Timedelta(days=4)                              # day boundary (16:00 UTC)
    gap = [d4 - 2 * H, d4 - H, d4, d4 + H]                      # 14:00-17:00 missing, across the boundary
    sim, res, fills = run(market(drop=gap), EvenDay())
    i0 = sim.index.get_loc(T0)
    assert (d4 + 2 * H, "decision") in fills                    # day 4's fill at 18:00, inside day 4
    day_of = [int(((t - T0) / H - 1) // 24) for t, _ in fills]
    assert sorted(day_of) == list(range(14))                    # one fill per clock day, none moved across days
    assert sim.index[i0 + 4 * 24] == d4 and res.equity[4 * 24] == res.equity[4 * 24 - 3]   # boundary value carried
    assert sim.index[i0 + 336] == T0 + pd.Timedelta(days=14)


def test_guard_fires_at_the_first_bar_after_a_gap_and_a_day_without_bars_stays_inactive():
    # A cash book: the guard's keep-alive buys 0.2% BTC on even days (13:00 UTC, hour 21 of the day) and the next
    # day's decision sells it, so the guard is what keeps the even days active.
    d2 = T0 + pd.Timedelta(days=2)
    guard_gap = [d2 + 20 * H, d2 + 21 * H]                      # 12:00-13:00 missing -> the guard trades at 14:00
    _, res, fills = run(market(drop=guard_gap), Cash(), keep_alive=0.002)
    guards = [t for t, k in fills if k == "guard"]
    assert d2 + 22 * H in guards and d2 + 21 * H not in guards
    assert res.active_days == 14
    d4 = T0 + pd.Timedelta(days=4)
    dead = [d4 + k * H for k in range(21, 25)]                  # 13:00-16:00 missing: no bar left for day 4's guard
    _, res, fills = run(market(drop=dead), Cash(), keep_alive=0.002)
    assert res.active_days == 13                                # that day is inactive, as it would be live
    assert not any(d4 + 20 * H < t <= d4 + 24 * H for t, _ in fills)


def test_scoring_reads_daily_equity_at_clock_times_whatever_the_steps():
    t0 = T0
    steps = pd.DatetimeIndex([t0 + k * H for k in range(339) if k not in (30, 31)])   # a bar engine's 337 steps
    values = np.arange(len(steps), dtype=float)
    E = clock_series(values, steps, t0, 336)
    assert len(E) == 337
    assert E[24] == values[steps.get_loc(t0 + 24 * H)]           # day 1 = the value at t0 + 24 h
    assert E[30] == E[29] == values[steps.get_loc(t0 + 29 * H)]  # a missing hour repeats the last value
    assert E[-1] == values[steps.get_loc(t0 + 336 * H)]          # the window ends at t0 + 14 days, not 337 steps
    with pytest.raises(ValueError):
        clock_series(values[1:], steps[1:], t0, 336)              # steps must start at t0


def test_guard_at_offset_11_trades_at_04_utc():
    _, res, fills = run(market(), Cash(), keep_alive=0.002, guard=11)
    guards = [t for t, k in fills if k == "guard"]
    assert guards and all(t.hour == 4 for t in guards)          # the 04:00 UTC bar = 12:00 HKT
    assert res.active_days == 14
