"""Exact inherited hourly Simulator; small fixed benchmark family, no API calls."""
from pathlib import Path
from dataclasses import replace
from concurrent.futures import ProcessPoolExecutor
import hashlib,json,copy,inspect
import numpy as np
import pandas as pd
import yaml
from src.config import load_config
from src.contracts import ModelSpec
from src.models import get
from backtest.data import load_market
from backtest.scoring.evaluate import simulate
from backtest.engine import Simulator,Costs
ROOT=Path(__file__).resolve().parents[4];MAIN=ROOT.parents[1]
OUT=MAIN/"results/book/20261015-simulator-edge-v1"
P=yaml.safe_load((Path(__file__).with_name("config.yaml")).read_text())["historical"]
NAMES=["book_e20combo_brk_cash","mom24_4h","mom72_4h","mom168_4h","mom24_24h","break24_trail4_hold24"]
class Momentum:
    def __init__(self,name,lookback,every):
        self.name=name;self.L=lookback
        self.spec=ModelSpec("book_gate_"+name,"momentum","book",every,float(P["research_band"]),False,"Fixed concentrated gate benchmark")
    def targets(self,v):
        c=v.close.loc[:v.t].reindex(columns=sorted(v.universe)).iloc[-(self.L+1):]
        if len(c)<=self.L:return pd.Series(dtype=float)
        s=(c.iloc[-1]/c.iloc[0]-1).replace([np.inf,-np.inf],np.nan)
        s=s[(c>0).all(axis=0)&np.isfinite(c).all(axis=0)].dropna().sort_values(ascending=False,kind="stable")
        return pd.Series({s.index[0]:float(P["exposure"])}) if len(s) else pd.Series(dtype=float)
def job(name):
    cfg=load_config();cfg=copy.deepcopy(cfg);cfg["harness"]["window_days"]=3
    cfg["scoring"]["cache_dir"]=str(OUT/"hourly_cache")
    mk=load_market(cfg)
    end=min(pd.Timestamp(P["end"],tz="UTC"),mk.close.index[-1])
    starts=pd.date_range(pd.Timestamp(P["start"],tz="UTC")+pd.Timedelta(hours=16),end-pd.Timedelta(hours=72),freq="D")
    if name!="break24_trail4_hold24":
        if name==NAMES[0]:model=get(name)
        else:
            z=next(x for x in P["momentum"] if x["name"]==name);L,R=z["lookback"],z["every"]
            model=Momentum(name,L,R);cfg["models"][model.spec.name]={"lookback_hours":L,"exposure":P["exposure"],"rebalance_hours":R,"research_source_sha256":hashlib.sha256(inspect.getsource(Momentum).encode()).hexdigest()}
        run=simulate(model,mk,cfg,starts,use_cache=True)
        E,G=run.equity,run.gross
        tr=run.trades
        meta={"source":"inherited_hourly_simulator","run_key":run.key,"model":name,"actual_roostoo_execution":False,
              "fees_total_usd":float(tr.fee_usd.sum()),"spread_total_usd":float(tr.spread_usd.sum()),
              "executed_order_rows":len(tr),"mean_order_rows_per_window":len(tr)/len(starts),
              "max_marked_gross":float(G.max()),"signed_baseline":name==NAMES[0],"starts":len(starts)}
    else:
        # A window starts flat, so its entry/peak/age chain starts here, not in shared history.
        cols=list(mk.close.columns);idx=mk.close.index
        C=mk.close.to_numpy();V=mk.quote_volume.reindex_like(mk.close)
        hi=mk.close.shift(1).rolling(P["breakout_lookback"],min_periods=P["breakout_lookback"]).max().to_numpy()
        v24=V.rolling(24,min_periods=24).sum().to_numpy();v7=(V.rolling(168,min_periods=168).sum()/7).to_numpy()
        U=np.zeros(C.shape,dtype=bool);pos=mk.universe_by_day.index.searchsorted(idx,side="right")-1;lookup={c:i for i,c in enumerate(cols)}
        for i,k in enumerate(pos):
            if k>=0:
                for c in mk.universe_by_day.iloc[k]:
                    if c in lookup:U[i,lookup[c]]=True
        sig=U&(C>hi)&(v24>v7)&np.isfinite(C)
        strength=np.where(sig,C/hi-1,-np.inf)
        dummy=pd.DataFrame(0.,index=pd.date_range(idx[0],idx[-1],freq="h"),columns=cols)
        sim=Simulator(mk,dummy,float(P["research_band"]),Costs(cfg["harness"]["fees"]["taker"],cfg["harness"]["fees"]["short"]),
                      cfg["harness"]["execution_lag_hours"],16,cfg["harness"]["activity_guard_offset_hours"],
                      cfg["harness"]["keep_alive_weight"],guard_utc_day=cfg["harness"]["guard_utc_day"],extra_cols=cols)
        E=np.zeros((len(starts),73));G=np.zeros_like(E);fees=spread=orders=0.
        for n,t in enumerate(starts):
            i0=idx.get_loc(t);rows=np.zeros((73,len(cols)));held=None;entry=0;peak=0.
            for h in range(73):
                i=i0+h
                if held is not None:
                    peak=max(peak,C[i,held])
                    if C[i,held]<=peak*(1-P["breakout_trail"]) or h-entry>=P["breakout_hold"] or not U[i,held]:held=None
                if held is None and np.isfinite(strength[i]).any():
                    held=int(np.argmax(strength[i]));entry=h;peak=C[i,held]
                if held is not None:rows[h,held]=P["exposure"]
            res=sim.run(sim.index.get_loc(t),72,trace=True,first=(np.arange(sim.index.get_loc(t),sim.index.get_loc(t)+73),rows,sim.index.get_loc(t)+73))
            E[n]=res.equity;G[n]=res.trace["gross"]
            for h,kind,w0,w1,eq,cost in res.trace["trades"]:
                delta=np.abs(w1-w0);fees+=float(delta.sum())*cfg["harness"]["fees"]["taker"]*eq*cfg["scoring"]["e0"]
                spread+=float(delta@sim.half)*eq*cfg["scoring"]["e0"];orders+=int((delta>1e-12).sum())
        meta={"source":"inherited_simulator_cash_start_breakout","model":name,"actual_roostoo_execution":False,
              "fees_total_usd":fees,"spread_total_usd":spread,"executed_order_rows":orders,
              "mean_order_rows_per_window":orders/len(starts),"max_marked_gross":float(G.max()),"starts":len(starts)}
    np.savez_compressed(OUT/f"{name}.hourly.npz",equity=E,gross=G,starts=starts.asi8)
    (OUT/f"{name}.hourly.json").write_text(json.dumps(meta,indent=2))
    records=[]
    for h in P["horizons"]:
        ret=E[:,h]/E[:,0]*(1-cfg["scoring"]["liquidation_cost"]*G[:,h])-1
        dd=-(E[:,:h+1]/np.maximum.accumulate(E[:,:h+1],axis=1)-1).min(1)
        records.extend({"model":name,"start":t,"hours":h,"return":float(r),"mdd":float(d)} for t,r,d in zip(starts,ret,dd))
    pd.DataFrame(records).to_parquet(OUT/f"{name}.hourly.parquet",index=False)
    print("DONE",name,len(starts),flush=True)
