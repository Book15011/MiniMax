"""Finite directional short pool; separate from frozen hourly score2."""
from pathlib import Path
import argparse,hashlib,json,time
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np,pandas as pd
from src.api.rules import parse_exchange_info
from src.config import load_config
from backtest.scoring.metrics import window_metrics,day_points
from research.book.intraday_short.engine import replay
from research.book.intraday_short.slow import slow_features as features
FAMILIES=("slow_breakdown",)
ROOT=Path("/home/ubuntu/test/MiniMax");OUT=ROOT/"results/book/20261010-intraday-short-v4"
DATA={};CFG={};SC={};RULES={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def score_risk(path,t0):
 hours=(len(path)-1)//60;hourly=path[::60].copy()
 result=window_metrics(hourly,0,SC,day_points(t0,hours,16),{"UTC":day_points(t0,hours,0)}).iloc[0]
 mdd=float((1-path/np.maximum.accumulate(path)).max())
 floor=SC["conventions"]["FLOORED"]["mdd"];a=float(SC["variants"]["V1"]["annualize"]);out={}
 for prefix,name in [("","CS"),("UTC.","CS_UTC")]:
  calmar=float(result[prefix+"m_daily"])*a/max(mdd,floor)
  out[name]=SC["composite"]["sortino"]*float(result[prefix+"FLOORED.V1.sortino"])+SC["composite"]["sharpe"]*float(result[prefix+"FLOORED.V1.sharpe"])+SC["composite"]["calmar"]*calmar
 return out
def case_job(item):
 key,start,is_prefix=item;t0=pd.Timestamp(start);end=t0+pd.Timedelta(hours=108 if is_prefix else 240)
 raw={s:z.loc[t0-pd.Timedelta(hours=48):end].copy() for s,z in DATA.items()}
 f=features(raw,CFG);idx=f["close"].loc[t0:end].index
 endpoints=[108*60] if is_prefix else [216*60,228*60,240*60]
 dest=OUT/"cases"/key;dest.mkdir(parents=True,exist_ok=True);rows=[];audits=[]
 for family in FAMILIES:
  for scenario in ("original","doubled","lag3"):
   c=CFG.copy()
   if scenario=="doubled":c["fee"]*=2;c["halfspread"]*=2
   if scenario=="lag3":c["lag_minutes"]=3
   r=replay(f["close"].loc[idx],f["signals"][family].loc[idx],f["sigma"].loc[idx],f["weak"].loc[idx],c,RULES,endpoints,f["strength"].loc[idx])
   stem=family+"-"+scenario
   r["events"].to_csv(dest/(stem+".events.csv"),index=False);r["cycles"].to_csv(dest/(stem+".cycles.csv"),index=False)
   np.savez_compressed(dest/(stem+".paths.npz"),equity=r["equity"],gross=r["gross"])
   for row in r["windows"].to_dict("records"):
    k=int(row["end_minute"]);path=r["equity"][:k+1].copy()
    if k<len(r["equity"])-1:path[-1]=CFG["seed"]*(1+row["return"])
    row.update(score_risk(path,t0));row.update(case=key,start=str(t0),model="book_m15_"+family,family=family,scenario=scenario,hours=k//60,prefix=is_prefix)
    rows.append(row)
   audits.append({"case":key,"family":family,"scenario":scenario,**r["audit"]})
 (dest/"status.json").write_text(json.dumps({"status":"PASS","audits":audits},indent=2))
 return rows,audits
def main():
 global DATA,CFG,SC,RULES
 p=argparse.ArgumentParser();p.add_argument("--score",action="store_true",required=True);p.parse_args()
 if (OUT/"evaluation_manifest.json").exists():raise ValueError("Preserve existing evaluation")
 deadline=time.monotonic()+7200
 while not (OUT/"data_manifest.json").exists():
  if time.monotonic()>deadline:raise ValueError("Minute data not ready after2h")
  time.sleep(20)
 cfg=load_config();CFG={**cfg["book_intraday_short"],**cfg["book_intraday_slow"]};SC=cfg["scoring"];manifest=json.loads((OUT/"data_manifest.json").read_text())
 files=[Path(__file__).resolve(),Path(__file__).with_name("engine.py"),Path(__file__).with_name("SLOW_PROTOCOL.md"),Path(__file__).with_name("slow.py"),Path("config.yaml"),Path("src/execution/planner.py"),Path("src/execution/paper.py"),Path("src/api/rules.py"),Path("backtest/scoring/metrics.py"),OUT/"data_manifest.json",OUT/"cases.parquet"]
 for symbol,record in manifest["datasets"].items():
  path=Path(record["path"])
  if sha(path)!=record["sha256"]:raise ValueError("Dataset changed")
  DATA[symbol]=pd.read_parquet(path);files.append(path)
 rulepath=ROOT/"results/book/20261010-short-next-prefix-v3/exchange_info.json";files.append(rulepath)
 RULES=parse_exchange_info(json.loads(rulepath.read_text()))
 before={str(path.resolve()):sha(path) for path in files};(OUT/"evaluation_before.json").write_text(json.dumps(before,indent=2))
 cases=pd.read_parquet(OUT/"cases.parquet")
 items=[(t.strftime("%Y%m%dT%H%M"),str(t),False) for t in cases.index]+[("prefix","2026-10-04 12:00:00+00:00",True)]
 allrows=[];audits=[];errors=[]
 with ProcessPoolExecutor(max_workers=4) as pool:
  futures={pool.submit(case_job,item):item for item in items}
  for f in as_completed(futures):
   try:
    rows,a=f.result();allrows+=rows;audits+=a
   except Exception as e:errors.append({"case":futures[f],"error":repr(e)})
   pd.DataFrame(allrows).to_csv(OUT/"window_results.partial.csv",index=False)
   (OUT/"evaluation_progress.json").write_text(json.dumps({"completed":len(audits)//3,"total":len(items),"failures":errors},indent=2))
   print("completed",len(audits)//3,"/",len(items),"failures",len(errors),flush=True)
 if errors:raise ValueError("Some cases failed; all failures retained")
 after={str(path.resolve()):sha(path) for path in files};(OUT/"evaluation_after.json").write_text(json.dumps(after,indent=2))
 if after!=before:raise ValueError("Frozen inputs changed")
 pd.DataFrame(allrows).to_csv(OUT/"window_results.csv",index=False)
 (OUT/"evaluation_manifest.json").write_text(json.dumps({"status":"PASS","case_count":len(items),"models":list(FAMILIES),"scenarios":["original","doubled","lag3"],"audit_max_equity_error":max(a["max_equity_error"] for a in audits),"audits":audits,"frozen_hashes":before,"window_results_sha256":sha(OUT/"window_results.csv"),"all_history_spent":True},indent=2))
 print("ALL EVALUATION PASS",flush=True)
if __name__=="__main__":main()
