"""Conditional historical frequencies; no current top20 probability inference."""
import numpy as np,pandas as pd
def summarize(f,hours):
    f=f.sort_values("start").copy()
    if not np.isfinite(f[["return","mdd"]]).all().all():raise ValueError("missing outcome")
    if f.start.duplicated().any():raise ValueError("duplicate start")
    if len(f)==0:return {"n_windows":0,"p19":None,"p215":None,"p25":None}
    t=pd.DatetimeIndex(f.start);end=t.tz_localize(None).to_period("Q").end_time.tz_localize("UTC")
    p=f.loc[t+pd.Timedelta(hours=hours)<=end].copy();p["quarter"]=p.start.dt.tz_localize(None).dt.to_period("Q")
    dis=[];next_t=t[0]
    for i,ts in enumerate(t):
        if ts>=next_t:dis.append(i);next_t=ts+pd.Timedelta(hours=hours)
    z=f.iloc[dis]
    hit=p["return"]>=1/.84-1;agg=p.assign(hit=hit).groupby("quarter",observed=True).agg(hits=("hit","sum"),n=("hit","size"))
    lower=upper=None
    if len(agg):
        rng=np.random.default_rng(20261015);draw=rng.integers(0,len(agg),(10000,len(agg)))
        freq=agg.hits.to_numpy()[draw].sum(1)/agg.n.to_numpy()[draw].sum(1)
        lower=float(np.quantile(freq,.05/26));upper=float(np.quantile(freq,1-.05/26))
    return {"n_windows":len(f),"n_disjoint":len(dis),"n_purged":len(p),"quarters":len(agg),
      "mean_return":float(f["return"].mean()),"median_return":float(f["return"].median()),"worst_return":float(f["return"].min()),
      "max_drawdown":float(f.mdd.max()),"p19":float((f["return"]>=.19).mean()),"p215":float((f["return"]>=.215).mean()),
      "p25":float((f["return"]>=.25).mean()),"p_gate0":float((f["return"]>=1/.84-1).mean()),
      "p_gate2":float((f["return"]>=1.02/.84-1).mean()),"p_loss10":float((f["return"]<=-.1).mean()),
      "p_loss20":float((f["return"]<=-.2).mean()),"disjoint_p19":float((z["return"]>=.19).mean()),
      "gate0_cluster_lower":lower,"gate0_cluster_upper":upper,"family":26,
      "actual_top20_probability":None,"fresh_evidence":False}
