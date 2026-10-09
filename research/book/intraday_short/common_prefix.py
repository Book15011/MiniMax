"""Matched endpoint valuation of already audited frozen baseline paths."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
ROOT=Path("/home/ubuntu/test/MiniMax");R=ROOT/"results/book";OUT=R/"20261010-intraday-short-v3"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 end=pd.Timestamp("2026-10-09 00:00Z");start=pd.Timestamp("2026-10-04 12:00Z")
 sources={
 "observed_literal_ledger":R/"20261010-short-next-prefix-v3/observed_literal_ledger_prefix_equity.csv",
 "frozen_calibrated_reconstruction":R/"20261010-clone-prefix-v1/clone_prefix_equity.csv",
 "baitoey_ovl_brk_dual":R/"20261010-short-next-prefix-v3/baitoey_ovl_brk_dual_prefix_equity.csv",
 "book_cashshort_confirm":R/"20261010-short-next-prefix-v3/book_cashshort_confirm_prefix_equity.csv",
 "book_cashshort_pullback":R/"20261010-short-next-prefix-v3/book_cashshort_pullback_prefix_equity.csv",
 "book_transition_short":R/"20261010-transition-prefix-v1/book_transition_short_prefix_equity.csv"}
 rows=[]
 for name,p in sources.items():
  f=pd.read_csv(p);f["time_utc"]=pd.to_datetime(f.time_utc,utc=True);f=f[(f.time_utc>=start)&(f.time_utc<=end)]
  if f.time_utc.iloc[0]!=start or f.time_utc.iloc[-1]!=end:raise ValueError("Endpoint absent")
  e=f.equity.to_numpy().copy();e[-1]-=.001*float(f.gross.iloc[-1])
  rows.append({"model":name,"return":float(e[-1]/100000-1),"MDD":float((1-e/np.maximum.accumulate(e)).max()),"start":str(start),"end":str(end),"scope":"existing full portfolio; cash100k; conditional observed ledger retains deficit" if name=="observed_literal_ledger" else "existing full portfolio; cash100k","source":str(p)})
 pd.DataFrame(rows).to_csv(OUT/"common_prefix_baselines.csv",index=False)
 (OUT/"common_prefix_manifest.json").write_text(json.dumps({"status":"PASS","source_pins":{str(p):sha(p) for p in sources.values()},"start":str(start),"end":str(end),"fee":.001,"limits":"Baseline uses accepted recorded quotes/archive1bp proxy and original fills; minute prototypes use declared5bp proxy each side and four assets. Same dates/capital, different universe/execution. Clone fitted period, literal19/33 remains. Not prospective edge or identical execution."},indent=2))
 print(pd.DataFrame(rows)[["model","return","MDD"]].to_string(index=False),flush=True)
if __name__=="__main__":main()
