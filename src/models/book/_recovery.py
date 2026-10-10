"""Finite recovery hypotheses on the exact brk-cash parent; PROTOCOL.md. Research only."""
from dataclasses import replace
import numpy as np
import pandas as pd
from src.contracts import MarketView
from src.models.book.book_e20combo_brk_cash import MODEL as BASE
from src.models.pol._combo import Combo

def causal(v):
    return replace(v,close=v.close.loc[:v.t],quote_volume=v.quote_volume.loc[:v.t])

def vol_factor(view,w,p):
    if w.empty: return 1.
    v=causal(view)
    slow,fast=int(p["slow_days"])*24,int(p["fast_days"])*24
    ix=pd.date_range(end=v.t,periods=slow+1,freq="h")
    px=v.close.reindex(index=ix,columns=w.index)
    returns=px.pct_change(fill_method=None).iloc[1:]
    complete=np.isfinite(returns).all(axis=1)
    risk=returns.mul(w,axis=1).sum(axis=1).where(complete)
    s,f=risk.iloc[-slow:].dropna(),risk.iloc[-fast:].dropna()
    if len(s)<slow*float(p["min_complete"]) or len(f)<fast*float(p["min_complete"]): return 1.
    sigs,sigf=float(s.std()),float(f.std())
    if not np.isfinite([sigs,sigf]).all() or sigf<=0: return 1.
    return float(np.clip(sigs/sigf,0.,1.))

def confirm_cash_shorts(view,w,p,*,down_mode):
    if down_mode or not (w<0).any(): return w.copy()
    v=causal(view)
    times=[v.t-pd.Timedelta(hours=int(p["short_confirm_hours"])),v.t]
    px=v.close.reindex(index=times,columns=w.index)
    valid=np.isfinite(px).all() & (px>0).all()
    ret=px.iloc[-1]/px.iloc[0]-1
    keep=(w>0) | ((w<0)&valid&(ret<=0))
    return w[keep].copy()

def adjusted(view,w,p,*,vol,short,down_mode):
    z=confirm_cash_shorts(view,w,p,down_mode=down_mode) if short else w.copy()
    if vol: z=z*vol_factor(view,z,p)
    return z[z!=0.]

class Recovery:
    VOL=False
    SHORT=False
    def targets(self,view):
        v=causal(view); p=v.params
        pv=replace(v,params=p["parent"])
        w=BASE.targets(pv)
        down=Combo.state(pv,p["parent"]["base"]["vt"])=="down"
        return adjusted(v,w,p,vol=self.VOL,short=self.SHORT,down_mode=down)
