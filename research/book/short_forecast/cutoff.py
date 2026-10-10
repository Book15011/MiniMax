"""Exclude target batches scheduled at the terminal mark or later."""
import pandas as pd
def executable_targets(weights,end,lag_minutes):
 end=pd.Timestamp(end)
 return {t:w for t,w in weights.items() if pd.Timestamp(t)+pd.Timedelta(minutes=lag_minutes)<end}
