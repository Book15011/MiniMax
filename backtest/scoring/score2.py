"""Offline score2 publication against an immutable market checkpoint.

It writes a separate append-only registry and leaderboard, never the primary
registry, original leaderboard, checkpoint, or live execution state.
"""
from __future__ import annotations
import hashlib,json,os,tempfile
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from backtest.scoring.registry import locked
from backtest.scoring.score import dumps,clean
from research.book.regime_eval.run import safe_path,sha,describe,PAPER_MODELS
from research.book.regime_eval.metrics import normalized_weights,continuation_returns,grouped_bootstrap_delta

REQUIRED=("frozen_config.json","validation.json","weighted_windows.parquet",
          "input_manifest.json","registered_snapshot.json","cache_inputs.json","paper_prefix.csv")


def atomic_write(path,content):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix="."+path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(content if isinstance(content,bytes) else content.encode())
            f.flush();os.fsync(f.fileno())
        os.replace(name,path)
    finally:
        Path(name).unlink(missing_ok=True)


def signature(score):
    return json.dumps([score["data"],score.get("inputs_sha256",{})],sort_keys=True)


def load_checkpoint(cfg):
    if cfg["book_score2"]["schema_version"]==2:
        from backtest.scoring.weak_board import load_checkpoint as load_weak
        return load_weak(cfg)
    options=cfg["book_score2"]
    if options["schema_version"]!=1:raise ValueError("unsupported score2 schema")
    root=safe_path(options["checkpoint"])
    manifest=json.loads((root/"artifact_manifest.json").read_text())
    hashes={}
    for name in REQUIRED:
        if name not in manifest or sha(root/name)!=manifest[name]["sha256"]:
            raise ValueError("frozen checkpoint changed or incomplete: "+name)
        hashes[name]=manifest[name]["sha256"]
    c=json.loads((root/"frozen_config.json").read_text())
    v=json.loads((root/"validation.json").read_text())
    if not v["integrity_pass"]:raise ValueError("checkpoint integrity failed")
    table=pd.read_parquet(root/"weighted_windows.parquet")
    if not table.index.is_unique or table.index.tz is None or not len(table):
        raise ValueError("invalid checkpoint window index")
    w=normalized_weights(table.weight.to_numpy())
    selected=table.selected.to_numpy(bool)
    if not selected.any():raise ValueError("checkpoint has no descriptive cases")
    if v["active_alpha"]==0 and not np.allclose(w,1/len(w),rtol=0,atol=1e-14):
        raise ValueError("fallback checkpoint weights are not uniform")
    if v["active_alpha"]>0 and not v["adaptive_pass"]:
        raise ValueError("adaptive weights lack passed gates")
    snapshots=json.loads((root/"registered_snapshot.json").read_text())
    baseline=next(e for e in snapshots if e["model"]==c["incumbent"])
    source=safe_path(baseline["score_json"])
    if sha(source)!=baseline["score_sha256"]:raise ValueError("incumbent score changed")
    incumbent=json.loads(source.read_text())
    starts=pd.DatetimeIndex(pd.to_datetime(incumbent["per_window"]["start"],utc=True))
    ix=starts.get_indexer(table.index)
    if (ix<0).any():raise ValueError("checkpoint windows do not align with baseline")
    cp={"root":root,"c":c,"v":v,"table":table,"w":w,"selected":selected,
        "starts":starts,"ix":ix,"signature":signature(incumbent),"incumbent_score":incumbent,
        "paper":pd.read_csv(root/"paper_prefix.csv",index_col=0),
        "original_model_keys":{e["model"]:e.get("run_key",incumbent["model"]["run_key"]) for e in snapshots},
        "input":json.loads((root/"input_manifest.json").read_text()),"hashes":hashes}
    # Mixing runs from changed metric/publisher code silently would invalidate comparisons.
    metric_hashes={"publisher":sha(Path(__file__)),
                   "continuation_metrics":sha(Path(continuation_returns.__code__.co_filename)),
                   "summary_metrics":sha(Path(describe.__code__.co_filename))}
    cp["metric_hashes"]=metric_hashes
    cp["protocol"]=hashlib.sha256(json.dumps({"schema":1,"checkpoint":hashes,
                                             "metric_sources":metric_hashes},sort_keys=True).encode()).hexdigest()[:20]
    pinned=json.loads((root/"cache_inputs.json").read_text())[c["incumbent"]]
    for item in pinned.values():
        if sha(safe_path(item["path"]))!=item["sha256"]:raise ValueError("frozen incumbent cache changed")
    cp["incumbent_returns"]=_trajectory(incumbent,cp)[0]
    for name,digest in hashes.items():
        if sha(root/name)!=digest:raise ValueError("checkpoint changed while reading")
    return cp


