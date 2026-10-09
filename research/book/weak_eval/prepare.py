"""Immutable remote snapshots for conditional weak-market experiments.

Historical matching states are measured at the fresh-cash window start. The
archived reference and recent ticker-assisted query remain separate profiles.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.binance_downloader import Manifest, Task, process
from src.data.loader import read_kline_zip
from src.validation.features import StateEngine,MarketData
from research.book.regime_eval.features import build_features
from research.book.regime_eval.run import safe_path, sha, dump


def _utc_index(frame):
    ix=frame.index
    if not isinstance(ix,pd.DatetimeIndex) or ix.tz is None or str(ix.tz)!="UTC":
        raise ValueError("bars require UTC-aware index")
    if not ix.is_unique or not ix.is_monotonic_increasing:
        raise ValueError("bars require unique increasing close times")
    if any(ix.minute) or any(ix.second) or any(ix.microsecond):
        raise ValueError("bars must lie on completed hourly close times")


def _timestamp(t):
    t=pd.Timestamp(t)
    if t.tz is None or str(t.tz)!="UTC" or t.minute or t.second or t.microsecond:
        raise ValueError("checkpoint requires completed UTC hour")
    return t


def exclude_irrelevant_offgrid(close,qv,earliest_needed):
    """Document malformed timestamps that cannot influence any usable state."""
    if not close.index.equals(qv.index):raise ValueError("price/volume source grids differ")
    ix=close.index
    if not isinstance(ix,pd.DatetimeIndex) or ix.tz is None or str(ix.tz)!="UTC":
        raise ValueError("bars require UTC-aware index")
    bad=(ix.minute!=0)|(ix.second!=0)|(ix.microsecond!=0)
    if ((ix>=earliest_needed)&bad).any():
        raise ValueError("off-grid timestamp within usable feature history")
    rows=[{"timestamp":str(t),"reason":"off-grid timestamp outside all candidate feature warmup"} for t in ix[bad]]
    return close.loc[~bad],qv.loc[~bad],rows


def join_panels(historical_close,historical_qv,live_close,live_qv,asof,complete_through=None):
    """Append live history without overwriting immutable historical observations.

    Setting complete_through excludes all ticker-only observations; omitting it
    deliberately preserves them for a separately labeled recent-price profile.
    """
    asof=_timestamp(asof)
    for f in [historical_close,historical_qv,live_close,live_qv]:_utc_index(f)
    if not historical_close.index.equals(historical_qv.index):
        raise ValueError("historical close/volume grids differ")
    if not live_close.index.equals(live_qv.index):
        raise ValueError("live close/volume grids differ")
    limit=asof if complete_through is None else min(asof,_timestamp(complete_through))
    end=historical_close.index.max()
    p=pd.concat([historical_close.loc[:limit],live_close.loc[(live_close.index>end)&(live_close.index<=limit)]]).sort_index()
    q=pd.concat([historical_qv.loc[:limit],live_qv.loc[(live_qv.index>end)&(live_qv.index<=limit)]]).sort_index()
    q=q.reindex(index=p.index,columns=p.columns)
    return p,q


def require_query_coverage(query,feature_cfg):
    n=int(query["universe_n"]);valid=int(query["breadth_valid_n"])
    need=math.ceil(n*float(feature_cfg["minimum_hour_coverage"]))
    if valid<need:
        raise ValueError(f"strict broad endpoint coverage {valid}/{n}; requires {need}/{n}")
    if n<int(feature_cfg["min_breadth_coins"]):
        raise ValueError("insufficient broad universe")
    cols=[f for group in feature_cfg["features"].values() for f in group]
    if not np.isfinite(query[cols].to_numpy(float)).all():
        raise ValueError("query matching requires finite causal features")


def reference_breadth(close,symbols,asof,feature_cfg):
    """Audit the archived universe without replacing a missing current coin."""
    asof=_timestamp(asof)
    lag=pd.Timedelta(hours=int(feature_cfg["breadth_hours"]))
    a=close.reindex(index=[asof],columns=symbols).iloc[0]
    b=close.reindex(index=[asof-lag],columns=symbols).iloc[0]
    valid=np.isfinite(a)&np.isfinite(b)&(a>0)&(b>0)
    n=len(symbols);nv=int(valid.sum())
    result={"universe_n":n,"breadth_valid_n":nv,"breadth48":np.nan,"alt_minus_btc48":np.nan}
    if n>=int(feature_cfg["min_breadth_coins"]) and nv>=math.ceil(n*feature_cfg["minimum_hour_coverage"]):
        r=np.log(a[valid]/b[valid]);result["breadth48"]=float((r>0).mean())
        if "BTCUSDT" in r.index:
            alt=r.drop("BTCUSDT")
            result["alt_minus_btc48"]=float(alt.median()-r["BTCUSDT"]) if len(alt) else np.nan
    return result


def build_states(close,qv,starts,asof,validation_cfg,feature_cfg,require_full_query=True):
    """Feature states at actual starts, grouping daily calculations by UTC hour."""
    asof=_timestamp(asof);starts=pd.DatetimeIndex(starts)
    if starts.tz is None or str(starts.tz)!="UTC" or not starts.is_unique or not len(starts):
        raise ValueError("nonempty unique UTC starts required")
    if any(starts.minute) or any(starts.second) or any(starts.microsecond):
        raise ValueError("starts must lie on completed UTC hours")
    if (starts>=asof).any():raise ValueError("historical starts must precede checkpoint")
    _utc_index(close);_utc_index(qv)
    frames=[]
    for hour in sorted(set(starts.hour)):
        times=starts[starts.hour==hour]
        settings={**feature_cfg,"state_grid_hour_utc":int(hour)}
        latest=times.max()
        frames.append(build_features(close.loc[:latest],qv.loc[:latest],times,validation_cfg,settings))
    historical=pd.concat(frames).reindex(starts)
    settings={**feature_cfg,"state_grid_hour_utc":int(asof.hour)}
    current=build_features(close.loc[:asof],qv.loc[:asof],pd.DatetimeIndex([asof]),validation_cfg,settings).iloc[0]
    if require_full_query:require_query_coverage(current,feature_cfg)
    return {"historical_features":historical,"query":current}


def archive_frame(path,day):
    """Verify complete 24 hourly bars, preserving the shared UTC-close convention."""
    day=_timestamp(day)
    if day.hour:raise ValueError("archive day must begin UTC midnight")
    raw=read_kline_zip(path)
    idx=pd.DatetimeIndex(pd.to_datetime(raw["open_time"],unit="ms",utc=True))+pd.Timedelta(hours=1)
    duration=raw["close_time"].to_numpy(dtype="int64")-raw["open_time"].to_numpy(dtype="int64")
    if not np.equal(duration,3_600_000-1).all():
        raise ValueError("archive requires complete hourly close intervals")
    expected=pd.date_range(day+pd.Timedelta(hours=1),day+pd.Timedelta(days=1),freq="h")
    if not idx.equals(expected):
        raise ValueError("archive requires exactly 24 unique ordered closed hourly bars")
    close=raw["close"].to_numpy(float);qv=raw["quote_volume"].to_numpy(float)
    if not np.isfinite(close).all() or (close<=0).any() or not np.isfinite(qv).all() or (qv<0).any():
        raise ValueError("invalid public archive prices/volumes")
    return pd.DataFrame({"close":close,"qv":qv},index=idx)


def fetch_daily_archives(symbols,day,out_dir,base_url,workers):
    """Optional checksum-verified public backfill; never modifies a live store."""
    day=_timestamp(day);out_dir=Path(out_dir)
    if not 1<=int(workers)<=8:raise ValueError("archive workers must be in [1,8]")
    if not base_url.rstrip("/").endswith("/data"):base_url=base_url.rstrip("/")+"/data"
    manifest=Manifest(out_dir/"archive_downloads.jsonl");raw=out_dir/"public_archive"
    tasks=[Task("spot","klines",s,"daily",day.strftime("%Y-%m-%d"),"1h") for s in sorted(set(symbols))]
    with ThreadPoolExecutor(max_workers=int(workers)) as pool:
        records=list(pool.map(lambda t:process(t,base_url,raw,manifest),tasks))
    frames={}
    for t,r in zip(tasks,records):
        if r["status"]=="ok":
            path=raw/t.symbol/t.filename
            frames[t.symbol]=archive_frame(path,day)
            if sha(path)!=r["sha256"]:raise ValueError("archive changed after checksum verification")
    return frames,records


def apply_verified_archives(close,qv,archive_dir,asof):
    """Apply checksum-attested public bars to independent copied snapshot frames."""
    asof=_timestamp(asof);archive_dir=Path(archive_dir)
    manifest=archive_dir/"archive_downloads.jsonl"
    latest={r["file"]:r for r in [json.loads(line) for line in manifest.read_text().splitlines() if line.strip()]}
    p=close.copy();q=qv.copy();records=[];changed_price=changed_volume=0
    for key,record in sorted(latest.items()):
        if record["status"]!="ok":continue
        if "-1h-" not in key:raise ValueError("reference requires hourly public archives")
        path=(archive_dir/"public_archive"/key).resolve()
        if (archive_dir/"public_archive").resolve() not in path.parents:
            raise ValueError("archive path outside provenance directory")
        if sha(path)!=record["sha256"]:raise ValueError("public archive checksum identity changed")
        day=pd.Timestamp(record["period"],tz="UTC")
        frame=archive_frame(path,day).loc[:asof]
        if not len(frame):continue
        symbol=record["symbol"]
        grid=p.index.union(frame.index)
        p=p.reindex(grid);q=q.reindex(grid)
        if symbol not in p:p[symbol]=np.nan;q[symbol]=np.nan
        changed_price+=int((p.loc[frame.index,symbol].to_numpy()!=frame["close"].to_numpy()).sum())
        changed_volume+=int((q.loc[frame.index,symbol].to_numpy()!=frame["qv"].to_numpy()).sum())
        p.loc[frame.index,symbol]=frame["close"].to_numpy()
        q.loc[frame.index,symbol]=frame["qv"].to_numpy()
        if sha(path)!=record["sha256"]:raise ValueError("public archive changed during parsing")
        records.append({"symbol":symbol,"period":record["period"],"path":str(path),"sha256":record["sha256"]})
    return p,q,{"records":records,"manifest_sha256":sha(manifest),
                "corrected_price_cells":changed_price,"corrected_volume_cells":changed_volume}


def require_verified_reference(proof,symbols,reference,feature_cfg):
    """Require publisher bars for all recent reference breadth and BTC states."""
    keys={(r["symbol"],r["period"]) for r in proof["records"]}
    reference=_timestamp(reference)
    if reference.hour:raise ValueError("publisher-backed reference must end at UTC midnight")
    breadth_days=pd.date_range(reference-pd.Timedelta(days=3),reference-pd.Timedelta(days=1),freq="D")
    # The 7-day volatility needs its first return's prior close, including the midnight anchor.
    btc_hours=int(feature_cfg["volatility_hours"][0])
    btc_days=pd.date_range((reference-pd.Timedelta(hours=btc_hours+1)).normalize(),
                          reference-pd.Timedelta(days=1),freq="D")
    missing=[(symbol,day.strftime("%Y-%m-%d")) for symbol in symbols for day in breadth_days
             if (symbol,day.strftime("%Y-%m-%d")) not in keys]
    missing += [("BTCUSDT",day.strftime("%Y-%m-%d")) for day in btc_days
                if ("BTCUSDT",day.strftime("%Y-%m-%d")) not in keys]
    if missing:raise ValueError("missing publisher reference archives: "+json.dumps(sorted(set(missing))))
    return {"breadth_days":[t.strftime("%Y-%m-%d") for t in breadth_days],
            "btc_days":[t.strftime("%Y-%m-%d") for t in btc_days],
            "reference_symbols":symbols,"all_required_archives_verified":True}


def prepare(cfg,starts,feature_cfg=None,archive_evidence=None):
    """Freeze reusable dual-profile inputs before any candidate results are read."""
    c=cfg["book_weak_eval"];f=feature_cfg or cfg["book_regime_eval"]
    asof=_timestamp(c["asof"]);reference=_timestamp(c["reference_asof"])
    if reference>asof:raise ValueError("reference cannot follow current checkpoint")
    out=safe_path(c["out_dir"]);out.mkdir(parents=True,exist_ok=True)
    hist=safe_path(c["historical_panel"]);live=safe_path(c["live_panel"])
    sources={"historical_close":hist/"panel_close_1h.parquet","historical_qv":hist/"panel_quote_volume_1h.parquet",
             "live_close":live/"close_1h.parquet","live_qv":live/"qv_1h.parquet","live_meta":live/"store_meta.json"}
    manifest_path=out/"input_manifest.json"
    definition={"features":f,"validation":cfg["validation"],"starts":[str(t) for t in starts],
                "asof":str(asof),"reference_asof":str(reference),"implementation_sha256":sha(Path(__file__))}
    archive_dir=safe_path(c["reference_archive_dir"]) if c.get("reference_archive_dir") else None
    if archive_dir:
        definition["archive_manifest_sha256"]=sha(archive_dir/"archive_downloads.jsonl")
    fingerprint=hashlib.sha256(json.dumps(definition,sort_keys=True,default=str).encode()).hexdigest()
    if manifest_path.exists():
        m=json.loads(manifest_path.read_text())
        if pd.Timestamp(m["asof"])!=asof or pd.Timestamp(m["reference_asof"])!=reference:
            raise ValueError("frozen checkpoint time differs")
        if m.get("preparation_sha256")!=fingerprint:raise ValueError("preparation definition differs from frozen snapshot")
        for name,digest in m["frozen_snapshots"].items():
            if sha(out/name)!=digest:raise ValueError("frozen snapshot changed: "+name)
        for record in m.get("publisher_overrides",{}).get("records",[]):
            if sha(safe_path(record["path"]))!=record["sha256"]:raise ValueError("publisher archive identity changed")
        for name in ["historical_close","historical_qv"]:
            if sha(sources[name])!=m["sources"][name]["sha256"]:
                raise ValueError("immutable historical source changed")
        p=pd.read_parquet(out/"close_snapshot.parquet");q=pd.read_parquet(out/"qv_snapshot.parquet")
        h=pd.read_parquet(out/"historical_features.parquet")
        if not h.index.equals(pd.DatetimeIndex(starts)):raise ValueError("frozen historical start grid differs")
        states=pd.read_parquet(out/"query_features.parquet")
        return {"historical_features":h,"query":states.loc[reference],"fresh_query":states.loc[asof],
                "close":p,"qv":q,"input_manifest":m}
    before={k:sha(v) for k,v in sources.items()}
    hp=pd.read_parquet(sources["historical_close"]);hq=pd.read_parquet(sources["historical_qv"])
    lp=pd.read_parquet(sources["live_close"]).loc[:asof];lq=pd.read_parquet(sources["live_qv"]).loc[:asof]
    meta=json.loads(sources["live_meta"].read_text())
    if before!={k:sha(v) for k,v in sources.items()}:raise ValueError("source changed during snapshot; retry")
    complete=_timestamp(meta["complete_through"])
    if reference>complete:raise ValueError("reference has not been archive-confirmed")
    warmup=max(201,int(cfg["validation"].get("universe",{}).get("min_history_days",0))+1,
               int(cfg["validation"].get("universe",{}).get("volume_days",0))+1)
    earliest=pd.DatetimeIndex(starts).min()-pd.Timedelta(days=warmup)
    hp,hq,excluded=exclude_irrelevant_offgrid(hp,hq,earliest)
    p,q=join_panels(hp,hq,lp,lq,asof)
    proof={}
    if archive_dir:p,q,proof=apply_verified_archives(p,q,archive_dir,asof)
    h=build_states(hp,hq,starts,min(reference,hp.index.max()),cfg["validation"],f,require_full_query=False)["historical_features"]
    settings={**f,"state_grid_hour_utc":reference.hour}
    ref=build_features(p.loc[:reference],q.loc[:reference],pd.DatetimeIndex([reference]),cfg["validation"],settings).iloc[0]
    require_query_coverage(ref,f)
    settings={**f,"state_grid_hour_utc":asof.hour}
    fresh=build_features(p.loc[:asof],q.loc[:asof],pd.DatetimeIndex([asof]),cfg["validation"],settings).iloc[0]
    default_fresh_counts={"valid":int(fresh.breadth_valid_n),"universe":int(fresh.universe_n)}
    universe_cfg={**cfg["validation"],"grid_hour_utc":reference.hour}
    reference_symbols=StateEngine(MarketData(p.loc[:reference],q.loc[:reference]),universe_cfg).universe(reference)
    publisher_reference=require_verified_reference(proof,reference_symbols,reference,f) if archive_dir else {}
    guarded_breadth=reference_breadth(p,reference_symbols,asof,f)
    for name,value in guarded_breadth.items():fresh[name]=value
    core=[name for group,names in f["features"].items() if group!="BREADTH" for name in names]
    if not np.isfinite(fresh[core].to_numpy(float)).all():raise ValueError("recent BTC profile has missing causal features")
    states=pd.DataFrame([ref,fresh],index=pd.DatetimeIndex([reference,asof]))
    if states.index.has_duplicates:states=states.iloc[:1]
    p.to_parquet(out/"close_snapshot.parquet");q.to_parquet(out/"qv_snapshot.parquet")
    h.to_parquet(out/"historical_features.parquet");states.to_parquet(out/"query_features.parquet")
    snapshots=["close_snapshot.parquet","qv_snapshot.parquet","historical_features.parquet","query_features.parquet"]
    m={"schema_version":1,"preparation_sha256":fingerprint,"asof":str(asof),"reference_asof":str(reference),
       "archive_complete_through":str(complete),"fresh_archive_confirmed":bool(asof<=complete),
       "sources":{k:{"path":str(v),"sha256":before[k]} for k,v in sources.items()},
       "frozen_snapshots":{name:sha(out/name) for name in snapshots},
       "fresh_ticker_only_used":[t for t in meta.get("ticker_only",[]) if reference<pd.Timestamp(t)<=asof],
       "archive_availability":archive_evidence or [],
       "publisher_overrides":proof,"publisher_reference":publisher_reference,
       "older_reference_history_provenance":"historical panel and archived-store metadata with immutable local SHA; direct publisher rechecks cover stated recent days only",
       "excluded_irrelevant_offgrid_rows":excluded,"earliest_feature_history_needed":str(earliest),
       "reference_broad_coverage":{"valid":int(ref.breadth_valid_n),"universe":int(ref.universe_n)},
       "fresh_broad_coverage":{"valid":int(fresh.breadth_valid_n),"universe":int(fresh.universe_n)},
       "fresh_universe_rule":"fixed last fully archived reference top30; missing coins never replaced",
       "fresh_reference_universe":reference_symbols,"untrusted_dynamic_fresh_counts":default_fresh_counts,
       "historical_state_clock":"actual cash-start t0, never t0+96h",
       "reference_age_hours":float((asof-reference)/pd.Timedelta(hours=1)),
       "preserved_old_failure":"Oct8 12UTC original broad query BCH absent29/30; original study unchanged",
       "competition_account":"UNVERIFIED; fresh-cash historical experiments only"}
    dump(manifest_path,m)
    return {"historical_features":h,"query":ref,"fresh_query":fresh,"close":p,"qv":q,"input_manifest":m}
