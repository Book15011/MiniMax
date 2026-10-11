from pathlib import Path
import json,subprocess
w=Path(__file__).resolve().parents[3];o=w.parents[1]/"results/book/20261011-recovery-selection-v1"
p=subprocess.run([str(w/".venv/bin/python"),"-B","-m","pytest","-q","tests","research/book/recovery_study/test_recovery.py","research/book/recovery_selection/test_selection.py"],cwd=w,capture_output=True,text=True)
(o/"full_tests.log").write_text(p.stdout+p.stderr)
(o/"full_tests.status.json").write_text(json.dumps({"returncode":p.returncode,"status":"PASS" if p.returncode==0 else "FAIL"},indent=2))
raise SystemExit(p.returncode)
