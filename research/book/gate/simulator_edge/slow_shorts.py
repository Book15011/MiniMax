"""Three fixed slower directional shorts; offline hourly execution proxy."""
from pathlib import Path
import hashlib,json,copy,inspect
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
import yaml
from src.contracts import ModelSpec
from src.config import load_config
from backtest.data import load_market
from backtest.scoring.evaluate import simulate
from research.book.gate.simulator_edge.historical import OUT
P=yaml.safe_load(Path(__file__).with_name("short_config.yaml").read_text())
class ShortMomentum:
    def __init__(self,L):
        self.L=L;self.spec=ModelSpec("book_gate_short"+str(L),"trend","book",P["rebalance_hours"],P["band"],True,"Fixed slower short gate proxy")
    def targets(self,v):
        anchor=v.t.floor(str(P["selection_hours"])+"h")
        c=v.close.loc[:anchor].reindex(columns=sorted(v.universe)).iloc[-(self.L+1):]
        if len(c)<=self.L:return pd.Series(dtype=float)
        s=(c.iloc[-1]/c.iloc[0]-1).replace([np.inf,-np.inf],np.nan)
        s=s[(c>0).all(axis=0)&np.isfinite(c).all(axis=0)].dropna().sort_values(kind="stable")
        if s.empty or s.iloc[0]>=0:return pd.Series(dtype=float)
        coin=s.index[0];current=v.close.loc[:v.t,coin].iloc[-1]
        if not np.isfinite(current) or current>c[coin].iloc[-1]*(1+P["squeeze_guard"]):return pd.Series(dtype=float)
        return pd.Series({coin:-float(P["exposure"])})
def job(L):
    cfg=copy.deepcopy(load_config());cfg["harness"]["window_days"]=3;cfg["scoring"]["cache_dir"]=str(OUT/"slow_short_cache")
    mk=load_market(cfg);model=ShortMomentum(L)
    cfg["models"][model.spec.name]={"lookback":L,**P,"source":hashlib.sha256(inspect.getsource(ShortMomentum).encode()).hexdigest()}
    starts=pd.to_datetime(np.load(OUT/"book_e20combo_brk_cash.hourly.npz")["starts"],utc=True)
    run=simulate(model,mk,cfg,starts,use_cache=True);name="slow_short"+str(L)
    np.savez_compressed(OUT/f"{name}.hourly.npz",equity=run.equity,gross=run.gross,starts=starts.asi8)
    records=[]
    for h in [68,72]:
        ret=run.equity[:,h]/run.equity[:,0]*(1-cfg["scoring"]["liquidation_cost"]*run.gross[:,h])-1
        dd=-(run.equity[:,:h+1]/np.maximum.accumulate(run.equity[:,:h+1],axis=1)-1).min(1)
        records.extend({"model":name,"start":t,"hours":h,"return":float(r),"mdd":float(d)} for t,r,d in zip(starts,ret,dd))
    pd.DataFrame(records).to_parquet(OUT/f"{name}.hourly.parquet",index=False)
    (OUT/f"{name}.hourly.json").write_text(json.dumps({"model":name,"run_key":run.key,"cache_model":model.spec.name,
      "max_marked_gross":float(run.gross.max()),"executed_order_rows":len(run.trades),
      "fees_total_usd":float(run.trades.fee_usd.sum()),"spread_total_usd":float(run.trades.spread_usd.sum()),
      "actual_roostoo_execution":False,"production_eligible":False},indent=2))
    print("DONE",name,len(starts),flush=True)
def main():
    with ProcessPoolExecutor(max_workers=2) as pool:list(pool.map(job,P["lookbacks"]))
    (OUT/"slow_short_complete.json").write_text(json.dumps({"status":"PASS","new_models":3,"total_family":26,
      "adaptive_research_not_fresh":True},indent=2))
if __name__=="__main__":main()