def main():
    with ProcessPoolExecutor(max_workers=2) as pool:list(pool.map(job,NAMES))
    frames=pd.concat([pd.read_parquet(OUT/f"{n}.hourly.parquet") for n in NAMES],ignore_index=True)
    rows=[]
    for (name,h),g in frames.groupby(["model","hours"]):
        for split,mask in [("calibration",g.start<pd.Timestamp(P["split"],tz="UTC")),
                           ("spent_historical_check",g.start>=pd.Timestamp(P["split"],tz="UTC"))]:
            f=g[mask].copy()
            if split=="calibration":f=f[f.start+pd.Timedelta(hours=int(h))<pd.Timestamp(P["split"],tz="UTC")]
            f["quarter"]=f.start.dt.tz_localize(None).dt.to_period("Q").astype(str)
            dis=f.iloc[::3]
            row={"candidate":name,"source":"hourly_proxy","split":split,"hours":int(h),"n_windows":len(f),
                 "n_disjoint_approx":len(dis),"median_return":f["return"].median(),"worst_return":f["return"].min(),
                 "mean_return":f["return"].mean(),"max_drawdown":f.mdd.max(),"p_loss10":(f["return"]<=-.1).mean(),
                 "p_loss20":(f["return"]<=-.2).mean(),"p19":(f["return"]>=.19).mean(),
                 "p215":(f["return"]>=.215).mean(),"p25":(f["return"]>=.25).mean(),
                 "actual_roostoo_execution":False,"top20_probability":None,"production_eligible":False}
            # Quarter cluster bootstrap, conditional family23; not project-wide or fresh.
            agg=f.assign(hit=f["return"]>=.19).groupby("quarter").agg(hits=("hit","sum"),n=("hit","size"))
            rng=np.random.default_rng(P["seed"]);draw=rng.integers(0,len(agg),(P["bootstrap_draws"],len(agg)))
            prob=agg.hits.to_numpy()[draw].sum(1)/agg.n.to_numpy()[draw].sum(1)
            row.update(p19_cluster_lower=float(np.quantile(prob,.05/P["family"])),
                       p19_cluster_upper=float(np.quantile(prob,1-.05/P["family"])),quarters=len(agg))
            rows.append(row)
    pd.DataFrame(rows).to_csv(OUT/"hourly_summary.csv",index=False)
    (OUT/"historical_complete.json").write_text(json.dumps({"status":"PASS","models":len(NAMES),"proxy_only":True},indent=2))
if __name__=="__main__":main()
