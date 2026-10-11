"""Reconstruct every reported row from raw caches and independently check executed costs."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
import pandas as pd
from src.config import load_config
from backtest.data import load_market
from backtest.scoring.metrics import window_metrics,day_points

ROOT=Path("/home/ubuntu/test/MiniMax/.worktrees/book-book-recovery-stress")
MAIN=ROOT.parents[1]
OUT=MAIN/"results/book/20261011-recovery-stress-v1"
ORIGINAL=MAIN/"results/book/20261011-rebound-recovery-v1"
NAMES=["book_e20combo_brk_cash","book_recovery_allshort24","book_recovery_rebound"]
SCENARIOS=["base","double_cost","extra_lag","combined"]
HORIZONS=[120,144,168,192,216,228,240,336]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    batch=json.loads((OUT/"batch_status.json").read_text())
    assert batch["status"]=="PASS" and batch["production_eligible"] is False
    before=json.loads((OUT/"inputs_before.json").read_text())
    after=json.loads((OUT/"inputs_after.json").read_text())
    assert before==after
    for path,expected in before["inputs"].items():
        assert sha(Path(path))==expected,path
    for name,manifest in before.items():
        if name in ["inputs","main_head"]: continue
        wt=MAIN/".worktrees"/name
        if name=="book-book-recovery-stress":
            subprocess.run(["git","merge-base","--is-ancestor",manifest["head"],"HEAD"],cwd=wt,check=True)
        else:
            assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=wt,text=True).strip()==manifest["head"]
        for rel,expected in manifest["files"].items():
            assert sha(wt/rel)==expected,str(wt/rel)
    assert subprocess.check_output(["git","rev-parse","main"],cwd=MAIN,text=True).strip()==before["main_head"]
    cfg=load_config();market=load_market(cfg)
    original_audit=json.loads((ORIGINAL/"independent_audit.json").read_text())
    oldhash={i["model"]:i["hashes"] for i in original_audit["identities"]}
    cases=pd.read_parquet(MAIN/"results/book/20261009-weak-eval-v2/cases.parquet")
    checks=[];count=0;max_r=max_dd=max_cs=max_summary=max_fee=max_spread=0.
    target_refs={}
    execution=[]
    for scenario in SCENARIOS:
        table=pd.read_csv(OUT/f"comparison.{scenario}.csv")
        decision=json.loads((OUT/f"decision.{scenario}.json").read_text())
        mult=2 if scenario in ["double_cost","combined"] else 1
        liq=cfg["scoring"]["liquidation_cost"]*mult
        for name in NAMES:
            meta=json.loads((OUT/f"{name}.{scenario}.json").read_text())
            assert meta["windows"]==2298
            assert meta["fees"]=={"taker":.001*mult,"short":.001*mult}
            assert meta["lag"]==(2 if scenario in ["extra_lag","combined"] else 1)
            assert meta["liquidation_cost"]==liq
            cache=Path(meta["cache_dir"]);key=meta["run_key"]
            paths={suffix:cache/f"{key}.{suffix}" for suffix in
                   ["json","arrays.npz","windows.parquet","targets.parquet","trades.parquet"]}
            hashes={suffix:sha(p) for suffix,p in paths.items()}
            if scenario=="base":
                assert all(hashes[s]==h for s,h in oldhash[name].items()),"original cache changed"
            cm=json.loads(paths["json"].read_text())
            assert cm["model"]==name and cm["key"]==key and not cm["long_only"]
            arrays=np.load(paths["arrays.npz"],allow_pickle=False)
            e,g=arrays["equity"],arrays["gross"]
            win=pd.read_parquet(paths["windows.parquet"]);starts=win.index
            assert e.shape==g.shape==(2298,337) and np.isfinite(e).all() and (e>0).all()
            targets=pd.read_parquet(paths["targets.parquet"])
            assert np.isfinite(targets.to_numpy()).all() and targets.abs().sum(axis=1).max()<=1+1e-9
            if scenario=="base": target_refs[name]=targets
            else: pd.testing.assert_frame_equal(targets,target_refs[name],check_exact=True,check_freq=False)
            trade=pd.read_parquet(paths["trades.parquet"])
            errfee=np.abs(trade.fee_usd-trade.notional_usd*.001*mult).max()
            half=market.half_spread.reindex(trade.series).to_numpy()*mult
            assert np.isfinite(half).all()
            errspread=np.abs(trade.spread_usd-trade.notional_usd*half).max()
            max_fee=max(max_fee,float(errfee));max_spread=max(max_spread,float(errspread))
            fee_by=trade.groupby("window_start").fee_usd.sum().reindex(starts,fill_value=0)/cfg["scoring"]["e0"]
            spread_by=trade.groupby("window_start").spread_usd.sum().reindex(starts,fill_value=0)/cfg["scoring"]["e0"]
            np.testing.assert_allclose(fee_by,win.fees_e0,atol=1e-12,rtol=1e-12)
            np.testing.assert_allclose(spread_by,win.spread_e0,atol=1e-12,rtol=1e-12)
            execution.append({"model":name,"scenario":scenario,"mean_fee_e0":float(win.fees_e0.mean()),
                              "mean_spread_e0":float(win.spread_e0.mean()),"mean_turnover":float(win.turnover.mean()),
                              "marked_gross_max":float(g.max()),"target_gross_max":float(targets.abs().sum(axis=1).max())})
            stored=pd.read_parquet(OUT/f"{name}.{scenario}.parquet")
            for h in HORIZONS:
                eq=e[:,:h+1];gross=g[:,h]
                ret=eq[:,-1]/eq[:,0]*(1-liq*gross)-1
                dd=(eq/np.maximum.accumulate(eq,axis=1)-1).min(axis=1)
                cs=window_metrics(eq,gross,{**cfg["scoring"],"liquidation_cost":liq},
                                  points=day_points(starts[0],h,16))["FLOORED.V1.composite"].to_numpy()
                f=stored.loc[stored.hours==h].set_index("start").loc[starts]
                max_r=max(max_r,float(np.max(np.abs(ret-f["return"].to_numpy()))))
                max_dd=max(max_dd,float(np.max(np.abs(dd-f.mdd.to_numpy()))))
                max_cs=max(max_cs,float(np.max(np.abs(cs-f.cs.to_numpy()))))
                rebuilt=pd.DataFrame({"return":ret,"mdd":dd,"cs":cs},index=starts)
                contexts={"all":starts,"recent_2024on":starts[starts>=pd.Timestamp("2024-01-01",tz="UTC")],
                          "weak_archived":cases.index[cases.weak_archived.astype(bool)],
                          "weak_fresh_btc":cases.index[cases.weak_fresh_btc.astype(bool)]}
                for context,ix in contexts.items():
                    a=rebuilt.loc[ix]
                    row=table.loc[(table.model==name)&(table.hours==h)&(table.context==context)].iloc[0]
                    values={"mean":a["return"].mean(),"median":a["return"].median(),"p10":a["return"].quantile(.1),
                            "worst":a["return"].min(),"mean_mdd":-a.mdd.mean(),"worst_mdd":-a.mdd.min(),"cs_mean":a.cs.mean()}
                    assert int(row["n"])==len(a)
                    max_summary=max(max_summary,max(abs(float(row[k])-float(v)) for k,v in values.items()))
                count+=len(starts)
            if scenario=="base":
                old=pd.read_parquet(ORIGINAL/f"{name}.base.parquet")
                kept=stored.loc[stored.hours.isin(old.hours.unique())].reset_index(drop=True)
                pd.testing.assert_frame_equal(kept,old,check_exact=True,check_freq=False)
            if name!=NAMES[0]:
                assert decision[name]["production_eligible"] is False
                assert decision[name]["original_historical_failure_veto"] is True
            assert hashes=={s:sha(p) for s,p in paths.items()},"cache changed during audit"
            checks.append({"model":name,"scenario":scenario,"key":key,"hashes":hashes})
    stability=json.loads((OUT/"calendar_stability.json").read_text())
    for key,record in stability.items():
        name,scenario,context=key.split(".")
        a=pd.read_parquet(OUT/f"{name}.{scenario}.parquet")
        b=pd.read_parquet(OUT/f"{NAMES[0]}.{scenario}.parquet")
        f=a.loc[a.hours==336].merge(b.loc[b.hours==336],on=["start","hours"],suffixes=("_new","_base"))
        if context=="recent_2024on": f=f.loc[f.start>=pd.Timestamp("2024-01-01",tz="UTC")]
        f["delta"]=f.return_new-f.return_base
        year=f.start.dt.year
        crossing=(f.start+pd.Timedelta(hours=336)).dt.year!=year
        purge=f.loc[~crossing]
        assert len(purge)==record["calendar_purged_n"]
        for row in record["calendar_years"]:
            z=purge.loc[purge.start.dt.year==row["year"]]
            assert len(z)==row["n"] and abs(z.delta.mean()-row["mean_delta"])<1e-12
        for row in record["leave_one_year_out"]:
            z=purge.loc[purge.start.dt.year!=row["omitted_year"]]
            assert len(z)==row["n"] and abs(z.delta.mean()-row["mean_delta"])<1e-12
    assert max(max_r,max_dd,max_cs,max_summary)<1e-12 and max(max_fee,max_spread)<1e-8
    result={"status":"PASS","model_horizon_rows":count,"max_return_error":max_r,"max_drawdown_error":max_dd,
            "max_cs_reconstruction_error":max_cs,"max_summary_error":max_summary,
            "max_fee_usd_error":max_fee,"max_spread_usd_error":max_spread,
            "shared_target_decisions_identical_across_all_stresses":True,"original_cache_hashes_preserved":True,
            "source_input_manifest_unchanged":True,"original_failure_veto_preserved":True,
            "actual_account":False,"production_eligible":False,"checks":checks}
    (OUT/"independent_audit.json").write_text(json.dumps(result,indent=2))
    pd.DataFrame(execution).to_csv(OUT/"execution_costs.csv",index=False)
    print(json.dumps({k:v for k,v in result.items() if k!="checks"},indent=2))
if __name__=="__main__":main()