def _trajectory(score,cp):
    c=cp["c"];m=score["model"]
    if not score["windows"]["full_run"]:raise ValueError("score2 requires a full run")
    if score["tool_version"]!=c["tool_version"]:raise ValueError("score2 tool version differs from checkpoint")
    if signature(score)!=cp["signature"]:raise ValueError("score2 data or input files differ from checkpoint")
    starts=pd.DatetimeIndex(pd.to_datetime(score["per_window"]["start"],utc=True))
    if not starts.equals(cp["starts"]):raise ValueError("score2 window order differs from checkpoint")
    name=m["name"];key=m["run_key"]
    base=safe_path(Path(c["cache_dir"])/name/key)
    paths={s:Path(str(base)+s) for s in [".arrays.npz",".windows.parquet",".json"]}
    before={s:{"path":str(p),"sha256":sha(p)} for s,p in paths.items()}
    meta=json.loads(paths[".json"].read_text())
    if meta["key"]!=key or meta["tool_version"]!=c["tool_version"] or meta["model"]!=name or meta.get("long_only",False):
        raise ValueError("score2 cache metadata mismatch")
    if not pd.read_parquet(paths[".windows.parquet"]).index.equals(starts):
        raise ValueError("score2 cached row order mismatch")
    with np.load(paths[".arrays.npz"],allow_pickle=False) as a:
        eq=a["equity"];gross=a["gross"]
        if eq.shape!=(len(starts),c["horizon_hours"]+1) or gross.shape!=eq.shape:
            raise ValueError("score2 cache dimensions mismatch")
        original=continuation_returns(eq,gross,0,c["close_fee"])
        if not np.allclose(original,np.asarray(score["per_window"]["R_liq"]),rtol=0,atol=1e-12):
            raise ValueError("score2 original liquidation accounting mismatch")
        ret=continuation_returns(eq,gross,c["prefix_hours"],c["close_fee"])[cp["ix"]]
        prefix=(eq[:,c["prefix_hours"]]/eq[:,0]-1)[cp["ix"]]
        selected=cp["ix"][cp["selected"]]
        curves=eq[selected,:c["prefix_hours"]+1]/eq[selected,0,None]-1
    if before!={s:{"path":str(p),"sha256":sha(p)} for s,p in paths.items()}:
        raise ValueError("score2 cache changed while reading")
    return ret,prefix,curves,before


def evaluate_score(score,cp):
    hard={name:bool(g["pass"]) for name,g in score["gates"].items() if g["hard"]}
    if not hard or bool(score["eligible"])!=all(hard.values()):
        raise ValueError("score2 original hard eligibility inconsistent")
    ret,prefix,curves,cache=_trajectory(score,cp)
    w=cp["w"];lw=normalized_weights(cp["selected"].astype(float))
    stat=describe(ret,w);look=describe(ret,lw);pre=describe(prefix,lw)
    row={"model":score["model"]["name"],"run_key":score["model"]["run_key"],
         "candidate":bool(score["model"]["candidate"]),"original_eligible":bool(score["eligible"]),
         "original_headline_ret":float(score["return_first"]["full"]["headline_ret"]),
         "original_cs_hit":float(score["return_first"]["full"]["cs_hit"]),
         "failed_hard_gates":",".join(k for k,v in hard.items() if not v),
         "weight_mode":cp["v"]["weight_mode"],"adaptive_pass":bool(cp["v"]["adaptive_pass"]),
         "rank":None,"production_eligible":False,
         **{"score2_"+k:v for k,v in stat.items()},**{"look_remainder_"+k:v for k,v in look.items()},
         **{"look_prefix_"+k:v for k,v in pre.items()}}
    name=row["model"]
    row["paper_identity_status"]="NO_PAPER_FOR_THIS_REVISION"
    if (name in PAPER_MODELS and PAPER_MODELS[name] in cp["paper"] and
            row["run_key"]==cp["original_model_keys"].get(name)):
        row["paper_identity_status"]="FROZEN_REPLAY; ACCOUNT_UNVERIFIED"
        path=cp["paper"][PAPER_MODELS[name]].to_numpy(float)
        if len(path)!=curves.shape[1] or not np.isfinite(path).all():
            raise ValueError("score2 paper prefix incomplete")
        lo=np.quantile(curves,.1,axis=0);hi=np.quantile(curves,.9,axis=0)
        observed=float(path[-1])
        row.update(paper_prefix_return=observed,
                   paper_prefix_percentile=float(np.dot(lw,prefix<=observed)),
                   paper_path_band_coverage=float(((path>=lo)&(path<=hi)).mean()))
    return row,ret,prefix,cache


