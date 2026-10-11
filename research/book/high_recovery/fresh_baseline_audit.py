from pathlib import Path
import copy,hashlib,json
import numpy as np,pandas as pd
from src.config import load_config
from src.models import get
from backtest.data import load_market
from backtest.scoring.windows import pool_starts
from backtest.scoring.evaluate import simulate
ROOT=Path("/home/ubuntu/test/MiniMax/.worktrees/book-book-high-recovery")
OUT=ROOT/"results/book/20261011-high-recovery-v1"
MAIN=ROOT.parents[1]
cfg=copy.deepcopy(load_config())
cfg["scoring"]["cache_dir"]=str(OUT/"fresh_baseline_cache")
market=load_market(cfg);starts=pool_starts(market,cfg)
run=simulate(get("book_e20combo_brk_cash"),market,cfg,starts,use_cache=False)
original=MAIN/"results/scoring/cache/book_e20combo_brk_cash/8c149ee12abb99c2"
a=np.load(str(original)+".arrays.npz",allow_pickle=False)
windows=pd.read_parquet(str(original)+".windows.parquet")
targets=pd.read_parquet(str(original)+".targets.parquet")
errors={k:float(np.max(np.abs(a[k]-getattr(run,k)))) for k in ["equity","gross","net","days"]}
assert run.key=="8c149ee12abb99c2"
pd.testing.assert_frame_equal(run.windows,windows,check_freq=False,check_exact=True)
pd.testing.assert_frame_equal(run.targets,targets,check_freq=False,check_exact=True)
assert max(errors.values())<1e-12
payload={"status":"PASS","run_key":run.key,"errors":errors,"cached_windows_targets_identical":True,
         "use_cache":False,"original_cache_untouched":True,"model":"book_e20combo_brk_cash",
         "runtime":run.meta["runtime_s"],"source_commit":"c67c093","actual_account":False}
(OUT/"fresh_baseline_audit.json").write_text(json.dumps(payload,indent=2))
print(json.dumps(payload,indent=2))
