"""Frozen single-hypothesis verification and ordinary score2 publication."""
from pathlib import Path
import hashlib,json,subprocess,sys
from src.config import load_config,resolve
from src.models import get
from backtest.evaluate import model_modules
ROOT=Path("/home/ubuntu/test/MiniMax");W=Path.cwd()
OUT=ROOT/"results/book/20261010-transition-short"
OUT.mkdir(parents=True,exist_ok=True)
if (OUT/"before_hashes.json").exists():raise ValueError("Preserve previous run")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=load_config();panel=resolve(cfg["harness"]["panel_dir"])
paths=[panel/n for n in ("panel_close_1h.parquet","panel_quote_volume_1h.parquet","universe.parquet","panel_notes.json")]
paths+=[W/"config.yaml",W/"research/book/short_next/TRANSITION_PROTOCOL.md"]
paths += [Path(sys.modules[m].__file__) for m in model_modules(get("book_transition_short"))]
before={str(p):sha(p) for p in paths}
(OUT/"before_hashes.json").write_text(json.dumps(before,indent=2))
status=[]
for name,args in [
 ("full_pytest",[sys.executable,"-B","-m","pytest","-q"]),
 ("book_transition_short",["scripts/lock","harness-book-weak-score","--","nice","-n","10",sys.executable,"-B","-m","backtest.run","--model","book_transition_short","--score2"])]:
 with (OUT/(name+".log")).open("w") as f:code=subprocess.call(args,stdout=f,stderr=subprocess.STDOUT)
 status.append({"job":name,"returncode":code});(OUT/"status.json").write_text(json.dumps(status,indent=2))
 if code:raise SystemExit(code)
after={str(p):sha(p) for p in paths}
(OUT/"after_hashes.json").write_text(json.dumps(after,indent=2))
if before!=after:raise ValueError("Frozen inputs changed")
print("All tests and ordinary score2 publication complete; hashes unchanged",flush=True)
