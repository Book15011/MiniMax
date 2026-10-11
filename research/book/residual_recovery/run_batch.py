from pathlib import Path
import json,subprocess
w=Path(__file__).resolve().parents[3]
o=w.parents[1]/"results/book/20261011-residual-recovery-v1"
jobs=[("paired","research.book.residual_recovery.run"),("tests","research.book.residual_recovery.run_tests")]
state=[]
for name,module in jobs:
    with (o/f"{name}.log").open("w") as log:
        p=subprocess.run([str(w/".venv/bin/python"),"-B","-m",module],cwd=w,stdout=log,stderr=subprocess.STDOUT)
    state.append({"job":name,"returncode":p.returncode})
    (o/"batch_status.json").write_text(json.dumps(state,indent=2))
    if p.returncode:
        raise SystemExit(p.returncode)
