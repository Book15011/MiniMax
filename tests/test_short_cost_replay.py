import numpy as np
import pandas as pd
import pytest
from backtest.data import Market
from backtest.engine import Costs
from research.book.short_diagnostics.cost_replay import replay_costs,scaled_market,check_equity

def fixture(short=False):
    ix=pd.date_range("2026-01-01T12:00Z",periods=6,freq="h")
    px=pd.DataFrame({"BTCUSDT":[100.]*6},index=ix)
    m=Market(px,px.copy(),pd.Series([("BTCUSDT",)],index=ix[:1]),pd.Series({"BTCUSDT":.001}))
    t=pd.DataFrame({"BTCUSDT":[-.5 if short else .5]},index=ix[:1])
    return m,t,ix

@pytest.mark.parametrize("short",[False,True])
def test_actual_double_cost_replay_and_exact_terminal_close(short):
    m,t,ix=fixture(short)
    a=replay_costs(m,t,ix[0],4,0,Costs(.001,.001),1,16,100,0,False,None)
    b=replay_costs(scaled_market(m,2),t,ix[0],4,0,Costs(.002,.002),1,16,100,0,False,None)
    assert a["liquidated_return"] == pytest.approx(.999*.999-1)
    assert b["liquidated_return"] == pytest.approx(.998*.998-1)
    assert a["turnover_including_liquidation"] == 1.
    assert a["terminal_gross"] == .5

def test_cost_scaling_does_not_mutate_market_or_scale_final_return():
    m,t,ix=fixture()
    original=m.half_spread.copy()
    stress=scaled_market(m,2)
    assert m.half_spread.equals(original)
    assert stress.close is m.close
    assert stress.half_spread.equals(original*2)

def test_cache_equity_mismatch_fails_closed_at_every_hour():
    eq=np.array([1.,.999,1.002])
    assert check_equity(eq,eq.copy()) == 0
    bad=eq.copy();bad[1]+=2e-12
    with pytest.raises(ValueError,match="original"):
        check_equity(eq,bad)
