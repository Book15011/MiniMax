"""Money/causality fixtures for the research minute short sleeve."""
from decimal import Decimal
import numpy as np
import pandas as pd
import pytest
from research.book.intraday_short.engine import features,replay,choose_entries
from src.api.rules import PairRule
CFG={"signal_minutes":15,"warmup_minutes":2880,"ema_minutes":1440,"breakout_minutes":60,"volume_multiple":1.5,"break_buffer":.0005,"rebound_prior":.003,"rebound_fail":-.0015,"bounce_move":.006,"relative_move":-.004,"relative_excess":-.003,"flow_max":.45,"sigma_floor":.004,"stop_floor":.006,"stop_sigma":2.0,"take_multiple":1.5,"max_hold_minutes":360,"cooldown_minutes":30,"max_positions":3,"max_short_gross":.25,"max_coin":.10,"risk_fraction":.0025,"fee":.001,"halfspread":.0005,"lag_minutes":1,"seed":100000.}
def data(n=3000):
 idx=pd.date_range("2025-01-01",periods=n,freq="min",tz="UTC")
 z=pd.DataFrame({"open":100.,"high":100.,"low":100.,"close":100.,"quote_volume":1000.,"taker_buy_quote":400.},index=idx)
 return {s:z.copy() for s in ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]}
def rules():return {s.removesuffix("USDT")+"/USD":PairRule(s.removesuffix("USDT")+"/USD",4,6,Decimal("1")) for s in data()}
def fixture_replay(prices,signal_at=0,lag=1,end=None,cost=1):
 idx=pd.date_range("2025-01-03",periods=len(prices),freq="min",tz="UTC")
 close=pd.DataFrame({"BTCUSDT":prices},index=idx)
 sig=pd.DataFrame({"BTCUSDT":False},index=idx);sig.iloc[signal_at,0]=True
 sigma=close*0+.01;weak=pd.Series(True,index=idx)
 cfg={**CFG,"signal_minutes":1,"lag_minutes":lag,"max_hold_minutes":1000,"fee":CFG["fee"]*cost,"halfspread":CFG["halfspread"]*cost}
 return replay(close,sig,sigma,weak,cfg,{"BTC/USD":rules()["BTC/USD"]},endpoints=[len(prices)-1] if end is None else end)
def test_features_ignore_future():
 d=data();f=features(d,CFG);cut=d["BTCUSDT"].index[-30]
 later={s:z.copy() for s,z in d.items()}
 for z in later.values():z.loc[z.index>cut,["open","high","low","close"]]*=1.8
 g=features(later,CFG)
 for key in f:
  if isinstance(f[key],dict):
   for name in f[key]:pd.testing.assert_frame_equal(f[key][name].loc[:cut],g[key][name].loc[:cut])
  elif isinstance(f[key],pd.DataFrame):pd.testing.assert_frame_equal(f[key].loc[:cut],g[key].loc[:cut])
  else:pd.testing.assert_series_equal(f[key].loc[:cut],g[key].loc[:cut])
def test_warmup_and_move_floor_dont_force_signals():
 f=features(data(),CFG)
 assert not any(x.to_numpy().any() for x in f["signals"].values())
def test_actual_fill_lag_and_fee_cash_reconcile():
 r=fixture_replay([100,99,98,97])
 assert r["events"].iloc[0].minute==1
 e=r["events"];entry=e.iloc[0];cover=e.iloc[-1]
 expected=entry.qty*(entry.price-cover.price)-entry.fee-cover.fee
 assert r["windows"].iloc[0]["return"]==pytest.approx(expected/100000)
 assert r["audit"]["max_equity_error"]<1e-7
def test_exit_trigger_fills_next_minute_and_gap_costs_more():
 r=fixture_replay([100,100,103,108,108])
 covers=r["events"].query("kind=='SHORT_CLOSE'")
 assert covers.iloc[0].minute==3
 assert covers.iloc[0].price>107
 assert covers.iloc[0].reason=="stop"
def test_terminal_censor_not_counted_as_completed_hit():
 r=fixture_replay([100,100,99,98])
 assert r["windows"].iloc[0].completed==0
 assert r["windows"].iloc[0].censored==1
def test_cost_increase_reexecutes_and_reduces_return():
 r=fixture_replay([100,100,99,98])
 stressed=fixture_replay([100,100,99,98],cost=2)
 assert stressed["windows"].iloc[0]["return"]<r["windows"].iloc[0]["return"]
 # Ordinary fixture ledger includes both entry and terminal fees.
 assert r["events"].fee.sum()>0
 assert r["windows"].iloc[0].fees>0
def test_limits_and_tie_break_are_deterministic():
 s=pd.Series(True,index=["XRPUSDT","ETHUSDT","BTCUSDT","SOLUSDT"])
 strength=pd.Series([1,1,1,1],index=s.index)
 selected=choose_entries(s,strength,{}, {},1000,0,CFG)
 assert list(selected)==["BTCUSDT","ETHUSDT","SOLUSDT"]
 assert sum(selected.values())<=.25+1e-12
 assert max(selected.values())<=.1
def test_no_unfilled_signal_counts_as_trade():
 r=fixture_replay([100,100,100],signal_at=2)
 assert len(r["events"])==0
 assert r["windows"].iloc[0].completed==0
 assert r["windows"].iloc[0].censored==0
def test_precision_is_not_rounded_up():
 r=fixture_replay([100,100.123456,100])
 q=r["events"].iloc[0].qty
 assert q==float(Decimal(str(q)).quantize(Decimal(".000001")))
def test_invalid_missing_quote_fails():
 with pytest.raises(ValueError):fixture_replay([100,float("nan"),99])

def test_future_prices_leave_prior_fills_unchanged():
 a=fixture_replay([100,100,99,98,98]);b=fixture_replay([100,100,99,98,50])
 pd.testing.assert_frame_equal(a["events"].query("minute<4"),b["events"].query("minute<4"))
