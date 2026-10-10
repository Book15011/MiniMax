"""Normal --score2 publication followed by shared-broker short episode diagnostics."""
from pathlib import Path
import argparse,hashlib,json,sys,subprocess
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np,pandas as pd,yaml
from src.config import load_config,resolve,universe,binance_symbol
from src.models import get
from backtest.data import load_market,Market
from backtest.engine import decide
from src.live.runner import live_universe,day_start
from research.book.price_trend.engine import replay,independent_audit
from src.validation.short_competition import summarize
from research.book.short_exhaustion.cutoff import executable_targets
from research.book.intraday_short import run as minute_metrics
ROOT=Path("/home/ubuntu/test/MiniMax")
STUDY=yaml.safe_load(Path("research/book/short_exhaustion/config.yaml").read_text());OUT=Path(STUDY["output"])
OLD=ROOT/"results/book/20261010-intraday-short-v2"
NAMES=tuple(STUDY["models"])
CFG={};DATA={};MARKET=None;PREFIX=None;RULES={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def case_job(item):
 key,start,prefix=item;t0=pd.Timestamp(start);hours=STUDY["prefix_hours"] if prefix else max(STUDY["horizons"]);end=t0+pd.Timedelta(hours=hours)
 prices=pd.DataFrame({s:z.loc[t0:end,"close"] for s,z in DATA.items()})
 expected=pd.date_range(t0,end,freq="min")
 if not prices.index.equals(expected) or prices.isna().any().any():raise ValueError("Incomplete minute case")
 market=PREFIX if prefix else MARKET
 alltimes=pd.date_range(t0,end,freq="h")
 dest=OUT/"cases"/key;dest.mkdir(parents=True,exist_ok=True);rows=[];audits=[]
 endpoints=[STUDY["prefix_hours"]] if prefix else STUDY["horizons"]
 for name in NAMES:
  model=get(name);pars=CFG["models"][name];prev=pd.Series(dtype=float);weights={}
  for t in alltimes:
   if t!=t0 and (t.hour-16)%model.spec.rebalance_hours:continue
   w=decide(model,market,t,pars,prev);weights[t]=w;prev=w
  (dest/(name+".targets.json")).write_text(json.dumps({str(t):w.to_dict() for t,w in weights.items()}))
  for scenario,cost in STUDY["costs"].items():
   for n in endpoints:
    stop=t0+pd.Timedelta(hours=n)
    c={"assets":["BTC","ETH","BNB","XRP"],"seed":STUDY["replay"]["seed"],"fee":cost["fee"],
      "proxy_half_spread":cost["halfspread"],"quote_max_age":STUDY["replay"]["quote_max_age"],"minute_max_age":STUDY["replay"]["minute_max_age"],
      "precisions":{a:RULES[a+"/USD"]["AmountPrecision"] for a in ("BTC","ETH","BNB","XRP")},
      "price_precisions":{a:RULES[a+"/USD"]["PricePrecision"] for a in ("BTC","ETH","BNB","XRP")},
      "min_order":STUDY["replay"]["min_order"],"cash_buffer":STUDY["replay"]["cash_buffer"],"band":model.spec.band,"order_spacing_seconds":STUDY["replay"]["order_spacing_seconds"],
      "start":str(t0),"end":str(stop)}
    ev,path,dec,fail,cycles,ep=replay(executable_targets(weights,stop,cost["lag_minutes"]),prices.loc[:stop],c,cost["lag_minutes"])
    if fail:raise ValueError("Shared broker replay failures: "+str(fail[:2]))
    audit=independent_audit(ev,path,prices.loc[:stop],c,ep)
    stem=name+"-"+scenario+"-"+str(n)
    ev.to_csv(dest/(stem+".events.csv"),index=False);pd.DataFrame(cycles).to_csv(dest/(stem+".cycles.csv"),index=False)
    path.to_parquet(dest/(stem+".path.parquet"),index=False)
    (dest/(stem+".endpoint.json")).write_text(json.dumps(ep,indent=2))
    p=path.copy();p.loc[p.index[-1],"equity"]=ep["full_cost_liquidated_equity"]
    basic=summarize(name,ev,p,cycles,ep,c)
    closed=[z for z in cycles if z["status"]=="completed"]
    raw=path.loc[pd.to_datetime(path.time_utc).dt.second==0,"equity"].to_numpy().copy();raw[-1]=ep["full_cost_liquidated_equity"]
    basic.update(minute_metrics.score_risk(raw,t0))
    basic.update(case=key,start=str(t0),prefix=prefix,scenario=scenario,hours=n,
      mean=basic["full_cost_liquidated_return"],return_=basic["full_cost_liquidated_return"],
      completed=len(closed),wins=sum(z["profitable"] for z in closed),censored=sum(z["status"]=="censored" for z in cycles),
      net_short_usd=float(sum((r.quantity*r.price_usd if r.action=="Open Short" else -r.quantity*r.price_usd)-r.fee for r in ev.itertuples() if r.action in ("Open Short","Cover Short"))),
      retrospective=True,no_activity_guard=True)
    basic["return"]=basic.pop("return_")
    rows.append(basic);audits.append({"case":key,"model":name,"scenario":scenario,"hours":n,**audit})
 return rows,audits
def evaluate():
 global CFG,DATA,MARKET,PREFIX,RULES
 if (OUT/"evaluation_manifest.json").exists():raise ValueError("Preserve existing evaluation")
 CFG=load_config();minute_metrics.SC=CFG["scoring"];MARKET=load_market(CFG)
 m=json.loads((OLD/"data_manifest.json").read_text());files=[]
 for s,z in m["datasets"].items():
  p=Path(z["path"])
  if sha(p)!=z["sha256"]:raise ValueError("Minute data changed")
  DATA[s]=pd.read_parquet(p);files.append(p)
 prefixroot=ROOT/"results/book/20261010-short-next-prefix-v3"
 pm=json.loads((prefixroot/"data_manifest.json").read_text())
 for n,z in pm["files"].items():
  if sha(prefixroot/n)!=z["sha256"]:raise ValueError("Prefix data changed")
  files.append(prefixroot/n)
 hc=pd.read_parquet(prefixroot/"hourly_close.parquet");qv=pd.read_parquet(prefixroot/"hourly_qv.parquet")
 allowed={binance_symbol(x) for x in universe(CFG)}
 grids=pd.date_range(day_start(pd.Timestamp("2026-10-04T12:00Z"),16),pd.Timestamp("2026-10-09T00:00Z"),freq="24h")
 uni=pd.Series({t:live_universe(hc,qv,t,CFG["validation"],allowed) for t in grids})
 PREFIX=Market(hc,qv,uni,pd.Series(.0005,index=hc.columns))
 rules=ROOT/"results/book/20261010-short-next-prefix-v3/exchange_info.json";RULES=json.loads(rules.read_text())["TradePairs"];files.append(rules)
 panel=resolve(CFG["harness"]["panel_dir"])
 files += [panel/n for n in ("panel_close_1h.parquet","panel_quote_volume_1h.parquet","universe.parquet")]
 files += [Path("config.yaml"),Path(__file__),Path("research/book/price_trend/engine.py"),Path("research/book/short_exhaustion/PROTOCOL.md"),Path("research/book/short_exhaustion/config.yaml"),
  Path("src/models/book/_bear_selective.py"),Path("src/models/book/_short_exhaustion.py"),Path("research/book/short_exhaustion/score.py"),Path("research/book/short_exhaustion/run_batch.py"),Path("research/book/short_exhaustion/test_model.py"),Path("research/book/short_exhaustion/original_config_semantics.json"),Path("research/book/short_exhaustion/cutoff.py"),Path("research/book/bear_selective/test_cutoff.py"),OLD/"data_manifest.json",OLD/"independent_data_audit.json",OLD/"cases.parquet",
  Path("src/validation/short_competition.py"),Path("src/execution/planner.py"),Path("src/execution/paper.py")]
 files += [Path("src/models/book")/(n+".py") for n in NAMES]
 before={str(p.resolve()):sha(p) for p in files};(OUT/"evaluation_before.json").write_text(json.dumps(before,indent=2))
 cases=pd.read_parquet(OLD/"cases.parquet");cases.to_parquet(OUT/"cases.parquet")
 items=[(t.strftime("%Y%m%dT%H%M"),str(t),False) for t in cases.index]+[("prefix","2026-10-04T12:00Z",True)]
 rows=[];audits=[];errors=[]
 with ProcessPoolExecutor(max_workers=STUDY["workers"]) as pool:
  futures={pool.submit(case_job,item):item for item in items}
  for f in as_completed(futures):
   try:r,a=f.result();rows+=r;audits+=a
   except Exception as e:errors.append({"case":futures[f],"error":repr(e)})
   pd.DataFrame(rows).to_csv(OUT/"window_results.partial.csv",index=False)
   (OUT/"evaluation_progress.json").write_text(json.dumps({"ledgers":len(audits),"failures":errors},indent=2))
   print("ledgers",len(audits),"failures",len(errors),flush=True)
 if errors:raise ValueError("Failures preserved; no complete ranking")
 after={str(p.resolve()):sha(p) for p in files};(OUT/"evaluation_after.json").write_text(json.dumps(after,indent=2))
 if after!=before:raise ValueError("Frozen inputs changed")
 pd.DataFrame(rows).to_csv(OUT/"window_results.csv",index=False)
 (OUT/"independent_execution_audit.json").write_text(json.dumps({"status":"PASS","ledgers":len(audits),"maximum_error":max(z["max_equity_error_usd"] for z in audits),"audits":audits},indent=2))
 (OUT/"evaluation_manifest.json").write_text(json.dumps({"status":"PASS","models":NAMES,"cases":len(items),"frozen_hashes":before,"window_results_sha256":sha(OUT/"window_results.csv"),"no_activity_guard":True,"all_history_spent":True},indent=2))
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--score",required=True,action="store_true");ap.parse_args()
 OUT.mkdir(exist_ok=True,parents=True)
 if (OUT/"status.json").exists():raise ValueError("Preserve previous batch")
 status=[]
 jobs=[("full_pytest",[sys.executable,"-B","-m","pytest","-q"])]
 jobs += [(n,[sys.executable,"-B","-m","backtest.run","--model",n,"--score2"]) for n in NAMES]
 for name,args in jobs:
  with (OUT/(name+".log")).open("w") as f:code=subprocess.call(args,stdout=f,stderr=subprocess.STDOUT)
  status.append({"job":name,"returncode":code});(OUT/"status.json").write_text(json.dumps(status,indent=2))
  print(name,code,flush=True)
  if code:raise SystemExit(code)
 evaluate()
 code=subprocess.call([sys.executable,"-B","-m","research.book.short_exhaustion.score","--score"])
 if code:raise SystemExit(code)
if __name__=="__main__":main()
