import numpy as np
import pandas as pd
from research.book.recovery_study.forward import T0,T1,ready,data_problem

def frames():
    ix=pd.date_range(T0,T1,freq="h")
    return pd.DataFrame({"BTCUSDT":100.,"ETHUSDT":10.},index=ix),pd.DataFrame({"BTCUSDT":1.,"ETHUSDT":1.},index=ix)

def test_forward_scores_wait_for_the_entire_frozen_period():
    assert not ready(T1-pd.Timedelta(hours=1))
    assert ready(T1)

def test_future_row_does_not_override_incomplete_store_metadata():
    close,qv=frames()
    assert data_problem(close,qv,T1-pd.Timedelta(hours=1))

def test_missing_hour_or_btc_price_cannot_score():
    close,qv=frames()
    assert data_problem(close.drop(T0+pd.Timedelta(hours=3)),qv,T1)
    close.loc[T0+pd.Timedelta(hours=5),"BTCUSDT"]=np.nan
    assert data_problem(close,qv,T1)

def test_bad_index_or_missing_volume_clock_cannot_score():
    close,qv=frames()
    assert data_problem(pd.concat([close,close.iloc[-1:]]),qv,T1)
    assert data_problem(close.iloc[::-1],qv,T1)
    assert data_problem(close,qv.drop(T1),T1)

def test_complete_clock_is_ready_without_imputing_unavailable_coins():
    close,qv=frames()
    close.loc[T0,"ETHUSDT"]=np.nan
    assert data_problem(close,qv,T1) is None
