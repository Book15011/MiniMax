"""Audited publication of six price-only portfolios and actual short episode results."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np,pandas as pd
from research.book.price_trend.run import OUT,NAMES,OLD
from research.book.intraday_short.report import clustered_interval,eligible
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
 if len(status)!=7 or any(z["returncode"] for z in status):raise ValueError("Tests or normal scoring incomplete")
 if json.loads((OUT/"evaluation_before.json").read_text())!=json.loads((OUT/"evaluation_after.json").read_text()):raise ValueError("Frozen inputs changed")
 f=pd.read_csv(OUT/"window_results.csv");cases=pd.read_parquet(OUT/"cases.parquet");summ=[];rows=[]
 for name in NAMES:
  bounds=[];accbounds=[];gates=[]
  for profile in ["weak_archived","weak_fresh_btc"]:
   starts=set(map(str,cases.index[cases[profile]]))
   for hours in [216,228,240]:
    x=f[(f.model==name)&(f.scenario=="original")&(f.hours==hours)&f.start.isin(starts)]
    if len(x)!=25:raise ValueError("Case coverage changed")
    lo,hi=clustered_interval(x,"return",alpha=.1/(14*6))
    al,ah=clustered_interval(x,"accuracy")
    doubled=f[(f.model==name)&(f.scenario=="doubled")&(f.hours==hours)&f.start.isin(starts)]["return"].mean()
    control=f[(f.model==name)&(f.scenario=="original")&(f.hours==228)&f.start.isin(set(map(str,cases.index[cases.positive_control]))) ]["return"].mean()
    quarters=pd.to_datetime(x.start,utc=True).dt.tz_localize(None).dt.to_period("Q").nunique()
    n=int(x.completed.sum());wins=int(x.wins.sum());fires=int(((x.completed+x.censored)>0).sum())
    gate=eligible(lo,n,quarters,fires,doubled,x["return"].median(),control);gates.append(gate);bounds.append(lo)
    z=dict(model=name,profile=profile,hours=hours,n=len(x),mean=float(x["return"].mean()),median=float(x["return"].median()),p10=float(x["return"].quantile(.1)),worst=float(x["return"].min()),CS=float(x.CS.mean()),MDD=float(x.maximum_drawdown.mean()),completed=n,wins=wins,accuracy=wins/n if n else np.nan,censored=int(x.censored.sum()),firing=fires,accuracy_lower90=al,accuracy_upper90=ah,lower_family90=lo,doubled_mean=doubled,control_mean=control,mean_gross=float(x.mean_gross_ratio.mean()),net_short_usd=float(x.net_short_usd.mean()),stronger_evidence=gate)
    summ.append(z)
    if hours==228:accbounds.append(al)
  primary=next(z for z in summ if z["model"]==name and z["profile"]=="weak_archived" and z["hours"]==228)
  rows.append({**primary,"selection_lower90":min(bounds),"worst_profile_accuracy_lower90":min(accbounds),"stronger_evidence":all(gates)})
 rank=pd.DataFrame(rows).sort_values(["selection_lower90","model"],ascending=[False,True]);rank["rank"]=range(1,len(rank)+1)
 rank["accuracy_rank"]=rank.worst_profile_accuracy_lower90.rank(ascending=False,method="min")
 rank["return_rank"]=rank["mean"].rank(ascending=False,method="min")
 rank.to_csv(OUT/"leaderboard_short.csv",index=False);pd.DataFrame(summ).to_csv(OUT/"profile_summary.csv",index=False)
 prefix=f[(f.prefix==True)&(f.scenario=="original")]
 prefix.to_csv(OUT/"prefix_comparison.csv",index=False)
 scenario=[]
 for profile in ["weak_archived","weak_fresh_btc"]:
  for label,mask in [("down",cases.future_return<=-.02),("rebound",cases.future_return>=.02)]:
   starts=set(map(str,cases.index[cases[profile]&mask]))
   for name in NAMES:
    x=f[(f.model==name)&(f.scenario=="original")&(f.hours==228)&f.start.isin(starts)]
    scenario.append(dict(profile=profile,scenario=label,model=name,n=len(x),mean=x["return"].mean(),wins=int(x.wins.sum()),completed=int(x.completed.sum()),censored=int(x.censored.sum()),CS=x.CS.mean(),MDD=x.maximum_drawdown.mean()))
 pd.DataFrame(scenario).to_csv(OUT/"scenario_summary.csv",index=False)
 text="# Price-based long/short and short-only research\n\n"
 text+=("No candidate passed all supplemental stronger-evidence rules. The task of finding a reliable improvement remains incomplete.\n\n" if not rank.stronger_evidence.any() else "Some retrospective stronger-evidence rules passed. Current-account switching and prospective superiority remain UNVERIFIED.\n\n")
 text+="Start with **Evidence**, then compare **Short wins/closed**, **Return mean**, **P10/Worst**, **MDD** and **CS**. A rank is a descriptive ordering; FAIL means the candidate has not earned a reliable-improvement claim. The clone's 85% execution agreement target is a different measure from profitable-short accuracy.\n\n"
 text+="**What period is measured?** The main rows average all 25 previously selected archive-weak lookalike windows,228 hours (9.5 days) each, starting from cash 100k. Include every selected window, even when the model stays inactive. A separate recent-BTC lookalike profile and 216/240 hour endpoints check sensitivity. Those cohorts were selected from information known at their start; they are not filtered to keep only later price falls. The window dates are in cases.parquet.\n\n"
 text+="**What is a correct short?** One episode begins when a coin first becomes short and ends when it becomes completely flat. Additions and partial covers belong to that episode. A win has positive net PnL after opening/closing fees and spread. Accuracy=winning completed episodes/completed episodes. Still-open episodes are censored from accuracy and remain included in portfolio return and net short PnL. Many orders or correlated coins do not create independent market experiments.\n\n"
 text+="**What do return and risk mean?** Return is the whole $100,000 portfolio after all fees, spread and analytical endpoint closing costs. Signed models include both longs and shorts; short-only versions show whether shorting alone helps. Median describes the middle selected window; P10 is the 10th percentile; Worst is the lowest return. MDD measures the biggest peak-to-trough loss in minute equity. CS uses the existing 0.4 Sortino + 0.3 Sharpe + 0.3 Calmar formula and daily convention, with minute MDD in Calmar. Higher CS is better, but it is not a percentage or an accuracy rate. Mean net short $ includes all short openings/covers plus endpoint costs; positive means shorting contributed profit. Mean gross shows how much capital exposure was used.\n\n"
 text+="**How are models ranked?** Conservative rank sorts the worst of six profile/horizon lower bounds on mean return. Quarter-cluster bootstrap 20,000 uses an adjustment across 14 hypotheses: previous 8 minute candidates plus these 6. Accuracy rank separately uses the worst-profile lower bound from the central 90% completed short accuracy interval at 228h. This correction does not undo repeated research on spent data. The unchanged main --score2 remains authoritative for competition ranking and also compares candidates against the incumbent. These 100% gross-cap portfolios differ from old 25% minute sleeves, so raw returns are not equal-risk comparisons.\n\n"
 text+=table(["Rank","Model","Lower return","Return mean","Median","P10","Worst","Short wins/closed","Short accuracy","Accuracy rank","Censored","Mean MDD","CS","Mean gross","Mean net short $","Evidence"],[[r.rank,r.model,pct(r.selection_lower90),pct(r.mean),pct(r.median),pct(r.p10),pct(r.worst),f"{r.wins}/{r.completed}",rate(r.accuracy),int(r.accuracy_rank) if pd.notna(r.accuracy_rank) else "-",r.censored,rate(r.MDD),f"{r.CS:.3f}",rate(r.mean_gross),f"{r.net_short_usd:.2f}","PASS" if r.stronger_evidence else "FAIL"] for r in rank.itertuples()])
 text+="\n\nAll clocks use completed hourly signals, 4h decisions, 1 hour execution lag, fixed 5pp band, shared planner/PaperBroker, 0.10% fee plus 0.05% halfspread each side. The historical minute quotes are publisher proxies. Doubled-cost and 2 hour lag reruns are in window_results.csv. Supplemental replay omits daily activity guard; ordinary --score2 includes it. Therefore these are trading-mechanism diagnostics, not complete live simulations. Fixed modern four-coin membership and current precision rules are historical proxy limitations.\n\n"
 text+="The unchanged stronger-evidence checks require all six lower bounds > 0, 30 completed shorts, 12 quarters, 12 firing windows in every context, positive doubled-cost mean, nonnegative median, and positive-control mean >= -1%. A descriptive first place never overrides a failed check. Full --score2 and live eligibility remain separate.\n\n"
 text+="## Same spent competition prefix\n\nOctober 4 20:00 HKT to October 9 08:00 HKT,100k seed. Current four-coin models use 1h lag and 5bp halfspread. Earlier observed/clone five-coin references use their own actual/fitted clocks and recorded quotes / 1bp proxy. This is a common-period conditional comparison, not identical execution or unseen validation.\n\n"
 text+=table(["Model","Full return","MDD","Short wins/closed","Censored","Net short $","Orders"],[[r.model,pct(r.full_cost_liquidated_return),rate(r.maximum_drawdown),f"{r.wins}/{r.completed}",r.censored,f"{r.net_short_usd:.2f}",r.strategy_orders] for r in prefix.itertuples()])
 text+="\n\nEarlier common-endpoint references: observed+5.2196%, prior clone+4.8661%; full provenance and risks in /home/ubuntu/test/MiniMax/results/book/20261010-intraday-short-v4/common_prefix_baselines.csv. The observed ledger retains its initial capital deficit and unconfirmed fee assumptions beyond T001.\n\n"
 text+="## Future-down scenarios are diagnostics\n\nscenario_summary.csv labels following 240h BTC return<= -2% as down and>= +2% as rebound. They never select main lookalikes or enter targets. profile_summary.csv shows every profile and 216/228/240h outcome and doubled-cost mean. No fresh market forecast is implied.\n\n"
 text+="## Entry timing is a separate accuracy question\n\nThe main scoreboard also saves /home/ubuntu/test/MiniMax/results/scoring/short_leaderboard_2.csv. Its precision_1h/3h/6h measures whether an onset would profit after a fixed holding horizon and assumed costs, using hourly prices. It is an HOURLY_PROXY_DESCRIPTIVE diagnostic, not the actual completed-episode hit rate above. For example, a profitable short still open at the competition-prefix endpoint contributes return here but is censored from completed accuracy. Keep these denominators and periods separate.\n\n"
 text+="## Separate newly inspected quote day\n\nAll six fixed candidates also ran on October 9 08:00 HKT to October 10 08:00 HKT, from cash 100k, with recorded unsigned bid/ask and the same1h lag. Actual-cost returns ranged from-0.9365%to-0.4663%; no candidate was profitable. Earliest/latest same-timestamp quote controls gave identical targets and fills. All36cost/lag/control ledgers passed independent accounting. This one-day check is newly inspected retrospective evidence, not a prospective trial, and is not mixed into the9.5 day lookalike score. Detail: /home/ubuntu/test/MiniMax/results/book/20261010-price-new-block-v2/RESULTS.md. The failed initial duplicate-quote attempt remains in the v1 folder.\n\n"
 text+="## Reproduce and add models\n\nRemote worktree /home/ubuntu/test/MiniMax/.worktrees/book-book-intraday-short. Registered candidates use .venv/bin/python -B -m backtest.run --model MODEL_NAME --score2 and automatically enter /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md from this branch. All-six batch: .venv/bin/python -B -m research.book.price_trend.run --score. Audited short table: .venv/bin/python -B -m research.book.price_trend.score --score. Existing batches refuse overwrite; new hypotheses need a new version/protocol. Publication from older teammates' branches may replace the sharedMarkdown link until reviewed integration. No main merge or live bot change was performed.\n"
 (OUT/"leaderboard_short.md").write_text(text);Path("research/book/price_trend/RESULTS.md").write_text(text)
 # Shared main Markdown is published under the existing scorer lock by --score2.
 # This report only writes its own artifacts; weak_render already links this table.
 (OUT/"report_manifest.json").write_text(json.dumps({"status":"PASS","source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"input_sha256":m["window_results_sha256"],"family_hypotheses":14,"all_history_spent":True},indent=2))
 print(rank[["rank","model","mean","accuracy","selection_lower90","stronger_evidence"]].to_string(index=False),flush=True)
if __name__=="__main__":main()
