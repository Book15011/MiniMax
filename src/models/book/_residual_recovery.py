"""Two frozen BTC-adjusted long-selection hypotheses. Pure directional research models."""
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
    """Beta trains strictly before both formation windows; no strategy-return fitting."""
    v=causal(view)
    train=int(p["beta_days"])*24
    formation=max(p["lookback_days"])*24
    cols=sorted(set(v.universe)|{"BTCUSDT"})
    ix=pd.date_range(end=v.t,periods=train+formation+1,freq="h")
    close=v.close.reindex(index=ix,columns=cols).where(lambda x:x>0)
    logrets=np.log(close).diff().iloc[1:]
    x=logrets["BTCUSDT"].iloc[:train]
    if x.notna().sum()<train*float(p["min_complete"]):
        return empty(),empty(),empty()
    beta={}
    residual={}
    for coin in sorted(v.universe):
        y=logrets[coin].iloc[:train]
        valid=x.notna()&y.notna()
        if valid.sum()<train*float(p["min_complete"]):
            continue
        a=x[valid].to_numpy();b=y[valid].to_numpy()
        variance=float(np.mean((a-a.mean())**2))
        if not np.isfinite(variance) or variance<=1e-24:
            continue
        coefficient=float(np.mean((a-a.mean())*(b-b.mean()))/variance)
        z=logrets[coin].iloc[-formation:]-coefficient*logrets["BTCUSDT"].iloc[-formation:]
        if not np.isfinite(z).all():
            continue
        terms=[]
        for days in p["lookback_days"]:
            zz=z.iloc[-int(days)*24:]
            sigma=float(zz.std())
            if sigma<=1e-12:
                if np.abs(zz).max()<=1e-12:
                    terms.append(0.)
                else:
                    terms=[];break
            else:
                terms.append(float(zz.sum()/(sigma*np.sqrt(len(zz)))))
        if terms:
            beta[coin]=coefficient
            residual[coin]=float(np.mean(terms))
    beta=pd.Series(beta,dtype=float)
    residual=pd.Series(residual,dtype=float).replace([np.inf,-np.inf],np.nan).dropna()
    raw=momentum_score(close,list(p["lookback_days"])).reindex(residual.index).dropna()
    return beta,residual,raw

def adjust(view,w,p,*,blend,up):
    if not up or not (w>0).any():
        return w.copy()
    v=causal(view)
    _,resid,raw=scores(v,p)
    if resid.empty:
        return w.copy()
    if blend:
        common=resid.index.intersection(raw.index)
        mix=float(p["blend_weight"])
        score=(1-mix)*raw.loc[common].rank(pct=True)+mix*resid.loc[common].rank(pct=True)
    else:
        score=resid.copy()
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

class ResidualRecovery:
    BLEND=False
    def targets(self,view):
        v=causal(view)
        p=v.params
        parent_view=replace(v,params=p["parent"])
        w=BASE.targets(parent_view)
        up=Combo.state(parent_view,p["parent"]["base"]["vt"])=="up"
        return adjust(v,w,p,blend=self.BLEND,up=up)
