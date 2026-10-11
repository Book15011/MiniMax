import numpy as np
import pandas as pd
import pytest
from research.book.recovery_stress.metrics import outcome, paired_stability

def test_terminal_fee_is_on_terminal_gross_and_drawdown_keeps_original_convention():
    equity=np.array([[1.,1.1,0.99],[1.,0.8,1.2]])
    gross=np.array([[0.,1.,0.5],[0.,1.,0.]])
    ret,dd=outcome(equity,gross,2,.002)
    np.testing.assert_allclose(ret,[-.01099,.2],atol=1e-12)
    np.testing.assert_allclose(dd,[-.1,-.2],atol=1e-12)
    assert equity[0,-1]==.99

def test_outcome_rejects_invalid_equity_or_horizon():
    with pytest.raises(ValueError): outcome(np.array([[1.,np.nan]]),np.zeros((1,2)),1,.001)
    with pytest.raises(ValueError): outcome(np.ones((1,2)),np.zeros((1,2)),2,.001)

def test_calendar_purge_and_disjoint_offsets_do_not_use_cross_year_outcomes():
    dates=pd.date_range('2023-12-20',periods=55,freq='D',tz='UTC')
    a=pd.DataFrame({'start':dates,'return':np.full(55,.02)})
    b=pd.DataFrame({'start':dates,'return':np.full(55,.01)})
    got=paired_stability(a,b,336)
    assert [v['year'] for v in got['calendar_years']]==[2024]
    assert got['calendar_years'][0]['n']==43
    assert got['calendar_years'][0]['mean_delta']==pytest.approx(.01)
    assert len(got['disjoint_offsets'])==14
    assert all(v['minimum_gap_hours']>=336 for v in got['disjoint_offsets'] if v['n']>1)
    assert got['strictly_positive_year_share']==1.
    assert got['leave_one_year_out']==[]

def test_paired_stability_rejects_unmatched_and_duplicate_windows():
    dates=pd.date_range('2024-01-01',periods=2,freq='D',tz='UTC')
    a=pd.DataFrame({'start':dates,'return':[.01,.02]})
    with pytest.raises(ValueError): paired_stability(a,a.iloc[:1],336)
    with pytest.raises(ValueError): paired_stability(pd.concat([a,a]),a,336)
