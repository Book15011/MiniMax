"""Wait for this run's publication, then execute the same fixed diagnostics."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
import pandas as pd,numpy as np
ROOT=Path("/home/ubuntu/test/MiniMax");W=Path.cwd()
OUT=ROOT/"results/book/20261010-transition-cost";OUT.mkdir(parents=True,exist_ok=True)
scorestatus=ROOT/"results/book/20261010-transition-short/status.json"
deadline=time.monotonic()+7200
while True:
 if scorestatus.exists():
  status=json.loads(scorestatus.read_text())
  if any(x["returncode"] for x in status):raise SystemExit("Primary run failed; no downstream publication")
  if len(status)==2:break
 if time.monotonic()>deadline:raise SystemExit("Primary run not complete within bounded wait")
 time.sleep(15)
scores=pd.read_csv(ROOT/"results/scoring/leaderboard_2.csv")
rows=scores[scores.model=="book_transition_short"]
if len(rows)!=1:raise ValueError("Unique published model required")
key=str(rows.iloc[0].run_key)
(OUT/"publication_identity.json").write_text(json.dumps({"model":"book_transition_short","key":key},indent=2))
proof=str(ROOT/"results/book/20261009-short-diagnostics/baseline_reproduction_v2.json")
jobs=[
 ("chronological",[sys.executable,"-B","research/book/short_next/chronological.py","--candidate","book_transition_short="+key,"--benchmark","baitoey_ovl_brk_dual=f30fa79cde92399a","--out",str(ROOT/"results/book/20261010-transition-chronological")]),
 ("cost",[sys.executable,"-B","research/book/short_next/cost_replay.py","--source-worktree",str(W),"--model","book_transition_short","--key",key,"--baseline-evidence",proof,"--out",str(OUT)])]
status=[]
for name,args in jobs:
 with (OUT/(name+".log")).open("w") as f:code=subprocess.call(args,stdout=f,stderr=subprocess.STDOUT)
 status.append({"job":name,"returncode":code});(OUT/"status.json").write_text(json.dumps(status,indent=2))
 if code:raise SystemExit(code)
baseline=ROOT/"results/book/20261010-short-next-cost"
a=pd.read_csv(OUT/"paired_windows.book_transition_short.csv")
b=pd.read_csv(baseline/"paired_windows.baitoey_ovl_brk_dual.csv")
if not a.start.equals(b.start) or len(a)!=160:raise ValueError("Frozen paired schedules differ")
summary=pd.concat([pd.read_csv(baseline/"summary.baitoey_ovl_brk_dual.csv"),pd.read_csv(OUT/"summary.book_transition_short.csv")],ignore_index=True)
summary.to_csv(OUT/"comparison_summary.csv",index=False)
rows=[]
for scenario in ("original","doubled"):
 d=a[scenario+"_liquidated_return"]-b[scenario+"_liquidated_return"]
 rows.append({"model":"book_transition_short","baseline":"baitoey_ovl_brk_dual","scenario":scenario,"n":160,"paired_mean":d.mean(),"paired_median":d.median(),"paired_p10":d.quantile(.1),"paired_worst":d.min(),"paired_win_share":(d>1e-12).mean()})
pd.DataFrame(rows).to_csv(OUT/"paired_top.csv",index=False)
pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/"manifest.book_transition_short.json",baseline/"manifest.baitoey_ovl_brk_dual.json",OUT/"paired_windows.book_transition_short.csv",baseline/"paired_windows.baitoey_ovl_brk_dual.csv"]}
(OUT/"comparison_manifest.json").write_text(json.dumps({"inputs":pins,"all_history_spent":True,"model_params_changed":False,"primary_metric_changed":False},indent=2))
print(summary.to_string(index=False),flush=True)
print("Fixed chronological and actual-cost diagnostics completed",flush=True)
