"""Automatic publication of conditional weak-market evidence; no live execution."""
from __future__ import annotations
import hashlib,io,json,os
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from backtest.scoring.score import clean,dumps
from backtest.scoring.registry import locked
from backtest.scoring.weak_risk import remainder_risk
from backtest.scoring.weak_short import short_diagnostics
from backtest.scoring.weak_stats import clustered_draws,simultaneous_bounds,tail_mean
from research.book.regime_eval.run import safe_path,sha,describe
from research.book.regime_eval.metrics import continuation_returns
from backtest.scoring.score2 import atomic_write,signature
from backtest.scoring.weak_render import render

PROFILES=("weak_archived","weak_fresh_btc")
EVIDENCE=("return","mdd","CS","CS_UTC","Sharpe","Sortino","Calmar")

def selection_score(cash_bounds,delta_bounds):
    return np.minimum(cash_bounds,delta_bounds).min(axis=1)

def rank_frame(frame):
    f=frame.sort_values(["selection_score","CS","model"],ascending=[False,False,True]).copy()
    f["rank"]=np.arange(1,len(f)+1);f["production_eligible"]=False
    return f

def load_checkpoint(cfg):
    root=safe_path(cfg["book_score2"]["checkpoint"])
    manifest=json.loads((root/"artifact_manifest.json").read_text())
    required={"frozen_config.json","registered_snapshot.json","cases.parquet","input_manifest.json","selection_validation.json","close_snapshot.parquet","source_cache_manifest.json"}
    if not required<=set(manifest):raise ValueError("weak checkpoint manifest incomplete")
    for name,value in manifest.items():
        if sha(root/name)!=value["sha256"]:raise ValueError("weak checkpoint changed: "+name)
    frozen=json.loads((root/"frozen_config.json").read_text());c=frozen["weak"];base=frozen["base"]
    if c!=cfg["book_weak_eval"] or frozen["scoring"]!=cfg["scoring"]:
        raise ValueError("weak settings differ from frozen protocol")
    cases=pd.read_parquet(root/"cases.parquet")
    if not cases.index.is_unique or cases.index.tz is None:raise ValueError("invalid weak case grid")
    for profile in PROFILES:
        if int(cases[profile].sum())!=c["lookalikes"]["k"]:raise ValueError("weak case count changed")
    snapshots=json.loads((root/"registered_snapshot.json").read_text())
    inc=next(e for e in snapshots if e["model"]==base["incumbent"])
    source=safe_path(inc["score_json"])
    if sha(source)!=inc["score_sha256"]:raise ValueError("fixed incumbent source changed")
    s=json.loads(source.read_text());starts=pd.DatetimeIndex(pd.to_datetime(s["per_window"]["start"],utc=True))
    ix=starts.get_indexer(cases.index)
    if (ix<0).any():raise ValueError("weak cases outside source cache")
    modules=["backtest/scoring/weak_board.py","backtest/scoring/weak_stats.py",
             "backtest/scoring/weak_risk.py","backtest/scoring/weak_short.py",
             "backtest/scoring/score2.py","backtest/scoring/metrics.py"]
    repo=Path(__file__).resolve().parents[2]
    metric_hashes={name:sha(repo/name) for name in modules}
    protocol=hashlib.sha256(json.dumps({"checkpoint":manifest,"metrics":metric_hashes},sort_keys=True).encode()).hexdigest()[:20]
    cp={"root":root,"c":c,"base":base,"cases":cases,"frozen":frozen,"snapshots":snapshots,
        "signature":signature(s),"starts":starts,"ix":ix,"protocol":protocol,"metric_hashes":metric_hashes,
        "input":json.loads((root/"input_manifest.json").read_text()),"incumbent_score":s,
        "validation":json.loads((root/"selection_validation.json").read_text()),
        "source_caches":json.loads((root/"source_cache_manifest.json").read_text())}
    pinned=json.loads((safe_path(c["source_checkpoint"])/"cache_inputs.json").read_text())[base["incumbent"]]
    for item in pinned.values():
        if sha(safe_path(item["path"]))!=item["sha256"]:raise ValueError("fixed incumbent cache changed")
    return cp

