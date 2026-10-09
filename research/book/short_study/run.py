"""Run exactly the three frozen candidates through the unchanged secondary scorer."""
from __future__ import annotations
import glob, hashlib, json, subprocess, sys
from pathlib import Path
from src.config import REPO_ROOT, load_config, resolve
from backtest.scoring.score2 import load_checkpoint

MODELS=("book_short_trend","book_short_rebound","book_short_breakdown")
OUT=resolve("results/book/20261009-short-study-v2")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def manifest():
    cfg=load_config();cp=load_checkpoint(cfg)
    panel=resolve(cfg["harness"]["panel_dir"])
    files=[panel/n for n in ("panel_close_1h.parquet","panel_quote_volume_1h.parquet","universe.parquet","panel_notes.json")]
    spreads=sorted(glob.glob(str(resolve(cfg["harness"]["spreads_snapshot_glob"]))))
    if spreads:files.append(Path(spreads[-1]))
    files += [REPO_ROOT/"config.yaml",REPO_ROOT/"src/models/book/_short_study.py",
              REPO_ROOT/"research/book/short_study/PROTOCOL.md"]
    files += [REPO_ROOT/f"src/models/book/{n}.py" for n in MODELS]
    return {"protocol":str(cp["protocol"]),"models":MODELS,
            "commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "hashes":{str(p):sha(p) for p in files}}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    before=manifest()
    path=OUT/"manifest_before.json"
    if path.exists():
        old=json.loads(path.read_text())
        assert old["hashes"]==before["hashes"],"Study source/data changed: use a new study identity"
    else:path.write_text(json.dumps(before,indent=2))
    status=[]
    try:
        with (OUT/"pytest.log").open("w") as f:
            code=subprocess.call([sys.executable,"-B","-m","pytest","-q"],stdout=f,stderr=subprocess.STDOUT)
        status.append({"stage":"full_pytest","returncode":code})
        (OUT/"status.json").write_text(json.dumps(status,indent=2))
        if code:return code
        for name in MODELS:
            with (OUT/f"{name}.log").open("w") as f:
                code=subprocess.call([sys.executable,"-B","-m","backtest.run","--model",name,"--score2"],
                                     stdout=f,stderr=subprocess.STDOUT)
            status.append({"stage":name,"returncode":code})
            (OUT/"status.json").write_text(json.dumps(status,indent=2))
            if code:return code
    finally:
        after=manifest()
        (OUT/"manifest_after.json").write_text(json.dumps(after,indent=2))
        assert before["hashes"]==after["hashes"],"Input/source changed during run"
    return 0

if __name__=="__main__":raise SystemExit(main())
