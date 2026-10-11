"""Read-only review of all compatible frozen runs on the new BTC-only market diagnostic."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
from src.config import load_config
from backtest.scoring.metrics import window_metrics,day_points
ROOT=Path(__file__).resolve().parents[3];MAIN=ROOT.parents[1]
OUT=MAIN/"results/book/20261011-recovery-current-context-v1"
BASE="book_e20combo_brk_cash"
NEW=["book_recovery_vol","book_recovery_short","book_recovery_both","book_recovery_abs","book_recovery_iv","book_recovery_abs_iv"]
def joint_bounds(D,ix,*,reps=50000):
    # Purge each outcome beyond its start quarter before resampling whole quarters.
    end=ix.tz_localize(None).to_period("Q").end_time.tz_localize("UTC")
    usable=(ix+pd.Timedelta(hours=192))<=end
    qs=ix[usable].tz_localize(None).to_period("Q").astype(str)
    unique=sorted(set(qs)); counts=np.array([(qs==q).sum() for q in unique])
    sums=np.stack([D[:,usable,:][:,qs==q,:].sum(axis=1) for q in unique],axis=1)
    rng=np.random.default_rng(20261011)
    mult=rng.multinomial(len(unique),np.ones(len(unique))/len(unique),size=reps)
    den=mult@counts
    observed=D[:,usable,:].mean(axis=1)
    # Joint 95% uniform maximum-deviation bound across every retained model x both horizons.
    # This remains exploratory after project-wide historical selection.
    penalty=[]
    for start in range(0,len(mult),2000):
        m=mult[start:start+2000]
        means=np.einsum("bq,mqh->bmh",m,sums)/den[start:start+2000,None,None]
        err=means-observed[None,:,:]
        penalty.extend(err.max(axis=(1,2)).tolist())
    critical=float(np.quantile(penalty,.95))
    lower=observed-critical
    return lower,critical,usable,unique

def main():
    cfg=load_config();raw=(MAIN/"results/scoring/leaderboard_2.csv").read_bytes()
    (OUT/"old_board_snapshot.csv").write_bytes(raw)
    from io import BytesIO
    board=pd.read_csv(BytesIO(raw))
    known=dict(zip(board.model,board.run_key))
    for n in NEW:
        folder="20261011-recovery-study-v1" if n in NEW[:3] else "20261011-recovery-selection-v1"
        p=MAIN/"results/book"/folder/f"{n}.base.json"
        known[n]=json.loads(p.read_text())["run_key"]
    matches=pd.read_csv(OUT/"btc_only_cases.csv");ix=pd.DatetimeIndex(pd.to_datetime(matches.t0,utc=True))
    fullbase=pd.read_parquet(MAIN/"results/book/20261011-recovery-study-v1"/f"{BASE}.base.parquet")
    basefull=fullbase[fullbase.hours==336].set_index("start")
    rows=[];per=[];excluded=[];identities=[];matrix=[];names=[]
    bh=0.001
    for n,key in sorted(known.items()):
        cd=MAIN/"results/scoring/cache"/n
        p={s:cd/f"{key}.{s}" for s in ["json","arrays.npz","windows.parquet"]}
        if not all(v.exists() for v in p.values()):
            excluded.append({"model":n,"reason":"cache artifact missing","run_key":key});continue
        meta=json.loads(p["json"].read_text())
        if meta.get("tool_version")!="3036a0d8bfdaa6a0" or meta.get("long_only") or meta.get("model")!=n:
            excluded.append({"model":n,"reason":"incompatible immutable run metadata","run_key":key});continue
        windows=pd.read_parquet(p["windows.parquet"])
        sel=windows.index.get_indexer(ix)
        if (sel<0).any():
            excluded.append({"model":n,"reason":"current diagnostic cases not covered","run_key":key});continue
        a=np.load(p["arrays.npz"]);E,G=a["equity"],a["gross"]
        Rs=[]
        for h in [168,192]:
            es,gs=E[sel,:h+1],G[sel,h]
            R=es[:,-1]/es[:,0]*(1-bh*gs)-1
            dd=(es/np.maximum.accumulate(es,axis=1)-1).min(1)
            cs=window_metrics(es,gs,cfg["scoring"],points=day_points(ix[0],h,16))["FLOORED.V1.composite"].to_numpy()
            rows.append({"model":n,"run_key":key,"hours":h,"n":len(ix),"mean":float(R.mean()),"median":float(np.median(R)),
                         "p10":float(np.quantile(R,.1)),"worst":float(R.min()),"mean_mdd":float(-dd.mean()),
                         "worst_mdd":float(-dd.min()),"cs_mean":float(cs.mean()),"production_eligible":False})
            per += [{"model":n,"run_key":key,"start":t,"hours":h,"return":float(x),"mdd":float(y)} for t,x,y in zip(ix,R,dd)]
            Rs.append(R)
        matrix.append(np.stack(Rs,axis=1));names.append(n)
        fullR=E[:,-1]/E[:,0]*(1-bh*G[:,-1])-1
        rows[-2]["full_mean"]=rows[-1]["full_mean"]=float(fullR.mean())
        rows[-2]["full_p10"]=rows[-1]["full_p10"]=float(np.quantile(fullR,.1))
        identities.append({"model":n,"run_key":key,"source_commit":meta.get("git",{}).get("commit"),
                           "sha256":{s:hashlib.sha256(v.read_bytes()).hexdigest() for s,v in p.items()}})
    X=np.stack(matrix,axis=0);b=X[names.index(BASE)]
    D=X-b[None,:,:]
    lower,critical,usable,unique=joint_bounds(D,ix)
    table=pd.DataFrame(rows)
    btable=table[table.model==BASE].set_index("hours")
    decisions=[]
    for i,n in enumerate(names):
        rr=table[table.model==n].set_index("hours")
        gates={"point_mean_both":bool((rr["mean"]>=btable["mean"]-1e-12).all()),
               "p10_both":bool((rr.p10>=btable.p10-1e-12).all()),
               "uniform_lower_both":bool((lower[i]>0).all()),
               "minimum_cases":bool(usable.sum()>=20 and len(unique)>=12)}
        decisions.append({"model":n,"lower_delta_168":float(lower[i,0]),"lower_delta_192":float(lower[i,1]),
                          "current_diag_pass":all(gates.values()),"gates":gates,"production_eligible":False})
    table.to_csv(OUT/"all_compatible_current_comparison.csv",index=False)
    pd.DataFrame(per).to_parquet(OUT/"all_compatible_current_per_case.parquet",index=False)
    dec=pd.DataFrame([{k:v for k,v in d.items() if k!="gates"} for d in decisions])
    dec.to_csv(OUT/"all_compatible_current_decisions.csv",index=False)
    ranking=table.pivot(index="model",columns="hours",values="mean").min(axis=1).sort_values(ascending=False)
    lines=["# Current-state model review — BTC-only exploratory diagnostic","",
      "**No live recommendation. Actual holdings and a prospective edge remain unverified.**","",
      "Frozen query: Oct11 01:00 HKT. Unlike the old Oct9 weak profile, BTC has rebounded over 48h.",
      "This matches BTC trend/returns/volatility only. It omits alt breadth because strict original broad coverage",
      "still fails at BCH (29/30). Adaptive scoring stays OFF. This table cannot establish the best live strategy.","",
      "25 matched, spaced historical cases; 7/8-day cash-start returns, 0.1% fees, spread and one-hour lag.",
      "Rank = lower of the two average returns, a point estimate, not a confidence score.",
      "Bounds resample purged quarters jointly across every included model and both horizons. All history is spent.",
      "Live endgame and real account switching are not simulated. CS follows the model-core daily-HKT convention.","",
      "| Rank | Model | 7-day mean | 8-day mean | 7-day bad10 | 8-day bad10 | Uniform lower delta (7/8d) | Diagnostic pass |",
      "|---|---|---:|---:|---:|---:|---|---|"]
    for j,n in enumerate(ranking.index,1):
        rr=table[table.model==n].set_index("hours");d=dec[dec.model==n].iloc[0]
        fmt=lambda x:f"{100*x:+.2f}%"
        lines.append(f"| {j} | {n} | {fmt(rr.loc[168,'mean'])} | {fmt(rr.loc[192,'mean'])} | {fmt(rr.loc[168,'p10'])} | {fmt(rr.loc[192,'p10'])} | {fmt(d.lower_delta_168)} / {fmt(d.lower_delta_192)} | {'YES (exploratory)' if d.current_diag_pass else 'NO'} |")
    (OUT/"leaderboard_current_diagnostic.md").write_text("\n".join(lines)+"\n")
    manifest={"status":"PASS","models_read":len(names),"frozen_board_rows":len(board),"new_task_models":6,
      "actual_family_models":len(names),"actual_family_contexts":len(names)*2,"selected_cases":len(ix),
      "purged_cases":int(usable.sum()),"quarters":len(unique),"uniform_critical_return":critical,
      "diagnostic_pass":[d["model"] for d in decisions if d["current_diag_pass"] and d["model"]!=BASE],
      "excluded":excluded,"identities":identities,"adaptive_activation":False,"production_eligible":False,
      "actual_holdings_verified":False,"project_wide_post_selection_control":False,
      "board_snapshot_sha256":hashlib.sha256(raw).hexdigest()}
    (OUT/"review_audit.json").write_text(json.dumps(manifest,indent=2,allow_nan=False))
    print("REVIEW COMPLETE",len(names),"models; diagnostic pass",manifest["diagnostic_pass"])
if __name__=="__main__":main()
