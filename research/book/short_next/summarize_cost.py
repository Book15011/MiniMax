"""Summarize the fixed160 executable cost cases and verify long-backbone equality."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd

TOP="baitoey_ovl_brk_dual"
NAMES=[TOP,"book_cashshort_confirm","book_cashshort_pullback"]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",required=True)
    ap.add_argument("--baseline-evidence",required=True)
    a=ap.parse_args(argv);out=Path(a.out)
    if (out/"comparison_manifest.json").exists():raise ValueError("preserve prior combined evidence")
    proof=json.loads(Path(a.baseline_evidence).read_text())
    sources={};frames={};summaries=[]
    for name in NAMES:
        mp=out/("manifest."+name+".json")
        m=json.loads(mp.read_text())
        if m["maximum_target_error"]>1e-12 or m["maximum_original_equity_error"]>1e-12:
            raise ValueError("original reproduction did not pass")
        if m["horizon_hours"]!=228 or m["fee_multiplier"]!=2 or m["half_spread_multiplier"]!=2:
            raise ValueError("scenario differs")
        p=out/("paired_windows."+name+".csv")
        f=pd.read_csv(p)
        if len(f)!=160 or f.start.tolist()!=m["starts"]:raise ValueError("case grid differs")
        if (f.model!=name).any():raise ValueError("model identity differs")
        frames[name]=f
        s=out/("summary."+name+".csv")
        summaries.append(pd.read_csv(s))
        sources[name]={"manifest":{"path":str(mp),"sha256":sha(mp)},
                       "windows":{"path":str(p),"sha256":sha(p)},"run_key":m["run_key"]}
    top=frames[TOP]
    paired=[]
    for name in NAMES[1:]:
        f=frames[name]
        if not f.start.equals(top.start) or not f.end.equals(top.end):raise ValueError("paired support differs")
        for scenario in ("original","doubled"):
            d=f[scenario+"_liquidated_return"]-top[scenario+"_liquidated_return"]
            paired.append(dict(model=name,baseline=TOP,scenario=scenario,n=len(d),
                paired_mean=float(d.mean()),paired_median=float(d.median()),paired_p10=float(d.quantile(.1)),
                paired_worst=float(d.min()),paired_win_share=float((d>0).mean())))
    summary=pd.concat(summaries,ignore_index=True)
    delta=[]
    for name,f in frames.items():
        d=f.doubled_liquidated_return-f.original_liquidated_return
        delta.append(dict(model=name,n=len(d),mean_delta=float(d.mean()),median_delta=float(d.median()),
                          p10_delta=float(d.quantile(.1)),worst_delta=float(d.min())))
    # Full stored target matrices must preserve the empirically reproduced
    # baseline's positive target chain, not merely a few synthetic examples.
    root=out.parent.parent.parent
    top_path=root/"results/scoring/cache"/TOP/(sources[TOP]["run_key"]+".targets.parquet")
    if sha(top_path)!=proof["stored_target_sha256"]:raise ValueError("baseline target proof changed")
    target=pd.read_parquet(top_path);preservation={}
    for name in NAMES[1:]:
        m=json.loads((out/("manifest."+name+".json")).read_text())
        p=root/"results/scoring/cache"/name/(m["run_key"]+".targets.parquet")
        if sha(p)!=m["cache_hashes"][str(p)]:raise ValueError("hybrid targets changed after exact replay")
        actual=pd.read_parquet(p)
        if not actual.index.equals(target.index):raise ValueError("hybrid/backbone schedule differs")
        cols=target.columns.union(actual.columns)
        d=actual.reindex(columns=cols,fill_value=0).clip(lower=0)-target.reindex(columns=cols,fill_value=0).clip(lower=0)
        error=float(np.abs(d.to_numpy()).max())
        if error>1e-12:raise ValueError("hybrid changed the long target chain")
        preservation[name]={"decisions":len(target),"maximum_positive_target_error":error,
            "hybrid_target_sha256":sha(p),"baseline_target_sha256":sha(top_path)}
    summary.to_csv(out/"summary.csv",index=False)
    pd.DataFrame(paired).to_csv(out/"paired_top.csv",index=False)
    pd.DataFrame(delta).to_csv(out/"paired_cost_deltas.csv",index=False)
    result={"analysis":"same160_fixed_cost_sensitivity","all_history_spent":True,
        "prospective_validation":False,"primary_metric_changed":False,"publication":False,
        "source_files":sources,"positive_backbone_preservation":preservation,
        "baseline_evidence":{"path":a.baseline_evidence,"sha256":sha(a.baseline_evidence)},
        "analysis_source":{"path":str(Path(__file__).resolve()),"sha256":sha(__file__)},
        "outputs":{p.name:sha(p) for p in [out/"summary.csv",out/"paired_top.csv",out/"paired_cost_deltas.csv"]}}
    (out/"comparison_manifest.json").write_text(json.dumps(result,indent=2))
    print(summary.to_string(index=False))
    print(pd.DataFrame(paired).to_string(index=False))
    print(json.dumps(preservation))
if __name__=="__main__":main()
