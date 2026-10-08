"""Retrospective prior-only forecast validation, separate from strategy returns."""
from __future__ import annotations
import numpy as np
import pandas as pd
from src.validation.selection import PickRules,mid_rank_pct
from .features import match_windows
from .metrics import eligible_pool,mix_weights,weighted_crps,weighted_quantile,block_bootstrap_interval

def validate_matching(features,states,outcomes,observations,queries,c):
    rules=PickRules(**c["lookalikes"],horizon_days=c["horizon_hours"]//24)
    rows=[];skipped=[]
    for d in queries:
        ok=eligible_pool(features.index,d,c["horizon_hours"],c["embargo_hours"])
        ok &= np.isfinite(features.to_numpy()).all(axis=1)&np.isfinite(outcomes.to_numpy()).all(axis=1)
        pool=features.loc[ok]
        if len(pool)<c["walkforward"]["min_pool"] or not np.isfinite(states.loc[d].to_numpy()).all():
            skipped.append({"query":str(d),"reason":"insufficient prior complete feature coverage","n":len(pool)});continue
        obs=observations.loc[d]
        if not np.isfinite(obs.to_numpy()).all():
            skipped.append({"query":str(d),"reason":"incomplete outcome"});continue
        pick=match_windows(pool,states.loc[d],c["features"],rules)
        if len(pick)!=rules.k:
            skipped.append({"query":str(d),"reason":"insufficient independent lookalikes under fixed spacing","n":len(pool),"selected":len(pick)});continue
        selected=pool.index.get_indexer(pick.t0)
        y=outcomes.loc[pool.index]
        ranks={name:mid_rank_pct(y[[name]].to_numpy(),y[[name]].to_numpy())[:,0] for name in y}
        observed={name:float(mid_rank_pct(y[[name]].to_numpy(),np.array([[obs[name]]]))[0,0]) for name in y}
        for alpha in c["alpha_candidates"]:
            w=mix_weights(len(pool),selected,alpha)
            crps={name:weighted_crps(ranks[name],w,observed[name]) for name in y}
            pup=float(np.dot(w,y.future_return.to_numpy()>0));actual=float(obs.future_return>0)
            rows.append({"query":d,"alpha":alpha,"n_pool":len(pool),"pool_max_end":pool.index.max()+pd.Timedelta(hours=c["horizon_hours"]),
                "phase":"SCREEN" if d<=pd.Timestamp(c["walkforward"]["screen_end"]) else "CONFIRM",
                "crps":float(np.mean(list(crps.values()))),"crps_return":crps["future_return"],
                "crps_drawdown":crps["future_drawdown"],"crps_vol":crps["future_vol"],
                "brier":(pup-actual)**2,"p_up":pup,"actual_up":actual,
                "coverage90":bool(weighted_quantile(y.future_return,w,.05)<=obs.future_return<=weighted_quantile(y.future_return,w,.95))})
    frame=pd.DataFrame(rows)
    if frame.empty: raise ValueError("no evaluable prior-only queries")
    screen=frame[frame.phase=="SCREEN"];confirm=frame[frame.phase=="CONFIRM"]
    means=screen.groupby("alpha").crps.mean()
    chosen=float(means.sort_index().idxmin())
    base=confirm[confirm.alpha==0].set_index("query")
    other=confirm[confirm.alpha==chosen].set_index("query")
    if not base.index.equals(other.index): raise ValueError("confirmation comparisons are unpaired")
    b=c["bootstrap"];block=c["walkforward"]["bootstrap_block_queries"]
    skill=block_bootstrap_interval((base.crps-other.crps).to_numpy(),block,b["reps"],b["seed"],b["level"])
    brier=block_bootstrap_interval((other.brier-base.brier).to_numpy(),block,b["reps"],b["seed"],b["level"])
    counts={phase:int(frame[frame.phase==phase]["query"].nunique()) for phase in ["SCREEN","CONFIRM"]}
    gates={"query_coverage":min(counts.values())>=c["walkforward"]["min_queries"],
           "adaptive_selected":chosen>0,
           "confirm_crps_improvement":skill["lower"]>c["gates"]["min_confirm_skill_lower"],
           "direction_not_degraded":brier["upper"]<=c["gates"]["max_brier_degradation"],
           "prior_only":bool((frame.pool_max_end<=frame["query"]-pd.Timedelta(hours=c["embargo_hours"])).all())}
    summary={"chosen_on_screen":chosen,"statistical_gates":gates,"statistical_pass":all(gates.values()),
             "confirm_crps_improvement":skill,"confirm_brier_degradation":brier,"queries":counts,"skipped":skipped,
             "phase_means":frame.groupby(["phase","alpha"])[["crps","crps_return","crps_drawdown","crps_vol","brier","coverage90"]].mean().reset_index().to_dict("records"),
             "interpretation":"Retrospective method validation; strategy development history is observed/spent."}
    return frame,summary


def activation_decision(summary,query,groups,asof,archive_complete,stability):
    """Missing live features disable adaptive weights; no data-coverage relaxation."""
    names=[name for columns in groups.values() for name in columns]
    missing=[name for name in names if name not in query or not np.isfinite(query[name])]
    confirmed=pd.Timestamp(asof)<=pd.Timestamp(archive_complete)
    passed=bool(summary["statistical_pass"] and not missing and confirmed and stability)
    active=float(summary["chosen_on_screen"]) if passed else 0.0
    return {"current_query_coverage":not missing,"current_missing_features":missing,
            "current_data_confirmed":confirmed,"stability_pass":bool(stability),
            "adaptive_pass":passed,"active_alpha":active,
            "weight_mode":"ADAPTIVE_VALIDATED" if active>0 else "UNIFORM_BASELINE_FALLBACK"}
