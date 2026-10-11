"""Fixed selection/sizing controls, independent of clone-fitted coefficients. Research only."""
from dataclasses import replace
import numpy as np
import pandas as pd
from src.models.book.book_e20combo_brk_cash import MODEL as BASE
from src.models.book._recovery import causal
from src.models.pol._combo import Combo
from src.models.baitoey._volume_signals import momentum_score

def adjust_selection(view,w,p,*,absolute,inverse,up):
    if not up or not (absolute or inverse):return w.copy()
    v=causal(view); z=w.copy(); longs=z[z>0]
    if longs.empty:return z
    h=int(p["vol_days"])*24
    ix=pd.date_range(end=v.t,periods=max(h,max(p["lookback_days"])*24)+1,freq="h")
    c=v.close.reindex(index=ix,columns=longs.index)
    if absolute:
        scores=momentum_score(c,list(p["lookback_days"]))
        keep=scores[scores>0].index
        z=z[(z<0)|z.index.isin(keep)]
        longs=z[z>0];c=c.reindex(columns=longs.index)
    if inverse and len(longs):
        rets=c.pct_change(fill_method=None).iloc[-h:].dropna(how="any")
        if len(rets)<h*float(p["min_complete"]):return z
        cov=rets.cov().to_numpy()*24.
        sigma=rets.std()*np.sqrt(24.)
        if not np.isfinite(sigma).all() or (sigma<=0).any():return z
        inv=1./sigma
        new=(inv/inv.sum()*float(longs.sum())).clip(upper=float(p["coin_cap"]))
        a=longs.to_numpy();b=new.to_numpy()
        oldrisk=np.sqrt(max(float(a@cov@a),0.));newrisk=np.sqrt(max(float(b@cov@b),0.))
        if newrisk>oldrisk and newrisk>0:new*=oldrisk/newrisk
        z=pd.concat([new[new>0],z[z<0]])
    return z[z!=0.]

class Selection:
    ABS=False
    IV=False
    def targets(self,view):
        v=causal(view);p=v.params;pv=replace(v,params=p["parent"])
        w=BASE.targets(pv)
        up=Combo.state(pv,p["parent"]["base"]["vt"])=="up"
        return adjust_selection(v,w,p,absolute=self.ABS,inverse=self.IV,up=up)
