"""Four-hour model replay on the fixed authoritative hourly prefix."""
from pathlib import Path
import hashlib,json,sys
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import prefix as base
from backtest.data import Market
from backtest.engine import decide
from backtest.evaluate import model_modules
from src.config import load_config
from src.models import get
from src.data.binance_downloader import Task,http_get,parse_checksum
ROOT=base.ROOT;SOURCE=ROOT/"results/book/20261010-short-next-prefix-v3"
OUT=ROOT/"results/book/20261010-transition-prefix-v1"
OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prepare():
 if (OUT/"prefix_plan.json").exists():raise ValueError("Preserve previous prefix")
 manifest=json.loads((SOURCE/"data_manifest.json").read_text())
 for n,r in manifest["files"].items():
  if sha(SOURCE/n)!=r["sha256"]:raise ValueError("Authoritative source changed")
  (OUT/n).write_bytes((SOURCE/n).read_bytes())
 (OUT/"data_manifest.json").write_bytes((SOURCE/"data_manifest.json").read_bytes())
 source=json.loads((SOURCE/"prefix_plan.json").read_text())
 unis=pd.Series({pd.Timestamp(t):u for t,u in source["universe"].items()})
 close=pd.read_parquet(OUT/"hourly_close.parquet");qv=pd.read_parquet(OUT/"hourly_qv.parquet")
 market=Market(close,qv,unis,pd.Series(.0001,index=close.columns))
 cfg=load_config();name="book_transition_short";model=get(name);params=cfg["models"][name]
 times=pd.date_range(pd.Timestamp(manifest["start"]),pd.Timestamp(manifest["end"]).floor("h"),freq="4h")
 prev=pd.Series(dtype=float);rows={};assets={"BNB","BTC","ETH","SOL","XRP"}
 for t in times:
  w=decide(model,market,t,params,prev);prev=w
  rows[str(t)]={s:float(v) for s,v in w.items()}
  assets.update(s.removesuffix("USDT") for s in w.index)
 modules={str(Path(sys.modules[m].__file__).resolve()):sha(sys.modules[m].__file__) for m in model_modules(model)}
 plan={"start":manifest["start"],"end":manifest["end"],"assets":sorted(assets),"seed":100000.,
 "models":{name:{"params":params,"spec":model.spec.__dict__,"source_hashes":modules,"targets":rows}},
 "universe":source["universe"],"data_manifest_sha256":sha(OUT/"data_manifest.json"),
 "source_prefix_plan_sha256":sha(SOURCE/"prefix_plan.json"),
 "warning":"Descriptive spent prefix, four-hour decisions, daily16UTC universe,1h lag,no activity guard"}
 (OUT/"prefix_plan.json").write_text(json.dumps(plan,indent=2))
 print("Frozen",len(times),"decisions",len(assets),"assets",flush=True)
def archive_receipt():
 plan=json.loads((OUT/"prefix_plan.json").read_text())
 old={}
 for p in [SOURCE/"prefix_archive_receipt.json",ROOT/"results/book/20261009-short-next/prefix_archive_receipt.json"]:
  for r in json.loads(p.read_text()):old[(r["symbol"],r["day"])]=r
 tasks=[Task("spot","klines",a+"USDT","daily",str(d.date()),"1m")
        for a in plan["assets"] for d in pd.date_range("2026-10-04","2026-10-08")]
 def fetch(t):
  r=old.get((t.symbol,t.period))
  if r:
   if sha(r["path"])!=r["sha256"]:raise ValueError("Prior archive changed")
   return r
  p=OUT/"raw"/t.symbol/t.filename;p.parent.mkdir(parents=True,exist_ok=True)
  url=t.url("https://data.binance.vision/data")
  side=http_get(url+".CHECKSUM").text;expected,filename=parse_checksum(side)
  if filename!=t.filename:raise ValueError("Checksum name differs")
  raw=p.read_bytes() if p.exists() else http_get(url).content
  if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError("Archive checksum differs")
  p.write_bytes(raw);p.with_suffix(p.suffix+".CHECKSUM").write_text(side)
  return {"symbol":t.symbol,"day":t.period,"url":url,"path":str(p),"sha256":expected,"status":"verified"}
 with ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(fetch,tasks))
 (OUT/"prefix_archive_receipt.json").write_text(json.dumps(records,indent=2))
def main():
 base.OUT=OUT;prepare();archive_receipt();base.fetch();base.replay()
 pins={str(p):sha(p) for p in [Path(__file__),Path(base.__file__),OUT/"prefix_plan.json",OUT/"fine_data_manifest.json",OUT/"data_manifest.json",SOURCE/"prefix_comparison.csv"]}
 (OUT/"wrapper_manifest.json").write_text(json.dumps({"source_pins":pins,"parameter_refit":False,"hourly_data_same_as_v3":True},indent=2))
if __name__=="__main__":main()