def evaluate_score(score,cp):
    base=cp["base"];model=score["model"]
    hard={k:bool(v["pass"]) for k,v in score["gates"].items() if v["hard"]}
    if not hard or bool(score["eligible"])!=all(hard.values()):raise ValueError("original hard eligibility inconsistent")
    if not score["windows"]["full_run"] or score["tool_version"]!=base["tool_version"]:
        raise ValueError("weak scoring requires compatible full tool run")
    if signature(score)!=cp["signature"]:raise ValueError("weak scoring data/input mismatch")
    starts=pd.DatetimeIndex(pd.to_datetime(score["per_window"]["start"],utc=True))
    if not starts.equals(cp["starts"]):raise ValueError("weak scoring window order mismatch")
    path=safe_path(Path(base["cache_dir"])/model["name"]/model["run_key"])
    paths={s:Path(str(path)+s) for s in (".arrays.npz",".windows.parquet",".json",".trades.parquet")}
    hashes={s:{"path":str(p),"sha256":sha(p)} for s,p in paths.items()}
    original=cp["source_caches"].get(model["name"])
    if original and original["run_key"]==model["run_key"]:
        if original["files"]!=hashes:raise ValueError("frozen registered model cache changed")
    meta=json.loads(paths[".json"].read_text())
    if meta["key"]!=model["run_key"] or meta["model"]!=model["name"] or meta["tool_version"]!=base["tool_version"] or meta.get("long_only",False):
        raise ValueError("weak cached metadata mismatch")
    if not pd.read_parquet(paths[".windows.parquet"]).index.equals(starts):
        raise ValueError("weak cache row order mismatch")
    with np.load(paths[".arrays.npz"],allow_pickle=False) as a:
        eq=a["equity"];gross=a["gross"]
        if eq.shape!=(len(starts),base["horizon_hours"]+1) or gross.shape!=eq.shape:
            raise ValueError("weak cache dimensions mismatch")
        old=continuation_returns(eq,gross,0,base["close_fee"])
        if not np.allclose(old,score["per_window"]["R_liq"],rtol=0,atol=1e-12):
            raise ValueError("weak original liquidation accounting mismatch")
        evidence={key:[] for key in EVIDENCE}
        for hours in cp["c"]["horizons_hours"]:
            values=remainder_risk(eq[cp["ix"]],gross[cp["ix"]],cp["cases"].index,0,hours,cp["frozen"]["scoring"])
            for key in EVIDENCE:evidence[key].append(values[key])
        evidence={key:np.stack(v,axis=1) for key,v in evidence.items()}
    trades=pd.read_parquet(paths[".trades.parquet"])
    panel=pd.read_parquet(cp["root"]/"close_snapshot.parquet")
    short=short_diagnostics(trades,panel,cp["cases"].index,cp["c"]["primary_hours"],cp["c"]["short"])
    if hashes!={s:{"path":str(p),"sha256":sha(p)} for s,p in paths.items()}:
        raise ValueError("weak model cache changed while reading")
    row={"model":model["name"],"run_key":model["run_key"],"candidate":bool(model["candidate"]),
         "original_eligible":bool(score["eligible"]),"failed_hard_gates":",".join(k for k,v in hard.items() if not v),
         "original_headline_ret":score["return_first"]["full"]["headline_ret"],
         "original_cs_hit":score["return_first"]["full"]["cs_hit"],
         "account_switch_validated":False,"initialization":"CASH_AT_T0"}
    return row,evidence,short,hashes

