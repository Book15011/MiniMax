import numpy as np,pandas as pd,pytest
from research.book.bear_selective.diagnostics.pnl import liquidation_curve
def sample(prices,actions):
 idx=pd.date_range("2020-01-01",periods=len(prices),freq="min",tz="UTC")
 e=pd.DataFrame([dict(time_utc=idx[i],action=a,quantity=q,price_usd=px,fee=q*px*.001) for i,a,q,px in actions])
 return pd.Series(prices,index=idx),e
def test_full_fee_cost_of_flat_roundtrip():
 p,e=sample([100,100],[(0,"Open Short",1,100),(1,"Cover Short",1,100)])
 z=liquidation_curve(p,e,.001,0)
 np.testing.assert_allclose(z,[-.2,-.2])
def test_rebound_profit_and_loss_are_not_confused():
 p,e=sample([100,90,101],[(0,"Open Short",1,100),(2,"Cover Short",1,101)])
 z=liquidation_curve(p,e,.001,0)
 assert np.isclose(z.max(),9.81) and np.isclose(z.iloc[-1],-1.201)
def test_additions_partial_covers_and_fees():
 p,e=sample([100,90,95,105],[(0,"Open Short",1,100),(1,"Cover Short",.5,90),(2,"Open Short",.5,95),(3,"Cover Short",1,105)])
 z=liquidation_curve(p,e,.001,0)
 expected=100-45+47.5-105-(.1+.045+.0475+.105)
 assert np.isclose(z.iloc[-1],expected)
def test_cover_more_than_opened_is_rejected():
 p,e=sample([100,100],[(0,"Open Short",1,100),(1,"Cover Short",2,100)])
 with pytest.raises(ValueError,match="quantity"):liquidation_curve(p,e,.001,0)
