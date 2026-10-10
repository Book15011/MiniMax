from dataclasses import replace
import numpy as np,pandas as pd
from src.contracts import MarketView
from src.config import load_config
from src.models.book._short_exhaustion import targets,entry_masks,allocate,mean_distance_mark
def params():return load_config()["models"]["book_short_volume_fade"]
def test_fee_hurdle_uses_bid_ask_and_both_fees():
 p=params();price=103.;mean=100.;entry=price*(1-p["halfspread"]);cover=mean*(1+p["halfspread"])
 expected=(entry-cover-p["fee"]*(entry+cover))/entry
 assert abs(mean_distance_mark(price,mean,p)-expected)<1e-14
def test_volume_rejection_entry_and_no_unconfirmed_upward_short():
 p=params();ix=pd.date_range("2026-01-01",periods=1100,freq="h",tz="UTC")
 x=pd.DataFrame(100.,index=ix,columns=p["coins"]);x.iloc[-5:]=np.array([100,101,102,103,102.7])[:,None]
 q=x*0+100;q.iloc[-4:-1]=300;sigma=pd.Series(.003,index=x.columns)
 yes=entry_masks(x,q,sigma,p,"volume");assert yes.all()
 x.iloc[-1]=103.2
 assert not entry_masks(x,q,sigma,p,"volume").any()
def test_future_price_or_volume_cannot_change_targets():
 p=params();t=pd.Timestamp("2026-10-05 01:00",tz="UTC")
 ix=pd.date_range(end=t+pd.Timedelta(hours=3),periods=1104,freq="h");rng=np.random.default_rng(2)
 x=pd.DataFrame(np.exp(np.cumsum(rng.normal(0,.003,(len(ix),4)),axis=0))*100,index=ix,columns=p["coins"]);q=x*100
 v=MarketView(t,x,q,tuple(p["coins"]),p);future=x.copy();fq=q.copy();future.loc[future.index>t]*=2;fq.loc[fq.index>t]*=10
 for family in ["volume","range","shock"]:
  pd.testing.assert_series_equal(targets(v,family),targets(replace(v,close=future,quote_volume=fq),family))
def test_kept_position_does_not_churn_with_new_entry_limits():
 p=params();coins=p["coins"];sigma=pd.Series(.004,index=coins);prev=pd.Series([-.05,0,0,0],index=coins)
 active=pd.Series(True,index=coins);entry=pd.Series([False,True,False,False],index=coins)
 w=allocate(sigma,prev,active,entry,p)
 assert w.iloc[0]==-.05 and (w<=0).all() and w.abs().sum()<=p["gross_cap"]+1e-12
 assert w.abs().max()<=p["coin_cap"]+1e-12
def test_invalid_selected_volume_returns_cash():
 p=params();ix=pd.date_range("2026-01-01",periods=1100,freq="h",tz="UTC");x=pd.DataFrame(100.,index=ix,columns=p["coins"]);q=x.copy();q.iloc[-1,0]=np.nan
 v=MarketView(ix[-1],x,q,tuple(p["coins"]),p)
 assert targets(v,"volume").empty
