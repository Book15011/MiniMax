import pandas as pd
from research.book.bear_selective.cutoff import executable_targets

def test_endpoint_start_and_later_decisions_are_pending():
 t=pd.Timestamp('2026-01-01T12:00Z')
 w={t-pd.Timedelta(hours=h):pd.Series({'BTCUSDT':-.1}) for h in [0,1,2,3]}
 chosen=executable_targets(w,t,60)
 assert set(chosen)=={t-pd.Timedelta(hours=2),t-pd.Timedelta(hours=3)}

def test_two_hour_lag_has_same_strict_endpoint_convention():
 t=pd.Timestamp('2026-01-01T12:00Z')
 w={t-pd.Timedelta(hours=h):pd.Series(dtype=float) for h in [1,2,3]}
 assert list(executable_targets(w,t,120))==[t-pd.Timedelta(hours=3)]
