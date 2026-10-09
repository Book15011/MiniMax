from pathlib import Path
import subprocess,sys,json
out=Path("results/book/20261009-short-cost-stress");out.mkdir(parents=True,exist_ok=True)
statuses=[]
for model in ("book_short_trend","book_short_rebound","book_short_breakdown"):
 with (out/(model+".log")).open("w") as f:
  code=subprocess.call([sys.executable,"-B","research/book/short_cost_stress/run.py","--model",model],stdout=f,stderr=subprocess.STDOUT)
 statuses.append({"model":model,"returncode":code})
 (out/"status.json").write_text(json.dumps(statuses,indent=2))
 if code:raise SystemExit(code)
raise SystemExit(subprocess.call([sys.executable,"-B","research/book/short_cost_stress/run.py","--summarize"]))
