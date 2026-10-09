"""Checksummed minute archives for the frozen case dates; no competition API."""
from pathlib import Path
import hashlib,json
from concurrent.futures import ThreadPoolExecutor,as_completed
import pandas as pd
from src.data.binance_downloader import Task,http_get,parse_checksum
from src.data.loader import read_kline_zip
ROOT=Path("/home/ubuntu/test/MiniMax")
OUT=ROOT/"results/book/20261010-intraday-short-v2"
CP=ROOT/"results/book/20261009-weak-eval-v2"
COINS=("BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 if (OUT/"data_manifest.json").exists():raise ValueError("Preserve completed dataset")
 cases=pd.read_parquet(CP/"cases.parquet")
 cases=cases[cases.weak_archived|cases.weak_fresh_btc|cases.positive_control].copy()
 prefix=pd.Timestamp("2026-10-04 12:00Z")
 starts=list(cases.index)+[prefix]
 months=set()
 for start in starts:
  end=start+pd.Timedelta(hours=240 if start!=prefix else 108)
  for t in pd.date_range((start-pd.Timedelta(hours=48)).normalize(),end.normalize(),freq="D"):
   if t.month!=10 or t.year!=2026:months.add(t.strftime("%Y-%m"))
 tasks=[Task("spot","klines",s,"monthly",m,"1m") for s in COINS for m in sorted(months)]
 # October monthly file is not published; exact daily warmup+prefix only.
 tasks += [Task("spot","klines",s,"daily",str(d.date()),"1m") for s in COINS for d in pd.date_range("2026-10-02","2026-10-08")]
 plan={"cases_sha256":sha(CP/"cases.parquet"),"protocol_sha256":sha(Path(__file__).with_name("PROTOCOL.md")),"cases":list(map(str,cases.index)),"tasks":[t.__dict__ for t in tasks]}
 planpath=OUT/"fetch_plan.json"
 if planpath.exists() and json.loads(planpath.read_text())!=plan:raise ValueError("Fetch plan changed")
 planpath.write_text(json.dumps(plan,indent=2));cases.to_parquet(OUT/"cases.parquet")
 def fetch(t):
  path=OUT/"raw"/t.symbol/t.filename;path.parent.mkdir(parents=True,exist_ok=True)
  url=t.url("https://data.binance.vision/data")
  prior=ROOT/"results/book/20261010-intraday-short-v1/raw"/t.symbol/t.filename
  if prior.exists() and prior.with_suffix(".zip.CHECKSUM").exists():
   checksum=prior.with_suffix(".zip.CHECKSUM").read_text();raw=prior.read_bytes()
  else:
   checksum=http_get(url+".CHECKSUM").text;raw=None
  digest,name=parse_checksum(checksum)
  if name!=t.filename:raise ValueError("Wrong filename")
  raw=(path.read_bytes() if path.exists() else http_get(url).content) if raw is None else raw
  if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError("Bad checksum")
  path.write_bytes(raw);path.with_suffix(".zip.CHECKSUM").write_text(checksum)
  return {"symbol":t.symbol,"period":t.period,"granularity":t.granularity,"path":str(path),"sha256":digest,"url":url}
 records=[];failures=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  futures={pool.submit(fetch,t):t for t in tasks}
  for f in as_completed(futures):
   try:records.append(f.result())
   except Exception as e:failures.append({"task":futures[f].__dict__,"error":repr(e)})
   (OUT/"fetch_receipt.json").write_text(json.dumps({"records":records,"failures":failures},indent=2))
   if (len(records)+len(failures))%20==0:print("fetched",len(records),"failed",len(failures),"of",len(tasks),flush=True)
 if failures:raise ValueError("Archive coverage failed; see receipts")
 datasets={}
 for symbol in COINS:
  parts=[]
  for r in records:
   if r["symbol"]!=symbol:continue
   d=read_kline_zip(r["path"]);d["timestamp"]=pd.to_datetime(d.open_time,unit="ms",utc=True)+pd.Timedelta(minutes=1)
   if not ((d.high>=d[["open","close","low"]].max(axis=1))&(d.low<=d[["open","close","high"]].min(axis=1))&(d.low>0)&(d.quote_volume>=0)&(d.taker_buy_quote>=0)&(d.taker_buy_quote<=d.quote_volume+1e-6)).all():raise ValueError("Invalid kline")
   parts.append(d.set_index("timestamp")[["open","high","low","close","quote_volume","taker_buy_quote"]])
  full=pd.concat(parts).sort_index()
  if not full.index.is_unique:raise ValueError("Duplicate minute")
  selected=[]
  for start in starts:
   end=start+pd.Timedelta(hours=240 if start!=prefix else 108)
   grid=pd.date_range(start-pd.Timedelta(hours=48),end,freq="min")
   z=full.reindex(grid)
   if z.isna().any().any():raise ValueError(f"Missing {symbol} {start}: {z.isna().any(axis=1).sum()} minutes")
   selected.append(z)
  data=pd.concat(selected).sort_index();data=data[~data.index.duplicated()]
  p=OUT/(symbol+".parquet");data.to_parquet(p);datasets[symbol]={"path":str(p),"sha256":sha(p),"rows":len(data)}
  print("validated",symbol,len(data),flush=True)
 manifest={"status":"PASS","datasets":datasets,"archive_count":len(records),"fetch_plan_sha256":sha(planpath),"cases_sha256":sha(OUT/"cases.parquet"),"close_index":"open time+1minute; usable at timestamp","failed_broad_universe":"29/30 BCH remains unrepaired"}
 (OUT/"data_manifest.json").write_text(json.dumps(manifest,indent=2));print("ALL DATA PASS",flush=True)
if __name__=="__main__":main()
