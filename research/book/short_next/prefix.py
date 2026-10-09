"""Fixed-prefix broad-universe comparison, using existing causal/planner helpers."""
from __future__ import annotations
import argparse,hashlib,io,json,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
import yaml
from backtest.data import Market
from backtest.engine import decide
from backtest.evaluate import model_modules
from src.config import load_config,universe,binance_symbol
from src.live.runner import live_universe,day_start
from src.models import get
from src.data.binance_downloader import Task,http_get,parse_checksum
from src.data.loader import read_kline_zip
from src.validation.short_competition import QuoteBook,replay_targets,summarize,observed_path

ROOT=Path("/home/ubuntu/test/MiniMax")
OUT=ROOT/"results/book/20261009-short-next"
NAMES=("baitoey_ovl_brk_dual","book_cashshort_confirm","book_cashshort_pullback")
BASE_KEY="f30fa79cde92399a"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify():
 m=json.loads((OUT/"data_manifest.json").read_text())
 for n,r in m["files"].items():
  if sha(OUT/n)!=r["sha256"]:raise ValueError("Frozen input changed: "+n)
 return m

def prepare():
 manifest=verify();cfg=load_config()
 if (OUT/"prefix_plan.json").exists():raise ValueError("Prefix target plan already frozen")
 close=pd.read_parquet(OUT/"hourly_close.parquet")
 qv=pd.read_parquet(OUT/"hourly_qv.parquet")
 start=pd.Timestamp(manifest["start"]);end=pd.Timestamp(manifest["end"])
 allowed={binance_symbol(x) for x in universe(cfg)}
 grids=pd.date_range(day_start(start,16),end.floor("h"),freq="24h")
 unis={t:live_universe(close,qv,t,cfg["validation"],allowed) for t in grids}
 market=Market(close,qv,pd.Series(unis),pd.Series(.0001,index=close.columns))
 baseline=next((ROOT/"results/scoring/score2/603da2948b68ee0f5c8a/baitoey_ovl_brk_dual").glob(BASE_KEY+"-*/score.json"))
 base_params=json.loads(baseline.read_text())["model"]["params"]
 times=sorted({start}|{t for t in grids if t>=start})
 plans={};assets={"BNB","BTC","ETH","SOL","XRP"}
 for name in NAMES:
  model=get(name);params=base_params if name==NAMES[0] else cfg["models"][name]
  prev=pd.Series(dtype=float);rows={}
  for t in times:
   w=decide(model,market,t,params,prev);prev=w
   rows[str(t)]={s:float(v) for s,v in w.items()}
   assets.update(s.removesuffix("USDT") for s in w.index)
  modules={str(Path(sys.modules[m].__file__).resolve()):sha(sys.modules[m].__file__) for m in model_modules(model)}
  # Legacy dynamic baseline omits INNER; pin the full known long dependency set explicitly.
  for rel in ["src/models/baitoey/_overlays.py","src/models/baitoey/baitoey_ovl_brk_dual.py","src/models/baitoey/baitoey_vt_dual.py","src/models/baitoey/baitoey_vt_mom.py","src/models/baitoey/_volume_signals.py","src/models/baselines/team_rot_ew.py"]:
   p=Path(rel).resolve();modules[str(p)]=sha(p)
  plans[name]={"params":params,"spec":model.spec.__dict__,"source_hashes":modules,"targets":rows}
 plan={"start":str(start),"end":str(end),"assets":sorted(assets),"seed":100000.0,"models":plans,
       "universe":{str(t):u for t,u in unis.items()},"baseline_score_sha256":sha(baseline),
       "data_manifest_sha256":sha(OUT/"data_manifest.json"),
       "warning":"Descriptive spent-data prefix; first cash-start12UTC then16UTC daily,1h lag; no activity guard"}
 (OUT/"prefix_plan.json").write_text(json.dumps(plan,indent=2))
 print(json.dumps({"assets":plan["assets"],"decisions":len(times),"targets":{n:x["targets"] for n,x in plans.items()}},indent=2),flush=True)

