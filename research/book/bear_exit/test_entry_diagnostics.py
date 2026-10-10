import pandas as pd,numpy as np
from research.book.bear_exit.entry_diagnostics import fixed_markout
def prices():
 return pd.Series([100.,99.,98.,97.],index=pd.date_range("2020-01-01",periods=4,freq="h",tz="UTC"))
def test_flat_price_accounts_for_both_fees_and_spread():
 p=prices()*0+100
 got=fixed_markout(99.95,p,p.index[0],1,.001,.0005,p.index[-1],60)
 assert np.isclose(got,-.3/99.95)
def test_real_entry_is_used_and_markout_is_profitable_on_decline():
 p=prices()
 z=fixed_markout(99.95,p,p.index[0],3,.001,.0005,p.index[-1],60)
 ask=97*1.0005
 assert np.isclose(z,(99.95-ask-.001*(99.95+ask))/99.95) and z>0
def test_outside_endpoint_is_censored_and_stale_price_not_reused():
 p=prices()
 assert np.isnan(fixed_markout(99.95,p,p.index[0],6,.001,.0005,p.index[-1],60))
 q=p.drop(p.index[-1])
 assert np.isnan(fixed_markout(99.95,q,p.index[0],3,.001,.0005,p.index[-1],60))
