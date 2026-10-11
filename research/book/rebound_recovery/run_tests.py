from pathlib import Path
import json,subprocess
w=Path(__file__).resolve().parents[3]
o=w.parents[1]/"results/book/20261011-rebound-recovery-v1"
args=["tests","research/book/recovery_study/test_recovery.py",
      "research/book/recovery_selection/test_selection.py","research/book/residual_recovery/test_residual.py","research/book/high_recovery/test_high.py","research/book/rebound_recovery/test_rebound.py",
      "research/book/recovery_study/test_current_review.py","research/book/recovery_study/test_forward.py"]
p=subprocess.run([str(w/".venv/bin/python"),"-B","-m","pytest","-q",*args],cwd=w,capture_output=True,text=True)
(o/"full_tests.log").write_text(p.stdout+p.stderr)
(o/"full_tests.status.json").write_text(json.dumps({"returncode":p.returncode,"status":"PASS" if p.returncode==0 else "FAIL"},indent=2))
raise SystemExit(p.returncode)
