"""Cost sensitivity through actual unchanged Simulator replay; no publication."""
from __future__ import annotations
import argparse,dataclasses,glob,hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np,pandas as pd,yaml
CFG=yaml.safe_load((Path(__file__).parent/"config.yaml").read_text())
sys.path.insert(0,CFG["source_worktree"])
from backtest.data import Market,load_market
from backtest.engine import Costs,Simulator
from backtest.evaluate import holdout_start
from backtest.scoring.evaluate import first_decisions,run_key
from backtest.scoring.windows import scored_starts
from src.config import load_config,resolve
from src.models import get

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for x in iter(lambda:f.read(1024*1024),b""):h.update(x)
 return h.hexdigest()

def scaled_market(market,multiplier):
 return dataclasses.replace(market,half_spread=market.half_spread.copy()*multiplier)

def replay_costs(market,targets,start,hours,band,costs,lag,anchor,guard,keep_alive,guard_utc,first):
 extra=sorted({c for w in first.decisions for c in w.index}) if first is not None else ()
 sim=Simulator(market,targets,band,costs,lag,anchor,guard,keep_alive,guard_utc_day=guard_utc,extra_cols=extra)
 i0=sim.index.get_loc(start)
 f=None if first is None else (np.array([sim.index.get_loc(t) for t in first.times]),sim.rows(first.decisions),
       sim.index.get_loc(first.until) if first.until is not None else i0+hours+1)
 result=sim.run(i0,hours,trace=True,first=f)
 w=result.trace["w_end"].copy()
 assert np.isclose(abs(w).sum(),result.trace["gross"][-1],rtol=0,atol=CFG["relative_tolerance"])
 # Actual terminal close in this simulator's cost model, from its final positions.
 zero,close_turnover,close_cost,close_orders=sim._trade(w,np.zeros_like(w),exact=True)
 assert not zero.any()
 fee_e0=spread_e0=0.
 for hour,kind,before,after,eq_before,cost in result.trace["trades"]:
  long=float(np.abs(np.maximum(after,0)-np.maximum(before,0)).sum())
  short=float(np.abs(np.minimum(after,0)-np.minimum(before,0)).sum())
  fee_e0+=(long*costs.taker+short*costs.short)*eq_before
  spread_e0+=float(np.abs(after-before)@sim.half)*eq_before
 terminal_fee=float(np.maximum(w,0).sum()*costs.taker+np.maximum(-w,0).sum()*costs.short)
 terminal_spread=float(abs(w)@sim.half)
 assert np.isclose(terminal_fee+terminal_spread,close_cost,rtol=0,atol=CFG["relative_tolerance"])
 return dict(mark_return=float(result.equity[-1]-1),liquidated_return=float(result.equity[-1]*(1-close_cost)-1),
             turnover=result.turnover,turnover_including_liquidation=result.turnover+close_turnover,
             fees_e0=fee_e0+terminal_fee*result.equity[-1],
             spreads_e0=spread_e0+terminal_spread*result.equity[-1],
             active_days=result.active_days,max_gross_after_trade=result.max_gross,
             terminal_gross=float(abs(w).sum()),equity=result.equity)

def verify_sources(cfg):
 root=Path(CFG["source_worktree"])
 def old(commit,path):
  return subprocess.check_output(["git","-C",str(root),"show",commit+":"+path])
 helper="src/models/book/_short_study.py"
 if (root/helper).read_bytes()!=old(CFG["frozen_model_commit"],helper):
  raise ValueError("frozen helper changed")
 original=yaml.safe_load(old(CFG["frozen_model_commit"],"config.yaml"))
 for model in CFG["models"]:
  if cfg["models"][model]!=original["models"][model]:raise ValueError("frozen parameters changed")
  p="src/models/book/"+model+".py"
  if (root/p).read_bytes()!=old(CFG["wrapper_identity_commit"],p):raise ValueError("wrapper identity changed")
 paths=[root/"config.yaml",root/helper,root/"backtest/engine.py",root/"backtest/data.py",
        root/"backtest/scoring/evaluate.py",root/"backtest/scoring/windows.py",root/"src/contracts.py"]
 paths+=[root/"src/models/book"/(n+".py") for n in CFG["models"]]
 panel=resolve(cfg["harness"]["panel_dir"])
 paths+=[panel/x for x in ("panel_close_1h.parquet","panel_quote_volume_1h.parquet","universe.parquet","panel_notes.json")]
 spread=sorted(glob.glob(str(resolve(cfg["harness"]["spreads_snapshot_glob"]))))
 if spread:paths.append(Path(spread[-1]))
 return {str(p):sha(p) for p in paths}

