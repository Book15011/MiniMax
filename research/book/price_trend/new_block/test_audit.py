import pandas as pd,pytest
from research.book.price_trend.new_block.audit import sides,audit
def test_future_quote_cannot_fill_past_gap():
 grid=pd.DatetimeIndex([pd.Timestamp("2026-10-09T01:00Z")])
 q=pd.DataFrame(dict(pair=["BTC/USD"],ts_utc=pd.to_datetime(["2026-10-09T01:00:01Z"],utc=True),max_bid=[99.],min_ask=[101.],last_price=[100.]))
 with pytest.raises(ValueError,match="past"):sides(q,grid,["BTC"])
 q.loc[0,"ts_utc"]=grid[0]-pd.Timedelta(seconds=31)
 with pytest.raises(ValueError,match="Stale"):sides(q,grid,["BTC"])
def test_quote_fee_and_terminal_cost_checked():
 grid=pd.date_range("2026-10-09",periods=2,freq="min",tz="UTC")
 q=pd.DataFrame(dict(pair=["BTC/USD"]*2,ts_utc=grid,max_bid=[49.,49.],min_ask=[50.,50.],last_price=[49.5,49.5]))
 ev=pd.DataFrame([dict(asset="BTC",action="Buy Long",quantity=2.,price_usd=50.,fee=.1,time_utc=grid[0],phase="strategy")])
 path=pd.DataFrame(dict(time_utc=grid,equity=[997.9,997.9],cash=[899.9,899.9]))
 ep=dict(full_cost_liquidated_equity=997.802)
 assert audit(ev,path,q,["BTC"],.001,1000.,ep)["status"]=="PASS"
 ev.loc[0,"fee"]=0.
 with pytest.raises(ValueError,match="fee"):audit(ev,path,q,["BTC"],.001,1000.,ep)
