"""Fixed near-high selection and parent-momentum blend. Directional research only."""
from dataclasses import replace
import numpy as np
import pandas as pd
from src.models.book._recovery import causal
from src.models.book.book_e20combo_brk_cash import MODEL as BASE
from src.models.pol._combo import Combo
from src.models.baitoey._volume_signals import momentum_score,breakdown_blocked,chase_blocked
from src.models.baitoey._overlays import blocked

def empty():
    return pd.Series(dtype=float)

def scores(view,p):
    """Inclusive hourly-close high proxy; require every positive formation close."""
    v=causal(view)
    hours=max(p["lookback_days"])*24
    cols=sorted(v.universe)
    ix=pd.date_range(end=v.t,periods=hours+1,freq="h")
    close=v.close.reindex(index=ix,columns=cols)
    valid=np.isfinite(close).all(axis=0)&(close>0).all(axis=0)
    close=close.loc[:,valid]
    if close.empty:
        return empty(),empty()
    terms=[np.log(close.iloc[-1]/close.iloc[-(int(d)*24+1):].max()) for d in p["lookback_days"]]
    high=(sum(terms)/len(terms)).replace([np.inf,-np.inf],np.nan).dropna()
    raw=momentum_score(close,list(p["lookback_days"])).reindex(high.index).dropna()
    return high,raw

def adjust(view,w,p,*,blend,up):
    if not up or not (w>0).any():
        return w.copy()
    v=causal(view)
    high,raw=scores(v,p)
    if high.empty:
        return w.copy()
    if blend:
        common=high.index.intersection(raw.index)
        mix=float(p["blend_weight"])
        score=(1-mix)*raw.loc[common].rank(pct=True)+mix*high.loc[common].rank(pct=True)
    else:
        score=high.copy()
    score=score.drop(index=w.index[w<0],errors="ignore")
    fp=p["filter_params"]
    need=int(fp["volume_long_days"])*24+max(int(fp["volume_short_hours"]),int(fp["chase_return_hours"]))+max(
        int(fp["exit_cooldown_hours"])+int(fp["exit_low_hours"]),int(fp["chase_window_hours"]))+1
    c=v.close.reindex(columns=score.index).iloc[-need:]
    q=v.quote_volume.reindex(index=c.index,columns=score.index)
    skip=set()
    if fp["early_exit"]:
        skip|=breakdown_blocked(c,q,fp)
    if fp["no_chase"]:
        skip|=chase_blocked(c,q,fp)
    skip|=blocked(v,list(score.index),int(p["channel_days"]),int(p["scan_days"]))
    score=score.drop(index=list(skip),errors="ignore").sort_index()
    if score.empty:
        return w.copy()
    rank=score.rank(ascending=False,method="first")
    held=[coin for coin in sorted(v.prev_targets.index)
          if v.prev_targets[coin]>0 and coin in rank and rank[coin]<=int(p["keep_rank"])]
    held=held[:int(p["k"])]
    for coin in rank.sort_values().index:
        if len(held)>=int(p["k"]):
            break
        if coin not in held:
            held.append(coin)
    new=pd.Series(float(w[w>0].sum())/len(held),index=sorted(held))
    cols=w.index.union(new.index).sort_values()
    hours=int(p["vol_days"])*24
    grid=pd.date_range(end=v.t,periods=hours+1,freq="h")
    ret=v.close.reindex(index=grid,columns=cols).pct_change(fill_method=None).iloc[1:].dropna(how="any")
    if len(ret)<hours*float(p["min_complete"]):
        return w.copy()
    cov=ret.cov().to_numpy()*24.
    if not np.isfinite(cov).all():
        return w.copy()
    oldlong=w.clip(lower=0).reindex(cols).fillna(0).to_numpy()
    newlong=new.reindex(cols).fillna(0).to_numpy()
    oldrisk=float(oldlong@cov@oldlong)
    newrisk=float(newlong@cov@newlong)
    if newrisk>oldrisk and newrisk>0:
        new*=np.sqrt(max(oldrisk,0)/newrisk)
    out=pd.concat([new[new>0],w[w<0]])
    a=w.reindex(cols).fillna(0).to_numpy()
    b=out.reindex(cols).fillna(0).to_numpy()
    if float(b@cov@b)>float(a@cov@a)+1e-12:
        return w.copy()
    return out

class HighRecovery:
    BLEND=False
    def targets(self,view):
        v=causal(view)
        p=v.params
        parent_view=replace(v,params=p["parent"])
        w=BASE.targets(parent_view)
        up=Combo.state(parent_view,p["parent"]["base"]["vt"])=="up"
        return adjust(v,w,p,blend=self.BLEND,up=up)
