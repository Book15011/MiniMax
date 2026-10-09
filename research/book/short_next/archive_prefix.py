"""Authoritative archived recent prefix signals; preserve rejected shadow repairs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib,json
import numpy as np,pandas as pd
from src.config import load_config
from backtest.data import load_market
from src.data.binance_downloader import Task,http_get,parse_checksum
from src.data.loader import read_kline_zip
ROOT=Path("/home/ubuntu/test/MiniMax")
OLD=ROOT/"results/book/20261009-short-next"
OUT=ROOT/"results/book/20261010-short-next-prefix-v3"
REJECTED=ROOT/"results/book/20261010-short-next-prefix-v2"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 if (OUT/"data_manifest.json").exists():raise ValueError("Authoritative prefix already frozen")
 scope=ROOT/"results/book/20261009-short-next-audit/ranking_repair_scope.json"
 symbols=json.loads(scope.read_text())["pre_topn_eligible_union"]
 if len(symbols)!=89:raise ValueError("Unexpected pre-ranking scope")
 old_receipt=json.loads((REJECTED/"repair_archive_receipt.json").read_text())
 prior={(r["symbol"],r["day"]):r for r in old_receipt}
 tasks=[Task("spot","klines",s,"daily",str(d.date()),"1h") for s in symbols for d in pd.date_range("2026-09-30","2026-10-08")]
 def fetch(t):
  found=prior.get((t.symbol,t.period))
  if found:
   if sha(found["path"])!=found["sha256"]:raise ValueError("Prior archive changed")
   return found
  p=OUT/"raw"/t.symbol/t.filename;p.parent.mkdir(parents=True,exist_ok=True)
  receipt=Path(str(p)+".CHECKSUM");url=t.url("https://data.binance.vision/data")
  check=receipt.read_text() if receipt.exists() else http_get(url+".CHECKSUM").text
  expected,filename=parse_checksum(check)
  if filename!=t.filename:raise ValueError("Checksum filename mismatch")
  raw=p.read_bytes() if p.exists() else http_get(url).content
  if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError("Bad publisher checksum")
  p.write_bytes(raw);receipt.write_text(check)
  return {"symbol":t.symbol,"day":t.period,"path":str(p),"url":url,"sha256":expected,"status":"verified"}
 records=[]
 with ThreadPoolExecutor(max_workers=4) as ex:
  pending=[ex.submit(fetch,t) for t in tasks]
  for f in as_completed(pending):
   records.append(f.result())
   if len(records)%40==0:
    (OUT/"fetch_progress.json").write_text(json.dumps({"verified":len(records),"required":len(tasks)}))
    print("verified",len(records),"/",len(tasks),flush=True)
 records=sorted(records,key=lambda r:(r["symbol"],r["day"]))
 (OUT/"hourly_archive_receipt.json").write_text(json.dumps(records,indent=2))
 original=json.loads((OLD/"data_manifest.json").read_text())
 for n,r in original["files"].items():
  if sha(OLD/n)!=r["sha256"]:raise ValueError("Original snapshot changed")
 template=pd.read_parquet(OLD/"hourly_close.parquet")
 hmarket=load_market(load_config());history_end=pd.Timestamp("2026-09-30T00:00Z")
 if hmarket.close.index.max()!=history_end:raise ValueError("Frozen historical endpoint changed")
 close=template.copy();qv=pd.read_parquet(OLD/"hourly_qv.parquet")
 history=template.index[template.index<=history_end]
 for target,source in [(close,hmarket.close),(qv,hmarket.quote_volume)]:
  for s in symbols:
   if s not in source:raise ValueError("Historical source lacks "+s)
   target.loc[history,s]=source[s].reindex(history)
 comparisons=[]
 for r in records:
  d=read_kline_zip(Path(r["path"])).sort_values("open_time")
  d.index=pd.to_datetime(d.open_time,unit="ms",utc=True)+pd.Timedelta(hours=1)
  expected=pd.date_range(pd.Timestamp(r["day"],tz="UTC")+pd.Timedelta(hours=1),periods=24,freq="h")
  if not d.index.equals(expected):raise ValueError("Archive clock/count mismatch")
  s=r["symbol"]
  for name,target,column in [("close",close,"close"),("qv",qv,"quote_volume")]:
   values=d[column].astype(float)
   if not np.isfinite(values).all() or not (values>0 if name=="close" else values>=0).all():raise ValueError("Invalid archive value")
   previous=target.loc[expected,s]
   rel=(previous-values).abs()/values.replace(0,np.nan)
   comparisons.append({"symbol":s,"day":r["day"],"field":name,"old_missing":int(previous.isna().sum()),
                       "exact_old_differences":int((previous.notna()&(previous!=values)).sum()),"max_relative_difference":float(rel.max()) if rel.notna().any() else None})
   target.loc[expected,s]=values
 grid=pd.date_range("2026-09-30T01:00Z","2026-10-09T00:00Z",freq="h")
 if close.loc[grid,symbols].isna().any().any() or qv.loc[grid,symbols].isna().any().any():raise ValueError("Authoritative recent data incomplete")
 close.to_parquet(OUT/"hourly_close.parquet");qv.to_parquet(OUT/"hourly_qv.parquet")
 pd.DataFrame(comparisons).to_csv(OUT/"shadow_archive_differences.csv",index=False)
 for n in ["exchange_info.json","universe_config.json"]:
  (OUT/n).write_bytes((OLD/n).read_bytes())
 (OUT/"source_store_meta.json").write_text(json.dumps({"complete_through":"2026-10-09T00:00Z","ticker_only":[],"source":"Frozen validated history + checksummed daily1h archives"}))
 cfg=load_config();from src.config import resolve
 panel=resolve(cfg["harness"]["panel_dir"])
 result={**original,"files":{n:{"sha256":sha(OUT/n)} for n in ["hourly_close.parquet","hourly_qv.parquet","exchange_info.json"]},
  "authoritative_recent":{"symbols":89,"archives":len(records),"hours_per_symbol":len(grid),
                         "receipt_sha256":sha(OUT/"hourly_archive_receipt.json"),"scope_sha256":sha(scope)},
  "historical_source":{str(panel/n):sha(panel/n) for n in ["panel_close_1h.parquet","panel_quote_volume_1h.parquet"]},
  "source_metadata":{"complete_through":"2026-10-09T00:00Z","ticker_only":[]},
  "warning":"Third separate prefix dataset: verified full recent hourly archive values replace conflicting shadow estimates. Earlier source is frozen validated historical panel. PAXG retains unused shadow column but is explicitly excluded before ranking. Original v1 and rejected v2 preserved; primary score2 data/protocol/thresholds unchanged; original fresh29/30 competition-query failure remains."}
 (OUT/"data_manifest.json").write_text(json.dumps(result,indent=2))
 print(json.dumps(result["authoritative_recent"]),flush=True)
if __name__=="__main__":main()
