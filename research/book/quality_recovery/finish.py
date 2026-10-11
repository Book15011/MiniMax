"""Sequential integrity repair and publication; retain first failed attempt."""
from pathlib import Path
import subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT.parents[1]/"results/book/20261011-quality-recovery-v1"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    results=[]
    for name in ["run","audit","publish_review","report"]:
        with (OUT/f"recheck_{name}.log").open("w") as f:
            p=subprocess.run([str(ROOT/".venv/bin/python"),"-B","-m","research.book.quality_recovery."+name],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
        results.append({"job":name,"returncode":p.returncode})
        (OUT/"verification_status.json").write_text(json.dumps(results,indent=2))
        if p.returncode:raise SystemExit(p.returncode)
        if name=="run":
            original=json.loads((OUT/"cached_runs_before_recheck.json").read_text())
            for model,item in original.items():
                meta=json.loads((OUT/f"{model}.base.json").read_text())
                assert item["run_key"]==meta["run_key"]
                folder=ROOT.parents[1]/"results/scoring/cache"/model
                assert all(sha(folder/f'{item["run_key"]}.{suffix}')==digest for suffix,digest in item["sha256"].items())
            (OUT/"cache_recheck_audit.json").write_text(json.dumps({"status":"PASS","all_three_run_keys_and_raw_cache_hashes_unchanged":True},indent=2))
if __name__=="__main__":main()
