"""Frozen candidate verification and ordinary score2 publication."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path("/home/ubuntu/test/MiniMax")
OUT=ROOT/"results/book/20261009-short-next"
W=Path.cwd()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paths=[ROOT/"data/validation/panel_close_1h.parquet"]
# Derive exact panel paths from configuration rather than guessing locations.
from src.config import load_config,resolve
cfg=load_config();panel=resolve(cfg["harness"]["panel_dir"])
paths=[panel/n for n in ("panel_close_1h.parquet","panel_quote_volume_1h.parquet","universe.parquet","panel_notes.json")]
paths+=[W/"config.yaml",W/"src/models/book/_cashshort.py",W/"src/models/book/book_cashshort_confirm.py",W/"src/models/book/book_cashshort_pullback.py"]
before={str(p):sha(p) for p in paths}
(OUT/"before_hashes.json").write_text(json.dumps(before,indent=2))
jobs=[("full_pytest",[sys.executable,"-B","-m","pytest","-q"])]
for name in ("book_cashshort_confirm","book_cashshort_pullback"):
 jobs.append((name,["scripts/lock","harness-book-weak-score","--","nice","-n","10",sys.executable,"-B","-m","backtest.run","--model",name,"--score2"]))
status=[]
for name,args in jobs:
 with (OUT/(name+".log")).open("w") as f:code=subprocess.call(args,stdout=f,stderr=subprocess.STDOUT)
 status.append({"job":name,"returncode":code});(OUT/"status.json").write_text(json.dumps(status,indent=2))
 if code:raise SystemExit(code)
after={str(p):sha(p) for p in paths}
(OUT/"after_hashes.json").write_text(json.dumps(after,indent=2))
if before!=after:raise ValueError("Frozen source or raw input changed during evaluation")
print("All tests and ordinary score2 publications completed; raw/source hashes identical",flush=True)
