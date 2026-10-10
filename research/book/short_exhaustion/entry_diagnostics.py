"""Fixed-horizon labels from actual simulated first fills; never strategy inputs."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fixed_markout(entry_price,prices,start,hours,fee,halfspread,end,max_age):
 t=pd.Timestamp(start)+pd.Timedelta(hours=hours)
 if t>pd.Timestamp(end):return np.nan
 i=prices.index.searchsorted(t,side="right")-1
 if i<0 or (t-prices.index[i]).total_seconds()>max_age:return np.nan
 ask=float(prices.iloc[i])*(1+halfspread)
 if not np.isfinite(ask) or ask<=0 or entry_price<=0:raise ValueError("Invalid entry/exit")
 return (entry_price-ask-fee*(entry_price+ask))/entry_price
def publish(out,study):
 root=Path("/home/ubuntu/test/MiniMax");old=root/"results/book/20261010-intraday-short-v2"
 manifest=json.loads((old/"data_manifest.json").read_text());data={}
 for symbol,z in manifest["datasets"].items():
  p=Path(z["path"])
  if sha(p)!=z["sha256"]:raise ValueError("Minute markout prices changed")
  data[symbol.removesuffix("USDT")]=pd.read_parquet(p,columns=["close"]).close
 windows=pd.read_csv(out/"window_results.csv");cases=pd.read_parquet(out/"cases.parquet")
 allowed=set(cases.index[np.logical_or.reduce([cases[p].to_numpy() for p in study["profiles"]])].strftime("%Y%m%dT%H%M"))
 chosen=windows[(windows.scenario=="original")&(windows.hours==study["primary_horizon"])&windows["case"].isin(allowed)]
 marks=[];pins={}
 cost=study["costs"]["original"]
 for w in chosen.itertuples():
  stem=out/"cases"/w.case/(w.model+"-original-"+str(study["primary_horizon"]))
  files=[Path(str(stem)+".cycles.csv"),Path(str(stem)+".events.csv")]
  for p in files:pins[str(p)]=sha(p)
  try:cy=pd.read_csv(files[0])
  except pd.errors.EmptyDataError:continue
  ev=pd.read_csv(files[1]);ev["time_utc"]=pd.to_datetime(ev.time_utc,utc=True)
  end=pd.Timestamp(w.start)+pd.Timedelta(hours=study["primary_horizon"])
  for c in cy.itertuples():
   t=pd.Timestamp(c.start)
   e=ev[(ev.asset==c.asset)&(ev.action=="Open Short")&(ev.time_utc==t)]
   if len(e)!=1:raise ValueError("Cannot identify exactly one executed episode onset")
   entry=float(e.iloc[0].price_usd)
   r=dict(case=w.case,model=w.model,asset=c.asset,time_utc=str(t),entry_price_usd=entry,status=c.status)
   for h in [1,3,6]:r["markout_"+str(h)+"h"]=fixed_markout(entry,data[c.asset],t,h,cost["fee"],cost["halfspread"],end,study["replay"]["minute_max_age"])
   marks.append(r)
 f=pd.DataFrame(marks,columns=["case","model","asset","time_utc","entry_price_usd","status","markout_1h","markout_3h","markout_6h"])
 f.to_csv(out/"executed_entry_markouts.csv",index=False);rows=[]
 for profile in study["profiles"]:
  keys=set(cases.index[cases[profile]].strftime("%Y%m%dT%H%M"))
  for name in study["models"]:
   x=f[(f.model==name)&f["case"].isin(keys)]
   row=dict(profile=profile,model=name,lookalike_windows=len(keys),firing_windows=x["case"].nunique(),onsets=len(x))
   for h in [1,3,6]:
    v=x["markout_"+str(h)+"h"];n=int(v.notna().sum());wins=int((v>0).sum())
    row.update({str(h)+"h_count":n,str(h)+"h_wins":wins,str(h)+"h_accuracy":wins/n if n else np.nan,str(h)+"h_mean_markout":v.mean(),str(h)+"h_censored":int(v.isna().sum())})
   rows.append(row)
 summary=pd.DataFrame(rows)
 summary["accuracy_rank_6h"]=summary.groupby("profile")["6h_accuracy"].rank(ascending=False,method="min")
 summary.to_csv(out/"entry_accuracy_1h_3h_6h.csv",index=False)
 if any(sha(p)!=v for p,v in pins.items()):raise ValueError("Entry ledger changed during labels")
 (out/"entry_diagnostics_manifest.json").write_text(json.dumps(dict(status="PASS",schema="SIMULATED_EXECUTED_ENTRY_MINUTE_PROXY",source_sha256=sha(__file__),ledgers=pins,onsets=len(f),input_result_sha256=sha(out/"window_results.csv")),indent=2))
 text="# Short timing after simulated fills\n\nStart with the win counts, firing-window count and then6haccuracy rank. This descriptive rank does not override the main return/risk/evidence table. Each profile includes all25fixed lookalikes, with cash windows visible through the firing denominator. All data is spent retrospective research.\n\n"
 text+="One onset is the first actual shared-broker simulated OpenShort fill in an episode. Additions/partial covers are not new onsets. From that actual filled bid, hypothetically hold the first quantity unchanged for1/3/6h, cover at the publisher-minute as-of ask proxy and charge both0.10%fees plus spread. This timing label ignores the strategy's intervening real exits and additions. It is a fixed-horizon entry diagnostic, not actual completed-trade PnL, live-fill accuracy or a forecast. A horizon extending beyond the window or missing a fresh price is censored, never counted as a failure or win.\n\n"
 text+="|Profile|Model|Firing windows|1h wins/n|3h wins/n|6h wins/n|6h accuracy|6h mean markout|6h accuracy rank|\n|---|---|---|---|---|---|---|---|---|\n"
 for r in rows:
  a=r["6h_accuracy"];m=r["6h_mean_markout"]
  rank=summary.loc[(summary.profile==r["profile"])&(summary.model==r["model"]),"accuracy_rank_6h"].iloc[0]
  fmt=lambda z:"unknown" if pd.isna(z) else f"{z:.2%}"
  text+=f'|{r["profile"]}|{r["model"]}|{r["firing_windows"]}/{r["lookalike_windows"]}|{r["1h_wins"]}/{r["1h_count"]}|{r["3h_wins"]}/{r["3h_count"]}|{r["6h_wins"]}/{r["6h_count"]}|{fmt(a)}|{fmt(m)}|{int(rank) if pd.notna(rank) else "-"}|\n'
 text+="\nThe main short_leaderboard_2.csv separately labels hourly TARGET onsets; these rows start from simulated EXECUTED entries after delay/band/rounding. Completed episode accuracy and portfolio return are in leaderboard_short.md. Correlated entries, overlapping profiles and short holding horizons do not become independent market experiments. All raw labels and censoring counts are retained in the CSV files.\n"
 (out/"entry_accuracy.md").write_text(text)
 Path("research/book/short_exhaustion/ENTRY_ACCURACY.md").write_text(text)
