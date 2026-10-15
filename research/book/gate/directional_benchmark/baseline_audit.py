"""Cash-start short-horizon audit of exact registered original-engine caches."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd,yaml
HERE=Path(__file__).parent;PROJECT=Path("/home/ubuntu/test/MiniMax")
OUT=PROJECT/"results/book/20261015-directional-benchmark-v1"
def main():
    cfg=yaml.safe_load((HERE/"config.yaml").read_text());records=[];inputs={}
    for model,key in [(cfg["main_model"],cfg["main_model_registry_run"]),(cfg["reference_model"],cfg["reference_registry_run"])]:
        base=PROJECT/"results/scoring/cache"/model/key
        windows=pd.read_parquet(str(base)+".windows.parquet")
        data=np.load(str(base)+".arrays.npz");E=data["equity"];G=data["gross"]
        assert len(windows)==len(E)
        inputs[model]={Path(str(base)+suffix).name:hashlib.sha256(Path(str(base)+suffix).read_bytes()).hexdigest() for suffix in [".windows.parquet",".arrays.npz",".json"]}
        meta=json.loads(Path(str(base)+".json").read_text())
        for hours in [1,10,24,50,68,336]:
            # Explicit terminal fee/spread proxy; ordinary cache E is marked, not liquidated.
            net=E[:,hours]/E[:,0]*(1-.001*G[:,hours])-1
            dd=(1-E[:,:hours+1]/np.maximum.accumulate(E[:,:hours+1],axis=1)).max(1)
            for split,mask in [("all_spent",np.ones(len(E),bool)),("2025_onward_spent",windows.index>=pd.Timestamp("2025-01-01",tz="UTC")),("2026_recent_spent",windows.index>=pd.Timestamp("2026-01-01",tz="UTC"))]:
                r=net[mask];starts=windows.index[mask];dis=[];last=None
                for i,t in enumerate(starts):
                    if last is None or t>=last+pd.Timedelta(hours=hours):dis.append(i);last=t
                records.append({"model":model,"run_key":key,"source_commit":meta.get("git",{}).get("commit"),"split":split,"hours":hours,
                  "windows":len(r),"disjoint_windows":len(dis),"mean_return":float(np.mean(r)),"median_return":float(np.median(r)),
                  "p_positive":float(np.mean(r>0)),"worst10_mean":float(np.sort(r)[:max(1,int(np.ceil(.1*len(r))))].mean()),
                  "worst_return":float(np.min(r)),"max_drawdown":float(dd[mask].max()),
                  "disjoint_mean_return":float(r[dis].mean()),"disjoint_p_positive":float(np.mean(r[dis]>0)),
                  "max_marked_gross":float(G[mask,:hours+1].max()),"actual_current_market_forecast":False,"maker_fills_tested":False})
    table=pd.DataFrame(records);table.to_csv(OUT/"registered_baseline_audit.csv",index=False)
    (OUT/"registered_baseline_inputs.json").write_text(json.dumps(inputs,indent=2))
    print(table[(table.hours==50)&(table.split=="2025_onward_spent")].to_string(index=False))
if __name__=="__main__":main()
