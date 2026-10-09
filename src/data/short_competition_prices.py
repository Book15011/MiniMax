"""Freeze verified minute warmup and existing recorded quotes; public data only."""
from pathlib import Path
import hashlib,json
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from src.data.binance_downloader import Task,http_get,parse_checksum
from src.data.loader import read_kline_zip

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    root=Path("/home/ubuntu/test/MiniMax")
    source=root/"results/book/20261009-observed-baseline"
    out=root/"results/book/20261009-short-competition"
    out.mkdir(parents=True,exist_ok=True)
    if (out/"data_manifest.json").exists():raise SystemExit("Frozen data exists; do not overwrite.")
    old=json.loads((source/"data_manifest.json").read_text())
    records=[]
    for r in old["archives"]:
        if r["status"]!="verified":raise ValueError("Existing archive not verified")
        p=root/r["path"]
        if sha(p)!=r["sha256"]:raise ValueError("Existing raw archive hash mismatch")
        records.append({**r,"path":str(p)})
    for name in ["quotes.parquet","archive_minutes.parquet","warmup_hourly.parquet"]:
        if sha(source/name)!=old[name]["sha256"]:raise ValueError("Existing snapshot hash mismatch")
    tasks=[Task("spot","klines",a+"USDT","daily",str(d.date()),"1m")
           for a in ["BNB","BTC","ETH","SOL","XRP"]
           for d in pd.date_range("2026-09-26","2026-09-29")]
    def fetch(t):
        p=out/"raw"/t.symbol/t.filename;p.parent.mkdir(parents=True,exist_ok=True)
        url=t.url("https://data.binance.vision/data")
        check=http_get(url+".CHECKSUM").text
        expected,name=parse_checksum(check)
        if name!=t.filename:raise ValueError("Wrong checksum filename")
        raw=p.read_bytes() if p.exists() else http_get(url).content
        if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError("Warmup checksum mismatch")
        p.write_bytes(raw)
        return dict(symbol=t.symbol,day=t.period,url=url,path=str(p),status="verified",sha256=expected)
    with ThreadPoolExecutor(max_workers=4) as ex:records+=list(ex.map(fetch,tasks))
    parts=[]
    for r in records:
        d=read_kline_zip(Path(r["path"]))
        d["timestamp"]=pd.to_datetime(d.open_time,unit="ms",utc=True)+pd.Timedelta(minutes=1)
        d["symbol"]=r["symbol"];parts.append(d)
    minute=pd.concat(parts,ignore_index=True).sort_values(["timestamp","symbol"])
    if minute.duplicated(["timestamp","symbol"]).any():raise ValueError("Duplicate source minute")
    minute.to_parquet(out/"archive_minutes.parquet",index=False)
    (out/"quotes.parquet").write_bytes((source/"quotes.parquet").read_bytes())
    corrected=source/"revisions/t001-confirmed/observed_trades_corrected.csv"
    (out/"observed_trades_corrected.csv").write_bytes(corrected.read_bytes())
    (out/"original_replica_config.yaml").write_bytes((source/"replica_config.yaml").read_bytes())
    (out/"original_clone_warmup_hourly.parquet").write_bytes((source/"warmup_hourly.parquet").read_bytes())
    manifest={"source_manifest_sha256":sha(source/"data_manifest.json"),"archives":records,
              "corrected_input_source":str(corrected),"original_clone_config_source":str(source/"replica_config.yaml"),
              "quote_source":"Existing frozen five-coin public Roostoo recorder snapshot, through Oct9 01:15UTC",
              "start":"2026-10-04T12:00Z","end":"2026-10-09T01:15Z",
              "files":{name:{"sha256":sha(out/name),"bytes":(out/name).stat().st_size}
                 for name in ["archive_minutes.parquet","quotes.parquet","observed_trades_corrected.csv",
                              "original_replica_config.yaml","original_clone_warmup_hourly.parquet"]}}
    (out/"data_manifest.json").write_text(json.dumps(manifest,indent=2))
    print(json.dumps({"verified_archives":len(records),"minute_rows":len(minute),
                     "first":str(minute.timestamp.min()),"last":str(minute.timestamp.max())}))
if __name__=="__main__":main()
