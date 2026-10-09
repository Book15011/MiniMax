"""Sequential authoritative-prefix preparation, fine data, and replay."""
from pathlib import Path
import subprocess,sys,json
ROOT=Path("/home/ubuntu/test/MiniMax")
OUT=ROOT/"results/book/20261010-short-next-prefix-v3"
status=[]
for stage in ("prepare","fetch","replay"):
 with (OUT/(stage+".log")).open("w") as f:
  code=subprocess.call([sys.executable,"-B","research/book/short_next/prefix.py",stage,"--out",str(OUT)],stdout=f,stderr=subprocess.STDOUT)
 status.append({"stage":stage,"returncode":code})
 (OUT/"status.json").write_text(json.dumps(status,indent=2))
 if code:raise SystemExit(code)
print("Authoritative prefix stages complete",flush=True)
