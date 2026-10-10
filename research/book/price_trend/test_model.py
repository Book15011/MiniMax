import numpy as np,pandas as pd
from src.contracts import MarketView,check_targets
from src.models.book._price_trend import PriceTrend,targets,forecast
P=dict(coins=["BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT"],warmup_multiplier=8,fast_hours=6,slow_hours=24,risk_hours=72,channel_hours=48,forecast_scale=2.,deadzone_z=.25,sigma_floor=1e-7,gross_cap=1.,coin_cap=.35,target_daily_vol=.025)
def view(direction=1):
 idx=pd.date_range("2025-01-01",periods=900,freq="h",tz="UTC")
 z=np.arange(900);base=np.exp(direction*z*.001+np.sin(z)*.0002)
 c=pd.DataFrame({s:(100+i*20)*base for i,s in enumerate(P["coins"])},index=idx)
 return MarketView(idx[-1],c,c*0,tuple(P["coins"]),P,{})
def test_bounded_money_and_short_sign():
 v=view(-1);w=targets(v,"fast",True)
 assert len(w)==4 and (w<0).all() and w.abs().sum()<=1+1e-12 and w.abs().max()<=.35+1e-12
 _,s=forecast(v.close.tail(193),P,"fast")
 assert (w.abs()*s*np.sqrt(24)).sum()<=.025+1e-10
def test_short_only_does_not_buy_rising_market():
 assert targets(view(1),"fast",True).empty
 assert (targets(view(1),"fast",False)>0).all()
def test_constant_prices_cash():
 v=view();v.close.iloc[:]=100.
 assert targets(v,"channel",True).empty
 assert targets(v,"fast",False).empty
def test_no_future_inference():
 v=view(-1);before=targets(v,"fast",True)
 extra=v.close.iloc[-3:].copy();extra.index=extra.index+pd.Timedelta(hours=3);extra*=5
 vv=MarketView(v.t,pd.concat([v.close,extra]),v.quote_volume,v.universe,P,{})
 pd.testing.assert_series_equal(before,targets(vv,"fast",True))
def test_missing_history_fails_closed():
 v=view(-1);v.close.iloc[-50,1]=np.nan
 assert targets(v,"fast",True).empty
def test_universe_contract():
 v=view(-1);v=MarketView(v.t,v.close,v.quote_volume,("BTCUSDT","ETHUSDT"),P,{})
 m=PriceTrend("book_price_fast_short","fast",True)
 w=check_targets(m.targets(v),v,m.spec)
 assert set(w.index)<=set(v.universe) and w.abs().sum()<=1
def test_channel_uses_only_known_completed_prices():
 v=view(-1)
 f,_=forecast(v.close,P,"channel")
 assert ((f>=-1)&(f<=1)).all() and (f==-1).all()
