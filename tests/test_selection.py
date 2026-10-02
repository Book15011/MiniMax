"""Leaderboard pick rules (backtest/scoring/selection.py): the margin keeps a far-but-uncorrelated model out of the tie
group; legacy is unchanged; the settings are validated."""
import pytest

from backtest.scoring import selection
from backtest.scoring.returnfirst import pick_order

TIES = {"top": {"diff": 0.0, "lo": 0.0, "hi": 0.0, "tied": True},
        "close": {"diff": -0.02, "lo": -0.05, "hi": +0.01, "tied": True},
        "far_uncorrelated": {"diff": -0.10, "lo": -0.19, "hi": +0.002, "tied": True},
        "near_correlated": {"diff": -0.04, "lo": -0.08, "hi": -0.002, "tied": False}}
ROWS = {"top": {"eligible": True, "headline_ret": 0.61, "cs_hit": 0.37, "min_sc": 1.0},
        "close": {"eligible": True, "headline_ret": 0.59, "cs_hit": 0.38, "min_sc": 0.9},
        "far_uncorrelated": {"eligible": True, "headline_ret": 0.51, "cs_hit": 0.45, "min_sc": 1.2},
        "near_correlated": {"eligible": True, "headline_ret": 0.57, "cs_hit": 0.39, "min_sc": 2.0}}


def test_legacy_lets_a_far_uncorrelated_model_win_on_risk():
    assert selection.apply_margin(TIES, None) is TIES
    assert pick_order(ROWS, TIES, 0.05)[0] == "far_uncorrelated"


def test_margin_keeps_the_tie_group_close_to_the_top():
    m = selection.apply_margin(TIES, 0.03)
    assert {n for n, v in m.items() if v["tied"]} == {"top", "close"}
    assert m["far_uncorrelated"]["tied_legacy"] is True and m["near_correlated"]["tied"] is False
    assert pick_order(ROWS, m, 0.05)[0] == "top"                       # within 0.05 CS: min(SCREEN, CONFIRM) decides


def test_settings_default_to_legacy_and_validate():
    assert selection.settings({}) == ("legacy", None)
    assert selection.settings({"selection": {"rule": "legacy", "tie_margin": 0.03}}) == ("legacy", None)
    assert selection.settings({"selection": {"rule": "margin", "tie_margin": 0.03}}) == ("margin", 0.03)
    assert selection.proposal_margin({}) == 0.03
    with pytest.raises(ValueError):
        selection.settings({"selection": {"rule": "best"}})
    with pytest.raises(ValueError):
        selection.settings({"selection": {"rule": "margin", "tie_margin": -0.1}})
