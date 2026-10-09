"""Independent zip and signed-cash audits, separate from the strategy engine."""
from pathlib import Path
import hashlib,io,json,zipfile
import numpy as np,pandas as pd
ROOT=Path("/home/ubuntu/test/MiniMax");OUT=ROOT/"results/book/20261010-intraday-short-v2"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit_data():
 m=json.loads((OUT/"data_manifest.json").read_text());receipts=json.loads((OUT/"fetch_receipt.json").read_text())
 if receipts["failures"]:raise ValueError("Unresolved archive failure")
 checks=[];cells=0;early=[]
 for symbol,record in m["datasets"].items():
  parts=[]
  for r in receipts["records"]:
   if r["symbol"]!=symbol:continue
   p=Path(r["path"]);checksum=p.with_suffix(".zip.CHECKSUM").read_text().split()
   if checksum[1]!=p.name or checksum[0]!=sha(p) or sha(p)!=r["sha256"]:raise ValueError("Archive checksum mismatch")
   with zipfile.ZipFile(p) as z:
    names=[n for n in z.namelist() if n.endswith(".csv")]
    if len(names)!=1:raise ValueError("Unexpected zip")
    frame=pd.read_csv(io.BytesIO(z.read(names[0])),header=None)
   opened=pd.to_numeric(frame.iloc[:,0]);closed=pd.to_numeric(frame.iloc[:,6])
   if opened.min()>=10**14:opened=opened//1000;closed=closed//1000
   if not ((closed>=opened)&(closed<opened+60000)).all():raise ValueError("Archive close outside nominal minute")
   if ((closed+1-opened)!=60000).any():
    early.append({"archive":str(p),"rows":int(((closed+1-opened)!=60000).sum()),"policy":"Use nominal open+60s; conservatively later than publisher actual close, never earlier"})
   idx=pd.to_datetime(opened,unit="ms",utc=True)+pd.Timedelta(minutes=1)
   pz=frame.iloc[:,[1,2,3,4,7,10]].astype(float);pz.columns=["open","high","low","close","quote_volume","taker_buy_quote"];pz.index=idx
   parts.append(pz)
  allbars=pd.concat(parts).sort_index()
  if not allbars.index.is_unique:raise ValueError("Archive duplicate")
  selected=pd.read_parquet(record["path"])
  if sha(record["path"])!=record["sha256"]:raise ValueError("Dataset changed")
  independently=allbars.reindex(selected.index)
  if independently.isna().any().any() or not np.array_equal(independently.to_numpy(),selected.to_numpy()):raise ValueError("Selected minute cells mismatch")
  cases=pd.read_parquet(OUT/"cases.parquet")
  for t in list(cases.index)+[pd.Timestamp("2026-10-04 12:00Z")]:
   hours=108 if t.year==2026 and t.month==10 else 240
   idx=pd.date_range(t-pd.Timedelta(hours=48),t+pd.Timedelta(hours=hours),freq="min")
   if not selected.loc[idx].index.equals(idx):raise ValueError("Case coverage")
  cells+=selected.size;checks.append({"symbol":symbol,"rows":len(selected),"fields":6,"status":"PASS"})
 result={"status":"PASS","archive_count":len(receipts["records"]),"independent_cells":cells,"checks":checks,"datasets":m["datasets"],"early_closed_bars":early}
 (OUT/"independent_data_audit.json").write_text(json.dumps(result,indent=2));print(result["status"],cells,flush=True)
def audit_execution():
 manifest=json.loads((OUT/"evaluation_manifest.json").read_text());data=json.loads((OUT/"data_manifest.json").read_text())
 bars={s:pd.read_parquet(r["path"]) for s,r in data["datasets"].items()}
 windows=pd.read_csv(OUT/"window_results.csv");maxerr=0.;checks=0;feeerr=0.
 for p in sorted((OUT/"cases").glob("*/*.events.csv")):
  family,scenario=p.name.removesuffix(".events.csv").rsplit("-",1)
  case=p.parent.name;w=windows[(windows.case==case)&(windows.family==family)&(windows.scenario==scenario)]
  if w.empty:raise ValueError("Missing window row")
  start=pd.Timestamp(w.iloc[0].start);hours=108 if case=="prefix" else 240
  idx=pd.date_range(start,start+pd.Timedelta(hours=hours),freq="min")
  half=.001 if scenario=="doubled" else .0005;fee=.002 if scenario=="doubled" else .001
  cash=np.full(len(idx),100000.);qty={s:np.zeros(len(idx)) for s in bars}
  e=pd.read_csv(p)
  if not e.empty:
   if not (e.minute.diff().dropna()>=0).all():raise ValueError("Event order")
   for row in e.itertuples():
    minute=int(row.minute);sign=-1 if row.kind=="SHORT_OPEN" else 1
    if row.kind not in ("SHORT_OPEN","SHORT_CLOSE"):raise ValueError("Unexpected trade")
    mark=float(bars[row.symbol].loc[idx[minute],"close"])*(1-half if row.kind=="SHORT_OPEN" else 1+half)
    if abs(mark-row.price)>1e-9:raise ValueError("Wrong execution quote")
    feeerr=max(feeerr,abs(row.fee-row.qty*row.price*fee))
    cash[minute:]+=(-sign*row.qty*row.price-row.fee);qty[row.symbol][minute:]+=sign*row.qty
   if any(abs(q[-1])>1e-7 for q in qty.values()):raise ValueError("Final short not closed")
  eq=cash.copy()
  for s,q in qty.items():eq+=q*bars[s].loc[idx,"close"].to_numpy()*(1+half)
  paths=np.load(p.with_name(p.name.replace(".events.csv",".paths.npz")))
  maxerr=max(maxerr,float(np.max(np.abs(eq-paths["equity"]))))
  for row in w.itertuples():
   end=int(row.end_minute);closefee=sum(max(0,-q[end])*float(bars[s].loc[idx[end],"close"])*(1+half)*fee for s,q in qty.items())
   val=eq[end]-closefee
   source=w[w.end_minute==end].iloc[0]
   if abs(val/100000-1-source["return"])>1e-10:raise ValueError("Endpoint liquidation mismatch")
  checks+=1
 if maxerr>1e-6 or feeerr>1e-7:raise ValueError("Independent cash/fee reconciliation")
 result={"status":"PASS","ledgers":checks,"max_equity_error_usd":maxerr,"max_fee_error_usd":feeerr,"minute_prices":"publisher close with declared per-side spread; not recorded historical quotes"}
 (OUT/"independent_execution_audit.json").write_text(json.dumps(result,indent=2));print(result,flush=True)
if __name__=="__main__":
 import argparse
 p=argparse.ArgumentParser();p.add_argument("part",choices=["data","execution"]);args=p.parse_args()
 audit_data() if args.part=="data" else audit_execution()
