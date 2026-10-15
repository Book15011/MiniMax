"""Reproduce all quote scenarios; independently reconstruct cash, costs, returns and drawdowns."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from research.book.gate.simulator_edge.quotes import load,features,run
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT.parents[1]/"results/book/20261015-simulator-edge-v1"
def main():
    b,a,l,rules,p=load();f=features(b,a,l,rules,p)
    frames=[("segment",pd.read_csv(OUT/"quote_summary.csv")),("window",pd.read_csv(OUT/"quote_windows.csv"))]
    folder=OUT/"audited_quote_traces";folder.mkdir(exist_ok=True)
    errors={"metric":0.,"return":0.,"drawdown":0.,"ledger_usd":0.,"fees_usd":0.};ids=[]
    for kind,frame in frames:
        for idx,row in frame.iterrows():
            opts={}
            if kind=="segment":
                opts={"extra_delay":{"lag_mult":2},"double_fees":{"fee_mult":2.},"partial_maker":{"partial":True},"optimistic_last":{"buy_rule":"last"}}.get(row.scenario,{})
                t0,t1=[pd.Timestamp(x,tz="UTC") for x in {"calibration":("2026-10-08","2026-10-13"),"validation":("2026-10-13","2026-10-14"),"recent_check":("2026-10-14","2026-10-15")}[row.split]]
            else:t0=pd.Timestamp(row.start);t1=t0+pd.Timedelta(hours=int(row.hours))
            z=run(row.candidate,b,a,l,f,rules,p,t0,t1,trace=True,**opts)
            trace=z.pop("_trace");e=trace["equity"];trips=z["trips"]
            ret=e[-1]/e[0]-1;dd=-(e/np.maximum.accumulate(e)-1).min()
            errors["return"]=max(errors["return"],abs(ret-z["return"]))
            errors["drawdown"]=max(errors["drawdown"],abs(dd-z["mdd"]))
            errors["ledger_usd"]=max(errors["ledger_usd"],abs(sum(x["net_pnl"] for x in trips)-ret*p["capital"]))
            errors["fees_usd"]=max(errors["fees_usd"],abs(sum(x["entry_fee"]+x["exit_fees"] for x in trips)-z["total_costs"]))
            for col in ["return","mdd","total_costs","crossed_spread_cost","ev_usd","win_rate"]:
                if col in row and pd.notna(row[col]) and z[col] is not None:errors["metric"]=max(errors["metric"],abs(float(row[col])-z[col]))
            assert z["trades"]==int(row.trades) and z["max_calls_minute"]<=20 and not z["terminal_price_missing"]
            name=f"{kind}_{idx:03}";np.savez_compressed(folder/(name+".npz"),**trace)
            (folder/(name+".json")).write_text(json.dumps({"candidate":row.candidate,"trips":trips,"period":[str(t0),str(t1)]},indent=2))
            ids.append({"trace":name,"sha256":hashlib.sha256((folder/(name+".npz")).read_bytes()).hexdigest()})
    assert max(errors["return"],errors["drawdown"])<1e-12 and errors["metric"]<1e-8
    assert max(errors["ledger_usd"],errors["fees_usd"])<1e-7
    table=pd.read_csv(OUT/"hourly_summary.csv");herr=oldmax=0.;hrows=0
    from src.config import load_config
    fee=load_config()["scoring"]["liquidation_cost"]
    for name in table.candidate.unique():
        raw=np.load(OUT/f"{name}.hourly.npz",allow_pickle=False)
        frame=pd.read_parquet(OUT/f"{name}.hourly.parquet")
        E,G=raw["equity"],raw["gross"];starts=pd.to_datetime(raw["starts"],utc=True)
        for h in [68,72]:
            ret=E[:,h]/E[:,0]*(1-fee*G[:,h])-1;dd=-(E[:,:h+1]/np.maximum.accumulate(E[:,:h+1],axis=1)-1).min(1)
            x=frame[frame.hours==h].set_index("start").loc[starts]
            herr=max(herr,float(np.abs(ret-x["return"].to_numpy()).max()),float(np.abs(dd-x.mdd.to_numpy()).max()));hrows+=len(x)
        old=OUT/"hourly_attempt1"/f"{name}.hourly.npz"
        if old.exists():
            prev=np.load(old,allow_pickle=False);oldmax=max(oldmax,float(np.abs(prev["equity"]-E).max()),float(np.abs(prev["gross"]-G).max()))
    assert herr<1e-12 and oldmax==0.
    result={"status":"PASS","quote_scenarios":len(ids),"quote_errors":errors,"hourly_outcome_rows":hrows,
            "max_hourly_return_drawdown_error":herr,"prior_completed_hourly_models_error_after_clock_repair":oldmax,
            "raw_quote_traces":ids,"instrumentation_changed_results":False,"actual_account_or_capacity_verified":False,
            "source_sha256":hashlib.sha256(Path(__file__).with_name("quotes.py").read_bytes()).hexdigest()}
    (OUT/"independent_verification.json").write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!="raw_quote_traces"},indent=2))
if __name__=="__main__":main()
