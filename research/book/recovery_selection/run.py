from pathlib import Path
from research.book.recovery_study import run as study
study.OUT=study.MAIN/"results/book/20261011-recovery-selection-v1"
study.NAMES=[study.BASE,"book_recovery_abs","book_recovery_iv","book_recovery_abs_iv"]
# Six hypotheses have now been tried in this task. More conservative new family bound.
_original=study.ci_quarters
def bound(frame):
    import numpy as np,pandas as pd
    t=pd.DatetimeIndex(frame.start)
    end=t.tz_localize(None).to_period("Q").end_time.tz_localize("UTC")
    f=frame.loc[(t+pd.Timedelta(hours=336))<=end].copy()
    f["quarter"]=pd.DatetimeIndex(f.start).tz_localize(None).to_period("Q").astype(str)
    g=f.groupby("quarter")["delta"].agg(["sum","count"])
    rng=np.random.default_rng(20261011);draw=rng.integers(0,len(g),size=(20000,len(g)))
    b=g["sum"].to_numpy()[draw].sum(1)/g["count"].to_numpy()[draw].sum(1)
    return {"lower":float(np.quantile(b,.05/6)),"upper":float(np.quantile(b,1-.05/6)),
            "n_quarters":len(g),"n_purged_windows":len(f),"hypotheses":6,"project_wide_post_selection_control":False}
study.ci_quarters=bound
if __name__=="__main__":
    study.main()
    import hashlib,json,subprocess
    p=Path(__file__).with_name("PROTOCOL.md")
    study.dump("selection_source.json",{"commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
        "protocol_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"new_hypotheses":3,"total_task_hypotheses":6})
