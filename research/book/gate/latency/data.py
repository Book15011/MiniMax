"""Public archive acquisition and causal inputs. Raw files remain untracked."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,io,json,zipfile,time
import numpy as np,pandas as pd,requests,yaml
ROOT=Path(__file__).resolve().parents[4];MAIN=ROOT.parents[1]
OUT=MAIN/"results/book/20261015-latency-gate-v1";HERE=Path(__file__).parent
CFG=yaml.safe_load((HERE/"config.yaml").read_text())
SNAP=MAIN/"results/book/20261015-simulator-edge-v1/public_exchange_snapshot.json"
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def download(item):
    symbol,day=item;name=f"{symbol}USDT-1s-{day}.zip"
    folder=OUT/"archive";folder.mkdir(exist_ok=True)
    path=folder/name;check=folder/(name+".CHECKSUM")
    url=f"https://data.binance.vision/data/spot/daily/klines/{symbol}USDT/1s/{name}"
    try:
        if not check.exists():
            r=requests.get(url+".CHECKSUM",timeout=30);r.raise_for_status();check.write_bytes(r.content)
        expected=check.read_text().split()[0]
        assert len(expected)==64
        if not path.exists():
            r=requests.get(url,timeout=45);r.raise_for_status()
            assert len(r.content)<50_000_000
            part=path.with_suffix(".zip.part");part.write_bytes(r.content)
            assert sha(part)==expected,"archive checksum mismatch";part.replace(path)
        assert sha(path)==expected
        print("ARCHIVE",symbol,day,"verified",flush=True)
        return {"symbol":symbol,"day":day,"path":str(path),"sha256":expected,"status":"PASS"}
    except (requests.RequestException,ValueError,AssertionError,IndexError) as e:
        print("MISSING",symbol,day,type(e).__name__,flush=True)
        return {"symbol":symbol,"day":day,"url":url,"status":"UNAVAILABLE","error":type(e).__name__}
def main():
    OUT.mkdir(exist_ok=True)
    items=[(s,d) for s in CFG["symbols"] for d in CFG["archive"]["days"]]
    with ThreadPoolExecutor(max_workers=CFG["archive"]["max_workers"]) as pool:rows=list(pool.map(download,items))
    (OUT/"archive_manifest.json").write_text(json.dumps(rows,indent=2))
    if any(r["status"]!="PASS" for r in rows):raise RuntimeError("Incomplete archive coverage; do not fabricate prices")
    series={};all_closed=[]
    for symbol in CFG["symbols"]:
        xs=[]
        for row in rows:
            if row["symbol"]!=symbol:continue
            with zipfile.ZipFile(row["path"]) as z:
                with z.open(z.namelist()[0]) as f:raw=pd.read_csv(f,header=None,usecols=[0,4,6,8])
            unit=1e6 if raw.iloc[0,0]>1e14 else 1e3
            assert (raw[6]>raw[0]).all() and ((raw[6]-raw[0])/unit<1.01).all()
            raw["available_bar_close"]=(raw[6].to_numpy()+1)/unit
            assert len(raw)==86400 and raw[0].is_monotonic_increasing
            xs.append(pd.Series(raw[4].to_numpy(float),index=raw.available_bar_close))
        s=pd.concat(xs).sort_index()
        assert not s.index.duplicated().any() and (s>0).all()
        series[symbol]=s
    ex=pd.DataFrame(series).sort_index()
    assert ex.notna().all().all()
    np.savez_compressed(OUT/"external_bars.npz",times=ex.index.to_numpy(float),close=ex.to_numpy(float),coins=np.array(CFG["symbols"]))
    parts=[];hashes={}
    wanted={s+"/USD" for s in CFG["symbols"]}
    for day in CFG["archive"]["days"]:
        path=MAIN/"results/book/scalp/quotes"/(day.replace("-","")+".csv");hashes[str(path)]=sha(path)
        for ch in pd.read_csv(path,chunksize=200000):
            parts.append(ch[ch.pair.isin(wanted)])
    q=pd.concat(parts,ignore_index=True);orig=len(q)
    valid=np.isfinite(q[["max_bid","min_ask","last_price"]]).all(1)&(q.max_bid>0)&(q.min_ask>=q.max_bid)&(q.last_price>0)
    invalid=int((~valid).sum());q=q[valid]
    q=q.drop_duplicates(["ts_utc","pair","max_bid","min_ask","last_price"]);exact=orig-invalid-len(q)
    conflict=q.duplicated(["ts_utc","pair"],keep=False);n_conflict=int(conflict.sum());q=q[~conflict]
    q["t"]=pd.to_datetime(q.ts_utc,utc=True).astype("int64")/1e9
    cols=[s+"/USD" for s in CFG["symbols"]]
    bid=q.pivot(index="t",columns="pair",values="max_bid").reindex(columns=cols).sort_index()
    ask=q.pivot(index="t",columns="pair",values="min_ask").reindex(index=bid.index,columns=cols)
    np.savez_compressed(OUT/"roostoo_history.npz",times=bid.index.to_numpy(float),bid=bid.to_numpy(float),ask=ask.to_numpy(float),coins=np.array(CFG["symbols"]))
    snap=json.loads(SNAP.read_text());rules={s:snap["exchangeInfo"]["TradePairs"][s+"/USD"] for s in CFG["symbols"]}
    (OUT/"rules.json").write_text(json.dumps(rules,indent=2))
    audit={"status":"PASS","archive_files":len(rows),"external_seconds":len(ex),"quote_frames":len(bid),
           "filtered_rows_invalid":invalid,"filtered_exact_duplicates_removed":exact,"filtered_conflicting_rows_quarantined":n_conflict,
           "input_hashes":hashes,"current_rules_snapshot_sha256":sha(SNAP),
           "external_historical_receive_times_known":False,"historical_external_book_known":False,
           "historical_clock_offset_known":False,"actual_fills_verified":False}
    (OUT/"data_audit.json").write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2),flush=True)
if __name__=="__main__":main()
