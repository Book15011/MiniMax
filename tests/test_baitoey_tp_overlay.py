"""Hand-built cases for research/baitoey/tp_overlay.py's per-window overlay."""
import numpy as np

from research.baitoey.tp_overlay import MAKER, TAKER, overlay_window

H = 30
DECISIONS = [0, 4, 28]                                                 # fills at hours 1, 5 and 29


def flat(v, n=H + 1):
    return np.full(n, float(v))


def case(high_at=None, target_close=None):
    """One coin bought at hour 1 with weight 0.5 of equity 1.0 at price 100; equity flat at 1.0."""
    E, G = flat(1.0), flat(0.5)
    close = {"AUSDT": flat(100.0)}
    high = {"AUSDT": flat(100.0)}
    if high_at is not None:
        high["AUSDT"][high_at] = 109.0
    if target_close is not None:
        close["AUSDT"][29:] = target_close
    trades = [(1, "AUSDT", 0.5)]
    return E, G, close, high, trades


def test_no_overlay_returns_the_engine_path():
    E, G, close, high, trades = case()
    out, g_end, st = overlay_window(E, G, close, high, trades, DECISIONS, None, 1.0, {"AUSDT": 0.0})
    assert np.allclose(out, E) and g_end == G[-1] and st["fills"] == 0


def test_the_bar_that_sets_or_fills_the_decision_never_fills_the_target():
    # high 109 only at hour 1 (the first decision's fill bar): the target 108 (100 x 1.08) must not fill there
    E, G, close, high, trades = case(high_at=1)
    st = overlay_window(E, G, close, high, trades, DECISIONS, 0.08, 1.0, {"AUSDT": 0.0})[2]
    assert st["fills"] == 0


def test_a_later_high_fills_at_the_target_and_the_buy_back_is_settled():
    # high 109 at hour 3: sells 0.005 units (0.5 / 100) at 108 with the maker fee; price stays 100 to hour 5,
    # where the coin is still held, so the sold units are bought back at 100 with the taker fee (half-spread 0)
    E, G, close, high, trades = case(high_at=3)
    out, g_end, st = overlay_window(E, G, close, high, trades, DECISIONS, 0.08, 1.0, {"AUSDT": 0.0})
    u = 0.5 / 100
    gain = u * (108 * (1 - MAKER) - 100) - u * 100 * TAKER
    assert st["fills"] == 1 and st["lower"] == 1 and st["higher"] == 0
    assert np.isclose(out[3], 1.0 + u * (108 * (1 - MAKER) - 100))     # cash instead of the coin until the settle
    assert np.isclose(out[5], 1.0 + gain) and np.isclose(out[-1], 1.0 + gain)


def test_a_partial_fraction_and_a_buy_back_higher():
    E, G, close, high, trades = case()
    high["AUSDT"][10] = 109.0                                          # inside the second cycle (fill bar 5, last 28)
    close["AUSDT"][29:] = 112.0                                        # settled at hour 29 above the 108 fill
    st = overlay_window(E, G, close, high, trades, DECISIONS, 0.08, 0.5, {"AUSDT": 0.0})[2]
    assert st["fills"] == 1 and st["higher"] == 1


def test_a_guard_trade_after_the_fill_is_skipped_not_sold_twice():
    # the engine halves the coin at hour 16 (a guard); the overlay sold it all at 108 at hour 10 and holds cash,
    # so the guard's sale is skipped (its cost credited back) and at hour 29 the overlay buys back the engine's
    # 0.0025 units, while the engine's own trade there is none
    E, G, close, high, trades = case()
    high["AUSDT"][10] = 109.0
    trades = [(1, "AUSDT", 0.5), (16, "AUSDT", 0.25)]
    out, _, st = overlay_window(E, G, close, high, trades, DECISIONS, 0.08, 1.0, {"AUSDT": 0.0})
    u = 0.005
    guard = -0.0025 * 100 + 0.0025 * 100 * TAKER                       # cash the overlay does not receive, cost saved
    assert np.isclose(out[12], 1.0 + u * (108 * (1 - MAKER) - 100))
    assert np.isclose(out[20], 1.0 + u * 108 * (1 - MAKER) + guard - 0.0025 * 100)
    assert np.isclose(out[29], 1.0 + u * (108 * (1 - MAKER) - 100))   # the skipped guard fee pays the smaller buy-back
    assert st["fills"] == 1 and st["lower"] == 1


def test_the_last_cycle_lowers_the_gross_at_the_end():
    E, G = flat(1.0, 337), flat(0.5, 337)
    close, high = {"AUSDT": flat(100.0, 337)}, {"AUSDT": np.where(np.arange(337) == 320, 109.0, 100.0)}
    decisions = [0] + list(range(4, 336, 24))
    out, g_end, st = overlay_window(E, G, close, high, [(1, "AUSDT", 0.5)], decisions, 0.08, 1.0, {"AUSDT": 0.0})
    assert st["fills"] == 1 and np.isclose(g_end, 0.0)
