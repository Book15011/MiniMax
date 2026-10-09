"""Independently reconstruct all recent hourly input cells from saved archives."""
from pathlib import Path
import hashlib,io,json,zipfile
import numpy as np,pandas as pd
ROOT=Path("/home/ubuntu/test/MiniMax")
INP=ROOT/"results/book/20261010-short-next-prefix-v3"
OUT=ROOT/"results/book/20261010-hourly-archive-audit";OUT.mkdir(parents=True,exist_ok=True)
if (OUT/"audit.json").exists():raise ValueError("Preserve existing evidence")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=json.loads((INP/"data_manifest.json").read_text())
records=json.loads((INP/"hourly_archive_receipt.json").read_text())
assert sha(INP/"hourly_archive_receipt.json")==m["authoritative_recent"]["receipt_sha256"]
close=pd.read_parquet(INP/"hourly_close.parquet");qv=pd.read_parquet(INP/"hourly_qv.parquet")
rows=[]
for r in records:
 p=Path(r["path"]);assert sha(p)==r["sha256"]
 with zipfile.ZipFile(p) as z:
  names=z.namelist();assert len(names)==1
  f=pd.read_csv(io.BytesIO(z.read(names[0])),header=None)
 unit="us" if f.iloc[0,0]>1e14 else "ms"
 ix=pd.DatetimeIndex(pd.to_datetime(f[0],unit=unit,utc=True))+pd.Timedelta(hours=1)
 expected=pd.date_range(pd.Timestamp(r["day"],tz="UTC")+pd.Timedelta(hours=1),periods=24,freq="h")
 assert ix.equals(expected)
 c=f[4].to_numpy(float);q=f[7].to_numpy(float)
 assert np.isfinite(c).all() and (c>0).all() and np.isfinite(q).all() and (q>=0).all()
 assert np.allclose(close.loc[ix,r["symbol"]],c,rtol=1e-12,atol=0)
 assert np.allclose(qv.loc[ix,r["symbol"]],q,rtol=1e-12,atol=0)
 rows.append({"symbol":r["symbol"],"day":r["day"],"bars":len(ix),"sha256":r["sha256"]})
assert len(records)==801 and len({r["symbol"] for r in records})==89
for p,h in m["historical_source"].items():assert sha(p)==h
hpaths=list(m["historical_source"])
hc=pd.read_parquet(next(p for p in hpaths if "panel_close" in p))
hq=pd.read_parquet(next(p for p in hpaths if "quote_volume" in p))
past=close.index[close.index<=pd.Timestamp("2026-09-30T00:00Z")]
symbols=sorted({r["symbol"] for r in records})
assert np.allclose(close.loc[past,symbols],hc.loc[past,symbols],equal_nan=True,rtol=0,atol=0)
assert np.allclose(qv.loc[past,symbols],hq.loc[past,symbols],equal_nan=True,rtol=0,atol=0)
pd.DataFrame(rows).to_csv(OUT/"archive_checks.csv",index=False)
proof={"status":"PASS","archives":801,"eligible_symbols":89,"bars_per_symbol":216,"recent_close_cells":801*24,"recent_volume_cells":801*24,"timestamp_semantics":"publisher open_time plus1h completed close", "historical_warmup_exact":True,"manifest_sha256":sha(INP/"data_manifest.json"),"receipt_sha256":sha(INP/"hourly_archive_receipt.json"),"input_hashes":{n:sha(INP/n) for n in ("hourly_close.parquet","hourly_qv.parquet")},"analysis_sha256":sha(__file__),"limits":"Does not repair missing BCH competition ticker; PAXG remains explicitly ineligible; does not create historical bid/ask"}
(OUT/"audit.json").write_text(json.dumps(proof,indent=2))
print(json.dumps(proof,indent=2),flush=True)
