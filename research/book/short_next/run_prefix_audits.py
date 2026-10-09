from pathlib import Path
import subprocess,sys,json
ROOT=Path("/home/ubuntu/test/MiniMax/results/book")
jobs=[('20261010-short-next-prefix-v3', '/home/ubuntu/test/MiniMax/results/book/20261010-short-next-prefix-v3-audit-v2'), ('20261010-transition-prefix-v1', '/home/ubuntu/test/MiniMax/results/book/20261010-transition-prefix-v1-audit')]
for src,out in jobs:
 with (Path(out)/"run.log").open("w") as f:
  code=subprocess.call([sys.executable,"-B","research/book/short_next/prefix_audit.py","--input",str(ROOT/src),"--out",out],stdout=f,stderr=subprocess.STDOUT)
 if code:raise SystemExit(code)
print("Both archived-prefix audits passed",flush=True)
