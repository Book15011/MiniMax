"""Replay fresh packets by observed receipt order, without assumed exchange clocks."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd,yaml
from research.book.gate.latency.core import causal_asof,gaps,simulate
from research.book.gate.latency.run import save_run
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT.parents[1]/"results/book/20261015-latency-gate-v1"
CFG=yaml.safe_load(Path(__file__).with_name("config.yaml").read_text())
def packets(path):return [json.loads(s) for s in path.read_text().splitlines() if s]
def prepare(kind,extra=0):
    coins=CFG["symbols"]
    rr=packets(OUT/("roostoo_capture.jsonl" if kind=="rest" else "roostoo_stream.jsonl"))
    rr=[r for r in rr if r.get("success") and r["data"].get("Success",True)]
    rr.sort(key=lambda r:r["receive_mono_ns"])
    t=np.array([r["receive_mono_ns"]/1e9 for r in rr])
    def val(r,s,key):
        x=r["data"].get("Data",{}).get(s+"/USD",{}).get(key)
        return float(x) if x is not None else np.nan
    bid=np.array([[val(r,s,"MaxBid") for s in coins] for r in rr])
    ask=np.array([[val(r,s,"MinAsk") for s in coins] for r in rr])
    ext=packets(OUT/("binance_capture.jsonl" if kind=="rest" else "binance_stream.jsonl"))
    eb=np.full_like(bid,np.nan);ea=eb.copy()
    for j,s in enumerate(coins):
        data=[]
        for row in ext:
            if kind=="rest":
                if not row.get("success"):continue
                for q in row["data"]:
                    if q.get("symbol")==s+"USDT":data.append((row["receive_mono_ns"]/1e9+extra,float(q["bidPrice"]),float(q["askPrice"])))
            elif row["data"].get("s")==s+"USDT":
                q=row["data"];data.append((row["receive_mono_ns"]/1e9+extra,float(q["b"]),float(q["a"])))
        data=np.array(sorted(data),float).reshape(-1,3)
        aligned=causal_asof(t,data[:,0],data[:,1:],3 if kind=="rest" else 30)
        eb[:,j],ea[:,j]=aligned[:,0],aligned[:,1]
    return t,bid,ask,eb,ea,rr,ext
def main():
    assert json.loads((OUT/"capture_complete.json").read_text())["status"]=="CAPTURE_COMPLETE"
    kinds=["rest"]
    if (OUT/"stream_complete.json").exists() and json.loads((OUT/"stream_complete.json").read_text())["status"]=="CAPTURE_COMPLETE":kinds.append("stream")
    rows=[];triprows=[];audits=[]
    rules=json.loads((OUT/"rules.json").read_text())
    for kind in kinds:
        t,b,a,eb,ea,rr,ext=prepare(kind)
        lg,sg,basis=gaps(t,b,a,eb,ea,CFG["signal"])
        np.savez_compressed(OUT/f"prospective_{kind}_inputs.npz",times=t,bid=b,ask=a,external_bid=eb,external_ask=ea,long_gap=lg,short_gap=sg,basis=basis)
        ages=[]
        for r in rr:
            ages.append((r["receive_mono_ns"]-r["send_mono_ns"])/1e9)
        audits.append({"kind":kind,"quote_frames":len(t),"external_packets":len(ext),"duration_seconds":float(t[-1]-t[0]),
            "rtt_median_seconds":float(np.median(ages)),"rtt_p95_seconds":float(np.quantile(ages,.95)),
            "aligned_external_fraction":float(np.isfinite(eb).mean()),"basis_valid_fraction":float(np.isfinite(basis).mean()),
            "long_gap25_coin_observations":int((lg>=.0025).sum()),"short_gap25_coin_observations":int((sg>=.0025).sum()),
            "external_book_max_age_seconds":3 if kind=="rest" else 30,"event_timestamp_known":False,
            "receive_order_causal":True,"actual_fills_verified":False,"actual_top20_probability":None})
        for sc in CFG["scenarios"]:
            if sc["name"] in ["clock0","clock6"]:continue
            if sc["name"]=="external_slow6":
                tt,bb,aa,eeb,eea,_,_=prepare(kind,4);ll,ss,_=gaps(tt,bb,aa,eeb,eea,CFG["signal"])
            else:ll,ss=lg,sg
            for cand in CFG["candidates"]:
                z=simulate(t,b,a,ll,ss,rules,CFG["symbols"],cand,CFG["signal"],sc["order_delay"],t[0],t[-1],sc["fee_multiplier"])
                tag=cand["name"]+"_"+kind+"_"+sc["name"]
                row,tr=save_run(z,tag,{"scenario":sc["name"],"split":"prospective_"+kind,"hours":(t[-1]-t[0])/3600,
                                      "source_family":"received_"+kind+"_book","order_delay":sc["order_delay"],
                                      "external_extra_delay":4 if sc["name"]=="external_slow6" else 0,"clock_offset":None})
                # save_run's default family describes historical data; override it explicitly.
                row["source_family"]="received_"+kind+"_book"
                trace=OUT/"traces"/(tag+".json");meta=json.loads(trace.read_text());meta["summary"]=row;trace.write_text(json.dumps(meta,separators=(",",":")))
                rows.append(row);triprows.extend(tr)
    pd.DataFrame(rows).to_csv(OUT/"prospective_summary.csv",index=False)
    pd.DataFrame(triprows).to_parquet(OUT/"prospective_trips.parquet",index=False)
    (OUT/"prospective_audit.json").write_text(json.dumps(audits,indent=2))
    (OUT/"prospective_complete.json").write_text(json.dumps({"status":"PASS","runs":len(rows),"sources":kinds,
         "source_sha256":hashlib.sha256(Path(__file__).with_name("core.py").read_bytes()).hexdigest(),
         "actual_execution_verified":False},indent=2))
    print("PROSPECTIVE COMPLETE",len(rows),"runs",flush=True)
if __name__=="__main__":main()
