"""Windows, days and the activity guard follow clock time, not bar counts (panel gaps: outages, maintenance)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest.data import Market
from backtest.engine import Costs, Simulator, compute_targets, decision_times
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


def test_scoring_window_is_14_days_of_clock_time_on_a_gap_market(tmp_path):
    import copy
    from backtest.scoring.evaluate import simulate
    from src.config import load_config
    cfg = copy.deepcopy(load_config())
    cfg["scoring"]["cache_dir"] = str(tmp_path)
    cfg["harness"]["keep_alive_weight"] = 0.0
    cfg["harness"]["fees"] = {"taker": FEE, "short": FEE}
    gap = T0 + pd.Timedelta(days=6, hours=3)
    run_ = simulate(Hold(), market(drop=[gap]), cfg, pd.DatetimeIndex([T0]), use_cache=False)
    w = run_.windows.iloc[0]
    assert w.R == pytest.approx((1 - FEE) * price(T0 + 336 * H) / price(T0 + H) - 1, rel=1e-12)
    assert run_.equity.shape == (1, 337) and w.active_days == 1
    assert list(run_.trades.time_utc) == [T0 + H] and list(run_.trades.hour) == [1]
