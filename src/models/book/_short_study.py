"""Research-frozen causal trend, rebound and breakdown mechanisms; no I/O."""
from __future__ import annotations
import numpy as np
import pandas as pd
from src.contracts import MarketView, ModelSpec

def frames(view):
    p=view.params
    coins=[c for c in p["coins"] if c in view.universe]
    n=max(max(p["lookbacks_hours"]),p["vol_hours"],p["volume_recent_hours"]+p["volume_base_hours"],
          p["breakdown_hours"],p["rebound_hours"],p["breadth_hours"])+1
    close=view.close.loc[:view.t].reindex(columns=coins).tail(n)
    qv=view.quote_volume.loc[:view.t].reindex(index=close.index,columns=coins)
    if len(close)<n or close.index[-1]!=view.t:
        return close.iloc[:0], qv.iloc[:0]
    # Clock-hour continuity is required. Missing current/volatility observations fail closed.
    if not np.all(np.diff(close.index.asi8)==pd.Timedelta(hours=1).value):
        return close.iloc[:0], qv.iloc[:0]
    return close,qv

def risk_weights(close, forecast, p):
    if close.empty:
        return pd.Series(dtype=float)
    x=close.tail(p["vol_hours"]+1)
    valid=x.notna().all() & (x>0).all()
    sigma=np.log(x.where(x>0)).diff().std(ddof=1)
    valid &= np.isfinite(sigma) & (sigma>0)
    sigma=sigma[valid]
    if sigma.empty:
        return pd.Series(dtype=float)
    inv=1/sigma
    base=(inv/inv.sum()).clip(upper=p["coin_cap"])
    w=base*forecast.reindex(base.index).fillna(0).clip(-1,1)
    conservative=float((w.abs()*sigma*np.sqrt(24)).sum())
    gross=float(w.abs().sum())
    scale=min(1.,p["gross_cap"]/gross if gross else 1.,
              p["target_daily_vol"]/conservative if conservative else 1.)
    return (w*scale)[lambda z:z!=0]

def trend(close,p):
    if close.empty:
        return pd.Series(dtype=float)
    sigma=np.log(close.tail(p["vol_hours"]+1).where(close>0)).diff().std(ddof=1)
    pieces=[]
    for h in p["lookbacks_hours"]:
        pieces.append(np.log(close.iloc[-1]/close.iloc[-h-1])/(sigma*np.sqrt(h)))
    return pd.concat(pieces,axis=1).mean(axis=1).clip(-1,1)

def rebounds(close,p):
    if close.empty:
        return pd.Series(dtype=bool)
    return close.iloc[-1] > close.iloc[-p["rebound_hours"]-1:-1].max()

class DirectionalStudy:
    def __init__(self,name,mode):
        self.mode=mode
        self.spec=ModelSpec(name=name,method="trend",author="book",rebalance_hours=1,
                           band=.03,uses_shorts=True,
                           description="Research-frozen "+mode+" with causal clocks and conservative volatility sizing")

    def targets(self,view:MarketView)->pd.Series:
        p=view.params
        prior=view.prev_targets.reindex([c for c in p["coins"] if c in view.universe]).dropna()
        prior=prior[prior!=0]
        daily=view.t.hour==p["entry_hour_utc"]
        check=(view.t.hour-p["entry_hour_utc"])%p["exit_check_hours"]==0
        if self.mode=="trend" and not daily:
            return prior
        if self.mode=="rebound" and not (daily or check):
            return prior
        if self.mode=="breakdown" and not check:
            return prior
        close,qv=frames(view)
        if close.empty:
            return pd.Series(dtype=float)
        stop=rebounds(close,p)
        if self.mode in ("trend","rebound"):
            if daily:
                forecast=trend(close,p)
                if self.mode=="rebound":
                    forecast=forecast.mask((forecast<0)&stop,0.)
                return risk_weights(close,forecast,p)
            # Exit-only intermediate checks; no intraday short re-entry.
            return prior[~((prior<0)&stop.reindex(prior.index).fillna(True))]
        recent=p["volume_recent_hours"];base=p["volume_base_hours"]
        numerator=qv.iloc[-recent:].mean()
        denominator=qv.iloc[-recent-base:-recent].mean()
        complete=(qv.iloc[-recent:].notna().all() &
                  qv.iloc[-recent-base:-recent].notna().all() &
                  (qv.iloc[-recent-base:]>=0).all())
        volume=complete & (denominator>0) & (numerator/denominator>=p["volume_ratio"])
        entry=close.iloc[-1]<close.iloc[-p["breakdown_hours"]-1:-1].min()
        r=np.log(close.iloc[-1]/close.iloc[-p["breadth_hours"]-1])
        valid=np.isfinite(r)
        weak=(int(valid.sum())>=p["breadth_min_coins"] and
              p["breadth_reference"] in r and np.isfinite(r[p["breadth_reference"]]) and
              r[p["breadth_reference"]]<0 and
              float((r[valid]>0).mean())<=p["breadth_positive_max"])
        held=prior.reindex(close.columns).fillna(0)<0
        selected=(held | (entry&volume&weak)) & ~stop
        return risk_weights(close,-selected.astype(float),p)
