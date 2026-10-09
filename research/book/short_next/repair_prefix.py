"""Fill only identified missing Oct4 hourly data from checksummed archives."""
from pathlib import Path
import hashlib,json
from concurrent.futures import ThreadPoolExecutor
import numpy as np,pandas as pd
from src.data.binance_downloader import Task,http_get,parse_checksum
from src.data.loader import read_kline_zip
ROOT=Path("/home/ubuntu/test/MiniMax")
OLD=ROOT/"results/book/20261009-short-next"
OUT=ROOT/"results/book/20261010-short-next-prefix-v2"
SCOPE=ROOT/"results/book/20261009-short-next-audit/ranking_repair_scope.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 if (OUT/"data_manifest.json").exists():raise ValueError("Repaired data already frozen")
 manifest=json.loads((OLD/"data_manifest.json").read_text())
 for n,r in manifest["files"].items():
  if sha(OLD/n)!=r["sha256"]:raise ValueError("Original frozen input changed")
 scope=json.loads(SCOPE.read_text());symbols=scope["eligible_symbols_needing_qv_repair"]
 if len(symbols)!=60:raise ValueError("Unexpected repair scope")
 tasks=[Task("spot","klines",s,"daily","2026-10-04","1h") for s in symbols]
 def fetch(t):
  p=OUT/"raw"/t.symbol/t.filename;p.parent.mkdir(parents=True,exist_ok=True)
  receipt=Path(str(p)+".CHECKSUM");url=t.url("https://data.binance.vision/data")
  check=receipt.read_text() if receipt.exists() else http_get(url+".CHECKSUM").text
  expected,filename=parse_checksum(check)
  if filename!=t.filename:raise ValueError("Checksum filename mismatch")
  raw=p.read_bytes() if p.exists() else http_get(url).content
  if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError("Bad checksum")
  p.write_bytes(raw);receipt.write_text(check)
  return {"symbol":t.symbol,"day":t.period,"path":str(p),"url":url,"sha256":expected,"status":"verified"}
 with ThreadPoolExecutor(max_workers=4) as ex:records=list(ex.map(fetch,tasks))
 (OUT/"repair_archive_receipt.json").write_text(json.dumps(records,indent=2))
 close=pd.read_parquet(OLD/"hourly_close.parquet");qv=pd.read_parquet(OLD/"hourly_qv.parquet")
 c=close.copy();v=qv.copy();audits=[];patches=[]
 for r in records:
  d=read_kline_zip(Path(r["path"])).sort_values("open_time")
  d.index=pd.to_datetime(d.open_time,unit="ms",utc=True)+pd.Timedelta(hours=1)
  expected=pd.date_range("2026-10-04T01:00Z",periods=24,freq="h")
  if not d.index.equals(expected):raise ValueError("Wrong/duplicate hourly grid: "+r["symbol"])
  s=r["symbol"];checks={"symbol":s}
  for name,target,col in [("close",c,"close"),("qv",v,"quote_volume")]:
   old=target.loc[expected,s];new=d[col].astype(float)
   if not np.isfinite(new).all() or not (new>0 if name=="close" else new>=0).all():raise ValueError("Invalid archive values")
   known=old.notna()
   checks[name+"_overlap"]=int(known.sum())
   diff=(old[known]-new[known]).abs()
   checks[name+"_max_abs_difference"]=float(diff.max()) if len(diff) else 0.0
   if not np.allclose(old[known],new[known],rtol=1e-8,atol=1e-6):raise ValueError("Archive overlap conflict: "+s+" "+name)
   missing=~known
   for t,value in new[missing].items():patches.append({"symbol":s,"time_utc":str(t),"field":name,"archive_value":float(value)})
   target.loc[expected[missing],s]=new[missing]
   checks[name+"_filled"]=int(missing.sum())
  audits.append(checks)
 audit=pd.DataFrame(audits)
 if audit.close_filled.sum()!=656 or audit.qv_filled.sum()!=656:raise ValueError("Unexpected number of repaired cells")
 for old,new in [(close,c),(qv,v)]:
  if not new.where(old.notna()).equals(old):raise ValueError("Nonmissing original data changed")
 if not c["BTCUSDT"].equals(close["BTCUSDT"]):raise ValueError("BTC source changed unexpectedly")
 c.to_parquet(OUT/"hourly_close.parquet");v.to_parquet(OUT/"hourly_qv.parquet")
 audit.to_csv(OUT/"repair_overlap_audit.csv",index=False);pd.DataFrame(patches).to_csv(OUT/"repaired_cells.csv",index=False)
 for name in ["exchange_info.json","universe_config.json","source_store_meta.json"]:
  (OUT/name).write_bytes((OLD/name).read_bytes())
 result={**manifest,"files":{n:{"sha256":sha(OUT/n),"source":str(OLD/n)} for n in ["hourly_close.parquet","hourly_qv.parquet","exchange_info.json"]},
         "repair":{"source_manifest_sha256":sha(OLD/"data_manifest.json"),"scope_sha256":sha(SCOPE),
                   "archive_receipt_sha256":sha(OUT/"repair_archive_receipt.json"),"archives":len(records),
                   "hourly_close_cells_filled":656,"hourly_qv_cells_filled":656,"nonmissing_preserved":True,
                   "overlap_checks":"rtol1e-8,atol1e-6; all completed known archive hours compared"},
         "warning":"Separate revised prefix dataset; original v1 preserved. Only identified NaNs filled from publisher-checksummed Oct4 hourly archives. Other original shadow values preserved and not independently rechecked here. Does not repair frozen fresh29/30 competition-query coverage."}
 (OUT/"data_manifest.json").write_text(json.dumps(result,indent=2))
 print(json.dumps(result["repair"]),flush=True)
if __name__=="__main__":main()
