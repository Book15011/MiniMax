import pandas as pd
from research.book.intraday_short.persistent import persistent_features
from test_book_intraday import data,CFG
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
