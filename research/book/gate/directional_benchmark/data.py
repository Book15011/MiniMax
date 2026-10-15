"""Public, checksum-verified minute features and recorded quote inputs; no signed APIs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import io,zipfile,hashlib,json,time,ssl
from research.book.gate.fast_exec.public_auth import PublicAuth
import numpy as np,pandas as pd,requests,yaml
HERE=Path(__file__).parent;PROJECT=Path("/home/ubuntu/test/MiniMax")
OUT=PROJECT/"results/book/20261015-directional-benchmark-v1"
CFG=yaml.safe_load((HERE/"config.yaml").read_text())
FEATURES=CFG["ridge_features"]
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
    return h.hexdigest()
def minute_archive(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None,"archive CRC"
        with z.open(z.namelist()[0]) as f:d=pd.read_csv(f,header=None,usecols=[0,4,6,7,10])
    unit="us" if d.iloc[0,0]>1e14 else "ms"
    idx=pd.to_datetime(d[6].to_numpy()+1,unit=unit,utc=True)
    assert idx.is_monotonic_increasing and not idx.duplicated().any()
    return pd.DataFrame({"close":d[4].to_numpy(float),"quote_volume":d[7].to_numpy(float),"buy_quote":d[10].to_numpy(float)},index=idx)
def features(d):
    d=d.reindex(pd.date_range(d.index[0],d.index[-1],freq="min"))
    c=d.close.where(d.close>0);r=np.log(c).diff();q=d.quote_volume;b=d.buy_quote
    f=pd.DataFrame(index=d.index)
    for n in [1,5,15]:f["ret"+str(n)]=np.log(c).diff(n)
    f["vol15"]=r.rolling(15,min_periods=15).std(ddof=0)
    f["flow1"]=(2*b/q-1).where(q>0).clip(-1,1)
    total=q.rolling(5,min_periods=5).sum()
    f["flow5"]=(2*b.rolling(5,min_periods=5).sum()/total-1).where(total>0).clip(-1,1)
    f["volume_ratio"]=(q.rolling(5,min_periods=5).mean()/q.shift(5).rolling(60,min_periods=60).mean()).replace([np.inf,-np.inf],np.nan)
    f["quote_volume_5m"]=total
    f["label"]=np.log(c.shift(-(CFG["feature_horizon_minutes"]+1))/c.shift(-1))
    f["label_end"]=f.index+pd.Timedelta(minutes=CFG["feature_horizon_minutes"]+1)
    return f
def fetch(item):
    coin,day=item;name=f"{coin}USDT-1m-{day}.zip";folder=OUT/"archive";folder.mkdir(exist_ok=True)
    file=folder/name;checksum=folder/(name+".CHECKSUM")
    url=f"https://data.binance.vision/data/spot/daily/klines/{coin}USDT/1m/{name}"
    try:
        if not checksum.exists():
            r=requests.get(url+".CHECKSUM",auth=PublicAuth(),verify=ssl.get_default_verify_paths().cafile,timeout=(5,25));r.raise_for_status();checksum.write_bytes(r.content)
        expected=checksum.read_text().split()[0]
        if not file.exists():
            r=requests.get(url,auth=PublicAuth(),verify=ssl.get_default_verify_paths().cafile,timeout=(5,30));r.raise_for_status();part=file.with_suffix(".part");part.write_bytes(r.content)
            assert sha(part)==expected;part.replace(file)
        assert sha(file)==expected
        return {"coin":coin,"day":day,"path":str(file),"sha256":expected,"status":"PASS"}
    except Exception as e:return {"coin":coin,"day":day,"status":"UNAVAILABLE","error":type(e).__name__}
def main():
    OUT.mkdir(exist_ok=True);rows=[];training=[];hashes={}
    stop=pd.Timestamp(CFG["train_end_exclusive"],tz="UTC")
    for coin in CFG["liquid_coins"]:
        p=PROJECT/f"data/binance_spot/klines_1m/{coin}USDT/{coin}USDT-1m-2026-08.zip"
        hashes[str(p)]=sha(p);d=minute_archive(p);f=features(d)
        f=f[(f.index>=pd.Timestamp(CFG["train_start"],tz="UTC"))&(f.label_end<stop)].copy();f["coin"]=coin;training.append(f)
    train=pd.concat(training).sort_index();train.to_parquet(OUT/"training_features.parquet")
    coefficients={}
    for name,cols in [("ridge_flow",CFG["ridge_features"]),("ridge_price",CFG["price_features"])]:
        tr=train.dropna(subset=cols+["label"]);X=tr[cols].to_numpy();y=tr.label.to_numpy()
        lo,hi=np.quantile(X,CFG["feature_clip_quantiles"],axis=0);X=np.clip(X,lo,hi);mu=X.mean(0);sd=X.std(0)
        assert (sd>0).all()
        Z=(X-mu)/sd;y=np.clip(y,*np.quantile(y,CFG["label_clip_quantiles"]));intercept=float(y.mean())
        beta=np.linalg.solve(Z.T@Z+CFG["ridge_alpha"]*np.eye(len(cols)),Z.T@(y-intercept))
        coefficients[name]={"columns":cols,"mean":mu.tolist(),"scale":sd.tolist(),"clip_lower":lo.tolist(),"clip_upper":hi.tolist(),"beta":beta.tolist(),"intercept":intercept,"training_rows":len(tr),"latest_label_end":str(tr.label_end.max())}
    (OUT/"coefficients.json").write_text(json.dumps(coefficients,indent=2))
    print("FIT",[(k,v["training_rows"]) for k,v in coefficients.items()],flush=True)
    days=pd.date_range(CFG["quote_start"],pd.Timestamp(CFG["quote_end_exclusive"])-pd.Timedelta(days=1),freq="D").strftime("%Y-%m-%d").tolist()
    with ThreadPoolExecutor(max_workers=CFG["max_workers"]) as pool:
        manifest=list(pool.map(fetch,[(c,d) for c in CFG["liquid_coins"] for d in days]))
    (OUT/"archive_manifest.json").write_text(json.dumps(manifest,indent=2))
    if any(r["status"]!="PASS" for r in manifest):raise RuntimeError("Incomplete public minute archive; no fabricated features")
    recent=[]
    for coin in CFG["liquid_coins"]:
        d=pd.concat([minute_archive(Path(r["path"])) for r in manifest if r["coin"]==coin]).sort_index()
        assert not d.index.duplicated().any()
        f=features(d);f["coin"]=coin;recent.append(f)
    pd.concat(recent).sort_index().to_parquet(OUT/"recent_features.parquet")
    quote_parts=[]
    for day in days:
        p=PROJECT/"results/book/scalp/quotes"/(day.replace("-","")+".csv")
        hashes[str(p)]=sha(p)
        d=pd.read_csv(p,usecols=["ts_utc","pair","max_bid","min_ask"])
        d["time"]=pd.to_datetime(d.pop("ts_utc"),utc=True)
        valid=np.isfinite(d[["max_bid","min_ask"]]).all(axis=1)&(d.max_bid>0)&(d.min_ask>=d.max_bid)
        d=d[valid].drop_duplicates()
        conflict=d.duplicated(["time","pair"],keep=False);d=d[~conflict]
        quote_parts.append(d)
    q=pd.concat(quote_parts,ignore_index=True);bid=q.pivot(index="time",columns="pair",values="max_bid").sort_index()
    ask=q.pivot(index="time",columns="pair",values="min_ask").reindex_like(bid)
    np.savez_compressed(OUT/"recorded_quotes.npz",times=bid.index.asi8,bid=bid.to_numpy(),ask=ask.to_numpy(),coins=np.array([p.removesuffix("/USD") for p in bid.columns]))
    snap=json.loads((PROJECT/"results/book/20261015-simulator-edge-v1/public_exchange_snapshot.json").read_text())
    (OUT/"pair_rules.json").write_text(json.dumps(snap["exchangeInfo"]["TradePairs"]))
    audit={"status":"PASS","source_hashes":hashes,"minute_archives":len(manifest),"quote_frames":len(bid),"coins":len(bid.columns),
      "current_pair_metadata_applied_retrospectively":True,"historical_queue_or_role_observed":False,"feature_availability_delay_seconds":CFG["feature_availability_delay_seconds"],"chronological_check_is_spent":True}
    (OUT/"data_audit.json").write_text(json.dumps(audit,indent=2));print(json.dumps(audit),flush=True)
if __name__=="__main__":main()
