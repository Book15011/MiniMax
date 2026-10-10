import numpy as np,pandas as pd
from research.book.price_trend.engine import replay,independent_audit
def test_shared_broker_long_short_flip_cash_and_cycles():
 idx=pd.date_range("2025-01-01",periods=721,freq="min",tz="UTC")
 prices=pd.DataFrame({"BTCUSDT":100*np.exp(-np.arange(721)*.0001)},index=idx)
 cfg=dict(assets=["BTC"],seed=100000.,fee=.001,proxy_half_spread=.0005,quote_max_age=0,minute_max_age=60,
  precisions={"BTC":5},price_precisions={"BTC":2},min_order=1.,cash_buffer=.001,band=.05,order_spacing_seconds=10.,start=str(idx[0]),end=str(idx[-1]))
 weights={idx[0]:pd.Series({"BTCUSDT":-.5}),idx[240]:pd.Series({"BTCUSDT":-.2}),idx[480]:pd.Series({"BTCUSDT":.25})}
 e,p,d,f,c,ep=replay(weights,prices,cfg,60)
 assert not f and len(c)==1 and c[0]["status"]=="completed" and c[0]["profitable"]
 a=independent_audit(e,p,prices,cfg,ep)
 assert a["status"]=="PASS" and ep["full_cost_liquidated_equity"]>100000
def test_terminal_short_is_censored_and_charges_full_fee():
 idx=pd.date_range("2025-01-01",periods=241,freq="min",tz="UTC")
 prices=pd.DataFrame({"BTCUSDT":100.},index=idx)
 cfg=dict(assets=["BTC"],seed=100000.,fee=.001,proxy_half_spread=.0005,quote_max_age=0,minute_max_age=60,
  precisions={"BTC":5},price_precisions={"BTC":2},min_order=1.,cash_buffer=.001,band=.05,order_spacing_seconds=10.,start=str(idx[0]),end=str(idx[-1]))
 e,p,d,f,c,ep=replay({idx[0]:pd.Series({"BTCUSDT":-.5})},prices,cfg,60)
 assert not f and c[0]["status"]=="censored" and ep["full_cost_liquidated_equity"]<100000
 assert independent_audit(e,p,prices,cfg,ep)["status"]=="PASS"
