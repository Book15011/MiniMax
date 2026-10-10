from pathlib import Path
import hashlib,json,os,subprocess,sys
OUT=Path("/home/ubuntu/test/MiniMax/results/book/20261010-daily-channel-v1")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 OUT.mkdir(exist_ok=True);os.environ["OPENBLAS_NUM_THREADS"]="1";os.environ["OMP_NUM_THREADS"]="1"
 if (OUT/"source_before.json").exists():raise ValueError("Preserve prior run")
 files=["config.yaml","src/models/book/book_daily_channel.py","research/book/daily_channel/run_batch.py","research/book/daily_channel/parameter_origin.json"]
 before={p:sha(p) for p in files};(OUT/"source_before.json").write_text(json.dumps(before,indent=2))
 rows=[]
 for name,args in [("full_tests",["pytest","-q"]),("model_tests",["pytest","-q","research/book/daily_channel/test_model.py"]),("normal_score",["backtest.run","--model","book_daily_channel","--score2"])]:
  with (OUT/(name+".log")).open("x") as f:code=subprocess.call([sys.executable,"-B","-m",*args],stdout=f,stderr=subprocess.STDOUT)
  rows.append(dict(job=name,returncode=code));(OUT/"status.json").write_text(json.dumps(rows,indent=2))
  if code:raise RuntimeError(name+" failed; evidence retained")
 after={p:sha(p) for p in files};(OUT/"source_after.json").write_text(json.dumps(after,indent=2))
 if before!=after:raise AssertionError("Source changed")
 (OUT/"complete.json").write_text(json.dumps(dict(status="PASS",model="book_daily_channel",calibration_only=True),indent=2))
if __name__=="__main__":main()
