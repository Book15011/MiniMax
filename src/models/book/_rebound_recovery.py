"""Frozen main-short rebound guards. Pure directional research models."""
from dataclasses import replace
import numpy as np
import pandas as pd
from src.models.book._recovery import causal
from src.models.book import _cashshort
from src.models.book.book_e20combo_brk_cash import MODEL as BASE

def rebounding(view,p):
    v=causal(view)
    if p["volume_fill_hours"]:
        v=replace(v,quote_volume=v.quote_volume.ffill(limit=int(p["volume_fill_hours"])))
    _,breadth=_cashshort.liquid_breadth(v,p["breadth"])
    if breadth is None or breadth<=float(p["breadth_majority"]):
        return False
    px=v.close.reindex(index=[v.t-pd.Timedelta(hours=int(p["rebound_hours"])),v.t],columns=[p["btc_symbol"]])
    if not _cashshort._valid_prices(px):
        return False
    return bool(px.iloc[-1,0]>px.iloc[0,0])

def adjust(view,w,p,*,market):
    v=causal(view)
    if not (w<0).any():
        return w.copy()
    if market:
        if not rebounding(v,p):
            return w.copy()
        z=w[w>0].copy()
    else:
        short=w.index[w<0]
        px=v.close.reindex(index=[v.t-pd.Timedelta(hours=int(p["confirm_hours"])),v.t],columns=short)
        ok=np.isfinite(px).all()&(px>0).all()
        rising=ok&(px.iloc[-1]>px.iloc[0])
        z=w.drop(index=rising.index[rising]).copy()
    if z.equals(w):
        return w.copy()
    hours=int(p["vol_days"])*24
    ix=pd.date_range(end=v.t,periods=hours+1,freq="h")
    c=v.close.reindex(index=ix,columns=w.index).where(lambda a:a>0)
    ret=c.pct_change(fill_method=None).iloc[1:].dropna(how="any")
    if len(ret)<hours*float(p["min_complete"]):
        return w.copy()
    cov=ret.cov().to_numpy()*24.
    if not np.isfinite(cov).all():
        return w.copy()
    a=w.to_numpy();b=z.reindex(w.index).fillna(0).to_numpy()
    oldrisk=max(float(a@cov@a),0.);newrisk=max(float(b@cov@b),0.)
    if newrisk>oldrisk:
        z*=np.sqrt(oldrisk/newrisk)
    return z[z!=0.]

class ReboundRecovery:
    MARKET=False
    def targets(self,view):
        v=causal(view);p=v.params
        w=BASE.targets(replace(v,params=p["parent"]))
        return adjust(v,w,p,market=self.MARKET)
