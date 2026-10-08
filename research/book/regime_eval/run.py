"""Remote-only offline CLI. Writes research outputs, never the official score registry."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
from src.config import REPO_ROOT,load_config,resolve
from src.validation.features import StateEngine,MarketData,CORE_GROUPS,GROUPS
from src.validation.selection import PickRules,select_lookalikes
from .features import build_features,market_outcomes,match_windows
from .metrics import (eligible_pool,mix_weights,normalized_weights,continuation_returns,weighted_quantile,grouped_bootstrap_delta)
from .validation import validate_matching,activation_decision

PAPER_MODELS={"pol_switch_vt_tl_e20v45":"e20v45 (deployed live)","pol_abl_shock":"pol_abl_shock (vt_mom + crash rule)",
 "baitoey_vt_mom":"vt_mom","book_orch":"H1 (book_orch)","book_vt_top4":"vt_top4","pol_switch_vt_tl":"pol_switch_vt_tl (e40)"}

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def safe_path(value):
    p=resolve(value).resolve();root=REPO_ROOT.resolve()
    # Worktree and shared-data paths remain inside the project.
    common=root.parent.parent if root.parent.name==".worktrees" else root
    if p!=common and common not in p.parents: raise ValueError("artifact outside remote project")
    return p

def dump(path,value):
    def default(x):
        if isinstance(x,np.generic):return x.item()
        return str(x)
    path.write_text(json.dumps(value,indent=2,default=default,allow_nan=False)+"\n")

def registered(c,entries=None):
    if entries is None:
        entries=[json.loads(s) for s in safe_path(c["registry"]).read_text().splitlines()]
    latest={}
    for e in sorted(entries,key=lambda x:x["ts"]):
        if e.get("full") and e.get("tool_version")==c["tool_version"]:latest[e["model"]]=e
    if c["incumbent"] not in latest:raise ValueError("incumbent cache unavailable")
    scores={};reference=None;notes=[]
    for name,e in sorted(latest.items()):
        p=safe_path(e["score_json"]);actual=sha(p)
        if actual!=e["score_sha256"]:raise ValueError("score hash mismatch: "+name)
        s=json.loads(p.read_text());t=pd.DatetimeIndex(pd.to_datetime(s["per_window"]["start"],utc=True))
        signature=json.dumps([s["data"],s.get("inputs_sha256",{})],sort_keys=True)
        if reference is None: reference=(t,signature)
        if not t.equals(reference[0]) or signature!=reference[1]:raise ValueError("incompatible model windows/data: "+name)
        scores[name]=s
        notes.append({"model":name,"candidate":e["candidate"],"eligible_original":e["eligible"],
          "run_key":e["run_key"],"score_json":str(p),"score_sha256":actual,
          "published_code":s.get("code"),"cached_code":s.get("code_when_cached"),"gates":e["gates"]})
    scratch=sorted(p.name for p in safe_path(c["cache_dir"]).iterdir() if p.is_dir() and p.name not in latest)
    return latest,scores,reference[0],notes,scratch

def frozen_registered(c,out):
    """Pin registry selection; later publications cannot rewrite this checkpoint."""
    snapshot=out/"registered_snapshot.json"
    entries=json.loads(snapshot.read_text()) if snapshot.exists() else None
    result=registered(c,entries)
    latest,_,_,inventory,_=result
    previous=out/"model_inventory.json"
    if previous.exists():
        old=json.loads(previous.read_text())["registered"]
        fields=("model","run_key","score_sha256","candidate")
        identity=lambda rows:sorted(tuple(row[k] for k in fields) for row in rows)
        if identity(old)!=identity(inventory):
            raise ValueError("registered selection differs from frozen evaluation")
    if not snapshot.exists():
        dump(snapshot,[latest[name] for name in sorted(latest)])
    return result

def prepare(cfg,c,out,starts):
    hist=safe_path(c["historical_panel"]);live=safe_path(c["live_panel"])
    files={"historical_close":hist/"panel_close_1h.parquet","historical_qv":hist/"panel_quote_volume_1h.parquet",
           "live_close":live/"close_1h.parquet","live_qv":live/"qv_1h.parquet","live_meta":live/"store_meta.json",
           "paper_equity":safe_path(c["paper_equity"])}
    asof=pd.Timestamp(c["asof"]);saved=out/"input_manifest.json"
    if saved.exists():
        manifest=json.loads(saved.read_text())
        if pd.Timestamp(manifest["asof"])!=asof:raise ValueError("frozen snapshot has another asof")
        for name,digest in manifest["frozen_snapshots"].items():
            if sha(out/name)!=digest:raise ValueError("frozen snapshot changed: "+name)
        for name in ["historical_close","historical_qv"]:
            if sha(files[name])!=manifest["sources"][name]["sha256"]:raise ValueError("immutable history changed: "+name)
        p=pd.read_parquet(files["historical_close"]);q=pd.read_parquet(files["historical_qv"])
        lp=pd.read_parquet(out/"live_close_snapshot.parquet");lq=pd.read_parquet(out/"live_qv_snapshot.parquet")
        paper=pd.read_csv(out/"paper_prefix.csv",index_col=0)
    else:
        before={k:sha(path) for k,path in files.items()}
        p=pd.read_parquet(files["historical_close"]);q=pd.read_parquet(files["historical_qv"])
        lp=pd.read_parquet(files["live_close"]).loc[:asof];lq=pd.read_parquet(files["live_qv"]).loc[:asof]
        meta=json.loads(files["live_meta"].read_text());paper=pd.read_csv(files["paper_equity"],index_col=0)
        if before!={k:sha(path) for k,path in files.items()}:raise ValueError("source changed during snapshot")
        paper.index=pd.to_datetime(paper.index,utc=True);paper=paper.loc[pd.Timestamp(c["competition_start"]):asof]
        lp.to_parquet(out/"live_close_snapshot.parquet");lq.to_parquet(out/"live_qv_snapshot.parquet");paper.to_csv(out/"paper_prefix.csv")
        manifest={"sources":{k:{"path":str(path),"sha256":before[k]} for k,path in files.items()},
          "asof":str(asof),"archive_complete_through":meta["complete_through"],
          "ticker_only_used":[t for t in meta.get("ticker_only",[]) if pd.Timestamp(t)<=asof],
          "frozen_snapshots":{name:sha(out/name) for name in ["live_close_snapshot.parquet","live_qv_snapshot.parquet","paper_prefix.csv"]},
          "competition_account":"UNVERIFIED; paper replay only","paper_identity":"CSV has no embedded immutable code/params"}
    paper.index=pd.to_datetime(paper.index,utc=True);expected=pd.date_range(pd.Timestamp(c["competition_start"]),asof,freq="h")
    if not paper.index.equals(expected) or not np.isfinite(paper.to_numpy()).all() or (paper.to_numpy()<=-1).any():raise ValueError("paper grid or equity corrupt")
    if len(paper)!=c["prefix_hours"]+1:raise ValueError("paper prefix incomplete")
    p=pd.concat([p,lp.loc[lp.index>p.index.max()]]).loc[:asof];q=pd.concat([q,lq.loc[lq.index>q.index.max()]]).loc[:asof]
    wf=c["walkforward"];queries=pd.date_range(pd.Timestamp(wf["start"]),pd.Timestamp(wf["end"]),freq=str(wf["step_days"])+"D")
    times=starts+pd.Timedelta(hours=c["prefix_hours"]);union=times.union(queries).union(pd.DatetimeIndex([asof])).sort_values()
    v=dict(cfg["validation"]);v["grid_hour_utc"]=c["state_grid_hour_utc"];states=build_features(p,q,union,v,c)
    features=states.reindex(times).copy();features.index=starts;outcomes=market_outcomes(p,starts,c["prefix_hours"],c["horizon_hours"],c)
    observed=market_outcomes(p,queries-pd.Timedelta(hours=c["prefix_hours"]),c["prefix_hours"],c["horizon_hours"],c);observed.index=queries
    features.to_parquet(out/"features.parquet");states.to_parquet(out/"states.parquet");outcomes.to_parquet(out/"market_outcomes.parquet")
    legacy_path=safe_path(Path(cfg["scoring"]["regimes"]).parent/"features.parquet");legacy_artifact=safe_path(cfg["scoring"]["validation_set"])
    old_v=json.loads(legacy_artifact.read_text())["parameters"]["validation"];old_v["grid_hour_utc"]=c["state_grid_hour_utc"]
    legacy=pd.read_parquet(legacy_path).reindex(times);legacy.index=starts
    engine=StateEngine(MarketData(p,q),old_v);legacy_query=engine.features(pd.DatetimeIndex([asof])).iloc[0]
    manifest["legacy_sources"]={str(path):sha(path) for path in [legacy_path,legacy_artifact]}
    manifest["coverage_failure_preserved"]="BCH exact12UTC price absent; broad30 universe has29 valid48h endpoints"
    dump(out/"input_manifest.json",manifest)
    return features,states,outcomes,observed,queries,manifest,legacy,legacy_query

def validate(cfg,c,out):
    latest,scores,starts,inventory,scratch=frozen_registered(c,out)
    dump(out/"model_inventory.json",{"registered":inventory,"unregistered_not_assessed":scratch});dump(out/"frozen_config.json",c)
    features,states,outcomes,obs,queries,manifest,legacy,legacy_query=prepare(cfg,c,out,starts)
    bad=outcomes.loc[~np.isfinite(outcomes.to_numpy()).all(axis=1)].copy()
    bad["reason"]="BTC forward endpoint or98%hourly outcome coverage unavailable"
    bad.to_csv(out/"coverage_exclusions.csv",index_label="window_start")
    wf,summary=validate_matching(features,states,outcomes,obs,queries,c);wf.to_csv(out/"walkforward.csv",index=False)
    d=pd.Timestamp(c["asof"]);mature=eligible_pool(starts,d,c["horizon_hours"],c["embargo_hours"])
    mature &= starts+pd.Timedelta(hours=c["horizon_hours"])<=pd.Timestamp(c["historical_end"])
    mature &= np.isfinite(outcomes.to_numpy()).all(axis=1)
    outcomes=outcomes.loc[mature];features=features.loc[outcomes.index]
    rules=PickRules(**c["lookalikes"],horizon_days=c["horizon_hours"]//24)
    required=[name for columns in c["features"].values() for name in columns]
    covered=bool(np.isfinite(states.loc[d,required].to_numpy()).all())
    eligible_features=features[np.isfinite(features[required].to_numpy()).all(axis=1)]
    chosen=summary["chosen_on_screen"];sensitivity=[];stability=False
    if covered:
        adaptive_pick=match_windows(eligible_features,states.loc[d],c["features"],rules)
        for k in [rules.k]+c["sensitivity_k"]:
            r=PickRules(k,rules.min_separation_days,rules.span_days,rules.max_per_span,rules.horizon_days)
            picked=match_windows(eligible_features,states.loc[d],c["features"],r)
            ix=eligible_features.index.get_indexer(picked.t0);w=mix_weights(len(eligible_features),ix,chosen);y=outcomes.loc[eligible_features.index]
            sensitivity.append({"k":k,"future_return_mean":float(np.dot(w,y.future_return)),"p_up":float(np.dot(w,y.future_return>0))})
        sens=pd.DataFrame(sensitivity)
        stability=bool(sens.future_return_mean.max()-sens.future_return_mean.min()<=c["gates"]["max_return_mean_sensitivity"] and sens.p_up.max()-sens.p_up.min()<=c["gates"]["max_up_probability_sensitivity"])
    summary.update(activation_decision(summary,states.loc[d],c["features"],d,manifest["archive_complete_through"],stability))
    summary.update({"sensitivity":sensitivity,"current_query":{k:float(v) if np.isfinite(v) else None for k,v in states.loc[d].items()},
       "historical_windows":len(outcomes),"registry_models":len(latest),"integrity_pass":True,"short_account_available":"UNVERIFIED",
       "shared_incumbent_transition_validated":False,"new_score_enabled":False})
    active=summary["active_alpha"]
    if active>0:
        pick=adaptive_pick;table=outcomes.loc[eligible_features.index].join(eligible_features);mode="ADAPTIVE_VALIDATED"
    else:
        table=outcomes.join(features);legacy=legacy.reindex(table.index)
        core=[name for group in CORE_GROUPS for name in GROUPS[group]]
        available=legacy.loc[np.isfinite(legacy[core].to_numpy()).all(axis=1),core]
        pick,_=select_lookalikes(available,legacy_query,CORE_GROUPS,rules);mode="LEGACY_CORE_DIAGNOSTIC"
    if len(pick)!=rules.k:raise ValueError("insufficient descriptive case windows")
    summary["case_matcher"]=mode;summary["case_warning"]="Legacy daily CORE may use older within-day asset closes; it does not remedy missing precise48h endpoints."
    idx=table.index.get_indexer(pick.t0);table["selected"]=table.index.isin(pick.t0);table["weight"]=mix_weights(len(table),idx,active)
    table["distance"]=pick.set_index("t0").distance.reindex(table.index);table.to_parquet(out/"weighted_windows.parquet")
    selected=table.loc[pick.t0].copy();selected["state_time"]=selected.index+pd.Timedelta(hours=c["prefix_hours"]);selected.to_csv(out/"lookalikes.csv",index_label="window_start")
    dump(out/"validation.json",summary)
    print(json.dumps({"stage":"validate","models":len(latest),"windows":len(table),"gates":summary["statistical_gates"],"query_coverage":covered,"adaptive_pass":summary["adaptive_pass"],"active_alpha":active,"case_matcher":mode,"out":str(out)}),flush=True)

def describe(x,w):
    return {"mean":float(np.dot(normalized_weights(w),x)),"median":weighted_quantile(x,w,.5),
      "p10":weighted_quantile(x,w,.1),"p90":weighted_quantile(x,w,.9),"positive":float(np.dot(normalized_weights(w),x>0)),
      "worst":float(np.min(x))}

def compare(cfg,c,out):
    validation=json.loads((out/"validation.json").read_text())
    if not validation["integrity_pass"]:raise ValueError("integrity gate failed")
    if json.loads((out/"frozen_config.json").read_text())!=c:raise ValueError("settings changed after validation")
    latest,scores,starts,inventory,scratch=frozen_registered(c,out)
    t=pd.read_parquet(out/"weighted_windows.parquet");sel=starts.get_indexer(t.index)
    if (sel<0).any():raise ValueError("window alignment failed")
    w=t.weight.to_numpy();lw=normalized_weights(t.selected.to_numpy(float))
    paper=pd.read_csv(out/"paper_prefix.csv",index_col=0)
    rows=[];returns={};prefixes={};curves={};g=c["bootstrap"]
    cache_file=out/"cache_inputs.json"
    previous_cache=json.loads(cache_file.read_text()) if cache_file.exists() else None
    cache_inputs={}

    for name,e in sorted(latest.items()):
        cp=safe_path(c["cache_dir"])/name/e["run_key"]
        paths={suffix:Path(str(cp)+suffix) for suffix in [".arrays.npz",".windows.parquet",".json"]}
        before={suffix:{"path":str(path),"sha256":sha(path)} for suffix,path in paths.items()}
        if previous_cache is not None and previous_cache.get(name)!=before:
            raise ValueError("frozen cache changed: "+name)
        cache_inputs[name]=before

        windows=pd.read_parquet(str(cp)+".windows.parquet")
        if not windows.index.equals(starts):raise ValueError("cache row order differs: "+name)
        with np.load(str(cp)+".arrays.npz") as arr:
            eq=arr["equity"];gross=arr["gross"]
            if eq.shape!=(len(starts),c["horizon_hours"]+1) or gross.shape!=eq.shape:raise ValueError("cache dimensions differ")
            ret=continuation_returns(eq,gross,c["prefix_hours"],c["close_fee"])
            original=continuation_returns(eq,gross,0,c["close_fee"])
            saved=np.asarray(scores[name]["per_window"]["R_liq"])
            if not np.allclose(original,saved,rtol=0,atol=1e-12):raise ValueError("terminal accounting differs: "+name)
            prefix=eq[:,c["prefix_hours"]]/eq[:,0]-1
            curves[name]=eq[sel[t.selected.to_numpy()],:c["prefix_hours"]+1]/eq[sel[t.selected.to_numpy()],0,None]-1
        if before!={suffix:{"path":str(path),"sha256":sha(path)} for suffix,path in paths.items()}:
            raise ValueError("cache changed while reading: "+name)
        returns[name]=ret[sel];prefixes[name]=prefix[sel]
        stat=describe(ret[sel],w);look=describe(ret[sel],lw);pre=describe(prefix[sel],lw)
        row={"model":name,"candidate":e["candidate"],"weight_mode":validation["weight_mode"],
          "original_headline_ret":e["headline_ret"]["full"],"original_cs_hit":e["cs_hit"]["full"],
          "original_eligible":e["eligible"],"report_only_failed_gates":",".join(k for k,v in e["gates"].items() if not v),
          **{"remainder_"+k:v for k,v in stat.items()},**{"look_remainder_"+k:v for k,v in look.items()},
          **{"look_prefix_"+k:v for k,v in pre.items()},"run_key":e["run_key"],
          "interpretation":"own historical continuation; no shared-account switch"}
        if name in PAPER_MODELS:
            observed=float(paper[PAPER_MODELS[name]].iloc[-1])
            path=paper[PAPER_MODELS[name]].to_numpy(float)
            bandlow=np.quantile(curves[name],.1,axis=0);bandhigh=np.quantile(curves[name],.9,axis=0)
            row.update({"paper_prefix_return":observed,"paper_prefix_percentile_in_look":float(np.dot(lw,prefix[sel]<=observed)),
              "look_share_within_2pp_of_paper":float(np.dot(lw,np.abs(prefix[sel]-observed)<=c["prefix_similarity_tolerance"])),
              "paper_path_band_coverage":float(((path>=bandlow)&(path<=bandhigh)).mean())})
        rows.append(row)
    dump(cache_file,cache_inputs)
    incumbent=returns[c["incumbent"]];candidate_count=sum(e["candidate"] for e in latest.values())
    family_level=1-(1-g["level"])/candidate_count
    for row in rows:
        name=row["model"];delta=returns[name]-incumbent
        ci=grouped_bootstrap_delta(t.index,delta,w,g["reps"],g["seed"],g["level"])
        fci=grouped_bootstrap_delta(t.index,delta,w,g["reps"],g["seed"],family_level)
        row.update({"delta_vs_incumbent":ci["mean"],"delta_lower90":ci["lower"],"delta_upper90":ci["upper"],
          "delta_lower_family":fci["lower"],"delta_upper_family":fci["upper"],
          "beat_incumbent_share":float(np.dot(w,delta>0)),"beat_cash_share":float(np.dot(w,returns[name]>0)),
          "beat_btc_share":float(np.dot(w,returns[name]>returns["team_btc_hold"]))})
    frame=pd.DataFrame(rows).sort_values("model")
    frame.to_csv(out/"all_registered_models.csv",index=False)
    pd.DataFrame({name:x for name,x in returns.items()},index=t.index).to_parquet(out/"model_continuations.parquet")
    pd.DataFrame({name:x for name,x in prefixes.items()},index=t.index).to_parquet(out/"model_prefixes.parquet")
    cases=t.loc[t.selected].copy()
    cases["state_time"]=cases.index+pd.Timedelta(hours=c["prefix_hours"])
    cases["incumbent_prefix_return"]=prefixes[c["incumbent"]][t.selected.to_numpy()]
    cases["incumbent_remainder_liq"]=incumbent[t.selected.to_numpy()]
    observed=paper[PAPER_MODELS[c["incumbent"]]].to_numpy(float)
    cases["paper_prefix_difference"]=cases.incumbent_prefix_return-observed[-1]
    cases["paper_prefix_path_rmse"]=np.sqrt(((curves[c["incumbent"]]-observed[None,:])**2).mean(axis=1))
    cases.to_csv(out/"incumbent_case_windows.csv",index_label="window_start")
    short={"status":"NOT_VALIDATED","scoring_table":"separate from main continuation table",
      "executable_event_ledger":"UNAVAILABLE; no minute/second strategy edge claimed",
      "minimum_independent_episodes":c["short"]["minimum_episodes"],"account_shorts":"UNVERIFIED",
      "prior_research":{"variants":72,"positive_all_three_periods":0,"positive_april_august_2026":0},
      "metrics":["continuation precision","rebound-first rate","remaining favorable excursion","causal cover delay",
                 "net expectancy after entry and cover","tail losses","independent episodes"],
      "reasons":["Existing minute timestamps/exit-lag assumptions require repair","Three days of second quotes insufficient",
                 "No shared-incumbent transition execution","HFT remains forbidden"]}
    dump(out/"short_diagnostics.json",short)
    pd.DataFrame([{"candidate":"NO_VALIDATED_LEDGER","status":"NOT_VALIDATED","independent_episodes":0,
      "continuation_precision":None,"rebound_first_rate":None,"remaining_favorable_excursion":None,
      "cover_delay":None,"net_expectancy":None,"tail_loss":None}]).to_csv(out/"short_timing_table.csv",index=False)
    dump(out/"comparison.json",{"integrity_pass":True,"models":len(frame),"candidates":candidate_count,
       "weight_mode":validation["weight_mode"],"adaptive_pass":validation["adaptive_pass"],
       "paper_incumbent_prefix":float(observed[-1]),"prefix_hours":c["prefix_hours"],
       "remaining_hours":c["horizon_hours"]-c["prefix_hours"],"window_neff":float(1/np.dot(w,w)),
       "month_clusters":int(t.index.tz_convert("UTC").strftime("%Y-%m").nunique()),
       "ranking_enabled":False,"reason":"Historical continuation diagnostics; adaptive and actual switch/account gates not passed"})
    report(out,c,validation,frame,cases,short)
    print(json.dumps({"stage":"compare","models":len(frame),"paper_incumbent_prefix":float(observed[-1]),
                     "weight_mode":validation["weight_mode"],"ranking_enabled":False,"out":str(out)}),flush=True)

def report(out,c,v,frame,cases,short):
    lines=["# Book regime evaluator: generated results","",
      "Snapshot: "+c["asof"]+". Prefix: "+str(c["prefix_hours"])+"h; remaining: "+str(c["horizon_hours"]-c["prefix_hours"])+"h.",
      "","**Weight mode: "+v["weight_mode"]+". Adaptive pass: "+str(v["adaptive_pass"])+".**",
      "","Artifact hashes, alignment and numerical integrity passed. Current market coverage and forecast usefulness are separate gates.",
      "","Chosen alpha on SCREEN: "+str(v["chosen_on_screen"])+". Active alpha: "+str(v["active_alpha"])+".",
      "","Confirmation CRPS improvement CI: "+json.dumps(v["confirm_crps_improvement"])+".",
      "","Confirmation Brier degradation CI: "+json.dumps(v["confirm_brier_degradation"])+".",
      "","Statistical gates: "+json.dumps(v["statistical_gates"])+".",
      "","Current complete archive data: "+str(v["current_data_confirmed"])+".",
      "","Current feature coverage: "+str(v["current_query_coverage"])+". Missing: "+", ".join(v["current_missing_features"])+".",
      "","Case-study matcher: "+v["case_matcher"]+". "+v["case_warning"],
      "","All "+str(len(frame))+" registered models are included. Another "+str(len(json.loads((out/'model_inventory.json').read_text())['unregistered_not_assessed']))+" unregistered research cache names are inventoried separately.",
      "","These are each model's own historical continuation, not switching from identical incumbent holdings. The original leaderboard is unchanged. Strategy models were developed on observed history; no pristine holdout claim.",
      "","## First 96 hours versus the e20 paper replay","",
      "| Model | Paper prefix | Legacy case prefix median | p10 | p90 | Paper percentile | Path band coverage |",
      "|---|---:|---:|---:|---:|---:|---:|"]
    for _,r in frame[frame.model.isin(PAPER_MODELS)].iterrows():
        lines.append("| "+r.model+" | "+f"{r.paper_prefix_return:.2%} | {r.look_prefix_median:.2%} | {r.look_prefix_p10:.2%} | {r.look_prefix_p90:.2%} | {r.paper_prefix_percentile_in_look:.1%} | {r.paper_path_band_coverage:.1%}"+" |")
    lines+=["","Legacy CORE case statistics never affect baseline weights. Prefix statistics are descriptive, not independent prediction tests: matching uses market observations from the already observed prefix. Paper is not the actual competition account.",
      "","## All registered models: historical continuation diagnostics","",
      "| Model | Mean remainder | p10 | Delta vs e20 | Family-adjusted lower delta | Original hard eligibility |",
      "|---|---:|---:|---:|---:|---:|"]
    for _,r in frame.iterrows():
        lines.append("| "+r.model+" | "+f"{r.remainder_mean:.2%} | {r.remainder_p10:.2%} | {r.delta_vs_incumbent:.2%} | {r.delta_lower_family:.2%} | {r.original_eligible}"+" |")
    lines+=["","Full data: all_registered_models.csv; selected historical cases: incumbent_case_windows.csv; chronological forecast audit: walkforward.csv.",
      "","## Separate short timing table","","```json",json.dumps(short,indent=2),"```",
      "","No executable short-event ledger is available, so timing scores are not fabricated. At least "+str(c["short"]["minimum_episodes"])+" episodes is only a minimum evidence guard, not proof of independence or profitability.",
      "","Reproduction: run the commands in the research README from Book's dedicated worktree. Hashes, frozen settings, and model provenance are stored in the accompanying JSON files."]
    (out/"REPORT.md").write_text("\n".join(lines)+"\n")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage",choices=["validate","compare"],required=True)
    args=parser.parse_args();cfg=load_config();c=cfg["book_regime_eval"]
    if pd.Timestamp(c["competition_start"])+pd.Timedelta(hours=c["prefix_hours"])!=pd.Timestamp(c["asof"]):raise ValueError("prefix date mismatch")
    if pd.Timestamp(c["competition_start"])+pd.Timedelta(hours=c["horizon_hours"])!=pd.Timestamp(c["competition_end"]):raise ValueError("competition horizon mismatch")
    out=safe_path(c["out_dir"]);out.mkdir(parents=True,exist_ok=True)
    if args.stage=="validate":validate(cfg,c,out)
    else:compare(cfg,c,out)

if __name__=="__main__":main()
