"""Read-only reconstruction of published diagnostics; no API or account access."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.config import load_config
from backtest.data import load_market
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT.parents[1]/"results/book/20261015-simulator-edge-v1"

def independent_cs(paths,hours,sc):
    # Explicit daily moments and floored ratios, without calling window_metrics.
    d=paths[:,[0,24,48,hours]]
    r=d[:,1:]/d[:,:-1]-1
    m=r.mean(1);s=r.std(1,ddof=1);down=np.sqrt(np.minimum(r,0).__pow__(2).mean(1))
    mdd=(1-paths/np.maximum.accumulate(paths,axis=1)).max(1)
    spec=sc["variants"]["V1"];fl=sc["conventions"]["FLOORED"];a=float(spec["annualize"])
    assert spec["returns"]=="daily"
    def ratio(x,y,f):
        y=np.maximum(y,f)
        return np.divide(x,y,out=np.zeros_like(x),where=y>0)
    sh=ratio(m,s,fl["s_daily"])*np.sqrt(a)
    so=ratio(m,down,fl["dd_daily"])*np.sqrt(a)
    num=m*a if spec["calmar"]=="mean" else paths[:,-1]/paths[:,0]-1
    ca=ratio(num,mdd,fl["mdd"])
    wc=sc["composite"]
    return wc["sortino"]*so+wc["sharpe"]*sh+wc["calmar"]*ca

def main():
    old=pd.read_csv(OUT/"publication_before_cs/edge_results.csv")
    now=pd.read_csv(OUT/"edge_results.csv")
    pd.testing.assert_frame_equal(old,now[old.columns],check_dtype=False,rtol=1e-12,atol=1e-12)
    sc=load_config()["scoring"];mk=load_market(load_config());btc=mk.close["BTCUSDT"]
    h=now[now.source_family=="hourly_proxy"]
    errors=[];checked=0
    for name,group in h.groupby("candidate"):
        raw=np.load(OUT/f"{name}.hourly.npz",allow_pickle=False)
        starts=pd.to_datetime(raw["starts"],utc=True)
        br=btc.reindex(starts).to_numpy()/btc.reindex(starts-pd.Timedelta(hours=168)).to_numpy()-1
        for hours in [68,72]:
            E=raw["equity"][:,:hours+1];G=raw["gross"][:,:hours+1]
            cs=independent_cs(E,hours,sc)
            for row in group[group.hours==hours].itertuples():
                cut=pd.Timestamp("2025-01-01",tz="UTC")
                mask=(starts>=cut) if row.split=="spent_historical_check" else (starts+pd.Timedelta(hours=hours)<cut)
                if row.regime!="all":mask&=(br<0) if row.regime=="btc7_negative" else (br>=0)
                errors.append(abs(float(cs[mask].mean())-row.cs_mean))
                assert np.isclose(G[mask].max(),row.group_max_marked_gross,rtol=0,atol=1e-12)
                assert np.isclose((G[mask].max(1)>1+1e-10).mean(),row.p_marked_gross_over_100,rtol=0,atol=1e-12)
                checked+=1
    w=pd.read_csv(OUT/"quote_windows.csv");quote_cs={}
    for i,row in w.iterrows():
        raw=np.load(OUT/"audited_quote_traces"/f"window_{i:03}.npz",allow_pickle=False)
        start=pd.Timestamp(row.start);hours=int(row.hours)
        ts=pd.to_datetime(raw["times"],unit="s",utc=True)
        path=pd.Series(raw["equity"][1:],index=ts)
        E=path.reindex(pd.date_range(start,start+pd.Timedelta(hours=hours),freq="h"),method="ffill").to_numpy()[None,:]
        cs=float(independent_cs(E,hours,sc)[0])
        quote_cs.setdefault((row.candidate,hours),[]).append(cs)
    for row in now[now.source_family=="roostoo_quote_windows"].itertuples():
        errors.append(abs(float(np.mean(quote_cs[row.candidate,int(row.hours)]))-row.cs_mean));checked+=1
    assert max(errors)<1e-10,max(errors)
    assert len(now)==411
    assert not now.production_eligible.fillna(False).any()
    assert now.actual_top20_probability.isna().all()
    summary={"status":"PASS","original_comparison_rows_unchanged":len(old),
             "cs_and_scope_groups_checked":checked,"cs_independent_max_error":max(errors),
             "marked_gross_groups_checked":len(h),"actual_top20_probability_unavailable":True,
             "production_eligible":False}
    (OUT/"cs_addition_audit.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
