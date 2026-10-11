"""Finite paired experiment; inherited rejection rules, eight-hypothesis bound."""
from pathlib import Path
import hashlib
from research.book.recovery_study import run as study
from research.book.recovery_selection.run import bound as _previous_bound
import numpy as np
import pandas as pd

study.OUT=study.MAIN/"results/book/20261011-residual-recovery-v1"
study.NAMES=[study.BASE,"book_recovery_resid","book_recovery_resid_blend"]
original_hashes=study.hashes
def hashes():
    h=original_hashes()
    for p in Path(__file__).parent.iterdir():
        if p.is_file() and "__pycache__" not in str(p):
            h[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    return h
study.hashes=hashes

original_dump=study.dump
def dump(name,obj):
    if name=="run_source.json":
        obj={**obj,"new_hypotheses":2,"total_task_hypotheses":8,
             "protocol_sha256":hashlib.sha256(Path(__file__).with_name("PROTOCOL.md").read_bytes()).hexdigest(),
             "prospective_cohort_modified":False,"actual_account":False}
    if name=="complete.json":
        obj={k:v for k,v in obj.items() if k not in ["prospective_start","prospective_end"]}
        obj["new_candidates_have_pre_start_forward_evidence"]=False
    original_dump(name,obj)
study.dump=dump

def bound(frame):
    t=pd.DatetimeIndex(frame.start)
    end=t.tz_localize(None).to_period("Q").end_time.tz_localize("UTC")
    f=frame.loc[(t+pd.Timedelta(hours=336))<=end].copy()
    f["quarter"]=pd.DatetimeIndex(f.start).tz_localize(None).to_period("Q").astype(str)
    g=f.groupby("quarter")["delta"].agg(["sum","count"])
    rng=np.random.default_rng(20261011)
    draw=rng.integers(0,len(g),size=(20000,len(g)))
    b=g["sum"].to_numpy()[draw].sum(1)/g["count"].to_numpy()[draw].sum(1)
    return {"lower":float(np.quantile(b,.05/8)),"upper":float(np.quantile(b,1-.05/8)),
            "n_quarters":len(g),"n_purged_windows":len(f),"hypotheses":8,
            "project_wide_post_selection_control":False}
study.ci_quarters=bound
if __name__=="__main__":
    study.main()
