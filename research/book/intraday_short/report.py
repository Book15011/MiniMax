"""Rank short-only minute research from frozen complete evidence, never tune it."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
ROOT=Path("/home/ubuntu/test/MiniMax");OUT=ROOT/"results/book/20261010-intraday-short-v2"
PROFILES=("weak_archived","weak_fresh_btc")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clustered_interval(f,kind,seed=41621,reps=20000,alpha=.05):
 dates=pd.to_datetime(f.start,utc=True).dt.tz_localize(None).dt.to_period("Q")
 if kind=="accuracy":
  grouped=pd.DataFrame({"group":dates.to_numpy(),"num":f.wins.to_numpy(),"den":f.completed.to_numpy()}).groupby("group")[["num","den"]].sum()
 else:
  grouped=pd.DataFrame({"group":dates.to_numpy(),"num":f["return"].to_numpy(),"den":1.}).groupby("group")[["num","den"]].sum()
 if not len(grouped) or grouped.den.sum()==0:return np.nan,np.nan
 rng=np.random.default_rng(seed);draw=rng.integers(0,len(grouped),size=(reps,len(grouped)))
 den=grouped.den.to_numpy()[draw].sum(axis=1);num=grouped.num.to_numpy()[draw].sum(axis=1)
 values=np.divide(num,den,out=np.full(reps,np.nan),where=den>0);values=values[np.isfinite(values)]
 return tuple(np.quantile(values,[alpha,1-alpha])) if len(values) else (np.nan,np.nan)
def eligible(lower,completed,quarters,firing_clusters,stress,median,control):
 return bool(lower>0 and completed>=30 and quarters>=12 and firing_clusters>=12 and stress>0 and median>=0 and control>=-.01)
def summary_row(f):
 return {"n":len(f),"firing":int((f.onsets>0).sum()),"mean":float(f["return"].mean()),"median":float(f["return"].median()),"p10":float(f["return"].quantile(.1)),"worst":float(f["return"].min()),"tail10":float(f["return"].nsmallest(max(1,int(np.ceil(len(f)*.1)))).mean()),"completed":int(f.completed.sum()),"censored":int(f.censored.sum()),"wins":int(f.wins.sum()),"accuracy":float(f.wins.sum()/f.completed.sum()) if f.completed.sum() else np.nan,"onsets":int(f.onsets.sum()),"MDD":float(f.MDD.mean()),"CS":float(f.CS.mean()),"CS_UTC":float(f.CS_UTC.mean()),"mean_gross":float(f.mean_gross.mean()),"fees":float(f.fees.mean()),"net_short_usd":float(f.net_short_usd.mean()),"orders":float(f.orders.mean())}
def table(headers,rows):
 return "\n".join(["| "+" | ".join(headers)+" |","|"+"|".join("---" for _ in headers)+"|"]+["| "+" | ".join(map(str,row))+" |" for row in rows])
def pct(x):return "unknown" if pd.isna(x) else f"{x:+.3%}"
def main(additional=None):
 for n in ["evaluation_manifest.json","independent_data_audit.json","independent_execution_audit.json"]:
  if json.loads((OUT/n).read_text())["status"]!="PASS":raise ValueError("Evidence failed: "+n)
 status=json.loads((OUT/"status.json").read_text())
 if len(status)!=2 or not all(x["returncode"]==0 for x in status):raise ValueError("Full tests/evaluation incomplete")
 m=json.loads((OUT/"evaluation_manifest.json").read_text())
 if sha(OUT/"window_results.csv")!=m["window_results_sha256"]:raise ValueError("Result changed")
 if json.loads((OUT/"evaluation_before.json").read_text())!=json.loads((OUT/"evaluation_after.json").read_text()):raise ValueError("Frozen inputs changed")
 data=pd.read_csv(OUT/"window_results.csv")
 extra_inputs={}
 roots=[] if additional is None else (list(additional) if isinstance(additional,(list,tuple)) else [additional])
 for extra in roots:
  extra=Path(extra)
  for name in ["evaluation_manifest.json","independent_data_audit.json","independent_execution_audit.json"]:
   if json.loads((extra/name).read_text())["status"]!="PASS":raise ValueError("Earlier evidence failed")
  old=json.loads((extra/"evaluation_manifest.json").read_text())
  digest=sha(extra/"window_results.csv")
  if digest!=old["window_results_sha256"]:raise ValueError("Earlier result changed")
  if sha(extra/"cases.parquet")!=sha(OUT/"cases.parquet"):raise ValueError("Earlier cases differ")
  if json.loads((extra/"evaluation_before.json").read_text())!=json.loads((extra/"evaluation_after.json").read_text()):raise ValueError("Earlier frozen inputs changed")
  extra_inputs[str(extra)]=digest
  data=pd.concat([pd.read_csv(extra/"window_results.csv"),data],ignore_index=True)
 if data.duplicated(["model","start","scenario","hours"]).any():raise ValueError("Duplicate model case")
 cases=pd.read_parquet(OUT/"cases.parquet");models=sorted(data.model.unique());summary=[];bounds=[];ranking=[]
 for name in models:
  primary={};lower=[];passes=[];accuracy_lows=[];stressmeans=[]
  for profile in PROFILES:
   starts=set(map(str,cases.index[cases[profile]]))
   for hours in (216,228,240):
    f=data[(data.model==name)&(data.scenario=="original")&(data.hours==hours)&data.start.isin(starts)]
    if len(f)!=25:raise ValueError("Profile lost a case")
    r=summary_row(f);lo,hi=clustered_interval(f,"return",alpha=.1/(len(models)*6))
    al,ah=clustered_interval(f,"accuracy")
    quarter=pd.to_datetime(f.start,utc=True).dt.tz_localize(None).dt.to_period("Q").nunique()
    stress=data[(data.model==name)&(data.scenario=="doubled")&(data.hours==hours)&data.start.isin(starts)]["return"].mean()
    control=data[(data.model==name)&(data.scenario=="original")&(data.hours==228)&data.start.isin(set(map(str,cases.index[cases.positive_control])))]["return"].mean()
    summary.append({"model":name,"profile":profile,"hours":hours,**r,"lower_family90":lo,"accuracy_lower90":al,"accuracy_upper90":ah,"quarters":quarter,"doubled_mean":stress,"positive_control_mean":control})
    lower.append(lo);passes.append(eligible(lo,r["completed"],quarter,r["firing"],stress,r["median"],control));bounds.append({"model":name,"profile":profile,"hours":hours,"lower_family90":lo,"upper_quantile":hi,"alpha":.1/(len(models)*6)})
    if hours==228:primary[profile]=r;accuracy_lows.append(al);stressmeans.append(stress)
  row={"model":name,"selection_lower_family90":min(lower),"worst_profile_accuracy_lower90":min(accuracy_lows),"worst_profile_mean":min(r["mean"] for r in primary.values()),"doubled_worst_profile_mean":min(stressmeans),"stronger_evidence":all(passes),**primary["weak_archived"]}
  ranking.append(row)
 rank=pd.DataFrame(ranking).sort_values(["selection_lower_family90","model"],ascending=[False,True]);rank["rank"]=range(1,len(rank)+1)
 rank["accuracy_rank"]=rank.worst_profile_accuracy_lower90.rank(method="min",ascending=False)
 rank["return_rank"]=rank.worst_profile_mean.rank(method="min",ascending=False)
 rank.to_csv(OUT/"leaderboard_short.csv",index=False);pd.DataFrame(summary).to_csv(OUT/"profile_summary.csv",index=False);pd.DataFrame(bounds).to_csv(OUT/"return_bounds.csv",index=False)
 rows=[]
 for r in rank.itertuples():
  rows.append([r.rank,r.model,pct(r.selection_lower_family90),int(r.accuracy_rank) if pd.notna(r.accuracy_rank) else "-",int(r.return_rank),f"{r.wins}/{r.completed}",pct(r.accuracy),f"{r.firing}/25",r.censored,pct(r.mean),pct(r.median),pct(r.p10),pct(r.worst),pct(r.MDD),f"{r.CS:.3f}",pct(r.doubled_worst_profile_mean),"YES" if r.stronger_evidence else "NO"])
 text="# Ranked minute short-only research\n\n"
 text+=("No model passed the declared stronger-evidence rules. Rank1 is a research priority, not a validated replacement.\n\n" if not rank.stronger_evidence.any() else "At least one model passed the retrospective evidence rules; prospective performance and current-account switching remain unverified.\n\n")
 text+=f"Read rank as a conservative experiment order. {len(models)} retained hypotheses; five initial mechanisms, two persistent-exit follow-ups and one slower breakdown when present. Follow-ups were chosen after observing initial regime-clear churn; all observations remain spent. Selection bound = worst of six weak-profile/horizon lower mean-return bounds; quarter bootstrap20,000 draws with Bonferroni adjustment across {len(models)} models x 6 contexts. A negative bound does not establish reliable positive return.\n\n"
 text+="Accuracy rank separately sorts worst-profile lower90% completed-cycle accuracy; return rank sorts worst-profile mean228h native-exposure return. These two ranks are descriptive, not independent selection evidence. Main displayed counts/returns/risk use archive-full25windows at228h. Full second-profile/horizon details are in profile_summary.csv.\n\n"
 text+="A signal counts only when a SHORT_OPEN filled. Accuracy = profitable fully closed cycles after both fees/spreads divided by completed cycles. Endpoint-forced closures are censored and excluded from accuracy, but included in return. All25windows, including no-trade windows, count in return. More signals in one window do not create independent market evidence.\n\n"
 text+="Return is the entire short-only cash-start portfolio, with25%maximum intended entry gross and10%percoin, not a100%invested short return or additive live-account contribution. Minute closes trigger exits, followed by one-minute market execution; a rebound gap can exceed the stop. Fees0.10% and halfspread0.05%each side. CS uses unchanged daily FLOORED.V1 HKT moments and weights, with sampled minute MDD in Calmar. CS UTC is in theCSV. This is a separate minute protocol, not hourly --score2 production registration.\n\n"
 text+=table(["Rank","Model","Family90% lower return","Accuracy rank","Return rank","Wins/closed","Cycle accuracy","Firing windows","Censored","Mean return","Median","P10","Worst","Mean MDD","CS","Doubled worst-profile mean","Stronger evidence"],rows)
 text+="\n\nStronger evidence requires all six lower bounds>0;30completed cycles,12quarters and12firing nonoverlap windows in each context; doubled-cost mean>0; median>=0; positive-control mean>=-1%. None of these rules is relaxed. Passing remains retrospective evidence, not a profit forecast or live-switch approval.\n\n"
 prefix=data[(data.prefix==True)&(data.scenario=="original")]
 text+="## Spent recent-prefix diagnostic\n\nOct4 20HKT toOct9 08HKT,100000cash. This ends75minutes before the prior clone/observed full-prefix report, so do not compare its returns to that longer endpoint. A separate common-endpoint comparison is saved when available.\n\n"
 text+=table(["Model","Short-only return","MDD","Wins/closed","Censored","Orders"],[[r["model"],pct(r["return"]),pct(r.MDD),f"{int(r.wins)}/{int(r.completed)}",int(r.censored),int(r.orders)] for _,r in prefix.iterrows()])
 if (OUT/"common_prefix_baselines.csv").exists():
  refs=pd.read_csv(OUT/"common_prefix_baselines.csv")
  text+="\n\n### Same dates: frozen full-portfolio references\n\nThese references use the sameOct4 20HKT-Oct9 08HKT dates and100kcapital, but five/broader assets and accepted recorded quotes/archive1bp proxy; prototypes use four assets and5bp stress. The clone was calibrated on this period and retains19/33literalagreement. Observed ledger keeps its literal deficit and fee assumptions. This table is conditional comparison, not identical-execution or prospective evidence.\n\n"
  text+=table(["Model/reference","Full portfolio return","MDD"],[[r["model"],pct(r["return"]),pct(r.MDD)] for _,r in refs.iterrows()])
 text+="\n\n## Down and rebound scenarios, labeled after the fact\n\nThis answers how shorts behaved when the historical market subsequently fell or rebounded. It does not estimate that such a move will happen now. These future labels never admit the main lookalikes or change the main rank. BTC following240h <=-2% is down, >=+2% is rebound; displayed strategy outcomes are228h. Counts are small and this horizon difference is intentional.\n\n"
 scenario_rows=[]
 for profile in PROFILES:
  for label,mask in [("future_down",cases.future_return<=-.02),("future_rebound",cases.future_return>=.02)]:
   selected=set(map(str,cases.index[cases[profile]&mask]))
   subset=data[(data.scenario=="original")&(data.hours==228)&data.start.isin(selected)]
   values=[]
   for model in models:
    f=subset[subset.model==model]
    if len(f):values.append({"model":model,**summary_row(f)})
   values=sorted(values,key=lambda r:(-r["mean"],r["model"]))
   for place,r in enumerate(values,1):scenario_rows.append({"profile":profile,"scenario":label,"scenario_rank":place,**r})
 pd.DataFrame(scenario_rows).to_csv(OUT/"scenario_summary.csv",index=False)
 text+=table(["Profile","Scenario","Scenario return rank","Model","N","Mean short-only return","Wins/closed","Censored","Mean MDD"],[[r["profile"],r["scenario"],r["scenario_rank"],r["model"],r["n"],pct(r["mean"]),f'{r["wins"]}/{r["completed"]}',r["censored"],pct(r["MDD"])] for r in scenario_rows])
 text+="\n\nThe family adjustment covers the declared minute hypotheses only; it does not undo adaptive choices informed by earlier hourly/clone research or create an untouched holdout. No scenario result upgrades the stronger-evidence flag.\n"
 text+="\n\n## Operational scope\n\nThese are supplemental research short sleeves, not validated complete competition bots. They omit the original activity guard and have not passed live-adapter/activity-day gates. Flow-confirmed variants require a live taker-buy quote feed; Roostoo ticker does not provide it. Minute OHLCV/flow availability on the deployment host is UNVERIFIED; archive backtests do not establish a usable live feed. Volume variants also require valid completed-bar volume. The shared hourly ModelSpec has not been changed.\n"
 text+="\n\n## Reproduce/read evidence\n\nRemote Book worktree: /home/ubuntu/test/MiniMax/.worktrees/book-book-intraday-short. Source/research: research/book/intraday_short/{PROTOCOL.md,FOLLOWUP_PROTOCOL.md,SLOW_PROTOCOL.md,RESEARCH.md,engine.py,run.py,run_persistent.py,run_slow.py,persistent.py,slow.py,audit.py,report.py}. Evaluate this frozen initial batch with .venv/bin/python -B -m research.book.intraday_short.run --score; persistent follow-ups use run_persistent --score; audited publication uses research.book.intraday_short.score --score --phase persistent (existing artifacts intentionally prevent overwrite). New experiments require a new output/version and frozen plan before outcomes. Hourly registered models continue to use --score2 and automatically regenerate the ranked hourly short section.\n\n"
 text+="Data:184checksummedarchives, four fixed coinsBTC/ETH/BNB/XRP; all historical weak/control dates retained. Initial five-coin plan failed a pre-listingSOLJuly2020 control and is preserved under v1; four-coin amendment preceded any minute outcome. Fresh BCH29/30query remains unrepaired. Some publisher zero-volume halt bars close early; nominal minute-end timestamp delays their use conservatively. Original overstrict interval-audit failure is retained. No recorded order-book execution, funding, borrow or API-latency reconstruction is claimed. Three-minute latency stress is in window_results.csv.\n"
 # Improve prose spacing only; model identifiers, numeric tables and paths stay literal.
 prose_replacements={
 "Rank1":"Rank 1","bootstrap20,000":"bootstrap with 20,000",
 "across7models x6contexts":"across 7 models x 6 contexts",
 "across5models x6contexts":"across 5 models x 6 contexts",
 "lower90%":"lower 90%","mean228h":"mean 228h","archive-full25windows at228h":"archive-full 25 windows at 228h",
 "All25windows":"All 25 windows","with25%maximum":"with 25% maximum","and10%percoin":"and 10% per coin",
 "a100%invested":"a 100% invested","Fees0.10%":"Fees 0.10%","halfspread0.05%each":"halfspread 0.05% each",
 "theCSV":"the CSV","bounds>0;30completed cycles,12quarters and12firing":"bounds > 0; 30 completed cycles, 12 quarters and 12 firing",
 "mean>0; median>=0; positive-control mean>=-1%":"mean > 0; median >= 0; positive-control mean >= -1%",
 "Oct4 20HKT toOct9 08HKT,100000cash":"October 4 at 20:00 HKT to October 9 at 08:00 HKT, starting with $100,000 cash",
 "ends75minutes":"ends 75 minutes","sameOct4 20HKT-Oct9 08HKT dates and100kcapital":"same dates and $100,000 starting capital",
 "quotes/archive1bp":"quotes/archive 1bp","and5bp":"and 5bp","retains19/33literalagreement":"retains 19/33 literal agreement",
 "following240h":"following 240h","outcomes are228h":"outcomes are 228h",
 "Data:184checksummedarchives, four fixed coinsBTC/ETH/BNB/XRP":"Data: 184 checksummed archives, four fixed coins: BTC, ETH, BNB and XRP",
 "pre-listingSOLJuly2020":"pre-listing SOL July 2020","Fresh BCH29/30query":"Fresh BCH 29/30 query"
 }
 lines=[]
 for line in text.splitlines():
  if not line.startswith("|"):
   for before,after in prose_replacements.items():line=line.replace(before,after)
  lines.append(line)
 text="\n".join(lines)+"\n"
 (OUT/"leaderboard_short.md").write_text(text);Path("research/book/intraday_short/RESULTS.md").write_text(text)
 (OUT/"report_manifest.json").write_text(json.dumps({"status":"PASS","source_sha256":sha(__file__),"input_sha256":sha(OUT/"window_results.csv"),"earlier_input_sha256":extra_inputs,"board_sha256":sha(OUT/"leaderboard_short.csv"),"ranking_family_models":len(models),"all_history_spent":True},indent=2))
 print(rank[["rank","model","selection_lower_family90","mean","accuracy","stronger_evidence"]].to_string(index=False),flush=True)
if __name__=="__main__":main()
