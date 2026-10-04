import pandas as pd

import src.models.baitoey._fast_switch as fs
from src.contracts import MarketView

IDX = pd.date_range("2026-01-01 00:00", periods=60, freq="h", tz="UTC")


class Inner:
    calls = 0

    def targets(self, view):
        Inner.calls += 1
        return pd.Series({"AUSDT": 0.5})


def view(end: int, fast: str = "up_and_down") -> MarketView:
    close = pd.DataFrame({"AUSDT": 100.0, "BTCUSDT": 100.0}, index=IDX).iloc[: end + 1]
    return MarketView(t=close.index[-1], close=close, quote_volume=close * 0 + 1e6, universe=("AUSDT", "BTCUSDT"),
                      params={"vt": {"switch": {"ema_days": 20, "hysteresis": 0.03, "state_days": 120}}, "fast": fast},
                      prev_targets=pd.Series({"BUSDT": 0.3}))


def run(states: dict, end: int, fast: str = "up_and_down"):
    fs._STATE.clear()
    m = fs.FastSwitch(); m.INNER = Inner(); Inner.calls = 0
    orig = fs.state_at
    fs.state_at = lambda v, t, sw: states.get(t.hour + 24 * (t.day - 1), "up")
    try:
        return m.targets(view(end, fast)), Inner.calls
    finally:
        fs.state_at = orig


def test_a_new_flip_decides_at_once_and_otherwise_the_book_is_held():
    flip = {h: "down" for h in range(40, 60)}                         # up until hour 39, down from hour 40
    assert run(flip, 40)[1] == 1                                      # 16:00 was hour 16 / 40: hour 40 is 16:00 day 2
    w, calls = run(flip, 41)                                          # 17:00: no new flip (already down at 16:00)
    assert calls == 0 and list(w.index) == []                         # BUSDT is not in the universe: held book is empty
    flip2 = {h: "down" for h in range(44, 60)}                        # flips at 20:00 on day 2
    assert run(flip2, 44)[1] == 1 and run(flip2, 45)[1] == 0


def test_down_only_and_never():
    up = {h: "down" for h in range(0, 44)}                            # down, flips up at hour 44
    assert run(up, 44, "down")[1] == 0                                # a flip to up waits for 16:00
    assert run(up, 44, "up_and_down")[1] == 1
    down = {h: "down" for h in range(44, 60)}
    assert run(down, 44, "never")[1] == 0
