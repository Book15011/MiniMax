"""One-command frozen-batch scoring, auditing and board refresh."""
from pathlib import Path
import argparse,json,subprocess,sys
ROOT=Path("/home/ubuntu/test/MiniMax")
def main():
 p=argparse.ArgumentParser();p.add_argument("--score",action="store_true",required=True);p.add_argument("--phase",choices=["initial","persistent"],default="persistent");args=p.parse_args()
 initial=args.phase=="initial";out=ROOT/"results/book"/("20261010-intraday-short-v2" if initial else "20261010-intraday-short-v3")
 status=out/"status.json"
 if not status.exists() or len(json.loads(status.read_text()))!=2 or any(x["returncode"]!=0 for x in json.loads(status.read_text())):
  raise SystemExit("Frozen evaluation incomplete/failed. Inspect status and logs; use a new version for changed models. This command will not overwrite failed trials.")
 for name in ["evaluation_manifest.json","independent_data_audit.json"]:
  if not (out/name).exists() or json.loads((out/name).read_text())["status"]!="PASS":raise SystemExit("Missing verified evidence: "+name)
 from research.book.intraday_short import audit,report
 audit.OUT=out
 if not (out/"independent_execution_audit.json").exists():audit.audit_execution()
 report.OUT=out;report.main(None if initial else ROOT/"results/book/20261010-intraday-short-v2")
 from research.book.intraday_short.refresh_hourly_board import main as refresh
 refresh()
 print("Scored, audited and published: "+str(out/"leaderboard_short.md"))
if __name__=="__main__":main()