def summarize(out):
 chunks=[]
 for name in CFG["models"]:
  path=out/("paired_windows."+name+".csv")
  if not path.exists():raise ValueError("not all frozen models completed")
  chunks.append(pd.read_csv(path))
 frame=pd.concat(chunks,ignore_index=True)
 dates=None
 for name,g in frame.groupby("model",sort=False):
  ix=pd.DatetimeIndex(pd.to_datetime(g.start,utc=True))
  if dates is None:dates=ix
  elif not dates.equals(ix):raise ValueError("paired model cases differ")
 rows=[]
 for name,g in frame.groupby("model",sort=False):
  for scenario in ("original","doubled"):
   z=g[scenario+"_liquidated_return"].to_numpy()
   rows.append(dict(model=name,scenario=scenario,n=len(z),mean=float(z.mean()),median=float(np.median(z)),
                    p10=float(np.quantile(z,CFG["quantile"])),worst=float(z.min()),
                    mean_turnover=float(g[scenario+"_turnover_including_liquidation"].mean()),
                    mean_fees_e0=float(g[scenario+"_fees_e0"].mean()),mean_spreads_e0=float(g[scenario+"_spreads_e0"].mean()),
                    mean_mark_return=float(g[scenario+"_mark_return"].mean())))
 summary=pd.DataFrame(rows);summary.to_csv(out/"summary.csv",index=False)
 paired=[]
 for name,g in frame.groupby("model",sort=False):
  d=g.doubled_liquidated_return-g.original_liquidated_return
  paired.append(dict(model=name,n=len(g),mean_delta=float(d.mean()),median_delta=float(d.median()),
                     p10_delta=float(d.quantile(CFG["quantile"])),worst_delta=float(d.min()),
                     stress_lower_fraction=float((d<0).mean())))
 pd.DataFrame(paired).to_csv(out/"paired_deltas.csv",index=False)
 print(summary.to_string(index=False))

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--model",choices=CFG["models"]);ap.add_argument("--summarize",action="store_true");args=ap.parse_args()
 out=Path(CFG["output"]);out.mkdir(parents=True,exist_ok=True)
 if args.summarize:summarize(out);return
 if args.model is None:raise ValueError("choose exactly one frozen model per replay process")
 cfg=load_config();before=verify_sources(cfg);model=get(args.model);market=load_market(cfg);h=cfg["harness"]
 starts=pd.date_range(CFG["window_first"],periods=CFG["window_count"],freq=str(CFG["window_spacing_days"])+"D")
 hours=int(CFG["horizon_hours"])
 if (starts[-1]+pd.Timedelta(hours=hours))>holdout_start(cfg):raise ValueError("cost cases reach sealed period")
 if not starts.isin(market.close.index).all():raise ValueError("fixed case lacks original market bar")
 pool=scored_starts(market,cfg);params=cfg["models"][args.model];key=run_key(model,params,False,pool,cfg,market)
 base=resolve(cfg["scoring"]["cache_dir"])/args.model/key
 files={suffix:Path(str(base)+"."+suffix) for suffix in ("json","targets.parquet","windows.parquet","arrays.npz")}
 missing=[str(p) for p in files.values() if not p.exists()]
 if missing:raise ValueError("original v2 cache not yet complete: "+json.dumps(missing))
 cached_before={str(p):sha(p) for p in files.values()}
 meta=json.loads(files["json"].read_text())
 if meta["key"]!=key or meta["model"]!=args.model or meta["long_only"]:raise ValueError("cached model identity differs")
 original_starts=pd.read_parquet(files["windows.parquet"]).index
 if not original_starts.equals(pool):raise ValueError("cache case grid differs from original scorer")
 ix=original_starts.get_indexer(starts)
 if (ix<0).any():raise ValueError("fixed cases absent in original cache")
 targets=pd.read_parquet(files["targets.parquet"])
 if not targets.index.is_unique or not targets.index.is_monotonic_increasing or str(targets.index.tz)!="UTC":
  raise ValueError("invalid cached decision clock")
 # Restore original nonzero decision order (model parameter coin order).
 shared=[r.reindex(params["coins"]).dropna().loc[lambda z:z!=0] for _,r in targets.iterrows()]
 firsts=first_decisions(model,market,starts,targets.index,shared,params,hours)
 with np.load(files["arrays.npz"],allow_pickle=False) as a:
  expected_equity=a["equity"][ix,:hours+1].copy()
 baseline=Costs(h["fees"]["taker"],h["fees"]["short"])
 stress=Costs(baseline.taker*CFG["fee_multiplier"],baseline.short*CFG["fee_multiplier"])
 smarket=scaled_market(market,CFG["half_spread_multiplier"])
 rows=[];curves={}
 for i,t in enumerate(starts):
  pairs={}
  for scenario,m,c in (("original",market,baseline),("doubled",smarket,stress)):
   result=replay_costs(m,targets,t,hours,model.spec.band,c,h["execution_lag_hours"],h["grid_hour_utc"],
                       h["activity_guard_offset_hours"],float(h.get("keep_alive_weight",0)),
                       bool(h.get("guard_utc_day",False)),firsts[t])
   if scenario=="original" and not np.allclose(result["equity"],expected_equity[i],rtol=0,atol=CFG["relative_tolerance"]):
    raise ValueError("original replay differs from original cached cash-start equity")
   curves.setdefault(scenario,[]).append(result.pop("equity"))
   pairs.update({scenario+"_"+k:v for k,v in result.items()})
  rows.append(dict(model=args.model,start=str(t),end=str(t+pd.Timedelta(hours=hours)),**pairs))
  if i%40==0:print(args.model,i+1,"/",len(starts),flush=True)
 after=verify_sources(cfg)
 if before!=after:raise ValueError("source or market input changed during cost replay")
 if cached_before!={str(p):sha(p) for p in files.values()}:raise ValueError("source cache changed during cost replay")
 pd.DataFrame(rows).to_csv(out/("paired_windows."+args.model+".csv"),index=False)
 np.savez_compressed(out/("curves."+args.model+".npz"),**{k:np.stack(v) for k,v in curves.items()})
 manifest=dict(identity=CFG["identity"],model=args.model,run_key=key,original_tool_version=meta["tool_version"],
               frozen_model_commit=CFG["frozen_model_commit"],wrapper_identity_commit=CFG["wrapper_identity_commit"],
               source_worktree=CFG["source_worktree"],source_hashes=before,cache_hashes=cached_before,
               config=CFG,starts=[str(t) for t in starts],baseline_cache_equity_prefix_identical=True,
               parameters_changed=False,terminal_liquidation="Simulator._trade(w_end,zero,exact=True) under each scenario",
               primary_compatible=False,status="separate descriptive cost sensitivity; no ranking publication")
 (out/("manifest."+args.model+".json")).write_text(json.dumps(manifest,indent=2))
 print(json.dumps({"model":args.model,"cases":len(starts),"run_key":key,"baseline_cache_equity_prefix_identical":True}),flush=True)
if __name__=="__main__":main()
