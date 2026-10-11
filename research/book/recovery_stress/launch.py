from pathlib import Path
import subprocess,json,os
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"results/book/20261011-recovery-stress-v1"
env=dict(os.environ,PYTHONPATH=str(ROOT),OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1")
commands={"stress":[str(ROOT/".venv/bin/python"),"-B","-m","research.book.recovery_stress.run"],
          "tests":[str(ROOT/".venv/bin/python"),"-B","-m","pytest","-q"]}
handles={k:(OUT/(k+".log")).open("w") for k in commands}
jobs={k:subprocess.Popen(v,cwd=ROOT,env=env,stdout=handles[k],stderr=subprocess.STDOUT) for k,v in commands.items()}
status={k:p.wait() for k,p in jobs.items()}
for h in handles.values(): h.close()
(OUT/"launch_status.json").write_text(json.dumps(status,indent=2))
raise SystemExit(int(any(status.values())))
