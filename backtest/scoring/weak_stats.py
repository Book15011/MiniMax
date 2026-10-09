"""Predeclared causal scenario selection and joint uncertainty for model comparisons."""
from __future__ import annotations
import numpy as np
import pandas as pd
from research.book.regime_eval.features import match_windows
from src.validation.selection import PickRules

def select_cases(features,query,asof,hours,cfg,mode="weak",groups=None,k=None):
    """Select matured historical states using predeclared observed features."""
    if mode not in ("weak","positive"):
        raise ValueError("selection mode must be weak or positive")
    declared=cfg["features"]
    groups=declared if groups is None else groups
    if not isinstance(groups,dict) or not groups:
        raise ValueError("nonempty predeclared feature groups required")
    for name,members in groups.items():
        if (name not in declared or not isinstance(members,(list,tuple)) or not members
                or list(members)!=list(declared[name])):
            raise ValueError("unknown or changed feature group")
    cols=[v for members in groups.values() for v in members]
    if len(cols)!=len(set(cols)) or not all(isinstance(v,str) and v for v in cols):
        raise ValueError("feature groups must contain unique named features")
    if (not isinstance(hours,(int,np.integer)) or isinstance(hours,(bool,np.bool_)) or hours<=0):
        raise ValueError("positive integer replay hours required")
    count=cfg["lookalikes"]["k"] if k is None else k
    if (not isinstance(count,(int,np.integer)) or isinstance(count,(bool,np.bool_)) or count<=0):
        raise ValueError("positive integer case count required")
    embargo=cfg["embargo_hours"]
    if (not isinstance(embargo,(int,np.integer)) or isinstance(embargo,(bool,np.bool_)) or embargo<0):
        raise ValueError("nonnegative integer embargo hours required")
    if (not isinstance(features,pd.DataFrame) or not features.columns.is_unique
            or not isinstance(features.index,pd.DatetimeIndex) or features.index.tz is None
            or features.index.isna().any() or not features.index.is_unique):
        raise ValueError("historical states require unique aware timestamps and feature columns")
    if not isinstance(query,pd.Series) or not query.index.is_unique:
        raise ValueError("query must be one uniquely labeled feature state")
    state_cols=["btc_ret48","breadth48"]+(["btc_ret24"] if mode=="weak" else [])
    required=list(dict.fromkeys(cols+state_cols))
    if not set(required)<=set(features.columns) or not set(cols)<=set(query.index):
        raise ValueError("historical or query matching features incomplete")
    try:
        query_values=query[cols].to_numpy(float)
        state_values=features[required].to_numpy(float)
        cutoff=pd.Timestamp(asof)
    except (TypeError,ValueError) as exc:
        raise ValueError("numeric features and a valid aware asof timestamp required") from exc
    if cutoff is pd.NaT or cutoff.tzinfo is None:
        raise ValueError("asof must be a valid aware timestamp")
    if not np.isfinite(query_values).all():
        raise ValueError("query features incomplete")
    f=features.loc[np.isfinite(state_values).all(axis=1)].sort_index().copy()
    mature=f.index+pd.Timedelta(hours=int(hours)+int(embargo))<=cutoff
    f=f.loc[mature]
    definition=cfg["weak"] if mode=="weak" else cfg["positive"]
    scenario=(f.btc_ret48>=definition["ret48_min"])&(f.btc_ret48<=definition["ret48_max"])
    if mode=="weak":
        scenario &= (f.breadth48<=definition["breadth_max"])&(f.btc_ret24<=definition["ret24_max"])
    else: scenario &= f.breadth48>=definition["breadth_min"]
    f=f.loc[scenario]
    rules=PickRules(**{**cfg["lookalikes"],"k":int(count)},horizon_days=int(np.ceil(hours/24)))
    if len(f)<rules.k:raise ValueError("insufficient causal scenario pool")
    picked=match_windows(f,query,groups,rules)
    if len(picked)!=rules.k:raise ValueError("insufficient separated causal cases")
    table=f.loc[picked.t0,cols].copy()
    table["distance"]=picked.set_index("t0").distance
    table["weight"]=1/len(table)
    return table.sort_index()

def clustered_draws(starts,reps,seed,hours=240):
    """Resample calendar-quarter clusters, conservatively joining overlaps.

    Quarter membership already groups separated windows from the same broad
    episode. If replay intervals share any time across a quarter boundary,
    their quarter labels are joined before resampling. Endpoint-only contact
    is also joined conservatively. The returned count is merged clusters.
    """
    t=pd.DatetimeIndex(starts)
    if (t.tz is None or not t.is_unique or t.isna().any() or not len(t)
            or not isinstance(reps,(int,np.integer)) or isinstance(reps,(bool,np.bool_))
            or reps<100):
        raise ValueError("unique valid aware starts and at least100 integer bootstrap draws required")
    if (not isinstance(hours,(int,np.integer)) or isinstance(hours,(bool,np.bool_)) or hours<=0):
        raise ValueError("positive integer replay hours required")
    t=t.tz_convert("UTC")
    labels=t.tz_localize(None).to_period("Q")
    raw=pd.factorize(labels,sort=True)[0]
    parent=np.arange(int(raw.max()+1))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]]
            i=int(parent[i])
        return i
    def join(i,j):
        ri,rj=root(int(i)),root(int(j))
        if ri!=rj:parent[max(ri,rj)]=min(ri,rj)
    order=np.argsort(t.asi8)
    width=pd.Timedelta(hours=int(hours))
    for pos,index in enumerate(order):
        for previous in order[:pos][::-1]:
            if t[index]-t[previous]>width:break
            join(raw[index],raw[previous])
    groups=pd.factorize(np.asarray([root(int(i)) for i in raw]),sort=True)[0]
    n=int(groups.max()+1)
    if n<2:raise ValueError("at least two nonoverlapping quarter clusters required")
    rng=np.random.default_rng(seed)
    draws=rng.multinomial(n,np.full(n,1/n),size=int(reps))
    mass=draws[:,groups].astype(float)
    return mass/mass.sum(axis=1,keepdims=True),n

