from types import SimpleNamespace
import numpy as np,pandas as pd,pytest
from src.models.book._short_forecast import training_samples,forecast,targets,short_mark
P=dict(coins=['BTCUSDT','ETHUSDT'],training_hours=480,returns_hours=[3,12,24],gap_hours=24,risk_hours=72,risk_reference=.004,training_stride=6,horizon_hours=6,execution_lag_hours=1,min_training_anchors=20,neighbors=24,min_neighbor_anchors=5,fee=.001,halfspread=.0005,ridge_penalty=1.,quadratic=True,gross_cap=.25,coin_cap=.1,target_daily_vol=.01,hours_per_day=24,sigma_floor=1e-10,entry_edge=.001,exit_edge=-.0005,edge_scale=.006,min_win_fraction=.55,scale_floor=1e-8)
def data():
 ix=pd.date_range('2026-01-01',periods=900,freq='h',tz='UTC');z=np.arange(900)
 return pd.DataFrame({'BTCUSDT':100*np.exp(.0002*z+.006*np.sin(z/7)),'ETHUSDT':50*np.exp(.0001*z+.008*np.cos(z/9))},index=ix)
def test_every_training_label_finishes_before_decision():
 x=data();t=x.index[800];X,y,anchors,q,sigma=training_samples(x,t,P)
 assert len(X)==len(y)==len(anchors)
 assert max(anchors)+pd.Timedelta(hours=7)<=t
 assert max(anchors)<t
 assert np.isfinite(X).all() and np.isfinite(y).all()
def test_label_charges_both_spreads_and_fees():
 r=.01
 expected=((1-.0005)-(1+r)*(1+.0005)-.001*((1-.0005)+(1+r)*(1+.0005)))/(1-.0005)
 assert short_mark(np.array([r]),P)[0]==pytest.approx(expected)
def test_future_quotes_cannot_change_forecast():
 x=data();t=x.index[800];other=x.copy();other.loc[other.index>t]*=50
 for family in ['analogue','ridge']:
  a=forecast(x,t,P,family);b=forecast(other,t,P,family)
  for left,right in zip(a,b):np.testing.assert_array_equal(left,right)
def test_targets_are_only_short_and_capped():
 x=data();t=x.index[800];p={**P,'entry_edge':-1,'min_win_fraction':0}
 v=SimpleNamespace(close=x,t=t,params=p,universe=list(x.columns),prev_targets=pd.Series(dtype=float))
 w=targets(v,'analogue')
 assert (w<=0).all() and abs(w).sum()<=.25+1e-12 and (abs(w)<=.1+1e-12).all()
def test_malformed_or_short_history_returns_cash():
 x=data().iloc[:30];v=SimpleNamespace(close=x,t=x.index[-1],params=P,universe=list(x.columns),prev_targets=pd.Series(dtype=float))
 assert targets(v,'analogue').empty
