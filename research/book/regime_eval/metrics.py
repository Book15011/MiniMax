"""Pure numeric metrics for the Book research evaluator; no orders or account I/O."""
from __future__ import annotations
import numpy as np
import pandas as pd

def normalized_weights(w):
    a=np.asarray(w,dtype=float)
    if a.ndim!=1 or not len(a) or not np.isfinite(a).all() or (a<0).any() or a.sum()<=0:
        raise ValueError("weights must be a nonempty finite nonnegative probability mass")
    return a/a.sum()

def _values(x,w):
    x=np.asarray(x,dtype=float); w=normalized_weights(w)
    if x.ndim!=1 or len(x)!=len(w) or not np.isfinite(x).all():
        raise ValueError("values must be finite and aligned with weights")
    return x,w

def continuation_returns(equity,gross,prefix_hours,close_fee):
    e=np.asarray(equity,dtype=float); g=np.asarray(gross,dtype=float)
    if e.ndim!=2 or e.shape!=g.shape or not e.size or not np.isfinite(e).all() or (e<=0).any():
        raise ValueError("equity must be finite positive aligned two-dimensional arrays")
    if not np.isfinite(g).all() or (g<0).any():
        raise ValueError("gross exposure must be finite nonnegative")
    if not isinstance(prefix_hours,(int,np.integer)) or not 0<=prefix_hours<e.shape[1]-1:
        raise ValueError("prefix must leave a remaining horizon")
    if not np.isfinite(close_fee) or close_fee<0 or (close_fee*g[:,-1]>=1).any():
        raise ValueError("invalid liquidation cost")
    return e[:,-1]*(1-close_fee*g[:,-1])/e[:,prefix_hours]-1

def weighted_quantile(x,w,q):
    x,w=_values(x,w)
    if not np.isfinite(q) or not 0<=q<=1: raise ValueError("quantile outside [0,1]")
    keep=w>0; x,w=x[keep],w[keep]
    order=np.argsort(x,kind="stable"); x,w=x[order],w[order]
    return float(x[min(np.searchsorted(np.cumsum(w),q,side="left"),len(x)-1)])

def weighted_crps(sample,w,observed):
    x,w=_values(sample,w)
    if not np.isfinite(observed): raise ValueError("observation must be finite")
    order=np.argsort(x,kind="stable"); x,w=x[order],w[order]
    wb=np.cumsum(w)-w; sb=np.cumsum(w*x)-w*x
    return float(np.dot(w,np.abs(x-observed))-np.dot(w,x*wb-sb))

def eligible_pool(starts,query,horizon_hours,embargo_hours):
    t=pd.DatetimeIndex(starts); d=pd.Timestamp(query)
    if t.tz is None or d.tzinfo is None or horizon_hours<=0 or embargo_hours<0:
        raise ValueError("UTC-aware times and positive horizon required")
    return np.asarray(t+pd.Timedelta(hours=horizon_hours)<=d-pd.Timedelta(hours=embargo_hours))

def mix_weights(n,picked,alpha):
    picked=np.asarray(picked,dtype=int)
    if not isinstance(n,(int,np.integer)) or n<=0 or not np.isfinite(alpha) or not 0<=alpha<=1:
        raise ValueError("invalid mixture")
    if picked.ndim!=1 or len(set(picked))!=len(picked) or (picked<0).any() or (picked>=n).any():
        raise ValueError("invalid selected indices")
    if alpha>0 and not len(picked): raise ValueError("positive adaptive mass requires selected windows")
    out=np.full(n,(1-alpha)/n,dtype=float)
    if len(picked): out[picked]+=alpha/len(picked)
    return normalized_weights(out)

def grouped_bootstrap_delta(starts,delta,w,reps,seed,level):
    x,w=_values(delta,w); t=pd.DatetimeIndex(starts)
    if len(t)!=len(x) or t.tz is None or reps<2 or not 0<level<1:
        raise ValueError("invalid bootstrap specification")
    labels=t.tz_convert("UTC").strftime("%Y-%m")
    groups=pd.factorize(labels,sort=True)[0]; n=int(groups.max()+1)
    mass=np.bincount(groups,weights=w,minlength=n)
    numerator=np.bincount(groups,weights=w*x,minlength=n)
    rng=np.random.default_rng(seed)
    draws=rng.integers(0,n,size=(reps,n))
    den=mass[draws].sum(axis=1); num=numerator[draws].sum(axis=1)
    valid=den>0
    if not valid.any(): raise ValueError("bootstrap has no positive mass")
    estimates=num[valid]/den[valid]; tail=(1-level)/2
    return {"mean":float(np.dot(w,x)),"lower":float(np.quantile(estimates,tail)),
            "upper":float(np.quantile(estimates,1-tail)),"clusters":n,"valid_reps":int(valid.sum())}

    cols=["episode_id","signal_time","entry_time","cover_signal_time","cover_time",
          "entry_bid","cover_ask","entry_lag_seconds","cover_lag_seconds"]
    if any(c not in events for c in cols) or not np.isfinite(fee) or fee<0 or minimum_events<1:
        raise ValueError("invalid short ledger or settings")
    if not len(events):
        return {"eligible":False,"n_events":0,"n_episodes":0,"mean_net":None}
    d=events.copy()
    if d.episode_id.isna().any(): raise ValueError("episode identity missing")
    for c in ["signal_time","entry_time","cover_signal_time","cover_time"]:
        d[c]=pd.to_datetime(d[c],utc=True,errors="raise")
        if d[c].isna().any(): raise ValueError("timestamp missing")
    numeric=d[["entry_bid","cover_ask","entry_lag_seconds","cover_lag_seconds"]].to_numpy(float)
    if not np.isfinite(numeric).all() or (numeric[:,:2]<=0).any() or (numeric[:,2:]<=0).any():
        raise ValueError("invalid executable prices or delays")
    entry_min=d.signal_time+pd.to_timedelta(d.entry_lag_seconds,unit="s")
    cover_min=d.cover_signal_time+pd.to_timedelta(d.cover_lag_seconds,unit="s")
    if (d.entry_time<entry_min).any() or (d.cover_time<cover_min).any() or (d.cover_signal_time<d.entry_time).any():
        raise ValueError("entry or cover violates causal availability and execution delay")
    ratio=d.cover_ask/d.entry_bid
    d["net"]=1-ratio-fee*(1+ratio)
    episode=d.groupby("episode_id",sort=False).net.mean()
    return {"eligible":bool(len(episode)>=minimum_events),"n_events":len(d),"n_episodes":len(episode),
            "mean_net":float(episode.mean()),"trade_mean_net":float(d.net.mean()),
            "positive_episode_share":float((episode>0).mean()),
            "worst_episode":float(episode.min()),"episode_net":episode.to_dict()}

def block_bootstrap_interval(values,block,reps,seed,level):
    x=np.asarray(values,dtype=float)
    if x.ndim!=1 or not len(x) or not np.isfinite(x).all() or block<1 or reps<2 or not 0<level<1:
        raise ValueError("invalid moving-block bootstrap")
    n=len(x); rng=np.random.default_rng(seed)
    origins=rng.integers(0,n,size=(reps,int(np.ceil(n/block))))
    idx=(origins[:,:,None]+np.arange(block)[None,None,:])%n
    draws=x[idx.reshape(reps,-1)[:,:n]].mean(axis=1); tail=(1-level)/2
    return {"mean":float(x.mean()),"lower":float(np.quantile(draws,tail)),
            "upper":float(np.quantile(draws,1-tail))}
