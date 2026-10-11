"""Independent rejection-only reporting math; no strategy or ranking logic."""
import numpy as np
import pandas as pd

def outcome(equity,gross,hours,liquidation_cost):
    e=np.asarray(equity,dtype=float);g=np.asarray(gross,dtype=float)
    if e.ndim!=2 or g.shape!=e.shape or not 0<hours<e.shape[1]:
        raise ValueError("invalid aligned hourly arrays/horizon")
    if not np.isfinite(e[:,:hours+1]).all() or (e[:,:hours+1]<=0).any():
        raise ValueError("invalid equity")
    if not np.isfinite(g[:,:hours+1]).all() or (g[:,:hours+1]<0).any() or not 0<=liquidation_cost<1:
        raise ValueError("invalid exposure/cost")
    ret=e[:,hours]/e[:,0]*(1-liquidation_cost*g[:,hours])-1
    dd=np.min(e[:,:hours+1]/np.maximum.accumulate(e[:,:hours+1],axis=1)-1,axis=1)
    return ret,dd

def paired_stability(candidate,baseline,hours=336):
    cols=["start","return"]
    a=candidate[cols].copy();b=baseline[cols].copy()
    if a.start.duplicated().any() or b.start.duplicated().any():
        raise ValueError("duplicate windows")
    f=a.merge(b,on="start",how="outer",suffixes=("_new","_base"),validate="one_to_one",indicator=True)
    if not f["_merge"].eq("both").all(): raise ValueError("unmatched windows")
    f=f.sort_values("start").drop(columns="_merge").reset_index(drop=True)
    t=pd.DatetimeIndex(f.start)
    if t.tz is None or not np.isfinite(f[["return_new","return_base"]]).all().all():
        raise ValueError("invalid time or outcome")
    f["delta"]=f.return_new-f.return_base
    end=t.tz_localize(None).to_period("Y").end_time.tz_localize(t.tz)
    p=f.loc[t+pd.Timedelta(hours=hours)<=end].copy()
    p["year"]=pd.DatetimeIndex(p.start).year
    years=[]
    for y,g in p.groupby("year"):
        years.append({"year":int(y),"n":len(g),"mean_delta":float(g.delta.mean()),
                      "mean_new":float(g.return_new.mean()),"mean_base":float(g.return_base.mean())})
    loo=[]
    for y in sorted(p.year.unique()):
        g=p.loc[p.year!=y]
        if len(g):
            loo.append({"omitted_year":int(y),"n":len(g),"mean_delta":float(g.delta.mean())})
    # Calendar-day residues retain all fourteen choices; not fourteen independent samples.
    anchor=t[0].normalize()
    residue=((t.normalize()-anchor)/pd.Timedelta(days=1)).astype(int)%14
    offsets=[]
    for offset in range(14):
        g=f.loc[residue==offset]
        ix=pd.DatetimeIndex(g.start)
        gap=float(np.min(np.diff(ix.asi8)/3.6e12)) if len(g)>1 else None
        if gap is not None and gap<336: raise ValueError("disjoint fortnight overlap")
        offsets.append({"offset":offset,"n":len(g),"minimum_gap_hours":gap,
                        "mean_delta":float(g.delta.mean()) if len(g) else None})
    d=f.delta.to_numpy();positive=d[d>1e-12]
    concentration=None
    if len(positive):
        k=max(1,int(np.ceil(len(positive)*.1)))
        concentration=float(np.sort(positive)[-k:].sum()/positive.sum())
    return {"n":len(f),"calendar_purged_n":len(p),"calendar_years":years,"leave_one_year_out":loo,
            "strictly_positive_year_share":float(np.mean([v["mean_delta"]>0 for v in years])) if years else None,
            "paired_win_share":float(np.mean(d>1e-12)),"paired_loss_share":float(np.mean(d<-1e-12)),
            "paired_tie_share":float(np.mean(np.abs(d)<=1e-12)),
            "largest_10pct_positive_windows_share_of_gross_gains":concentration,
            "disjoint_offsets":offsets,"independent_holdout":False,"post_selection_descriptive_only":True}
