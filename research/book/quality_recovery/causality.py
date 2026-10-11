"""Independent actual historical-view metamorphic checks; no P&L search."""
from dataclasses import replace
from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.config import load_config
from src.contracts import MarketView,check_targets
from src.models import get
from src.models.book.book_e20combo_brk_cash import MODEL as BASE
from backtest.data import load_market
from backtest.engine import view_frames,universe_at
from backtest.scoring.windows import pool_starts

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT.parents[1]/"results/book/20261011-quality-recovery-v1"

def main():
    cfg=load_config();mk=load_market(cfg);starts=pool_starts(mk,cfg)
    times=starts[np.linspace(0,len(starts)-1,12,dtype=int)]
    rows=[]
    for name in ["book_recovery_quality","book_recovery_quality_blend"]:
        model=get(name);p=cfg["models"][name]
        for t in times:
            tc=t-pd.Timedelta(hours=24)
            c,q=view_frames(mk.close,mk.quote_volume,tc)
            prev=model.targets(MarketView(tc,c,q,universe_at(mk,tc),p))
            c,q=view_frames(mk.close,mk.quote_volume,t)
            v=MarketView(t,c,q,universe_at(mk,t),p,prev)
            w=check_targets(model.targets(v),v,model.spec)
            parent=BASE.targets(replace(v,params=p["parent"]))
            short=lambda x:x[x<0].sort_index()
            pd.testing.assert_series_equal(short(w),short(parent))
            assert w.abs().sum()<=parent.abs().sum()+1e-12
            future=pd.date_range(t+pd.Timedelta(hours=1),periods=72,freq="h")
            fc=pd.DataFrame(np.linspace(1e3,1e6,len(future))[:,None]*np.ones((1,len(c.columns))),index=future,columns=c.columns)
            fq=fc*1e9
            z=model.targets(replace(v,close=pd.concat([c,fc]),quote_volume=pd.concat([q,fq])))
            pd.testing.assert_series_equal(w,z)
            cols=w.index.union(parent.index).sort_values()
            grid=pd.date_range(end=t,periods=721,freq="h")
            ret=c.reindex(index=grid,columns=cols).pct_change(fill_method=None).iloc[1:].dropna(how="any")
            signed_delta=long_delta=0.
            if len(cols) and len(ret)>=648:
                cov=ret.cov().to_numpy()*24.
                old=parent.reindex(cols).fillna(0).to_numpy();new=w.reindex(cols).fillna(0).to_numpy()
                signed_delta=float(new@cov@new-old@cov@old)
                a=np.clip(old,0,None);b=np.clip(new,0,None)
                long_delta=float(b@cov@b-a@cov@a)
                assert signed_delta<=1e-12 and long_delta<=1e-12
            else:
                pd.testing.assert_series_equal(w,parent)
            rows.append({"model":name,"t":str(t),"parent_gross":float(parent.abs().sum()),"new_gross":float(w.abs().sum()),
                         "changed":not w.sort_index().equals(parent.sort_index()),
                         "signed_variance_delta":signed_delta,"long_variance_delta":long_delta})
    result={"status":"PASS","real_decisions":len(rows),"future_rows_appended_per_decision":72,
            "shorts_exact_given_same_view":True,"gross_no_increase":True,"risk_checks_pass":True,
            "actual_account":False,"production_eligible":False,"rows":rows}
    (OUT/"real_causal_audit.json").write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!="rows"}))
if __name__=="__main__":main()
