"""Independent raw-cache reconstruction and configuration audit."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np,pandas as pd,yaml
from src.config import load_config
from backtest.scoring.metrics import window_metrics,day_points
ROOT=Path(__file__).resolve().parents[3]
MAIN=ROOT.parents[1]
OUT=MAIN/"results/book/20261011-rebound-recovery-v1"
BASE="book_e20combo_brk_cash"
NAMES=[BASE,"book_recovery_allshort24","book_recovery_rebound"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    complete=json.loads((OUT/"complete.json").read_text())
    assert complete["status"]=="PASS"
    before=json.loads((OUT/"inputs_before.json").read_text())
    after=json.loads((OUT/"inputs_after.json").read_text())
    assert before==after
    assert all(sha(Path(p))==value for p,value in before.items())
    cfg=load_config()
    live=MAIN/".worktrees/pol-live-brk"
    assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=live,text=True).strip()=="ef1b0dd23fde620db407f13ecabadc1447c39669"
    livecfg=yaml.safe_load((live/"config.yaml").read_text())
    for key in ["live","harness","scoring","validation"]:
        assert cfg[key]==livecfg[key],key
    assert cfg["models"][BASE]==livecfg["models"][BASE]
    inherited=0
    for rel in subprocess.check_output(["git","ls-files","src","backtest"],cwd=live,text=True).splitlines():
        if rel.endswith(".py"):
            assert (ROOT/rel).read_bytes()==(live/rel).read_bytes(),rel
            inherited+=1
    # Verify the prior future cohort was not edited at all.
    prior=MAIN/".worktrees/book-book-recovery-study"
    assert not subprocess.check_output(["git","status","--porcelain"],cwd=prior,text=True).strip()
    assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=prior,text=True).strip()=="1c96a043d465cd9c144b604cc9b872f4a23b9de6"
    residual=MAIN/".worktrees/book-book-residual-recovery"
    assert not subprocess.check_output(["git","status","--porcelain"],cwd=residual,text=True).strip()
    assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=residual,text=True).strip()=="fab1fbb"+subprocess.check_output(["git","rev-parse","fab1fbb"],cwd=residual,text=True).strip()[7:]
    high=MAIN/".worktrees/book-book-high-recovery"
    assert not subprocess.check_output(["git","status","--porcelain"],cwd=high,text=True).strip()
    assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=high,text=True).strip()==subprocess.check_output(["git","rev-parse","d7a5c8a"],cwd=high,text=True).strip()
    assert json.loads((MAIN/"results/book/20261011-high-recovery-v1/fresh_baseline_audit.json").read_text())["status"]=="PASS"
    table=pd.read_csv(OUT/"comparison.base.csv")
    cases=pd.read_parquet(MAIN/"results/book/20261009-weak-eval-v2/cases.parquet")
    maxr=maxdd=maxcs=maxsummary=0.
    checked=0
    identities=[]
    for name in NAMES:
        meta=json.loads((OUT/f"{name}.base.json").read_text())
        key=meta["run_key"]
        folder=MAIN/"results/scoring/cache"/name
        paths={suffix:folder/f"{key}.{suffix}" for suffix in ["json","arrays.npz","windows.parquet","targets.parquet"]}
        original={k:sha(v) for k,v in paths.items()}
        cm=json.loads(paths["json"].read_text())
        assert cm["model"]==name and cm["key"]==key and not cm["long_only"]
        assert cm["tool_version"]=="3036a0d8bfdaa6a0"
        win=pd.read_parquet(paths["windows.parquet"])
        starts=win.index
        assert len(starts)==2298
        a=np.load(paths["arrays.npz"],allow_pickle=False)
        equity,gross=a["equity"],a["gross"]
        assert equity.shape==gross.shape==(len(starts),337)
        targets=pd.read_parquet(paths["targets.parquet"])
        assert np.isfinite(targets.to_numpy()).all()
        assert targets.abs().sum(axis=1).max()<=1+1e-9
        stored=pd.read_parquet(OUT/f"{name}.base.parquet")
        for hours in [168,192,216,228,240,336]:
            e=equity[:,:hours+1];g=gross[:,hours]
            ret=e[:,-1]/e[:,0]*(1-cfg["scoring"]["liquidation_cost"]*g)-1
            dd=(e/np.maximum.accumulate(e,axis=1)-1).min(axis=1)
            cs=window_metrics(e,g,cfg["scoring"],points=day_points(starts[0],hours,16))["FLOORED.V1.composite"].to_numpy()
            data=stored[stored.hours==hours].set_index("start").loc[starts]
            maxr=max(maxr,float(np.max(np.abs(ret-data["return"].to_numpy()))))
            maxdd=max(maxdd,float(np.max(np.abs(dd-data.mdd.to_numpy()))))
            maxcs=max(maxcs,float(np.max(np.abs(cs-data.cs.to_numpy()))))
            rebuilt=pd.DataFrame({"return":ret,"mdd":dd,"cs":cs},index=starts)
            contexts={"all":starts,"recent_2024on":starts[starts>=pd.Timestamp("2024-01-01",tz="UTC")],
                      "weak_archived":cases.index[cases.weak_archived.astype(bool)],
                      "weak_fresh_btc":cases.index[cases.weak_fresh_btc.astype(bool)]}
            for label,ix in contexts.items():
                f=rebuilt.loc[ix]
                row=table[(table.model==name)&(table.hours==hours)&(table.context==label)].iloc[0]
                values={"mean":f["return"].mean(),"median":f["return"].median(),"p10":f["return"].quantile(.1),
                        "worst":f["return"].min(),"mean_mdd":-f.mdd.mean(),"worst_mdd":-f.mdd.min(),"cs_mean":f.cs.mean()}
                assert row["n"]==len(f)
                maxsummary=max(maxsummary,max(abs(float(row[k])-float(v)) for k,v in values.items()))
            checked+=len(starts)
        assert original=={k:sha(v) for k,v in paths.items()}
        identities.append({"model":name,"run_key":key,"hashes":original})
    assert max(maxr,maxdd,maxcs,maxsummary)<1e-12
    result={"status":"PASS","model_horizon_rows":checked,"max_return_error":maxr,"max_mdd_error":maxdd,
            "max_cs_error":maxcs,"max_summary_error":maxsummary,"inherited_runtime_files_unchanged":inherited,
            "exact_live_harness_scoring_validation_and_parent":True,"prior_forward_worktree_unchanged":True,
            "all_input_hashes_unchanged":True,"identities":identities,
            "production_eligible":False,"actual_holdings_verified":False}
    (OUT/"independent_audit.json").write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!="identities"},indent=2))
if __name__=="__main__":main()