def fetch():
 verify();plan=json.loads((OUT/"prefix_plan.json").read_text())
 if (OUT/"fine_data_manifest.json").exists():raise ValueError("Fine data already frozen")
 old=json.loads((ROOT/"results/book/20261009-short-competition/data_manifest.json").read_text())
 oldmap={(x["symbol"],x["day"]):x for x in old["archives"]}
 prior=ROOT/"results/book/20261009-short-next/prefix_archive_receipt.json"
 if prior.exists():oldmap.update({(x["symbol"],x["day"]):x for x in json.loads(prior.read_text())})
 tasks=[Task("spot","klines",a+"USDT","daily",str(d.date()),"1m")
        for a in plan["assets"] for d in pd.date_range("2026-10-04","2026-10-08")]
 def download(t):
  prior=oldmap.get((t.symbol,t.period))
  if prior:
   p=Path(prior["path"])
   if sha(p)!=prior["sha256"]:raise ValueError("Old verified archive changed")
   return {**prior,"path":str(p)}
  p=OUT/"raw"/t.symbol/t.filename;p.parent.mkdir(parents=True,exist_ok=True)
  url=t.url("https://data.binance.vision/data")
  expected,filename=parse_checksum(http_get(url+".CHECKSUM").text)
  if filename!=t.filename:raise ValueError("Wrong checksum filename")
  raw=p.read_bytes() if p.exists() else http_get(url).content
  if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError("Bad archive checksum")
  p.write_bytes(raw)
  return {"symbol":t.symbol,"day":t.period,"url":url,"path":str(p),"sha256":expected,"status":"verified"}
 receipt=OUT/"prefix_archive_receipt.json"
 if receipt.exists():
  records=json.loads(receipt.read_text())
  expected={(t.symbol,t.period) for t in tasks}
  if {(r["symbol"],r["day"]) for r in records}!=expected:raise ValueError("Archive receipt task mismatch")
  for r in records:
   if sha(r["path"])!=r["sha256"]:raise ValueError("Archive receipt hash mismatch")
 else:
  with ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(download,tasks))
  receipt.write_text(json.dumps(records,indent=2))
 parts=[]
 for r in records:
  d=read_kline_zip(Path(r["path"]));d["timestamp"]=pd.to_datetime(d.open_time,unit="ms",utc=True)+pd.Timedelta(minutes=1)
  d["symbol"]=r["symbol"];parts.append(d[["timestamp","symbol","close","quote_volume"]])
 minute=pd.concat(parts,ignore_index=True).sort_values(["timestamp","symbol"])
 if minute.duplicated(["timestamp","symbol"]).any():raise ValueError("Duplicate archive minute")
 counts=minute.groupby("symbol").size()
 if not (counts==7200).all():raise ValueError("Incomplete five-day minute archive")
 minute.to_parquet(OUT/"prefix_minutes.parquet",index=False)
 chunks=[];receipts=[];end=pd.Timestamp(plan["end"]);pairs={a+"/USD" for a in plan["assets"]}
 for day in pd.date_range("2026-10-05","2026-10-09"):
  p=ROOT/"results/book/scalp/quotes"/(day.strftime("%Y%m%d")+".csv")
  selected=[]
  for chunk in pd.read_csv(p,chunksize=150000):
   stamp=pd.to_datetime(chunk.ts_utc,utc=True)
   z=chunk[(stamp<=end)&chunk.pair.isin(pairs)].copy()
   if len(z):selected.append(z)
   if stamp.min()>end:break
  x=pd.concat(selected,ignore_index=True) if selected else pd.DataFrame()
  if len(x):chunks.append(x)
  receipts.append({"source":str(p),"selected_rows":len(x),"selected_prefix_sha256":hashlib.sha256(x.to_csv(index=False).encode()).hexdigest(),
                   "note":"Canonical selected prefix receipt; growing source is not claimed immutable"})
 quotes=pd.concat(chunks,ignore_index=True);quotes["ts_utc"]=pd.to_datetime(quotes.ts_utc,utc=True)
 quotes=quotes.sort_values(["ts_utc","pair"])
 duplicates=quotes[quotes.duplicated(["ts_utc","pair"],keep=False)]
 duplicates.to_csv(OUT/"quote_duplicate_evidence.csv",index=False)
 distinct=quotes.drop_duplicates()
 conflict=distinct[distinct.duplicated(["ts_utc","pair"],keep=False)]
 bad_keys=pd.MultiIndex.from_frame(conflict[["ts_utc","pair"]].drop_duplicates())
 raw_bad=pd.MultiIndex.from_frame(quotes[["ts_utc","pair"]]).isin(bad_keys)
 quotes[raw_bad].to_csv(OUT/"quote_quarantined_conflicts.csv",index=False)
 bad=pd.MultiIndex.from_frame(distinct[["ts_utc","pair"]]).isin(bad_keys)
 quote_policy={"rule":"Collapse only identical full rows; quarantine all rows at any conflicting timestamp/pair; use prior unambiguous asof<=30s else unchanged verified minute proxy<=120s",
               "selected_rows":len(quotes),"identical_repetitions_removed":len(quotes)-len(distinct),
               "conflicting_keys_quarantined":len(bad_keys),"conflicting_rows_quarantined":int(raw_bad.sum()),
               "retained_rows":int((~bad).sum())}
 quotes=distinct.loc[~bad].copy()
 if quotes.duplicated(["ts_utc","pair"]).any():raise ValueError("Quote quarantine failed")
 quotes.to_parquet(OUT/"prefix_quotes.parquet",index=False)
 result={"archives":records,"quote_receipts":receipts,"plan_sha256":sha(OUT/"prefix_plan.json"),
         "files":{n:sha(OUT/n) for n in ["prefix_minutes.parquet","prefix_quotes.parquet","quote_duplicate_evidence.csv","quote_quarantined_conflicts.csv"]},
         "quote_policy":quote_policy,
         "proxy":"1bp halfspread, checksummed Binance1m, before recorder; recorded Roostoo asof quotes preferred"}
 (OUT/"fine_data_manifest.json").write_text(json.dumps(result,indent=2))
 print(json.dumps({"verified_archives":len(records),"minute_rows":len(minute),"quote_rows":len(quotes)}),flush=True)