def _save_score(score,cfg,cp):
    row,ret,prefix,cache=evaluate_score(score,cp)
    blob=dumps(score).encode();digest=hashlib.sha256(blob).hexdigest()
    root=safe_path(cfg["book_score2"]["artifacts"])/cp["protocol"]/row["model"]
    key=row["run_key"]+"-"+digest[:16]
    source=root/(key+".score.json");vector=root/(key+".returns.npy")
    if source.exists() and sha(source)!=digest:raise ValueError("score2 saved source tampered")
    atomic_write(source,blob)
    import io
    buf=io.BytesIO();np.save(buf,ret,allow_pickle=False)
    vec=buf.getvalue()
    if vector.exists() and sha(vector)!=hashlib.sha256(vec).hexdigest():
        raise ValueError("score2 saved returns tampered")
    atomic_write(vector,vec)
    return {"ts":datetime.now(timezone.utc).isoformat(),"protocol":cp["protocol"],"model":row["model"],
            "run_key":row["run_key"],"row":row,"source_score":str(source),"source_sha256":digest,
            "returns":str(vector),"returns_sha256":sha(vector),"cache_inputs":cache,"metric_hashes":cp["metric_hashes"]}


def _entries(cfg):
    path=safe_path(cfg["book_score2"]["registry"])
    if not path.exists():return []
    try:return [json.loads(line) for line in path.read_text().splitlines()]
    except json.JSONDecodeError as exc:raise ValueError("score2 registry corrupt; refusing rewrite") from exc


def _frame(entries,cp):
    latest={};attempts={}
    for e in entries:
        if e["protocol"]==cp["protocol"]:
            latest[e["model"]]=e;attempts[e["model"]]=attempts.get(e["model"],0)+1
    if not latest:raise ValueError("no score2 rows for this checkpoint; run import-score2 or --score2")
    count=max(1,sum(bool(e["row"]["candidate"]) for e in latest.values()))
    b=cp["c"]["bootstrap"];rows=[]
    for name,e in sorted(latest.items()):
        source=safe_path(e["source_score"]);vector=safe_path(e["returns"])
        if sha(source)!=e["source_sha256"] or sha(vector)!=e["returns_sha256"]:
            raise ValueError("score2 published artifacts changed: "+name)
        score=json.loads(source.read_text())
        if signature(score)!=cp["signature"] or score["model"]["name"]!=name or score["model"]["run_key"]!=e["run_key"]:
            raise ValueError("score2 saved source identity mismatch")
        ret=np.load(vector,allow_pickle=False)
        if ret.shape!=cp["w"].shape or not np.isfinite(ret).all():raise ValueError("score2 saved vector corrupt")
        row=dict(e["row"])
        if not np.isclose(row["score2_mean"],np.dot(cp["w"],ret),rtol=0,atol=1e-14):
            raise ValueError("score2 saved summary inconsistent")
        delta=ret-cp["incumbent_returns"]
        ci=grouped_bootstrap_delta(cp["table"].index,delta,cp["w"],b["reps"],b["seed"],b["level"])
        family=grouped_bootstrap_delta(cp["table"].index,delta,cp["w"],b["reps"],b["seed"],1-(1-b["level"])/count)
        row.update(delta_vs_incumbent=ci["mean"],delta_lower90=ci["lower"],delta_upper90=ci["upper"],
                   delta_lower_family=family["lower"],delta_upper_family=family["upper"],attempts=attempts[name])
        row["rank"]=None;row["production_eligible"]=False
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["candidate","model"],ascending=[False,True])


