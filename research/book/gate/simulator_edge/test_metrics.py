import numpy as np,pandas as pd,pytest
from research.book.gate.simulator_edge.metrics import summarize
def frame():
    return pd.DataFrame({"start":pd.to_datetime(["2025-03-28 16:00","2025-03-31 16:00","2025-04-03 16:00"],utc=True),
                         "return":[.20,.30,-.10],"mdd":[.02,.03,.1]})
def test_exact_gate_and_quarter_boundary_purge():
    z=summarize(frame(),72)
    assert z["p19"]==2/3 and z["n_purged"]==2 and z["quarters"]==2
    assert z["n_disjoint"]==3 and z["p_gate0"]==2/3
def test_missing_outcomes_are_not_zero_risk_success():
    f=frame();f.loc[0,"return"]=np.nan
    with pytest.raises(ValueError):summarize(f,72)
def test_gaps_do_not_create_fake_independent_samples():
    f=frame();f.loc[1,"start"]=f.loc[0,"start"]+pd.Timedelta(hours=1)
    assert summarize(f,72)["n_disjoint"]==2
