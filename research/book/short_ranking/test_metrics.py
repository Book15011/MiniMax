import numpy as np,pandas as pd
from research.book.short_ranking.metrics import confusion,wilson_lower,combined_scores,block_rows
CFG=dict(horizon_hours=6,lag_minutes=60,settlement_minutes=1,fee=.001,halfspread=.0005,minimum_short_weight=.01)
def test_same_win_rate_with_more_observations_has_stronger_lower_bound():
 assert wilson_lower(25,50,.9)>wilson_lower(2,4,.9)>0
def test_f1_penalizes_missed_profitable_opportunities():
 a=confusion(np.array([1,1,1,1,0,0],bool),np.array([1,0,0,0,1,0],bool))
 b=confusion(np.array([1,1,1,1,0,0],bool),np.array([1,1,0,0,1,1],bool))
 assert a["precision"]==b["precision"]==.5 and a["f1"]<b["f1"] and a["fn"]==3
def test_return_component_changes_score_at_equal_signal_quality():
 x=pd.DataFrame(dict(model=["loss","gain"],selection_lower90=[-.01,.01],f1_lower90=[.3,.3],accuracy_reliability=[.4,.4]))
 y=combined_scores(x,dict(return_weight=.5,f1_weight=.3,accuracy_weight=.2)).set_index("model")
 assert y.loc["gain","score"]>y.loc["loss","score"]
def test_fixed_blocks_use_actual_holdings_ignore_dust_and_censor_endpoint():
 start=pd.Timestamp("2026-01-01",tz="UTC");end=start+pd.Timedelta(hours=14)
 ix=pd.date_range(start,end,freq="min")
 prices=pd.DataFrame({"BTCUSDT":np.linspace(100,90,len(ix))},index=ix)
 path=pd.DataFrame(dict(time_utc=ix,equity=1000.,BTC=-1.))
 out,censored=block_rows(path,prices,start,end,["BTC"],CFG)
 assert len(out)==2 and censored==1 and out.predicted.all() and out.positive.all()
 path["BTC"]=-.001
 dust,_=block_rows(path,prices,start,end,["BTC"],CFG)
 assert not dust.predicted.any() and confusion(dust.positive,dust.predicted)["fn"]==2
