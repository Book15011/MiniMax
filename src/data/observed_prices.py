"""Freeze public market data for an offline observed-transaction study. No credentials."""
from __future__ import annotations
import argparse,hashlib,io,json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from src.data.binance_downloader import Task,http_get,NotFound,parse_checksum
from src.data.loader import read_kline_zip

ASSETS=("BNB","BTC","ETH","SOL","XRP")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True);a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    if (out/"data_manifest.json").exists():
        raise SystemExit("Snapshot already frozen; use a fresh output directory for a new study.")
    manifest={"input_sha256":sha(out/"observed_trades.csv"),"quotes":[],"archives":[]}
    chunks=[]
    for p in sorted(Path("results/book/scalp/quotes").glob("2026100[5-9].csv")):
        # Bound reads before parsing: the last file may be appended by its recorder.
        size=p.stat().st_size
        with p.open("rb") as f: raw=f.read(size)
        raw=raw[:raw.rfind(b"\n")+1]
        q=pd.read_csv(io.BytesIO(raw))
        q=q[q.pair.isin([s+"/USD" for s in ASSETS])].copy()
        q["ts_utc"]=pd.to_datetime(q.ts_utc,utc=True)
        q=q[q.ts_utc<=pd.Timestamp("2026-10-09T01:15:00Z")]
        chunks.append(q)
        manifest["quotes"].append({"source":str(p),"bounded_bytes":len(raw),"prefix_sha256":hashlib.sha256(raw).hexdigest(),"selected_rows":len(q)})
    q=pd.concat(chunks,ignore_index=True).sort_values(["ts_utc","pair"])
    q.to_parquet(out/"quotes.parquet",index=False)
    tasks=[Task("spot","klines",s+"USDT","daily",str(d.date()),"1m")
           for s in ASSETS for d in pd.date_range("2026-09-30","2026-10-08")]
    def fetch(t):
        dest=out/"raw"/t.symbol/t.filename;dest.parent.mkdir(parents=True,exist_ok=True)
        existing=Path("data/binance_spot/klines_1m")/t.key
        url=t.url("https://data.binance.vision/data")
        try:
            check=http_get(url+".CHECKSUM").text
            expected,name=parse_checksum(check)
            if name!=t.filename: raise ValueError("checksum filename mismatch")
            if dest.exists(): raw=dest.read_bytes()
            elif existing.exists(): raw=existing.read_bytes()
            else: raw=http_get(url).content
            actual=hashlib.sha256(raw).hexdigest()
            if expected!=actual: raise ValueError("checksum mismatch")
            dest.write_bytes(raw)
            return {"symbol":t.symbol,"day":t.period,"url":url,"status":"verified","sha256":actual,"path":str(dest)}
        except NotFound:
            return {"symbol":t.symbol,"day":t.period,"url":url,"status":"unpublished_404"}
    with ThreadPoolExecutor(max_workers=4) as ex:
        for rec in ex.map(fetch,tasks): manifest["archives"].append(rec)
    pieces=[]
    for rec in manifest["archives"]:
        if rec["status"]!="verified":continue
        d=read_kline_zip(Path(rec["path"]))
        d["timestamp"]=pd.to_datetime(d.open_time,unit="ms",utc=True)+pd.Timedelta(minutes=1)
        d["symbol"]=rec["symbol"];pieces.append(d)
    minute=pd.concat(pieces,ignore_index=True).sort_values(["timestamp","symbol"])
    minute=minute.drop_duplicates(["timestamp","symbol"])
    minute.to_parquet(out/"archive_minutes.parquet",index=False)
    h=pd.read_parquet("results/book/shadow/h1/close_1h.parquet")
    h=h.loc[pd.Timestamp("2026-09-01T00:00Z"):pd.Timestamp("2026-10-09T01:00Z"),[s+"USDT" for s in ASSETS]]
    h.to_parquet(out/"warmup_hourly.parquet")
    manifest["warmup_source"]="results/book/shadow/h1/close_1h.parquet (ticker-assisted recent hourly; minute decisions prefer archive/quotes)"
    for name in ["quotes.parquet","archive_minutes.parquet","warmup_hourly.parquet"]:
        manifest[name]={"sha256":sha(out/name),"bytes":(out/name).stat().st_size}
    (out/"data_manifest.json").write_text(json.dumps(manifest,indent=2))
    print(json.dumps({"quotes":len(q),"archive_minutes":len(minute),"archives":pd.Series([r["status"] for r in manifest["archives"]]).value_counts().to_dict(),"hourly_shape":h.shape}))
if __name__=="__main__":main()
