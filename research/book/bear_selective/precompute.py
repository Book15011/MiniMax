"""Prepare one independent scoring cache without changing any leaderboard."""
from pathlib import Path
import argparse,json,logging
from src.config import load_config
from src.models import get
from backtest.data import load_market
from backtest.scoring.score import scored_starts,simulated_starts
from backtest.scoring.evaluate import simulate
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--model",required=True);a=ap.parse_args()
 logging.basicConfig(level=logging.INFO)
 cfg=load_config();m=load_market(cfg)
 starts=scored_starts(m,cfg,None);sim=simulated_starts(m,cfg,starts)
 result=simulate(get(a.model),m,cfg,sim,use_cache=True,log=logging.getLogger("precompute"))
 out=Path("/home/ubuntu/test/MiniMax/results/book/20261010-bear-selective-v1/precompute")/(a.model+"-scoring.json")
 out.write_text(json.dumps(dict(status="PASS",model=a.model,windows=len(result.windows),cache_only=True),indent=2))
if __name__=="__main__":main()