def replay():
 verify();plan=json.loads((OUT/"prefix_plan.json").read_text());m=json.loads((OUT/"fine_data_manifest.json").read_text())
 if sha(OUT/"prefix_plan.json")!=m["plan_sha256"]:raise ValueError("Plan changed")
 for n,h in m["files"].items():
  if sha(OUT/n)!=h:raise ValueError("Fine input changed")
 raw=pd.read_parquet(OUT/"prefix_minutes.parquet")
 prices=raw.pivot(index="timestamp",columns="symbol",values="close").sort_index()
 quotes=pd.read_parquet(OUT/"prefix_quotes.parquet")
 rules=json.loads((OUT/"exchange_info.json").read_text())["TradePairs"]
 for a in plan["assets"]:
  if a+"/USD" not in rules or not rules[a+"/USD"]["CanTrade"]:raise ValueError("No public pair rule: "+a)
 basic={"assets":plan["assets"],"seed":plan["seed"],"fee":.001,"min_order":1.0,"cash_buffer":.001,
        "precisions":{a:rules[a+"/USD"]["AmountPrecision"] for a in plan["assets"]},
        "price_precisions":{a:rules[a+"/USD"]["PricePrecision"] for a in plan["assets"]},
        "minute_max_age":120,"quote_max_age":30,"proxy_half_spread":.0001,"order_spacing_seconds":10,
        "start":plan["start"],"end":plan["end"]}
 book=QuoteBook(prices,quotes,basic);results=[];failures={}
 for name,recipe in plan["models"].items():
  for p,h in recipe["source_hashes"].items():
   if sha(p)!=h:raise ValueError("Model source changed since frozen plan")
  weights={pd.Timestamp(t):pd.Series(w,dtype=float) for t,w in recipe["targets"].items()}
  cfg={**basic,"band":recipe["spec"]["band"]}
  e,path,dec,fail,cycles,endpoint=replay_targets(weights,book,cfg,60)
  e.to_csv(OUT/(name+"_prefix_events.csv"),index=False);path.to_csv(OUT/(name+"_prefix_equity.csv"),index=False)
  pd.DataFrame(cycles).to_csv(OUT/(name+"_prefix_short_cycles.csv"),index=False)
  pd.DataFrame(fail).to_csv(OUT/(name+"_prefix_failures.csv"),index=False)
  (OUT/(name+"_prefix_decisions.json")).write_text(json.dumps(dec,indent=2))
  (OUT/(name+"_prefix_endpoint.json")).write_text(json.dumps(endpoint,indent=2))
  results.append(summarize(name,e,path,cycles,endpoint,cfg));failures[name]=len(fail)
 obs=pd.read_csv(ROOT/"results/book/20261009-observed-baseline/revisions/t001-confirmed/observed_trades_corrected.csv")
 obs["time_utc"]=[pd.Timestamp(str(r.date)+" "+str(r.time),tz="Asia/Hong_Kong").tz_convert("UTC") for _,r in obs.iterrows()]
 e,path,endpoint,cycles=observed_path(obs,book,basic,{"T001":19.98});name="observed_literal_ledger"
 e.to_csv(OUT/(name+"_prefix_events.csv"),index=False);path.to_csv(OUT/(name+"_prefix_equity.csv"),index=False)
 (OUT/(name+"_prefix_endpoint.json")).write_text(json.dumps(endpoint,indent=2))
 results.append(summarize(name,e,path,cycles,endpoint,basic))
 frame=pd.DataFrame(results);frame.to_csv(OUT/"prefix_comparison.csv",index=False)
 (OUT/"prefix_audit.json").write_text(json.dumps({"failure_counts":failures,"plan_sha256":sha(OUT/"prefix_plan.json"),
       "runner_sha256":sha(__file__),"fine_manifest_sha256":sha(OUT/"fine_data_manifest.json"),"config":basic,
       "warnings":["No activity guard in this diagnostic; primary score2 includes it","Observed T001fee confirmed; other observed fees assumed0.1%",
       "Observed literal ledger retains initial100k capital deficit","Signal source and verification are stated in pinned data_manifest.json; do not infer historical bid/ask coverage",
       "No independent holdout; archived proxy precedes recorder; minute samples may understate intraminute drawdown"]},indent=2))
 print(frame.to_string(index=False));print("failures",failures,flush=True)
 if any(failures.values()):raise ValueError("Fine replay has failures; do not use as complete comparison")

if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("stage",choices=("prepare","fetch","replay"));ap.add_argument("--out",type=Path,default=OUT);a=ap.parse_args();OUT=a.out.resolve()
 if (ROOT/"results/book").resolve() not in OUT.parents:raise ValueError("Output outside dedicated Book results")
 {"prepare":prepare,"fetch":fetch,"replay":replay}[a.stage]()