def save_score(score,cfg,cp):
    row,evidence,short,cache=evaluate_score(score,cp)
    blob=dumps(score).encode();digest=hashlib.sha256(blob).hexdigest()
    root=safe_path(cfg["book_score2"]["artifacts"])/cp["protocol"]/row["model"]/(row["run_key"]+"-"+digest[:16])
    root.mkdir(parents=True,exist_ok=True)
    buf=io.BytesIO();np.savez_compressed(buf,**evidence)
    files={"score.json":blob,"evidence.npz":buf.getvalue()}
    for name,frame in [("short_windows.parquet",short["windows"]),("short_episodes.parquet",short["episodes"])]:
        buf=io.BytesIO();frame.to_parquet(buf);files[name]=buf.getvalue()
    for name,data in files.items():
        p=root/name
        if p.exists() and sha(p)!=hashlib.sha256(data).hexdigest():raise ValueError("weak saved evidence changed")
        atomic_write(p,data)
    artifacts={name:{"path":str(root/name),"sha256":sha(root/name)} for name in files}
    return {"schema_version":2,"ts":datetime.now(timezone.utc).isoformat(),"protocol":cp["protocol"],
            "model":row["model"],"run_key":row["run_key"],"source_sha256":digest,"row":row,
            "artifacts":artifacts,"cache_inputs":cache,"short_summary":short["summary"],
            "metric_hashes":cp["metric_hashes"]}

def entries(cfg):
    p=safe_path(cfg["book_score2"]["registry"])
    if not p.exists():return []
    try:return [json.loads(line) for line in p.read_text().splitlines()]
    except json.JSONDecodeError as exc:raise ValueError("score2 registry corrupt") from exc

def read_evidence(entry,cp):
    for item in entry["artifacts"].values():
        if sha(safe_path(item["path"]))!=item["sha256"]:raise ValueError("weak published artifacts changed")
    source=safe_path(entry["artifacts"]["score.json"]["path"])
    if sha(source)!=entry["source_sha256"]:raise ValueError("weak source digest inconsistent")
    s=json.loads(source.read_text())
    expected={"model":s["model"]["name"],"run_key":s["model"]["run_key"],"candidate":bool(s["model"]["candidate"]),
              "original_eligible":bool(s["eligible"]),"original_headline_ret":s["return_first"]["full"]["headline_ret"],
              "original_cs_hit":s["return_first"]["full"]["cs_hit"],
              "failed_hard_gates":",".join(k for k,v in s["gates"].items() if v["hard"] and not v["pass"]),
              "initialization":"CASH_AT_T0","account_switch_validated":False}
    if any(entry["row"].get(k)!=v for k,v in expected.items()):raise ValueError("weak registry metadata differs from source")
    if signature(s)!=cp["signature"] or s["model"]["run_key"]!=entry["run_key"] or s["model"]["name"]!=entry["model"]:
        raise ValueError("weak saved source identity mismatch")
    with np.load(safe_path(entry["artifacts"]["evidence.npz"]["path"]),allow_pickle=False) as a:
        result={key:a[key].copy() for key in EVIDENCE}
    shape=(len(cp["cases"]),len(cp["c"]["horizons_hours"]))
    if any(x.shape!=shape or not np.isfinite(x).all() for x in result.values()):raise ValueError("weak evidence vector invalid")
    windows=pd.read_parquet(safe_path(entry["artifacts"]["short_windows.parquet"]["path"]))
    if not windows.index.equals(cp["cases"].index):raise ValueError("weak short window order mismatch")
    return result,windows

