"""Finite historical evaluation; archive signals, observed Roostoo execution quotes."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import hashlib,json
import numpy as np,pandas as pd,yaml
from research.book.gate.latency.core import causal_asof,gaps,simulate
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT.parents[1]/"results/book/20261015-latency-gate-v1"
CFG=yaml.safe_load(Path(__file__).with_name("config.yaml").read_text())
def ts(s):return pd.Timestamp(s,tz="UTC").timestamp()
def save_run(z,tag,extra):
    times=z.pop("_times");equity=z.pop("_equity");trips=z.pop("trips")
    traces=OUT/"traces";traces.mkdir(exist_ok=True)
    np.savez_compressed(traces/(tag+".npz"),times=times,equity=equity)
    record={**z,**extra,"tag":tag,"latency_penalty":True,"source_family":"archive_tradeclose_roostoo_quotes"}
    (traces/(tag+".json")).write_text(json.dumps({"summary":record,"trips":trips},separators=(",",":")))
    return record,[{**r,"tag":tag,"candidate":z["candidate"],**extra} for r in trips]
def scenario_job(scenario):
    R=np.load(OUT/"roostoo_history.npz",allow_pickle=False);X=np.load(OUT/"external_bars.npz",allow_pickle=False)
    coins=R["coins"].tolist();t=R["times"]+scenario["clock_offset"];bid,ask=R["bid"],R["ask"]
    ext=causal_asof(t,X["times"]+scenario["external_delay"],X["close"],3)
    lg,sg,basis=gaps(t,bid,ask,ext,ext,CFG["signal"])
    rules=json.loads((OUT/"rules.json").read_text());records=[];trades=[]
    intervals=[("calibration",ts("2026-10-08"),ts("2026-10-13")-1e-6),
               ("validation",ts("2026-10-13"),ts("2026-10-14")-1e-6),
               ("spent_recent_check",ts("2026-10-14"),ts("2026-10-15")-1e-6)]
    for cand in CFG["candidates"]:
        for split,start,end in intervals:
            z=simulate(t,bid,ask,lg,sg,rules,coins,cand,CFG["signal"],scenario["order_delay"],start,end,scenario["fee_multiplier"])
            tag=cand["name"]+"_"+scenario["name"]+"_"+split
            r,tr=save_run(z,tag,{"scenario":scenario["name"],"split":split,"hours":(end-start)/3600,
                                  "clock_offset":scenario["clock_offset"],"order_delay":scenario["order_delay"],"external_delay":scenario["external_delay"]})
            records.append(r);trades.extend(tr)
        if scenario["name"]=="base":
            for h in [68,72]:
                for day in [8,9,10,11]:
                    start=ts(f"2026-10-{day:02} 16:00");end=start+h*3600
                    z=simulate(t,bid,ask,lg,sg,rules,coins,cand,CFG["signal"],scenario["order_delay"],start,end,scenario["fee_multiplier"])
                    tag=cand["name"]+f"_window_{h}_{day:02}"
                    r,tr=save_run(z,tag,{"scenario":"base","split":"spent_cash_window","hours":h,"start":start,
                                        "clock_offset":scenario["clock_offset"],"order_delay":scenario["order_delay"],"external_delay":scenario["external_delay"]})
                    records.append(r);trades.extend(tr)
    print("DONE",scenario["name"],len(records),"runs",flush=True)
    return records,trades
def main():
    assert json.loads((OUT/"data_audit.json").read_text())["status"]=="PASS"
    with ProcessPoolExecutor(max_workers=2) as pool:results=list(pool.map(scenario_job,CFG["scenarios"]))
    rows=[r for part in results for r in part[0]];trades=[r for part in results for r in part[1]]
    pd.DataFrame(rows).to_csv(OUT/"historical_summary.csv",index=False)
    pd.DataFrame(trades).to_parquet(OUT/"historical_trips.parquet",index=False)
    (OUT/"historical_complete.json").write_text(json.dumps({"status":"PASS","runs":len(rows),"candidates":4,
         "source_sha256":hashlib.sha256(Path(__file__).with_name("core.py").read_bytes()).hexdigest(),
         "config_sha256":hashlib.sha256(Path(__file__).with_name("config.yaml").read_bytes()).hexdigest(),
         "actual_execution_verified":False},indent=2))
    print("HISTORICAL COMPLETE",len(rows),"runs",len(trades),"simulated trips",flush=True)
if __name__=="__main__":main()
