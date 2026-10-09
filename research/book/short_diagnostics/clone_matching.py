"""Independent global maximum-flow audit; never changes the frozen matcher."""
from __future__ import annotations
import argparse,hashlib,json
from collections import deque
from decimal import Decimal
from pathlib import Path
import pandas as pd

def maximum_flow(adj,n_pred):
    n_obs=len(adj);sink=1+n_obs+n_pred
    capacity=[{} for _ in range(sink+1)]
    def edge(a,b):
        capacity[a][b]=1;capacity[b][a]=0
    for i,neighbors in enumerate(adj):
        edge(0,1+i)
        for j in neighbors:edge(1+i,1+n_obs+j)
    for j in range(n_pred):edge(1+n_obs+j,sink)
    while True:
        parent={0:None};queue=deque([0])
        while queue and sink not in parent:
            a=queue.popleft()
            for b,c in capacity[a].items():
                if c>0 and b not in parent:parent[b]=a;queue.append(b)
        if sink not in parent:break
        b=sink
        while parent[b] is not None:
            a=parent[b];capacity[a][b]-=1;capacity[b][a]+=1;b=a
    return [(i,j) for i,neighbors in enumerate(adj) for j in neighbors if capacity[1+i][1+n_obs+j]==0]

def time_allowed(o,p,convention):
    if pd.isna(o) or pd.isna(p):return False
    delta=int(p.value-o.value)
    second=1000000000
    if convention=="frozen_interval_distance":
        return -120*second <= delta <= 180*second
    if convention=="half_open_existence":
        return -120*second <= delta < 180*second
    if convention=="displayed_minute":
        return abs(delta)<=120*second
    raise ValueError("unknown time convention")

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--out",required=True)
    a=ap.parse_args(argv);root=Path("/home/ubuntu/test/MiniMax")
    observed=root/"results/book/20261009-observed-baseline/revisions/t001-confirmed/observed_trades_corrected.csv"
    directory=root/"results/book/20261009-clone-reconcile"
    predicted=directory/"selected_events.csv"
    metrics_file=directory/"selected_metrics.json"
    matcher=root/".worktrees/book-book-observed-baseline/src/validation/observed_baseline.py"
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    paths=[observed,predicted,metrics_file,matcher,directory/"selection_freeze.json"]
    before={str(p):sha(p) for p in paths}
    obs=pd.read_csv(observed,dtype={"quantity":str})
    obs["ts"]=[pd.Timestamp(r.date+" "+r.time,tz="Asia/Hong_Kong").tz_convert("UTC") for r in obs.itertuples()]
    pred=pd.read_csv(predicted,dtype={"quantity":str});pred["ts"]=pd.to_datetime(pred.time_utc,utc=True)
    if len(obs)!=33 or len(pred)!=31:raise ValueError("fixed observed/predicted event counts changed")
    results=[];matched_sets={};all_edges=[]
    tolerance=Decimal(".05")+Decimal("1e-12")
    for convention in ["frozen_interval_distance","half_open_existence","displayed_minute"]:
        for quantity in [True,False]:
            adj=[]
            for i,o in obs.iterrows():
                neighbors=[]
                for j,p in pred.iterrows():
                    if o.asset!=p.asset or o.action!=p.action:continue
                    qe=abs(Decimal(p.quantity)/Decimal(o.quantity)-1)
                    allowed=time_allowed(o.ts,p.ts,convention) and (not quantity or qe<=tolerance)
                    if allowed:neighbors.append(j)
                adj.append(neighbors)
            pairs=maximum_flow(adj,len(pred));m=len(pairs)
            precision=m/len(pred);recall=m/len(obs)
            results.append(dict(convention=convention,quantity_required=quantity,matched=m,
                observed=len(obs),predicted=len(pred),precision=precision,recall=recall,
                f1=2*m/(len(obs)+len(pred))))
            matched_sets[(convention,quantity)]=set(pairs)
    saved=json.loads(metrics_file.read_text())["all"]
    pairs={(x["observed_index"],x["predicted_index"]) for x in saved["pairs"]}
    independent=matched_sets[("frozen_interval_distance",True)]
    if len(pairs)!=len(independent) or saved["matched"]!=len(independent):
        raise ValueError("independent maximum cardinality differs from reported strict count")
    if len({i for i,j in pairs})!=len(pairs) or len({j for i,j in pairs})!=len(pairs):
        raise ValueError("reported pairs double count events")
    audit=[]
    for i,o in obs.iterrows():
        for j,p in pred.iterrows():
            if o.asset!=p.asset or o.action!=p.action:continue
            dt=(p.ts-o.ts).total_seconds();interval=max(-dt,dt-60,0)
            qe=abs(Decimal(p.quantity)/Decimal(o.quantity)-1)
            row=dict(observed_index=i,trade_id=o.trade_id,predicted_index=j,asset=o.asset,action=o.action,
                observed_quantity=o.quantity,predicted_quantity=p.quantity,
                observed_minute_start=str(o.ts),observed_minute_end_excluded=str(o.ts+pd.Timedelta(minutes=1)),
                predicted_time=str(p.ts),seconds_from_displayed_minute=dt,
                frozen_interval_distance_seconds=interval,quantity_relative_error=str(qe),
                quantity_ok=qe<=tolerance,
                frozen_time_ok=time_allowed(o.ts,p.ts,"frozen_interval_distance"),
                half_open_time_ok=time_allowed(o.ts,p.ts,"half_open_existence"),
                displayed_minute_time_ok=time_allowed(o.ts,p.ts,"displayed_minute"),
                published_pair=(i,j) in pairs,independent_flow_pair=(i,j) in independent)
            if row["published_pair"] and not(row["quantity_ok"] and row["frozen_time_ok"]):
                raise ValueError("published pair violates frozen matching criteria")
            audit.append(row)
    out=Path(a.out).resolve()
    if (root/"results/book") not in out.parents:raise ValueError("dedicated Book results directory required")
    if (out/"matcher_audit.json").exists():raise ValueError("preserve previous audit")
    out.mkdir(parents=True,exist_ok=True)
    frame=pd.DataFrame(audit);frame.to_csv(out/"all_same_action_pairs.csv",index=False)
    frame.loc[frame.published_pair].to_csv(out/"published_pair_audit.csv",index=False)
    pd.DataFrame(results).to_csv(out/"maximum_matching_sensitivity.csv",index=False)
    boundary=frame.loc[(frame.seconds_from_displayed_minute==180)&frame.frozen_time_ok]
    boundary.to_csv(out/"upper_boundary_pairs.csv",index=False)
    if before!={str(p):sha(p) for p in paths}:raise ValueError("input changed during independent audit")
    result={"status":"PASS_UNDER_FROZEN_INTERVAL_DISTANCE","inputs":before,"results":results,
        "independent_algorithm":"unit-capacity maximum flow, BFS augmenting paths; no project matcher imported",
        "all_published_pairs_valid":True,"published_and_independent_pairs_equal":pairs==independent,
        "published_pairs":len(pairs),"upper_boundary_eligible_pairs":len(boundary),
        "upper_boundary_published_strict_pairs":int(boundary.published_pair.sum()),
        "boundary_trade_ids":boundary.trade_id.tolist(),
        "exact_half_open_existential_issue":"The infimum distance to [minute,minute+60s) includes its unattained upper limit. At predicted=minute+180s, no actual observed second within that half-open minute has distance<=120s. Frozen code nevertheless includes that boundary; do not silently alter it.",
        "earlier_28_of_33_ceiling":"Applies to a fixed09:05 batch against displayed-minute or strict half-open-existence matching because five09:02 rows miss timing. It does not apply to the frozen interval-distance code's inclusive end-distance boundary.",
        "target85_percent":"At least29/33 observed matches; current result19 under frozen convention and16 in stated timing sensitivities. All five dates calibrated; no prospective claim.",
        "source_sha256":sha(__file__)}
    result["outputs"]={p.name:sha(p) for p in out.glob("*.csv")}
    (out/"matcher_audit.json").write_text(json.dumps(result,indent=2))
    print(pd.DataFrame(results).to_string(index=False))
    print("Boundary pairs",boundary[["trade_id","predicted_index","quantity_ok","published_pair"]].to_dict("records"))
if __name__=="__main__":main()