def make_frame(all_entries,cp):
    latest={};attempts={}
    for e in all_entries:
        if e.get("protocol")==cp["protocol"]:
            latest[e["model"]]=e;attempts[e["model"]]=attempts.get(e["model"],0)+1
    if not latest:raise ValueError("no weak scores for current protocol")
    fixed=cp["base"]["incumbent"];names=sorted(latest)
    inc=names.index(fixed) if fixed in names and latest[fixed]["run_key"]==cp["incumbent_score"]["model"]["run_key"] else None
    evidences={name:read_evidence(latest[name],cp) for name in names}
    if inc is None:
        _,ev,sh,_=evaluate_score(cp["incumbent_score"],cp)
        names.append("__fixed_incumbent");evidences["__fixed_incumbent"]=(ev,sh["windows"]);inc=len(names)-1
    cases=cp["cases"];nh=len(cp["c"]["horizons_hours"]);primary=cp["c"]["horizons_hours"].index(cp["c"]["primary_hours"])
    x=np.stack([np.tile(evidences[name][0]["return"],(1,len(PROFILES))) for name in names])
    w=np.stack([cases[p].to_numpy(float)/cases[p].sum() for p in PROFILES for h in range(nh)],axis=1)
    union=cases[list(PROFILES)].any(axis=1).to_numpy();b=cp["c"]["bootstrap"]
    local,clusters=clustered_draws(cases.index[union],b["reps"],b["seed"],max(cp["c"]["horizons_hours"]))
    draws=np.zeros((len(local),len(cases)));draws[:,union]=local
    bounds=simultaneous_bounds(x,inc,draws,b["level"],w)
    scores=selection_score(bounds["cash_family_lower"],bounds["delta_family_lower"])
    rows=[];short_rows=[];details=[];jackknife=[];sensitivity=[]
    for i,name in enumerate(names):
        if name=="__fixed_incumbent":continue
        entry=latest[name];ev,sw=evidences[name];row=dict(entry["row"])
        a=cases.weak_archived.to_numpy(bool);fresh=cases.weak_fresh_btc.to_numpy(bool);r=ev["return"][a,primary]
        summary=describe(r,np.ones(len(r)))
        row.update({"selection_score":float(scores[i]),"robust_mean":float(bounds["mean"][i].min()),
                    "fresh_mean":float(ev["return"][fresh,primary].mean()),
                    "delta_vs_incumbent":float(bounds["delta"][i,primary]),
                    "cash_lower90":float(bounds["cash_lower90"][i,primary]),
                    "cash_upper90":float(bounds["cash_upper90"][i,primary]),
                    "delta_lower90":float(bounds["delta_lower90"][i,primary]),
                    "delta_upper90":float(bounds["delta_upper90"][i,primary]),
                    "cash_family_lower":float(bounds["cash_family_lower"][i].min()),
                    "delta_family_lower":float(bounds["delta_family_lower"][i].min()),
                    "CS":float(ev["CS"][a,primary].mean()),"CS_UTC":float(ev["CS_UTC"][a,primary].mean()),
                    "CS_HIT_positive":float(ev["CS"][a,primary][r>0].mean()) if (r>0).any() else None,
                    "mdd_mean":float(ev["mdd"][a,primary].mean()),"mdd_worst":float(ev["mdd"][a,primary].max()),
                    "tail10_mean":tail_mean(r,.1),"win_vs_incumbent":float((r>evidences[names[inc]][0]["return"][a,primary]).mean()),
                    "attempts":attempts[name],**{"return_"+k:v for k,v in summary.items()}})
        row["strengthened_evidence"]=bool(scores[i]>0 and row["original_eligible"] and clusters>=cp["c"]["min_clusters"]
            and all(cp["validation"]["quarter_clusters"][p]>=cp["c"]["min_clusters"] for p in PROFILES))
        rows.append(row)
        for profile in PROFILES:
            mask=cases[profile].to_numpy(bool);sub=sw.loc[mask]
            counts={key:int(sub[key].sum()) for key in sub if key.endswith("h") and key.startswith(("valid_","correct_","wrong_direction_","cost_only_loss_","unresolved_","rebound_losses_"))}
            sr={"model":name,"profile":profile,"onsets":int(sub.onsets.sum()),"windows_with_onsets":int((sub.onsets>0).sum()),
                "total_windows":len(sub),"terminal_censored":int(sub.terminal_censored.sum()),**counts}
            for h in cp["c"]["short"]["horizons_hours"]:
                v=sr.get(f"valid_{h}h",0);sr[f"precision_{h}h"]=sr.get(f"correct_{h}h",0)/v if v else None
                numerator=draws[:,mask]@sub[f"correct_{h}h"].to_numpy(float)
                denominator=draws[:,mask]@sub[f"valid_{h}h"].to_numpy(float);ok=denominator>0
                sr[f"precision_{h}h_lower90"]=float(np.quantile(numerator[ok]/denominator[ok],.05)) if ok.any() else None
                sr[f"precision_{h}h_upper90"]=float(np.quantile(numerator[ok]/denominator[ok],.95)) if ok.any() else None
            for key in ("closed_episodes","reweighted_episodes","cover_proxy_valid","cover_proxy_wins","cover_rebound_losses",
                        "barrier_take_profit_sampled","barrier_stop_loss_sampled","barrier_censored","barrier_missing_price","barrier_intrahour_ambiguous"):
                sr[key]=int(sub[key].sum())
            support=sub["valid_6h"]>0
            sr["window_precision_6h"]=float(sub.loc[support,"precision_6h"].mean()) if support.any() else None
            sr["window_mean_proxy_net_6h"]=float(sub.loc[support,"mean_proxy_net_6h"].mean()) if support.any() else None
            valid6=int(sub.valid_6h.sum())
            sr["trade_mean_proxy_net_6h"]=float((sub.mean_proxy_net_6h.fillna(0)*sub.valid_6h).sum()/valid6) if valid6 else None
            sr["minimum_onsets_met"]=bool(sr["onsets"]>=cp["c"]["short"]["minimum_episodes"])
            sr["status"]="HOURLY_PROXY_DESCRIPTIVE" if sr["onsets"] else "NO_SHORT_ONSETS"
            short_rows.append(sr)
        for column in cases:
            if column.startswith(PROFILES) and not column.endswith("_distance") and "_k" in column:
                mask=cases[column].to_numpy(bool);rr=ev["return"][mask,primary]
                sensitivity.append({"model":name,"profile":column,"n":len(rr),"mean":float(rr.mean()),
                    "delta_vs_incumbent":float((rr-evidences[names[inc]][0]["return"][mask,primary]).mean())})
        qlabels=cases.index.tz_localize(None).to_period("Q").astype(str)
        for q in sorted(set(qlabels[union])):
            remain=(qlabels!=q)&union;means=[]
            for p in PROFILES:
                mask=remain&cases[p].to_numpy(bool)
                for h in range(nh):
                    rr=ev["return"][mask,h];ir=evidences[names[inc]][0]["return"][mask,h]
                    means.extend([float(rr.mean()),float((rr-ir).mean())])
            jackknife.append({"model":name,"omitted_quarter":q,"robust_mean_advantage":min(means)})
        for wi,t in enumerate(cases.index):
            for hi,h in enumerate(cp["c"]["horizons_hours"]):
                details.append({"model":name,"window_start":str(t),"hours":h,
                    **{key:float(ev[key][wi,hi]) for key in EVIDENCE},
                    "btc_forward240":float(cases.future_return.iloc[wi]),
                    **{p:bool(cases[p].iloc[wi]) for p in PROFILES}})
        control=cases.positive_control.to_numpy(bool)
        for label,mask in [("positive_control",control),
            ("future_down_stress",a&(cases.future_return.to_numpy()<=cp["c"]["stress"]["future_down"])),
            ("future_rebound_stress",a&(cases.future_return.to_numpy()>=cp["c"]["stress"]["future_rebound"]))]:
            rr=ev["return"][mask,primary]
            row[label+"_n"]=len(rr);row[label+"_mean"]=float(rr.mean()) if len(rr) else None
    frame=rank_frame(pd.DataFrame(rows))
    evidence={"clusters":clusters,"bootstrap_reps":bounds["valid_reps"],"family_quantile":bounds["family_quantile"],
              "contexts":len(PROFILES)*nh,"family_models":len(names),"method":"centered standardized maximum; fixed bootstrap SE",
              "fresh_archive_confirmed":cp["input"]["fresh_archive_confirmed"]}
    return frame,pd.DataFrame(short_rows),pd.DataFrame(details),pd.DataFrame(sensitivity),pd.DataFrame(jackknife),evidence

