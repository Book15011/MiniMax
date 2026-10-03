import numpy as np
import pandas as pd

from src.config import load_config
from src.contracts import MarketView
from src.models.baitoey._alt_switch import AltSwitch, alt_state

SW = load_config()["models"]["pol_switch_vt_tl_e20v45"]["switch"]
N = (int(SW["state_days"]) + 3 * int(SW["ema_days"])) * 24 + 50
IDX = pd.date_range("2026-01-01 00:00", periods=N, freq="h", tz="UTC")


def view(alt_drift: float, btc_drift: float) -> MarketView:
    k = np.arange(N)
    px = {"BTCUSDT": 100 * (1 + btc_drift) ** k, "ETHUSDT": 100 * (1 + btc_drift) ** k,
          "AUSDT": 10 * (1 + alt_drift) ** k, "BUSDT": 5 * (1 + alt_drift) ** k}
    close = pd.DataFrame(px, index=IDX)
    return MarketView(t=IDX[-1], close=close, quote_volume=close * 0 + 1e6, universe=tuple(px), params={}, prev_targets=pd.Series(dtype=float))


def test_the_state_follows_the_altcoins_not_btc():
    assert alt_state(view(+0.0005, -0.0005), SW) == "up"
    assert alt_state(view(-0.0005, +0.0005), SW) == "down"


def test_both_needs_btc_and_the_altcoins_up():
    assert AltSwitch.state(view(+0.0005, -0.0005), {"switch": SW, "market": "both"}) == "down"
    assert AltSwitch.state(view(+0.0005, +0.0005), {"switch": SW, "market": "both"}) == "up"
    assert AltSwitch.state(view(+0.0005, -0.0005), {"switch": SW, "market": "alts"}) == "up"



def noisy_view(end: int | None = None) -> MarketView:
    rng = np.random.default_rng(0)
    k = np.arange(N)
    px = {}
    for j in range(10):
        drift = 0.0006 if j < 6 else -0.0006                          # six winners, four losers
        px[f"C{j}USDT"] = 10 * np.exp(drift * k + 0.003 * rng.standard_normal(N).cumsum())
    close = pd.DataFrame(px, index=IDX).iloc[: end]
    return MarketView(t=close.index[-1], close=close, quote_volume=close * 0 + 1e6, universe=tuple(px), params={},
                      prev_targets=pd.Series(dtype=float))


def test_the_momentum_basket_follows_the_recent_winners_without_look_ahead():
    from src.models.baitoey._alt_switch import momentum_index
    full, cut = noisy_view(), noisy_view(N - 49)
    idx = momentum_index(full, 500)
    assert idx.iloc[-1] > idx.iloc[0] * 1.05                           # holding the winners rises
    a, b = momentum_index(cut, 100), momentum_index(full, 300)
    common = a.index
    assert np.allclose(a / a.iloc[0], b.loc[common] / b.loc[common].iloc[0])   # later prices do not change the past
