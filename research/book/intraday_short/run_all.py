from pathlib import Path
import subprocess,sys,json
out=Path("results/book/20261010-intraday-short-v2");status=[]
for name,args in [("full_pytest",[sys.executable,"-B","-m","pytest","-q"]),("evaluation",[sys.executable,"-B","-m","research.book.intraday_short.run","--score"])]:
 with (out/(name+".log")).open("w") as f:code=subprocess.call(args,stdout=f,stderr=subprocess.STDOUT)
 status.append({"job":name,"returncode":code});(out/"status.json").write_text(json.dumps(status,indent=2))
 if code:raise SystemExit(code)