def simultaneous_bounds(values,incumbent,draws,level,weights=None):
    """One joint centered, standardized bootstrap bound using fixed bootstrap SE."""
    try:
        x=np.asarray(values,float);d=np.asarray(draws,float);confidence=float(level)
    except (TypeError,ValueError) as exc:
        raise ValueError("numeric values, draws and confidence level required") from exc
    if (x.ndim!=3 or d.ndim!=2 or any(v<=0 for v in x.shape)
            or x.shape[1]!=d.shape[1] or not np.isfinite(x).all()
            or not np.isfinite(confidence) or not 0<confidence<1):
        raise ValueError("finite nonempty model/window/context values required")
    m,n,c=x.shape
    if (not isinstance(incumbent,(int,np.integer)) or isinstance(incumbent,(bool,np.bool_))
            or not 0<=incumbent<m):
        raise ValueError("incumbent must be a valid integer model index")
    if (len(d)<2 or not np.isfinite(d).all() or (d<0).any()
            or not np.isfinite(d.sum(axis=1)).all() or (d.sum(axis=1)<=0).any()):
        raise ValueError("at least two finite nonnegative positive-mass bootstrap draws required")
    d=d/d.sum(axis=1,keepdims=True)
    try:
        w=np.ones((n,c))/n if weights is None else np.asarray(weights,float)
    except (TypeError,ValueError) as exc:
        raise ValueError("numeric context weights required") from exc
    if (w.shape!=(n,c) or not np.isfinite(w).all() or (w<0).any()
            or not np.isfinite(w.sum(axis=0)).all() or (w.sum(axis=0)<=0).any()):
        raise ValueError("invalid context weights")
    w=w/w.sum(axis=0)
    dw=d[:,:,None]*w[None,:,:]
    den=dw.sum(axis=1);valid=(den>0).all(axis=1)
    if valid.sum()<2 or valid.sum()<len(d)*.95:
        raise ValueError("too many empty profile bootstrap draws")
    dw=dw[valid]/den[valid,None,:]
    mean=np.einsum("mnc,nc->mc",x,w)
    boot=np.einsum("rnc,mnc->rmc",dw,x,optimize=True)
    delta=mean-mean[incumbent];boot_delta=boot-boot[:,incumbent:incumbent+1,:]
    stacked=np.stack([mean,delta],axis=-1)
    resampled=np.stack([boot,boot_delta],axis=-1)
    if not np.isfinite(stacked).all() or not np.isfinite(resampled).all():
        raise ValueError("bootstrap estimates are not finite")
    se=resampled.std(axis=0,ddof=1)
    if not np.isfinite(se).all():
        raise ValueError("bootstrap standard errors are not finite")
    for context in range(c):
        support=w[:,context]>0
        cash_values=x[:,support,context]
        paired_values=cash_values-x[incumbent,support,context][None,:]
        nonconstant=np.stack([np.ptp(cash_values,axis=1)>1e-14,
                              np.ptp(paired_values,axis=1)>1e-14],axis=-1)
        if np.any((se[:,context,:]<=1e-14)&nonconstant):
            raise ValueError("degenerate bootstrap: nonconstant supported returns have zero standard error")
    z=np.divide(resampled-stacked[None,:,:,:],se[None,:,:,:],
                out=np.zeros_like(resampled),where=se[None,:,:,:]>1e-14)
    critical=max(0.,float(np.quantile(z.max(axis=(1,2,3)),confidence)))
    lower=stacked-critical*se
    # Only numerically constant supported values or contrasts may be exact.
    lower=np.where(se<=1e-14,stacked,lower)
    tail=(1-confidence)/2
    return {"mean":mean,"delta":delta,"cash_family_lower":lower[:,:,0],
            "delta_family_lower":lower[:,:,1],"family_lower":np.minimum(lower[:,:,0],lower[:,:,1]),
            "cash_lower90":np.quantile(boot,tail,axis=0),
            "cash_upper90":np.quantile(boot,1-tail,axis=0),
            "delta_lower90":np.quantile(boot_delta,tail,axis=0),
            "delta_upper90":np.quantile(boot_delta,1-tail,axis=0),
            "family_quantile":critical,"valid_reps":int(valid.sum()),"standard_error":se,
            "boot_means":boot}

def tail_mean(x,fraction):
    a=np.sort(np.asarray(x,float))
    if a.ndim!=1 or not len(a) or not np.isfinite(a).all() or not 0<fraction<=1:
        raise ValueError("invalid tail sample")
    mass=len(a)*fraction;whole=int(np.floor(mass));part=mass-whole
    total=a[:whole].sum()+(part*a[whole] if whole<len(a) else 0.)
    return float(total/mass)