def atomic_batch(payloads):
    """Stage all generated views before replacement, restoring on commit error."""
    import tempfile
    staged={};previous={};replaced=[]
    try:
        for path,value in payloads.items():
            path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
            previous[path]=path.read_bytes() if path.exists() else None
            data=value if isinstance(value,bytes) else value.encode()
            fd,name=tempfile.mkstemp(prefix="."+path.name+".staged.",dir=path.parent)
            staged[path]=Path(name)
            with os.fdopen(fd,"wb") as f:f.write(data);f.flush();os.fsync(f.fileno())
        try:
            for path,temp in staged.items():
                os.replace(temp,path);replaced.append(path)
        except BaseException:
            for path in reversed(replaced):
                if previous[path] is None:path.unlink(missing_ok=True)
                else:atomic_write(path,previous[path])
            raise
    finally:
        for temp in staged.values():temp.unlink(missing_ok=True)

def publish_scores(scores,cfg,cp):
    prepared=[save_score(score,cfg,cp) for score in scores]
    with locked("scoring-score2"):
        old=entries(cfg);current={}
        identity=lambda e:(e["protocol"],e["model"],e["run_key"],e["source_sha256"])
        for e in old:current[(e["protocol"],e["model"])]=identity(e)
        new=[]
        for e in prepared:
            key=(e["protocol"],e["model"]);ident=identity(e)
            if current.get(key)!=ident:new.append(e);current[key]=ident
        combined=old+new
        frame,short,details,sensitivity,jackknife,evidence=make_frame(combined,cp)
        text=render(cp,frame,short,evidence)
        registry=safe_path(cfg["book_score2"]["registry"])
        board=safe_path(cfg["book_score2"]["leaderboard"])
        payloads={safe_path(cfg["book_score2"]["csv"]):frame.to_csv(index=False),
                  board:text,board.with_name("short_leaderboard_2.csv"):short.to_csv(index=False)}
        if new:
            prefix=registry.read_text() if registry.exists() else ""
            payloads[registry]=prefix+"".join(json.dumps(clean(e),sort_keys=True,allow_nan=False)+"\n" for e in new)
        for name,data in [("model_windows.csv",details),("sensitivity.csv",sensitivity),("leave_quarter_out.csv",jackknife),("all_models.csv",frame),("short_table.csv",short)]:
            payloads[cp["root"]/name]=data.to_csv(index=False)
        payloads[cp["root"]/"comparison_validation.json"]=json.dumps(clean(evidence),indent=2,allow_nan=False)+"\n"
        atomic_batch(payloads)
    return board,frame

def publish(score,cfg,report_path=None):
    cp=load_checkpoint(cfg);board,frame=publish_scores([score],cfg,cp)
    if report_path is not None:
        r=frame.loc[frame.model==score["model"]["name"]].iloc[0]
        if r.run_key!=score["model"]["run_key"]:raise ValueError("published revision differs from requested run")
        atomic_write(safe_path(report_path),f"# Weak-market score2: {r.model}\n\nExperimental rank{r['rank']}, score{r.selection_score:+.2%}, mean{r.return_mean:+.2%}, p10{r.return_p10:+.2%}, CS{r.CS:+.3f}.\n\nFull instructions/results:{board}. Conditional evidence only; current-account switch UNVERIFIED.\n")
    return board

def import_registered(cfg):
    cp=load_checkpoint(cfg);scores=[]
    for e in cp["snapshots"]:
        p=safe_path(e["score_json"])
        if sha(p)!=e["score_sha256"]:raise ValueError("registered source changed:"+e["model"])
        scores.append(json.loads(p.read_text()))
    return publish_scores(scores,cfg,cp)[0]

def refresh(cfg):
    cp=load_checkpoint(cfg)
    return publish_scores([],cfg,cp)[0]
