import numpy as np,pandas as pd
from research.book.recovery_study.review_current import joint_bounds
def test_zero_edge_is_never_a_positive_improvement():
    ix=pd.date_range("2021-01-01",periods=25,freq="30D",tz="UTC")
    lower,critical,usable,quarters=joint_bounds(np.zeros((4,25,2)),ix,reps=1000)
    assert (lower==0).all() and critical==0
def test_constant_gain_is_preserved_and_quarter_crossings_are_purged():
    ix=pd.DatetimeIndex(["2022-01-01","2022-03-31","2022-05-01","2022-07-01"],tz="UTC")
    d=np.zeros((2,4,2));d[1,:,:]=.01
    lower,critical,usable,quarters=joint_bounds(d,ix,reps=1000)
    assert usable.tolist()==[True,False,True,True]
    assert np.allclose(lower[1],.01)
def test_adding_a_volatile_comparison_cannot_make_uniform_bound_less_conservative():
    ix=pd.date_range("2021-01-01",periods=25,freq="30D",tz="UTC")
    d=np.zeros((2,25,2));d[1,:,:]=.01
    _,a,_,_=joint_bounds(d,ix,reps=1000)
    z=np.stack([np.linspace(-.2,.2,25),np.linspace(.2,-.2,25)],axis=1)
    _,b,_,_=joint_bounds(np.concatenate([d,z[None,:,:]],axis=0),ix,reps=1000)
    assert b>=a
