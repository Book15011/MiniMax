import numpy as np
import pandas as pd
import pytest

from src.config import load_config
from src.contracts import check_targets
from src.models.baitoey.baitoey_rot_max import MODEL, btc_below_average
from src.models.baselines.team_rot_ew import rotation_targets
from tests.test_baitoey_volume_timing import market, view

P = load_config()["models"]["baitoey_rot_max"]


@pytest.mark.parametrize("k", [6, 4, 3])
def test_fully_invested_top_k_equal_weights(k):
    close, qv = market()
    p = {**P, "k": k, "btc_gate": False}
    v = view(close, qv, p)
    w = check_targets(MODEL.targets(v), v, MODEL.spec)
    assert len(w) == k and w.sum() == pytest.approx(1.0) and np.allclose(w, 1.0 / k)
    pd.testing.assert_series_equal(MODEL.targets(v), rotation_targets(v, p))


@pytest.mark.parametrize("hours_low, gated", [(50, True), (10, False)])
def test_btc_gate_needs_two_days_below_the_20_day_average(hours_low, gated):
    close, qv = market()
    close["BTCUSDT"] = np.linspace(100.0, 120.0, len(close))
    close.iloc[-hours_low:, close.columns.get_loc("BTCUSDT")] *= 0.9
    assert btc_below_average(close["BTCUSDT"], 20, 2) is gated
    w = MODEL.targets(view(close, qv, {**P, "btc_gate": True}))
    assert w.empty is gated


def test_btc_gate_stays_open_on_missing_data():
    close, _ = market()
    close["BTCUSDT"] = np.linspace(100.0, 120.0, len(close))
    close.iloc[-50:, close.columns.get_loc("BTCUSDT")] *= 0.9
    assert btc_below_average(close["BTCUSDT"], 20, 2) is True
    close.iloc[-25, close.columns.get_loc("BTCUSDT")] = np.nan   # yesterday's daily close
    assert btc_below_average(close["BTCUSDT"], 20, 2) is False
