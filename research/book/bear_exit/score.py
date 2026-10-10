"""Audited publication of six price-only portfolios and actual short episode results."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np,pandas as pd
from research.book.bear_exit.run import OUT,NAMES,OLD,STUDY
from research.book.intraday_short.report import clustered_interval,eligible
from research.book.bear_exit.audit import terminal_audit
from research.book.bear_exit.entry_diagnostics import publish as publish_entries
def table(headers,rows):
 return "\n".join(["| "+" | ".join(headers)+" |","|"+"|".join("---" for _ in headers)+"|"]+["| "+" | ".join(map(str,row))+" |" for row in rows])
def pct(x):return "unknown" if pd.isna(x) else f"{x:+.3%}"
def rate(x):return "unknown" if pd.isna(x) else f"{x:.3%}"
def main():
 p=argparse.ArgumentParser();p.add_argument("--score",required=True,action="store_true");p.parse_args()
 m=json.loads((OUT/"evaluation_manifest.json").read_text());a=json.loads((OUT/"independent_execution_audit.json").read_text())
 if m["status"]!="PASS" or a["status"]!="PASS":raise ValueError("Incomplete audited evidence")
 if hashlib.sha256((OUT/"window_results.csv").read_bytes()).hexdigest()!=m["window_results_sha256"]:raise ValueError("Result changed")
 status=json.loads((OUT/"status.json").read_text())
 if len(status)!=len(NAMES)+1 or any(z["returncode"] for z in status):raise ValueError("Tests or normal scoring incomplete")
 if json.loads((OUT/"evaluation_before.json").read_text())!=json.loads((OUT/"evaluation_after.json").read_text()):raise ValueError("Frozen inputs changed")
 f=pd.read_csv(OUT/"window_results.csv");cases=pd.read_parquet(OUT/"cases.parquet");summ=[];rows=[]
 terminal_checks=[]
 for z in f.itertuples():
  stem=OUT/"cases"/z.case/(z.model+"-"+z.scenario+"-"+str(z.hours))
  events=pd.read_csv(str(stem)+".events.csv",dtype={"quantity":str})
  endpoint=json.loads(Path(str(stem)+".endpoint.json").read_text())
  proof=terminal_audit(events,STUDY["replay"]["seed"],STUDY["costs"][z.scenario]["fee"],endpoint["full_cost_liquidated_equity"])
  terminal_checks.append(dict(case=z.case,model=z.model,scenario=z.scenario,hours=z.hours,**proof))
 (OUT/"terminal_short_quantity_audit.json").write_text(json.dumps(dict(status="PASS",ledgers=len(terminal_checks),
   maximum_residual_quantity=max(z["maximum_residual_quantity"] for z in terminal_checks),
   maximum_cash_error_usd=max(z["cash_equity_error_usd"] for z in terminal_checks),
   source_sha256=hashlib.sha256(Path("research/book/bear_exit/audit.py").read_bytes()).hexdigest()),indent=2))

 for name in NAMES:
  bounds=[];accbounds=[];gates=[]
  for profile in STUDY["profiles"]:
   starts=set(map(str,cases.index[cases[profile]]))
   for hours in STUDY["horizons"]:
    x=f[(f.model==name)&(f.scenario=="original")&(f.hours==hours)&f.start.isin(starts)]
    if len(x)!=25:raise ValueError("Case coverage changed")
    lo,hi=clustered_interval(x,"return",alpha=.1/(STUDY["hypotheses"]*6))
    al,ah=clustered_interval(x,"accuracy")
    doubled=f[(f.model==name)&(f.scenario=="doubled")&(f.hours==hours)&f.start.isin(starts)]["return"].mean()
    control=f[(f.model==name)&(f.scenario=="original")&(f.hours==STUDY["primary_horizon"])&f.start.isin(set(map(str,cases.index[cases.positive_control]))) ]["return"].mean()
    quarters=pd.to_datetime(x.start,utc=True).dt.tz_localize(None).dt.to_period("Q").nunique()
    n=int(x.completed.sum());wins=int(x.wins.sum());fires=int(((x.completed+x.censored)>0).sum())
    gate=eligible(lo,n,quarters,fires,doubled,x["return"].median(),control);gates.append(gate);bounds.append(lo)
    z=dict(model=name,profile=profile,hours=hours,n=len(x),mean=float(x["return"].mean()),median=float(x["return"].median()),p10=float(x["return"].quantile(.1)),worst=float(x["return"].min()),CS=float(x.CS.mean()),MDD=float(x.maximum_drawdown.mean()),completed=n,wins=wins,accuracy=wins/n if n else np.nan,censored=int(x.censored.sum()),firing=fires,accuracy_lower90=al,accuracy_upper90=ah,lower_family90=lo,doubled_mean=doubled,control_mean=control,mean_gross=float(x.mean_gross_ratio.mean()),net_short_usd=float(x.net_short_usd.mean()),stronger_evidence=gate)
    summ.append(z)
    if hours==STUDY["primary_horizon"]:accbounds.append(al)
  primary=next(z for z in summ if z["model"]==name and z["profile"]=="weak_archived" and z["hours"]==228)
  rows.append({**primary,"selection_lower90":min(bounds),"worst_profile_accuracy_lower90":min(accbounds),"stronger_evidence":all(gates)})
 rank=pd.DataFrame(rows).sort_values(["selection_lower90","model"],ascending=[False,True]);rank["rank"]=range(1,len(rank)+1)
 rank["accuracy_rank"]=rank.worst_profile_accuracy_lower90.rank(ascending=False,method="min")
 rank["return_rank"]=rank["mean"].rank(ascending=False,method="min")
 rank.to_csv(OUT/"leaderboard_short.csv",index=False);pd.DataFrame(summ).to_csv(OUT/"profile_summary.csv",index=False)
 prefix=f[(f.prefix==True)&(f.scenario=="original")]
 prefix.to_csv(OUT/"prefix_comparison.csv",index=False)
 control=STUDY["models"][0];pairs=[]
 for profile in STUDY["profiles"]:
  starts=set(map(str,cases.index[cases[profile]]))
  for hours in STUDY["horizons"]:
   base=f[(f.model==control)&(f.scenario=="original")&(f.hours==hours)&f.start.isin(starts)].set_index("start")
   for name in NAMES:
    x=f[(f.model==name)&(f.scenario=="original")&(f.hours==hours)&f.start.isin(starts)].set_index("start")
    delta=(x["return"]-base["return"]).rename("return").reset_index()
    lo,hi=clustered_interval(delta,"return",alpha=.1/(STUDY["hypotheses"]*6))
    pairs.append(dict(model=name,control=control,profile=profile,hours=hours,mean_delta=delta["return"].mean(),lower90=lo,upper90=hi))
 pd.DataFrame(pairs).to_csv(OUT/"paired_control.csv",index=False)
 scenario_rows=[]
 for profile in STUDY["profiles"]:
  for label,mask in [("future_down",cases.future_return<=-.02),("future_rebound",cases.future_return>=.02)]:
   starts=set(map(str,cases.index[cases[profile]&mask]))
   for name in NAMES:
    x=f[(f.model==name)&(f.scenario=="original")&(f.hours==STUDY["primary_horizon"])&f.start.isin(starts)]
    n=int(x.completed.sum());wins=int(x.wins.sum())
    scenario_rows.append(dict(profile=profile,future_label=label,model=name,windows=len(x),mean_return=x["return"].mean(),p10=x["return"].quantile(.1),worst=x["return"].min(),wins=wins,completed=n,accuracy=wins/n if n else np.nan,MDD=x.maximum_drawdown.mean(),CS=x.CS.mean()))
 scenario_table=pd.DataFrame(scenario_rows);scenario_table.to_csv(OUT/"scenario_summary.csv",index=False)
 publish_entries(OUT,STUDY)
 text="# Cost-filtered short entries and faster exits\n\n"
 text+="This new cohort uses the corrected strict endpoint rule; prior selective v1 failures remain preserved. Entire batches starting at/after the endpoint are pending, not partly executed. The unchanged guard control is reused in normal scoring only after source/parameter/artifact verification.\n\n"
 text+=("No model clears all reliable-improvement checks. These are research ranks; live switching remains unsupported.\n\n" if not rank.stronger_evidence.any() else "Some retrospective gates pass; prospective superiority and a live-account switch remain UNVERIFIED.\n\n")
 text+="Read **Evidence** first, then **Return**, **Short wins/closed**, **Accuracy**, **P10/Worst**, **MDD** and **CS**. Rank1 alone is not a recommendation. The clone's85%trade agreement is a separate objective.\n\n"
 text+="The four rows compare the unchanged bearish guard with three fixed hypotheses under the same25%gross/10%coin caps,1%daily-risk cap,hourly decisions,1h lag and1pp band. Cost_guard requires a new entry's past6hdecline to exceed1.5times estimated roundtripcost. Fast_exit adds EMA3and2hreturn exits. Trail_exit adds a rebound exit from the previous12hclosed-price low. These are past-price conditions, not profit estimates or stops tied to actual entry fills. Held positions inherit the guard's shrink-only rule. Cash remains valid.\n\n"
 text+="The main rows average ALL25archive-weak windows of228hours(9.5days) from cash100k, including inactive cases. Recent-BTC lookalikes and216/240h horizons are additional fixed checks. These start-information-selected windows include later rebounds, not only falling markets. The228hperiod is a frozen benchmark, not today's remaining competition time. All history is spent retrospective research.\n\n"
 text+="A completed short episode runs from flat to short to flat, aggregating partial covers. It is correct only if net profit after fees and spread is positive. Accuracy=wins/completed; open episodes are censored from accuracy but included at full closing cost in return. Tiny sample accuracy cannot establish reliability. The main scoreboard's1/3/6h onset precision is a separate fixed-horizon proxy.\n\n"
 text+="Conservative rank sorts the worst of six profile/horizon quarter-cluster lower bounds on mean return. Bootstrap20000 and simultaneous adjustment use21declared short hypotheses(previous8minute+6price+4selective+these3new); repeated earlier research still limits inference. Accuracy rank uses the worst-profile90%interval lower bound at228h. Return rank sorts mean portfolio return. P10 and Worst describe losses; MDD is minute peak-to-trough loss; CS keeps0.4Sortino+0.3Sharpe+0.3Calmar. Mean gross is realised exposure, which can differ despite identical caps.\n\n"
 text+=table(["Rank","Model","Lower return","Return","Median","P10","Worst","Short wins/closed","Accuracy","Accuracy rank","Censored","MDD","CS","Mean gross","Evidence"],[[r.rank,r.model,pct(r.selection_lower90),pct(r.mean),pct(r.median),pct(r.p10),pct(r.worst),f"{r.wins}/{r.completed}",rate(r.accuracy),int(r.accuracy_rank) if pd.notna(r.accuracy_rank) else "-",r.censored,rate(r.MDD),f"{r.CS:.3f}",rate(r.mean_gross),"PASS" if r.stronger_evidence else "FAIL"] for r in rank.itertuples()])
 text+="\n\nThe unchanged evidence checks require every profile/horizon lower bound>0,at least30completed shorts,12quarters and12firing windows, positive doubled-cost mean, nonnegative median and positive-control mean>=-1%. No thresholds were loosened. paired_control.csv shows within-window return differences from the equal-risk control; absolute profit and normal --score2 incumbent comparisons must also pass.\n\n"
 text+="## When historical prices actually fell or rebounded\n\nThese conditional labels are diagnostic only: future240hBTCreturn<=-2% is down and>=+2% is rebound. Returns here remain the main228hportfolio endpoint. They do not select training windows, enter targets, alter the main rank or prove the next market direction. Neutral cases remain included in the full25windowtable. Small subgroup results are weaker evidence.\n\n"
 scenario_main=scenario_table[scenario_table.profile=="weak_archived"]
 text+=table(["Future case","Model","Windows","Mean return","P10","Worst","Net wins/closed","Accuracy","MDD","CS"],[[z.future_label,z.model,z.windows,pct(z.mean_return),pct(z.p10),pct(z.worst),f"{z.wins}/{z.completed}",rate(z.accuracy),rate(z.MDD),f"{z.CS:.3f}"] for z in scenario_main.itertuples()])
 text+="\n\nBoth profiles are retained in scenario_summary.csv.\n\n"
 text+="## Early competition prefix: already used\n\nOctober4 20:00HKT to October9 08:00HKT,100kseed. These conditional results do not provide held-out evidence.\n\n"
 text+=table(["Model","Full return","MDD","Wins/closed","Censored","Net short USD","Orders"],[[r.model,pct(r.full_cost_liquidated_return),rate(r.maximum_drawdown),f"{r.wins}/{r.completed}",r.censored,f"{r.net_short_usd:.2f}",r.strategy_orders] for r in prefix.itertuples()])
 text+="\n\nEarlier observed reference+5.2196%and prior clone+4.8661%use this common endpoint but different five-coin holdings and execution assumptions. They are conditional references, not equivalent-risk measurements.\n\n"
 text+="Actual executed-entry timing has a separate table: entry_accuracy.md and entry_accuracy_1h_3h_6h.csv. It ranks fixed1/3/6h after-cost marks from simulated first fills, with endpoint censoring. This is distinct from completed-trade accuracy and the main hourly target-onset proxy.\n\n"
 text+="## Files and reruns\n\nleaderboard_short.csv has ranks. profile_summary.csv retains all six contexts and cost stress. window_results.csv contains every ledger outcome; cases.parquet gives checkpoint dates; paired_control.csv compares each model with the equal-risk guard control. cases/ contains full events, cycles and minute equity. independent_execution_audit.json checks accounting; evaluation_before/after.json pins source/data; status.json records tests and normal-score jobs.\n\n"
 text+="From /home/ubuntu/test/MiniMax/.worktrees/book-book-bear-exit run .venv/bin/python -B -m backtest.run --model MODEL --score2 for automatic entry in /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md. Rebuild this frozen report with .venv/bin/python -B -m research.book.bear_exit.score --score. The full batch refuses overwrite; new hypotheses need a new version. Normal --score2 includes the daily activity guard; this supplemental replay omits it. Both use the shared planner/PaperBroker. Historical minute execution prices here use0.05%halfspread proxies and0.10%fees each side; doubled-cost and2h lag runs are retained.\n\n"
 text+="Source data limitations include the fixed modern four-coin cohort and current precision rules, proxy archive spreads, and the absence of the live account's inherited holdings. All adaptive gates remain unchanged, including BCHabsent29/30coverage. No main merge, signed API action or live bot change occurred.\n"
 (OUT/"leaderboard_short.md").write_text(text);Path("research/book/bear_exit/RESULTS.md").write_text(text)
 (OUT/"report_manifest.json").write_text(json.dumps(dict(status="PASS",source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),input_sha256=m["window_results_sha256"],family_hypotheses=STUDY["hypotheses"],all_history_spent=True,audit_helper_sha256=hashlib.sha256(Path("research/book/bear_exit/audit.py").read_bytes()).hexdigest(),entry_helper_sha256=hashlib.sha256(Path("research/book/bear_exit/entry_diagnostics.py").read_bytes()).hexdigest()),indent=2))
 print(rank[["rank","model","mean","accuracy","selection_lower90","stronger_evidence"]].to_string(index=False),flush=True)
if __name__=="__main__":main()
