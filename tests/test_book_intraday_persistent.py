import pandas as pd
from research.book.intraday_short.persistent import persistent_features
from src.config import load_config
CFG=load_config()["book_intraday_short"]
def data():
 idx=pd.date_range("2025-01-01",periods=3000,freq="min",tz="UTC")
 z=pd.DataFrame({"open":100.,"high":100.,"low":100.,"close":100.,"quote_volume":1000.,"taker_buy_quote":400.},index=idx)
 return {s:z.copy() for s in ["BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT"]}
def test_persistent_entries_are_original_entries():
 from research.book.intraday_short.engine import features
 d=data();base=features(d,CFG);f=persistent_features(d,{**CFG,"exit_rebound_buffer":.005})
 pd.testing.assert_frame_equal(f["signals"]["flow_persistent"],base["signals"]["flow_breakout"])
 pd.testing.assert_frame_equal(f["signals"]["volume_persistent"],base["signals"]["volume_breakout"])
def test_persistent_regime_is_causal():
 d=data();f=persistent_features(d,{**CFG,"exit_rebound_buffer":.005});cut=d["BTCUSDT"].index[-10]
 later={s:z.copy() for s,z in d.items()}
 for z in later.values():z.loc[z.index>cut,["open","high","low","close"]]*=2
 g=persistent_features(later,{**CFG,"exit_rebound_buffer":.005})
 pd.testing.assert_series_equal(f["weak"].loc[:cut],g["weak"].loc[:cut])
