"""Run fixed diagnostics without changing model parameters or rankings."""
from pathlib import Path
import subprocess,sys,json,hashlib
ROOT=Path("/home/ubuntu/test/MiniMax");W=Path.cwd()
OUT=ROOT/"results/book/20261010-short-next-cost"
OUT.mkdir(parents=True,exist_ok=True)
proof=str(ROOT/"results/book/20261009-short-diagnostics/baseline_reproduction_v2.json")
models=[("baitoey_ovl_brk_dual","f30fa79cde92399a"),("book_cashshort_confirm","8254f1c7a7530833"),("book_cashshort_pullback","497ddefabf20ec3e")]
jobs=[]
chron=[sys.executable,"-B","research/book/short_next/chronological.py"]
for name,key in models[1:]:chron+=["--candidate",name+"="+key]
chron+=["--benchmark",models[0][0]+"="+models[0][1],"--out",str(ROOT/"results/book/20261010-short-next-chronological")]
jobs.append(("chronological",chron))
for name,key in models:
 jobs.append((name,[sys.executable,"-B","research/book/short_next/cost_replay.py","--source-worktree",str(W),"--model",name,"--key",key,"--baseline-evidence",proof,"--out",str(OUT)]))
jobs.append(("summary",[sys.executable,"-B","research/book/short_next/summarize_cost.py","--out",str(OUT),"--baseline-evidence",proof]))
status=[]
for name,args in jobs:
 with (OUT/(name+".log")).open("w") as f:code=subprocess.call(args,stdout=f,stderr=subprocess.STDOUT)
 status.append({"job":name,"returncode":code});(OUT/"status.json").write_text(json.dumps(status,indent=2))
 if code:raise SystemExit(code)
print("All fixed chronological/cost diagnostics complete",flush=True)
