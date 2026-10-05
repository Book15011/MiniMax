"""Hand-computed cases for research/baitoey/scalp.py's minute simulator."""
import numpy as np

from research.baitoey.scalp import MAKER, TAKER, INVEST, scalp_coin

STEP = 1.0


def bars(rows):
    o, h, l, c = (np.array(x, dtype=float) for x in zip(*rows))
    return o, h, l, c


def test_one_round_trip_through_fills():
    # close 100 -> buy limit at 99; bar 1 trades through 99 (low 98.5); bar 2 trades through 100 (high 100.5)
    o, h, l, c = bars([(100, 100, 100, 100), (100, 100, 98.5, 99), (99, 100.5, 99, 100)])
    eq, liq, fees, trips, wins, calls = scalp_coin(o, h, l, c, STEP)
    units = INVEST / 99 * (1 - MAKER)
    cash = 1 - INVEST + units * 100 * (1 - MAKER)
    assert trips[2] == 1 and wins[2] == 1 and np.isclose(eq[2], cash)
    assert calls[0] == 1 and calls[1] == 1                             # the buy, then the sell after the fill


def test_touch_fills_but_through_does_not():
    o, h, l, c = bars([(100, 100, 100, 100), (100, 100, 99, 99.5), (99.5, 99.8, 99.2, 99.5)])
    eq_t = scalp_coin(o, h, l, c, STEP, fill="touch")[0]
    eq_th = scalp_coin(o, h, l, c, STEP, fill="through")[0]
    assert eq_th[-1] == 1.0                                            # never filled: cash untouched
    assert eq_t[-1] != 1.0                                             # filled at 99 under TOUCH, marked at 99.5


def test_stop_and_gap():
    # fill at 99 in bar 1; bar 2 low reaches 96 (= 99 - 3): stop at 95 with the taker fee
    o, h, l, c = bars([(100, 100, 100, 100), (100, 100, 98.5, 99), (99, 99, 96, 97)])
    eq = scalp_coin(o, h, l, c, STEP)[0]
    units = INVEST / 99 * (1 - MAKER)
    assert np.isclose(eq[2], 1 - INVEST + units * 95 * (1 - TAKER))
    # gap: bar 2 opens at 94, below the stop: sold at 93
    o, h, l, c = bars([(100, 100, 100, 100), (100, 100, 98.5, 99), (94, 95, 93.5, 94)])
    eq = scalp_coin(o, h, l, c, STEP)[0]
    assert np.isclose(eq[2], 1 - INVEST + units * 93 * (1 - TAKER))


def test_stop_counts_before_target_in_the_same_bar():
    o, h, l, c = bars([(100, 100, 100, 100), (100, 100, 98.5, 99), (99, 101, 95.5, 100)])
    trips, wins = scalp_coin(o, h, l, c, STEP)[3:5]
    assert trips[2] == 1 and wins[2] == 0
