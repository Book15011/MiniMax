"""Regenerate presentation from published numbers, without evaluating or tuning."""
from pathlib import Path
import hashlib,json
import pandas as pd
from src.config import load_config
from backtest.scoring.weak_board import load_checkpoint,atomic_batch
from backtest.scoring.registry import locked
from backtest.scoring.weak_render import render,short_rank_view
ROOT=Path("/home/ubuntu/test/MiniMax")
def main():
 cfg=load_config();cp=load_checkpoint(cfg);root=ROOT/"results/scoring"
 with locked("scoring-score2"):
  sources=[root/"leaderboard_2.csv",root/"short_leaderboard_2.csv",root/"registry_2.jsonl"]
  before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
  frame=pd.read_csv(sources[0]);short=pd.read_csv(sources[1])
  evidence=json.loads((cp["root"]/"comparison_validation.json").read_text())
  text=render(cp,frame,short,evidence)
  if before!={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}:raise ValueError("Concurrent input change")
  atomic_batch({root/"leaderboard_2.md":text,root/"short_leaderboard_ranked_2.csv":short_rank_view(short).to_csv(index=False)})
 out=ROOT/"results/book/20261010-intraday-short-v2";out.mkdir(parents=True,exist_ok=True)
 (out/"hourly_presentation_manifest.json").write_text(json.dumps({"protocol":cp["protocol"],"unchanged_numeric_source_hashes":before,"rank_formula":"within-profile lower90%6h precision; separately windowmean6hunitproxy","presentation_source":str(Path(__file__).resolve())},indent=2))
 print("Published presentation only; primary numeric CSV and registry unchanged",flush=True)
if __name__=="__main__":main()
