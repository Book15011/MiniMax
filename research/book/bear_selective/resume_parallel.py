"""Resume unchanged model scores in parallel, preserving the interrupted batch."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,subprocess,sys
from research.book.bear_selective import run as study
def main():
 out=study.OUT
 prior=json.loads((out/"status_interrupted_sequential.json").read_text())
 note=json.loads((out/"orchestration_interruption.json").read_text())
 if note["interrupted_model"]!="book_bear_guard":raise RuntimeError("Unexpected interruption")
 errors=[z for z in prior if z["returncode"]]
 if errors!=[dict(job="book_bear_guard",returncode=-15)]:raise RuntimeError("Unexpected prior failure; preserve it")
 done={z["job"]:z for z in prior if z["returncode"]==0}
 if set(done)!={"full_pytest","book_bear_trend_control"}:raise RuntimeError("Unexpected completed jobs")
 pending=[name for name in study.NAMES if name not in done]
 def task(name):
  with (out/(name+".resumed.log")).open("x") as f:
   code=subprocess.call([sys.executable,"-B","-m","backtest.run","--model",name,"--score2"],stdout=f,stderr=subprocess.STDOUT)
  return dict(job=name,returncode=code)
 with ThreadPoolExecutor(max_workers=len(pending)) as pool:
  jobs=[pool.submit(task,n) for n in pending]
  for f in as_completed(jobs):
   z=f.result();done[z["job"]]=z
   rows=[done[n] for n in ["full_pytest",*study.NAMES] if n in done]
   (out/"status.json").write_text(json.dumps(rows,indent=2));print(z,flush=True)
 if len(done)!=len(study.NAMES)+1 or any(z["returncode"] for z in done.values()):raise RuntimeError("Normal score job failed; see retained logs")
 study.evaluate()
 code=subprocess.call([sys.executable,"-B","-m","research.book.bear_selective.score","--score"])
 (out/"resume_status.json").write_text(json.dumps(dict(status="PASS" if code==0 else "FAIL",score_returncode=code,original_interruption_preserved=True),indent=2))
 raise SystemExit(code)
if __name__=="__main__":main()
