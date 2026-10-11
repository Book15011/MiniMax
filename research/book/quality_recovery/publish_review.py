"""Append the two frozen trials to the previous immutable 135-model diagnostic."""
from pathlib import Path
import hashlib,json,os,tempfile
from backtest.scoring.registry import locked
import numpy as np,pandas as pd
from research.book.recovery_study.review_current import joint_bounds
ROOT=Path(__file__).resolve().parents[3];MAIN=ROOT.parents[1]
TRIAL=MAIN/"results/book/20261011-quality-recovery-v1"
OLD=MAIN/"results/book/20261011-rebound-current-context-v1"
CASES=MAIN/"results/book/20261011-recovery-current-context-v1/btc_only_cases.csv"
OUT=MAIN/"results/book/20261011-quality-current-context-v1"
BASE="book_e20combo_brk_cash"
NEW=["book_recovery_quality","book_recovery_quality_blend"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix="."+path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"w") as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        Path(tmp).unlink(missing_ok=True)
def main():
    assert json.loads((TRIAL/"independent_audit.json").read_text())["status"]=="PASS"
    assert json.loads((TRIAL/"full_tests.status.json").read_text())["status"]=="PASS"
    OUT.mkdir(exist_ok=True)
    matches=pd.read_csv(CASES)
    starts=pd.DatetimeIndex(pd.to_datetime(matches.t0,utc=True))
    old_summary=pd.read_csv(OLD/"all_compatible_current_comparison.csv")
    old_summary=old_summary.drop(columns=["lower_delta_168","lower_delta_192","current_diag_pass",
                "production_eligible_decision","rank"],errors="ignore")
    per=pd.read_parquet(OLD/"all_compatible_current_per_case.parquet")
    audit=json.loads((OLD/"review_audit.json").read_text())
    for item in audit["identities"]:
        folder=MAIN/"results/scoring/cache"/item["model"]
        for suffix,digest in item["sha256"].items():
            assert sha(folder/f'{item["run_key"]}.{suffix}')==digest
    summaries=[old_summary];outcomes=[per];identities=list(audit["identities"])
    for name in NEW:
        frame=pd.read_parquet(TRIAL/f"{name}.base.parquet")
        meta=json.loads((TRIAL/f"{name}.base.json").read_text())
        key=meta["run_key"]
        rows=[]
        for hours in [168,192]:
            f=frame[frame.hours==hours].set_index("start").loc[starts]
            whole=frame[frame.hours==336]
            rows.append({"model":name,"run_key":key,"hours":hours,"n":len(f),
                         "mean":f["return"].mean(),"median":f["return"].median(),
                         "p10":f["return"].quantile(.1),"worst":f["return"].min(),
                         "mean_mdd":-f.mdd.mean(),"worst_mdd":-f.mdd.min(),"cs_mean":f.cs.mean(),
                         "full_mean":whole["return"].mean(),"full_p10":whole["return"].quantile(.1),
                         "production_eligible":False})
            p=f.rename_axis("start").reset_index()[["start","return","mdd"]].copy()
            p["model"]=name;p["run_key"]=key;p["hours"]=hours
            outcomes.append(p)
        summaries.append(pd.DataFrame(rows))
        folder=MAIN/"results/scoring/cache"/name
        paths={s:folder/f"{key}.{s}" for s in ["json","arrays.npz","windows.parquet"]}
        identities.append({"model":name,"run_key":key,"source_commit":json.loads(paths["json"].read_text()).get("git",{}).get("commit"),
                           "sha256":{s:sha(p) for s,p in paths.items()}})
    table=pd.concat(summaries,ignore_index=True)
    allper=pd.concat(outcomes,ignore_index=True)
    names=sorted(table.model.unique())
    assert sha(CASES)=="1bda71b170fca18780ade194d0401fd3a0cd3dfa2553b17716f3ffa345103707"
    assert len(names)==135 and len(allper)==135*25*2
    X=np.stack([np.stack([allper[(allper.model==n)&(allper.hours==h)].set_index("start").loc[starts,"return"].to_numpy()
                         for h in [168,192]],axis=1) for n in names])
    D=X-X[names.index(BASE)][None,:,:]
    lower,critical,usable,quarters=joint_bounds(D,starts)
    base=table[table.model==BASE].set_index("hours")
    decisions=[]
    for i,name in enumerate(names):
        row=table[table.model==name].set_index("hours")
        passed=bool((row["mean"]>=base["mean"]-1e-12).all() and (row.p10>=base.p10-1e-12).all()
                    and (lower[i]>0).all() and usable.sum()>=20 and len(quarters)>=12)
        decisions.append({"model":name,"lower_delta_168":lower[i,0],"lower_delta_192":lower[i,1],
                          "current_diag_pass":passed,"production_eligible":False})
    dec=pd.DataFrame(decisions)
    ranking=table.pivot(index="model",columns="hours",values="mean").min(axis=1).sort_values(ascending=False)
    lines=["# Recovery model comparison — frozen BTC-only diagnostic","",
      "**No live recommendation. Adaptive scoring remains OFF.**","",
      "Prior guard cost/delay/calendar audit: /home/ubuntu/test/MiniMax/results/book/20261011-recovery-stress-v1/README.md",
      "Its failed reliability checks remain a veto; new rank positions do not override them.","",
      "Query remains Oct11 01:00 HKT; 25 spaced BTC-only historical matches. This refresh adds two fixed research models",
      "without reselecting windows. Newer price-only context is saved separately; it does not change these cases.",
      "Rank = lower of 7/8-day average after-cost cash-start returns. Rank is a point estimate, not proof of an edge.",
      "The uniform 95% lower differences account jointly for 135 models and 2 horizons with 23 purged cases in 14 quarters.",
      "All history is spent. Strict broad coverage still fails at BCH: 29/30. Actual holdings and endgame replay are unverified.",
      "The fourteen new recovery models have model-core results here; full original competition gate eligibility is UNVERIFIED.",
      "CS and drawdown are in the CSV. Short-imitation F1 is distinct from profitable-short accuracy; neither is inferred here.","",
      "| Rank | Model | 7-day mean | 8-day mean | 7-day bad10 | 8-day bad10 | Lower difference (7/8 days) | Diagnostic pass |",
      "|---|---|---:|---:|---:|---:|---|---|"]
    fmt=lambda x:f"{100*x:+.2f}%"
    for rank,name in enumerate(ranking.index,1):
        row=table[table.model==name].set_index("hours");d=dec[dec.model==name].iloc[0]
        lines.append(f"| {rank} | {name} | {fmt(row.loc[168,'mean'])} | {fmt(row.loc[192,'mean'])} | {fmt(row.loc[168,'p10'])} | {fmt(row.loc[192,'p10'])} | {fmt(d.lower_delta_168)} / {fmt(d.lower_delta_192)} | {'YES (exploratory)' if d.current_diag_pass else 'NO'} |")
    lines+=["","Research protocols and reading guide: /home/ubuntu/test/MiniMax/.worktrees/book-book-quality-recovery/research/book/quality_recovery/README.md",
            "Original live bot and existing leaderboard_2 have not been changed."]
    table=table.merge(dec,on="model",suffixes=("","_decision"))
    table["rank"]=table.model.map({name:i for i,name in enumerate(ranking.index,1)})
    text="\n".join(lines)+"\n"
    (OUT/"leaderboard_current_diagnostic.md").write_text(text)
    table.to_csv(OUT/"all_compatible_current_comparison.csv",index=False)
    allper.to_parquet(OUT/"all_compatible_current_per_case.parquet",index=False)
    dec.to_csv(OUT/"all_compatible_current_decisions.csv",index=False)
    manifest={"status":"PASS","models":len(names),"cases":len(starts),"purged_cases":int(usable.sum()),
              "quarters":len(quarters),"contexts":len(names)*2,"uniform_critical_return":critical,
              "diagnostic_pass":dec.loc[(dec.model!=BASE)&dec.current_diag_pass,"model"].tolist(),
              "adaptive_activation":False,"production_eligible":False,"actual_holdings_verified":False,
              "original_135_model_competition_eligibility_validated":False,
              "previous_cases_sha256":sha(CASES),"identities":identities}
    (OUT/"review_audit.json").write_text(json.dumps(manifest,indent=2,allow_nan=False))
    # Independent checks before any public shortcut is replaced.
    prior=table[table.model.isin(old_summary.model.unique())].set_index(["model","hours"]).sort_index()
    previous=old_summary.set_index(["model","hours"]).sort_index()
    numerical=["mean","median","p10","worst","mean_mdd","worst_mdd","cs_mean","full_mean","full_p10"]
    olderr=float(np.max(np.abs(prior[numerical].to_numpy()-previous[numerical].to_numpy())))
    assert olderr<1e-12
    rawerr=0.
    for name in NEW:
        meta=json.loads((TRIAL/f"{name}.base.json").read_text())
        folder=MAIN/"results/scoring/cache"/name;key=meta["run_key"]
        arrays=np.load(folder/f"{key}.arrays.npz",allow_pickle=False)
        windows=pd.read_parquet(folder/f"{key}.windows.parquet")
        selected=windows.index.get_indexer(starts)
        assert (selected>=0).all()
        equity,gross=arrays["equity"][selected],arrays["gross"][selected]
        from src.config import load_config
        liquidation=load_config()["scoring"]["liquidation_cost"]
        for hours in [168,192]:
            expected=equity[:,hours]/equity[:,0]*(1-liquidation*gross[:,hours])-1
            dd=(equity[:,:hours+1]/np.maximum.accumulate(equity[:,:hours+1],axis=1)-1).min(axis=1)
            f=allper[(allper.model==name)&(allper.hours==hours)].set_index("start").loc[starts]
            rawerr=max(rawerr,float(np.max(np.abs(f["return"].to_numpy()-expected))),
                       float(np.max(np.abs(f.mdd.to_numpy()-dd))))
    assert rawerr<1e-12 and table.production_eligible.eq(False).all()
    secondary=MAIN/"results/scoring/leaderboard_2.csv"
    secondary_before=sha(secondary)
    (OUT/"independent_audit.json").write_text(json.dumps({"status":"PASS","prior_models":133,
        "new_models":2,"models":135,"per_case_rows":len(allper),"max_prior_summary_error":olderr,
        "max_new_return_mdd_error":rawerr,"original_score2_sha256":secondary_before,
        "cases_reselected":False,"production_eligible":False},indent=2))
    # Same public recovery shortcuts, separate from the old score2 leaderboard.
    scoring=MAIN/"results/scoring"
    trials=pd.concat([pd.read_csv(MAIN/f"results/book/{folder}/comparison.base.csv") for folder in
        ["20261011-recovery-study-v1","20261011-recovery-selection-v1","20261011-residual-recovery-v1","20261011-high-recovery-v1","20261011-rebound-recovery-v1","20261011-quality-recovery-v1"]],ignore_index=True)
    trials=trials.drop_duplicates(["model","scenario","context","hours"])
    with locked("scoring-recovery"):
        atomic(scoring/"leaderboard_recovery.md",text)
        atomic(scoring/"leaderboard_recovery.csv",table.to_csv(index=False))
        atomic(scoring/"recovery_trials.csv",trials.to_csv(index=False))
    pub={str(scoring/n):sha(scoring/n) for n in ["leaderboard_recovery.md","leaderboard_recovery.csv","recovery_trials.csv"]}
    (OUT/"publication_audit.json").write_text(json.dumps({"status":"PASS","artifacts":pub,"production_eligible":False},indent=2))
    assert sha(secondary)==secondary_before
    print("Published",len(names),"models; diagnostic passes",manifest["diagnostic_pass"])
if __name__=="__main__":main()
