import numpy as np
from probe import bounded_weights,shrunk_cov,portfolio_features

def test_absolute_cap_and_gross():
 x=np.array([[2.,-2.,.1],[.1,.2,-.1]])
 w=bounded_weights(x,1.,.3)
 assert np.max(np.abs(w))<=.3+1e-12
 assert np.max(np.sum(np.abs(w),axis=1))<=1
 assert np.allclose(w[1],[.1,.2,-.1])

def test_covariance_shrinkage_diagonal():
 r=np.array([[1.,2.],[2.,5.],[4.,6.],[5.,8.]])*.01
 c=shrunk_cov(r,1.)
 assert np.allclose(c,np.diag(np.diag(c)))
 assert np.linalg.eigvalsh(c).min()>0

def test_causal_feature_prefix():
 import pandas as pd
 ix=pd.date_range("2026-09-01",periods=200,freq="h",tz="UTC")
 h=pd.DataFrame({"A":np.exp(np.arange(200)*.001),"B":np.exp(np.arange(200)*-.001)},index=ix)
 t=ix[170]
 a=portfolio_features(h,[t],"momentum",24,0,72,1.,"raw")
 h.iloc[171:]=1e20
 b=portfolio_features(h,[t],"momentum",24,0,72,1.,"raw")
 assert np.allclose(a,b)

def test_vectorized_scale_grid():
 x=np.array([[.2,-.1],[.5,-.7]])
 k=np.array([.5,2.])[:,None,None]
 w=bounded_weights(x[None,:,:],k,.4)
 assert w.shape==(2,2,2)
 assert np.all(np.abs(w).sum(axis=-1)<=1+1e-12)
 assert np.allclose(w[0,0],[.1,-.05])

def test_twostage_prediction_excludes_future():
 import pandas as pd
 from execution_probe import mechanism_weights
 ix=pd.date_range("2026-09-01",periods=200,freq="h",tz="UTC")
 h=pd.DataFrame({a+"USDT":np.exp(np.arange(200)*(.001+j*.0002)+np.sin(np.arange(200))*.001) for j,a in enumerate(("BNB","BTC","ETH","SOL","XRP"))},index=ix)
 t=ix[170]
 pars={"kind":"two","lookback":23,"fast":5,"lag":2,"vol_window":24,"forecast_clip":.005,"power":1,"k":.0024,"cap":.5}
 a=mechanism_weights(h,[t],pars)[t]
 h.iloc[171:]=1e20
 b=mechanism_weights(h,[t],pars)[t]
 assert np.allclose(a,b)
 assert np.abs(a).sum()<=1+1e-12

def test_covariance_shrinkage_positive_definite():
 r=np.array([[1.,1.],[2.,2.],[3.,3.],[4.,4.]])*.01
 c=shrunk_cov(r,.25)
 assert np.allclose(c,c.T)
 assert np.linalg.eigvalsh(c).min()>0
