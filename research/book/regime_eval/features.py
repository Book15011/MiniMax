"""Causal price-only matching; outcomes never enter the matching functions."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from src.validation.features import MarketData,StateEngine
from src.validation.selection import greedy_pick,mid_rank_pct

ALLOWED_FEATURES={"btc_ret24","btc_ret48","btc_ret168","btc_ret720","btc_ma200","btc_high720","breadth48","alt_minus_btc48","btc_vol168","btc_volratio"}

def settings(cfg):
    return cfg["book_regime_eval"] if "book_regime_eval" in cfg else cfg

def build_features(close,qv,state_times,validation_cfg,cfg):
    c=settings(cfg); times=pd.DatetimeIndex(state_times)
    if not len(times) or times.tz is None or close.index.tz is None:
        raise ValueError("nonempty UTC-aware state times required")
    times=times.tz_convert("UTC")
    close=close.copy();close.index=close.index.tz_convert("UTC")
    qv=qv.copy();qv.index=qv.index.tz_convert("UTC")
    hour=int(c["state_grid_hour_utc"])
    if any(t.hour!=hour or t.minute or t.second for t in times):
        raise ValueError("state must lie on the completed declared grid")
    latest=times.max()
    raw=close.loc[:latest].copy(); qv=qv.loc[:latest].reindex_like(raw)
    full=pd.date_range(raw.index.min(),latest,freq="h")
    raw=raw.reindex(full); qv=qv.reindex(full)
    v={**validation_cfg,"grid_hour_utc":hour}
    eng=StateEngine(MarketData(raw,qv),v)
    btc=raw["BTCUSDT"]; log=np.log(btc); returns=log.diff()
    feat=pd.DataFrame(index=times)
    for h in c["fast_hours"]:
        feat["btc_ret"+str(h)]=(log-log.shift(int(h))).reindex(times)
    feat["btc_ma200"]=eng.btc_features()["T3"].reindex(times)
    long_h=max(c["fast_hours"])
    need=math.ceil(long_h*c["minimum_hour_coverage"])
    feat["btc_high"+str(long_h)]=(btc/btc.rolling(long_h+1,min_periods=need).max()-1).reindex(times)
    short_v,long_v=c["volatility_hours"]
    vs=returns.rolling(short_v,min_periods=math.ceil(short_v*c["minimum_hour_coverage"])).std()
    vl=returns.rolling(long_v,min_periods=math.ceil(long_v*c["minimum_hour_coverage"])).std()
    feat["btc_vol"+str(short_v)]=(vs*np.sqrt(c["annual_hours"])).reindex(times)
    feat["btc_volratio"]=(vs/vl).reindex(times)
    breadth=[]; rel=[]; universe_n=[]; valid_n=[]; breadth_h=int(c["breadth_hours"])
    for t in times:
        u=eng.universe(t)
        a=raw.loc[t,u]; b=raw.reindex([t-pd.Timedelta(hours=breadth_h)])[u].iloc[0]
        r=np.log(a/b); valid=np.isfinite(r)&(a>0)&(b>0)
        universe_n.append(len(u));valid_n.append(int(valid.sum()))
        if valid.sum()<c["min_breadth_coins"] or valid.mean()<c["minimum_hour_coverage"]:
            breadth.append(np.nan);rel.append(np.nan);continue
        breadth.append(float((r[valid]>0).mean()))
        alt=r[valid].drop("BTCUSDT",errors="ignore")
        br=np.log(btc.loc[t]/btc.reindex([t-pd.Timedelta(hours=breadth_h)]).iloc[0])
        rel.append(float(alt.median()-br) if len(alt) else np.nan)
    feat["breadth48"]=breadth;feat["alt_minus_btc48"]=rel
    feat["universe_n"]=universe_n;feat["breadth_valid_n"]=valid_n
    required=[f for group in c["features"].values() for f in group]
    return feat[required+["universe_n","breadth_valid_n"]]

def match_windows(pool_features,query,groups,rules):
    columns=[x for g in groups.values() for x in g]
    forbidden=lambda x: x in {"R","R_liq"} or x.startswith(("future_","Y"))
    if not columns or len(set(columns))!=len(columns) or not set(columns)<=ALLOWED_FEATURES or any(forbidden(x) for x in columns):
        raise ValueError("outcomes cannot be matching features")
    ref=pool_features[columns].to_numpy(float); q=query[columns].to_numpy(float)
    if not len(ref) or not np.isfinite(ref).all() or not np.isfinite(q).all():
        raise ValueError("matching requires complete finite feature coverage")
    pct=mid_rank_pct(ref,ref); qp=mid_rank_pct(ref,q[None,:])[0]
    d=np.zeros(len(ref));offset=0
    for group in groups.values():
        n=len(group)
        if not n: raise ValueError("empty feature group")
        d+=np.mean((pct[:,offset:offset+n]-qp[offset:offset+n])**2,axis=1)/len(groups)
        offset+=n
    distance=pd.Series(np.sqrt(d),index=pool_features.index)
    selected=greedy_pick(distance.sort_values(kind="stable").index,rules)
    return pd.DataFrame({"t0":selected,"distance":distance.loc[selected].to_numpy()})

def market_outcomes(close,starts,prefix_hours,horizon_hours,cfg):
    c=settings(cfg); btc=close["BTCUSDT"]; rows=[]
    if not 0<=prefix_hours<horizon_hours: raise ValueError("invalid outcome horizon")
    for t in starts:
        times=pd.date_range(t+pd.Timedelta(hours=prefix_hours),t+pd.Timedelta(hours=horizon_hours),freq="h")
        path=btc.reindex(times)
        if path.notna().mean()<c["minimum_hour_coverage"] or pd.isna(path.iloc[0]) or pd.isna(path.iloc[-1]):
            rows.append([np.nan]*3);continue
        r=np.log(path).diff()
        rows.append([float(path.iloc[-1]/path.iloc[0]-1),
                     float((1-path/path.cummax()).max()),
                     float(r.std()*np.sqrt(c["annual_hours"]))])
    return pd.DataFrame(rows,index=starts,columns=["future_return","future_drawdown","future_vol"])