def render(cp,frame,cfg):
    c=cp["c"];v=cp["v"];q=v["current_query"]
    status="passed" if v["adaptive_pass"] else "DISABLED: adaptive evidence gates did not pass"
    direction=v["statistical_gates"].get("direction_not_degraded",False)
    lines=["# Leaderboard 2: checkpoint continuation diagnostics","",
           "**Production ranking: DISABLED.** These models continue their own historical holdings; shared-incumbent switching is unvalidated.",
           "",f"Adaptive weighting: **{status}**. Active alpha: {v['active_alpha']}. Mode: {v['weight_mode']}.",
           "",f"Frozen market checkpoint: {c['asof']} ({pd.Timestamp(c['asof']).tz_convert('Asia/Shanghai')}). "
              f"Observed prefix: {c['prefix_hours']}h; remaining: {c['horizon_hours']-c['prefix_hours']}h.",
           "",f"Checkpoint ID: {cp['protocol']}; source tool: {c['tool_version']}. {len(frame)} latest model rows; "
              f"{len(cp['table'])} historical windows. New rows update this board; the market checkpoint does not advance automatically.",
           "","## How to read","",
           "- Start with the evidence gates below. Passed code tests do not establish predictive skill.",
           "- Score2 mean/median are remaining-period historical returns after terminal liquidation cost. "
              "A +2% mean is not a prediction of +2% over the coming ten days.",
           "- p10 is the 10th percentile (bad-tail threshold); worst is the worst observed remaining-period result.",
           f"- Delta compares with the FIXED incumbent {c['incumbent']} / {cp['incumbent_score']['model']['run_key']}, "
              "including when that model name is later rescored with different code.",
           "- Lower delta bounds reflect paired calendar-month bootstrap uncertainty. Family lower accounts nominally for multiple candidates; "
              "finite bootstrap tails and cross-month dependence remain limits.",
           "- Original eligible means the original scoring hard gates passed; it does not mean eligible for deployment.",
           "- Rows are alphabetical within candidate/reference groups. Blank rank means no validated production ranking.",
           "- LOOK statistics use the saved legacy descriptive cases and never override failed gates. "
              "Paper prefixes are replays, not verified live-account equity.",
           "","## Evidence gates","",
           "| Check | Result |","|---|---|",
           f"| Direction nondegradation | {'PASS' if direction else 'FAIL: uncertainty still permits degradation'} |",
           f"| Exact current breadth endpoints | {int(q['breadth_valid_n'])}/{int(q['universe_n'])}; "
              f"{'PASS' if v['current_query_coverage'] else 'FAIL; unchanged coverage guard'} |",
           f"| Archive confirmation | {'PASS' if v['current_data_confirmed'] else 'FAIL'}; complete through "
              f"{cp['input']['archive_complete_through']} |",
           "| Common-account switch execution | UNVALIDATED |",
           "| Separate short timing score | NOT_VALIDATED; executable event ledger unavailable |","",
           (cp["input"].get("coverage_failure_preserved","")
            if not v["current_query_coverage"] else "Current declared feature coverage passed."),
           "No imputation, universe rewrite or threshold relaxation forces activation.",
           "","## Candidates and references","",
           "| Rank | Model | Type | Score2 mean | Median | p10 | Worst | Delta vs fixed incumbent | Lower90 delta | Family lower delta | Original eligible | Runs |",
           "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|"]
    for _,r in frame.iterrows():
        lines.append(f"| -- | {r.model} | {'candidate' if r.candidate else 'reference'} | {r.score2_mean:+.2%} | "
                     f"{r.score2_median:+.2%} | {r.score2_p10:+.2%} | {r.score2_worst:+.2%} | "
                     f"{r.delta_vs_incumbent:+.2%} | {r.delta_lower90:+.2%} | {r.delta_lower_family:+.2%} | "
                     f"{'PASS' if r.original_eligible else 'FAIL: '+r.failed_hard_gates} | {r.attempts} |")
    lines+=["","## Paper prefix resemblance","",
            "| Model | Paper prefix | Legacy prefix median | Legacy p10 | Legacy p90 | Paper percentile | Path band coverage |",
            "|---|---:|---:|---:|---:|---:|---:|"]
    if "paper_prefix_return" in frame:
        for _,r in frame[frame.paper_prefix_return.notna()].iterrows():
            lines.append(f"| {r.model} | {r.paper_prefix_return:+.2%} | {r.look_prefix_median:+.2%} | "
                         f"{r.look_prefix_p10:+.2%} | {r.look_prefix_p90:+.2%} | "
                         f"{r.paper_prefix_percentile:.1%} | {r.paper_path_band_coverage:.1%} |")
    lines+=["","Percentiles are descriptive case frequencies, not p-values or calibrated probabilities. "
            "Pointwise bands are not simultaneous confidence bands.",
            "","## Update commands","",
            "Run from a worktree containing this implementation:",
            "","    .venv/bin/python -B -m backtest.run --model book_NAME --score2",
            "    .venv/bin/python -B -m backtest.run --model book_NAME --score --score2",
            "    .venv/bin/python -B -m backtest.scoring leaderboard2","",
            "--score2 computes a full compatible backtest and updates only this secondary registry/board. "
            "--score --score2 updates both boards using one scoring computation. --score alone retains its original behavior. "
            "A partial run, changed tool/data/window set or corrupted artifact is rejected. "
            "A failed new publication preserves the previously published board.",
            "",f"CSV: {safe_path(cfg['book_score2']['csv'])}",
            f"Registry: {safe_path(cfg['book_score2']['registry'])}",
            f"Frozen research report: {cp['root']}/REPORT.md",
            "Detailed usage: docs/SCORE2.md. No merge or live-bot change is implied by publication."]
    return "\n".join(lines)+"\n"


