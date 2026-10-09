"""Statistical display must include non-firing windows and reject tiny evidence."""
import numpy as np,pandas as pd
from research.book.intraday_short.report import clustered_interval,eligible,summary_row
def test_all_loss_bound_cannot_be_positive():
 t=pd.date_range("2020-01-01",periods=16,freq="QS",tz="UTC")
 f=pd.DataFrame({"start":t,"return":-.01,"wins":0,"completed":3})
 lo,hi=clustered_interval(f,"return",seed=4,reps=2000,alpha=.01)
 assert lo<0 and hi<0
def test_empty_accuracy_is_unknown_not_success():
 f=pd.DataFrame({"start":[pd.Timestamp("2020-01-01",tz="UTC")],"return":[0.],"wins":[0],"completed":[0]})
 lo,hi=clustered_interval(f,"accuracy",seed=4,reps=100)
 assert np.isnan(lo) and np.isnan(hi)
def test_insufficient_count_or_quarters_cannot_pass():
 assert not eligible(lower=.01,completed=2,quarters=15,firing_clusters=15,stress=.01,median=.01,control=0.)
 assert not eligible(lower=.01,completed=100,quarters=3,firing_clusters=15,stress=.01,median=.01,control=0.)
 assert not eligible(lower=-.01,completed=100,quarters=15,firing_clusters=15,stress=.01,median=.01,control=0.)
def test_zero_trade_window_counts_in_return():
 f=pd.DataFrame({"return":[.02,0.],"completed":[1,0],"censored":[0,0],"wins":[1,0],"onsets":[1,0],"MDD":[.01,0.],"CS":[1.,0.],"CS_UTC":[1.,0.],"mean_gross":[.1,0.],"fees":[30,0.],"net_short_usd":[2000,0.],"orders":[2,0]})
 r=summary_row(f)
 assert r["mean"]==.01 and r["n"]==2 and r["firing"]==1
