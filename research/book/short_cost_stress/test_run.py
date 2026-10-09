import numpy as np,pandas as pd
from run import replay_costs,scaled_market
from backtest.data import Market
from backtest.engine import Costs

def synthetic():
 ix=pd.date_range("2026-01-01T12:00Z",periods=6,freq="h")
 close=pd.DataFrame({"BTCUSDT":[100.]*6},index=ix)
 m=Market(close,close.copy(),pd.Series([("BTCUSDT",)],index=ix[:1]),pd.Series({"BTCUSDT":.001}))
 tg=pd.DataFrame({"BTCUSDT":[.5]},index=ix[:1])
 return m,tg,ix

def test_double_cost_actual_replay_and_liquidation():
 m,tg,ix=synthetic()
 a=replay_costs(m,tg,ix[0],4,.0,Costs(.001,.001),1,16,100,0,False,None)
 b=replay_costs(scaled_market(m,2),tg,ix[0],4,.0,Costs(.002,.002),1,16,100,0,False,None)
 assert np.isclose(a["mark_return"],-.001)
 assert np.isclose(a["liquidated_return"],.999*.999-1)
 assert np.isclose(b["mark_return"],-.002)
 assert np.isclose(b["liquidated_return"],.998*.998-1)
 assert np.isclose(a["turnover_including_liquidation"],1.)
 assert b["liquidated_return"]<a["liquidated_return"]

def test_short_fees_and_spread_are_applied():
 m,tg,ix=synthetic();tg.iloc[:]=-.5
 a=replay_costs(m,tg,ix[0],4,.0,Costs(.001,.001),1,16,100,0,False,None)
 b=replay_costs(scaled_market(m,2),tg,ix[0],4,.0,Costs(.002,.002),1,16,100,0,False,None)
 assert np.isclose(a["liquidated_return"],.999*.999-1)
 assert np.isclose(b["liquidated_return"],.998*.998-1)

def test_scaled_market_preserves_original():
 m,tg,ix=synthetic();before=m.half_spread.copy()
 z=scaled_market(m,2)
 assert m.half_spread.equals(before)
 assert z.close is m.close
 assert np.allclose(z.half_spread,before*2)