def _write(entries,cp,cfg):
    frame=_frame(entries,cp)
    atomic_write(safe_path(cfg["book_score2"]["csv"]),frame.to_csv(index=False))
    board=safe_path(cfg["book_score2"]["leaderboard"])
    atomic_write(board,render(cp,frame,cfg))
    return board,frame


def _publish_scores(scores,cfg,cp):
    prepared=[_save_score(s,cfg,cp) for s in scores]
    path=safe_path(cfg["book_score2"]["registry"])
    with locked("scoring-score2"):
        entries=_entries(cfg)
        identity=lambda e:(e["protocol"],e["model"],e["run_key"],e["source_sha256"])
        seen={identity(e) for e in entries};new=[]
        for e in prepared:
            if identity(e) not in seen:new.append(e);seen.add(identity(e))
        all_entries=entries+new
        # Validate all current rows before mutating the registry or public board.
        frame=_frame(all_entries,cp);text=render(cp,frame,cfg)
        path.parent.mkdir(parents=True,exist_ok=True)
        if new:
            with path.open("a") as f:
                for e in new:f.write(json.dumps(clean(e),sort_keys=True,allow_nan=False)+"\n")
                f.flush();os.fsync(f.fileno())
        atomic_write(safe_path(cfg["book_score2"]["csv"]),frame.to_csv(index=False))
        board=safe_path(cfg["book_score2"]["leaderboard"]);atomic_write(board,text)
    return board,frame


def publish(score,cfg,report_path=None):
    if cfg["book_score2"]["schema_version"]==2:
        from backtest.scoring import weak_board
        return weak_board.publish(score,cfg,report_path)
    cp=load_checkpoint(cfg);board,frame=_publish_scores([score],cfg,cp)
    if report_path is not None:
        r=frame.loc[frame.model==score["model"]["name"]].iloc[0]
        text=(f"# Score2: {r.model}\n\nCheckpoint {cp['protocol']}; {cp['c']['asof']}.\n\n"
              f"Mode {r.weight_mode}; production ranking DISABLED.\n\n"
              f"Mean {r.score2_mean:+.2%}; median {r.score2_median:+.2%}; p10 {r.score2_p10:+.2%}; "
              f"worst {r.score2_worst:+.2%}.\n\nDelta vs fixed incumbent {r.delta_vs_incumbent:+.2%}; "
              f"family lower {r.delta_lower_family:+.2%}.\n\nRead the instructions and gates in {board}.\n")
        atomic_write(safe_path(report_path),text)
    return board


def import_registered(cfg):
    if cfg["book_score2"]["schema_version"]==2:
        from backtest.scoring import weak_board
        return weak_board.import_registered(cfg)
    cp=load_checkpoint(cfg)
    entries=json.loads((cp["root"]/"registered_snapshot.json").read_text())
    scores=[]
    for e in entries:
        path=safe_path(e["score_json"])
        if sha(path)!=e["score_sha256"]:raise ValueError("registered source changed: "+e["model"])
        scores.append(json.loads(path.read_text()))
    return _publish_scores(scores,cfg,cp)[0]


def refresh(cfg):
    if cfg["book_score2"]["schema_version"]==2:
        from backtest.scoring import weak_board
        return weak_board.refresh(cfg)
    cp=load_checkpoint(cfg)
    with locked("scoring-score2"):
        return _write(_entries(cfg),cp,cfg)[0]
