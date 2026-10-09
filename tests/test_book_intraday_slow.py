import pandas as pd
from src.config import load_config
from research.book.intraday_short.slow import slow_features
def sample():
 idx=pd.date_range("2025-01-01",periods=3000,freq="min",tz="UTC")
 z=pd.DataFrame({"open":100.,"high":100.,"low":100.,"close":100.,"quote_volume":1000.,"taker_buy_quote":400.},index=idx)
 z.iloc[2880,z.columns.get_indexer(["open","high","low","close"])]=95.
 z.iloc[2880,z.columns.get_loc("quote_volume")]=20000.
 return {s:z.copy() for s in ["BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT"]}
def cfg():
 c=load_config();return {**c["book_intraday_short"],**c["book_intraday_slow"]}
def test_break_uses_preceding_range_and_completed_bar():
 f=slow_features(sample(),cfg())
 assert f["signals"]["slow_breakdown"].iloc[2880].all()
 assert not f["signals"]["slow_breakdown"].iloc[:2880].to_numpy().any()
def test_future_prices_cannot_change_slow_signal():
 d=sample();cut=d["BTCUSDT"].index[2890];f=slow_features(d,cfg())
 for z in d.values():z.loc[z.index>cut,["open","high","low","close"]]*=2
 g=slow_features(d,cfg())
 pd.testing.assert_frame_equal(f["signals"]["slow_breakdown"].loc[:cut],g["signals"]["slow_breakdown"].loc[:cut])
 pd.testing.assert_series_equal(f["weak"].loc[:cut],g["weak"].loc[:cut])
