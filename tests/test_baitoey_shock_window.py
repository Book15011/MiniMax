import numpy as np
import pandas as pd

from src.config import load_config
from src.contracts import MarketView
from src.models.baitoey._shock_window import ShockWindow
from src.models.pol.pol_abl_shock import MODEL as SHOCK

P = load_config()["models"]["pol_abl_shock"]
N = 30 * 24


def view(btc: np.ndarray, end: int) -> MarketView:
    idx = pd.date_range("2024-01-01 01:00", periods=len(btc), freq="h", tz="UTC")
    close = pd.DataFrame({"BTCUSDT": btc}, index=idx).iloc[: end + 1]
    return MarketView(t=close.index[-1], close=close, quote_volume=close * 0 + 1e6, universe=("BTCUSDT",),
                      params=P, prev_targets=pd.Series(dtype=float))


def path(drop: float, hours: int, at: int = N - 30) -> np.ndarray:
    k = np.arange(N)
    px = 100 * (1 + 0.002 * np.sin(k / 7))
    px[at:] *= np.array(np.linspace(1, 1 - drop, hours + 1).tolist() + [1 - drop] * (N - at - hours - 1))
    return px


def test_with_a_4_hour_window_it_is_pol_abl_shock_exactly():
    for drop, hours in ((0.06, 3), (0.06, 6), (0.04, 2), (0.0, 1)):
        px = path(drop, hours)
        for end in range(N - 40, N):
            v = view(px, end)
            assert ShockWindow.shocked(v, {**P, "shock_hours": 4}) == SHOCK.shocked(v, P)
            assert ShockWindow.shocked(v, P) == SHOCK.shocked(v, P)                       # default is 4 h


def test_the_window_decides_whether_a_slow_drop_counts():
    v = view(path(0.06, 6), N - 1)                                   # 6% over 6 hours, ending inside the last 24 h
    assert ShockWindow.shocked(v, {**P, "shock_hours": 8})
    assert not ShockWindow.shocked(v, {**P, "shock_hours": 2})
