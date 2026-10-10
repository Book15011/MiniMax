"""Publish the requested sample-aware rank from immutable audited ledgers."""
from pathlib import Path
from decimal import Decimal
import argparse,hashlib,json
import numpy as np,pandas as pd,yaml
from research.book.short_ranking.metrics import confusion,wilson_lower,combined_scores,block_rows,f1_interval
CFG=yaml.safe_load(Path("research/book/short_ranking/config.yaml").read_text())
OUT=Path(CFG["output"]);BASE=Path(CFG["combined"])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def table(headers,rows):
 return "\n".join(["| "+" | ".join(headers)+" |","|"+"|".join("---" for _ in headers)+"|"]+["| "+" | ".join(map(str,row))+" |" for row in rows])
def pct(x):return f"{x:.2%}" if np.isfinite(x) else "unknown"
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--score",required=True,action="store_true");ap.parse_args()
 if (OUT/"manifest.json").exists():raise ValueError("Preserve previous published ranking")
 OUT.mkdir(parents=True,exist_ok=True)
 source={str(p.resolve()):sha(p) for p in Path("research/book/short_ranking").glob("*") if p.is_file()}
 manifest=json.loads((BASE/"manifest.json").read_text())
 if manifest["status"]!="PASS" or manifest["unique_models"]!=CFG["models"] or manifest["family_hypotheses"]!=27:raise ValueError("Wrong parent cohort")
 before={str(BASE/"manifest.json"):sha(BASE/"manifest.json")}
 for n,h in manifest["outputs"].items():
  if sha(BASE/n)!=h:raise ValueError("Combined parent changed")
  before[str(BASE/n)]=h
 for n,h in manifest["inputs"].items():
  if sha(n)!=h:raise ValueError("Combined proof/source changed")
  before[n]=h
 data=Path(CFG["data"]);dm=json.loads((data/"data_manifest.json").read_text())
 before[str(data/"data_manifest.json")]=sha(data/"data_manifest.json")
 prices={}
 for a in CFG["assets"]:
  z=dm["datasets"][a+"USDT"];p=Path(z["path"])
  if sha(p)!=z["sha256"]:raise ValueError("Minute data changed")
  before[str(p)]=z["sha256"];prices[a+"USDT"]=pd.read_parquet(p,columns=["close"]).close
 prices=pd.DataFrame(prices)
 parents={};owner={}
 for name in CFG["parents"]:
  p=Path(name);parents[p]=pd.read_csv(p/"window_results.csv")
  for model in parents[p].model.unique():
   if model in owner:
    if model!=CFG["control"]:raise ValueError("Unexpected repeated model")
   else:owner[model]=p
 if len(owner)!=CFG["models"]:raise ValueError("Model coverage differs")
 cases=pd.read_parquet(Path(CFG["parents"][0])/"cases.parquet")
 selected=cases[cases[CFG["profiles"]].any(axis=1)]
 rows=[];case_rows=[];censored_rows=[];audit_rows=[]
 for ci,start in enumerate(selected.index):
  key=start.strftime("%Y%m%dT%H%M");end=start+pd.Timedelta(hours=CFG["primary_hours"])
  for model,parent in sorted(owner.items()):
   stem=parent/"cases"/key/(model+"-original-"+str(CFG["primary_hours"]))
   pp=Path(str(stem)+".path.parquet");ep=Path(str(stem)+".events.csv")
   before[str(pp)]=sha(pp);before[str(ep)]=sha(ep)
   path=pd.read_parquet(pp);events=pd.read_csv(ep)
   events["time_utc"]=pd.to_datetime(events.time_utc,utc=True)
   block,censored=block_rows(path,prices,start,end,CFG["assets"],CFG)
   # Independently rebuild signed quantities from each audited order, rather than trusting path columns.
   maximum=0.
   for t,z in block.groupby("block_start",sort=False):
    known=events[events.time_utc<=pd.Timestamp(t)]
    quantities={a:Decimal("0") for a in CFG["assets"]}
    for e in known.itertuples():
     if e.action not in ["Open Short","Cover Short"]:raise ValueError("Unexpected long event")
     quantities[e.asset]+=Decimal(str(e.quantity))*(-1 if e.action=="Open Short" else 1)
    for e in z.itertuples():
     mid=float(prices.at[pd.Timestamp(t),e.asset+"USDT"])
     eq=float(path.loc[pd.to_datetime(path.time_utc,utc=True)<=pd.Timestamp(t)].iloc[-1].equity)
     expected=max(0.,-float(quantities[e.asset]))*mid*(1+CFG["halfspread"])/eq
     maximum=max(maximum,abs(expected-e.short_weight))
     if bool(expected>=CFG["minimum_short_weight"])!=e.predicted:raise ValueError("Independent holdings classification mismatch")
     ratio=float(prices.at[pd.Timestamp(e.block_end),e.asset+"USDT"])/mid
     expected_mark=((1-CFG["halfspread"])-ratio*(1+CFG["halfspread"])-CFG["fee"]*((1-CFG["halfspread"])+ratio*(1+CFG["halfspread"])))/(1-CFG["halfspread"])
     if not np.isclose(expected_mark,e.after_cost_mark,atol=1e-12,rtol=0) or bool(expected_mark>0)!=e.positive:raise ValueError("Independent after-cost label mismatch")
   if maximum>1e-10:raise ValueError("Independent exposure mismatch")
   summary=confusion(block.positive,block.predicted)
   if sum(summary[k] for k in ["tp","fp","fn","tn"])!=len(block):raise ValueError("Confusion coverage mismatch")
   if summary["tp"]+summary["fn"]!=int(block.positive.sum()) or summary["tp"]+summary["fp"]!=int(block.predicted.sum()):raise ValueError("Confusion denominator mismatch")
   den=summary["precision"]+summary["recall"]
   alternate=2*summary["precision"]*summary["recall"]/den if den else 0.
   if not np.isclose(alternate,summary["f1"],atol=1e-12,rtol=0):raise ValueError("Independent F1 mismatch")
   rows.append(block.assign(case=key,start=str(start),model=model))
   case_rows.append(dict(case=key,start=str(start),model=model,blocks=len(block),censored=censored,**summary))
   censored_rows.append(dict(case=key,model=model,censored=censored))
   audit_rows.append(dict(case=key,model=model,blocks=len(block),maximum_exposure_error=maximum,status="PASS"))
  print("cases",ci+1,"of",len(selected),flush=True)
 raw=pd.concat(rows,ignore_index=True);cf=pd.DataFrame(case_rows);profiles=[]
 for profile in CFG["profiles"]:
  starts=set(map(str,cases.index[cases[profile]]))
  for model in sorted(owner):
   x=raw[(raw.model==model)&raw.start.isin(starts)];z=cf[(cf.model==model)&cf.start.isin(starts)]
   if len(z)!=25:raise ValueError("Lost preselected windows")
   lower,upper=f1_interval(z,CFG);counts=confusion(x.positive,x.predicted)
   profiles.append(dict(model=model,profile=profile,windows=len(z),blocks=len(x),censored=int(z.censored.sum()),f1_lower90=lower,f1_upper90=upper,**counts))
 pf=pd.DataFrame(profiles)
 base=pd.read_csv(BASE/"leaderboard_short.csv").rename(columns={"rank":"conservative_return_rank"})
 details=pd.read_csv(BASE/"profile_summary.csv");enriched=[]
 for z in base.to_dict("records"):
  p=pf[pf.model==z["model"]];primary=p[p.profile==CFG["profiles"][0]].iloc[0].to_dict()
  d=details[(details.model==z["model"])&(details.hours==CFG["primary_hours"])]
  w=min(wilson_lower(int(a.wins),int(a.completed),CFG["confidence"]) for a in d.itertuples())
  old=float(z["worst_profile_accuracy_lower90"]);reliability=max(0.,min(w,old)) if np.isfinite(old) else 0.
  enriched.append(z|{k:v for k,v in primary.items() if k not in ["profile","f1_lower90"]}|dict(f1_lower90=float(p.f1_lower90.min()),accuracy_reliability=reliability,wilson_lower90=w,minimum_context_closed=int(d.completed.min())))
 rank=combined_scores(pd.DataFrame(enriched),CFG)
 if any(sha(p)!=h for p,h in before.items()) or any(sha(p)!=h for p,h in source.items()):raise ValueError("Frozen evidence changed")
 text="# Short leaderboard: return, F1 and reliable accuracy\n\n"
 text+="**Research rank only: every model still fails the reliable-profit checks.** The clone's 85% trade-agreement target is separate. No trading strategy, historical window, existing return or evidence flag changed.\n\n"
 text+="Score = return points (up to50) + opportunity-F1 points (up to30) + sample-aware completed-accuracy points (up to20). Return points use the existing conservative after-cost return percentile among these13models. F1 points use the worse-profile quarter-cluster90%lower bound. Accuracy points use the smaller of quarter-cluster and Wilson90%lower bounds. A high rank can still lose money. These are exploratory weights, not a calibrated prediction of future profit.\n\n"
 text+="Two wins from four and25from50have the same50%raw accuracy; the second has a higher sample-size lower bound. The quarter check also reflects dependence between trades. Trade count is shown, and more trading is never rewarded by itself.\n\n"
 text+=table(["Rank","Model","Score","Return /50","F1 /30","Accuracy /20","Mean return","Wins/closed","Raw accuracy","Accuracy reliability","MDD","CS","Evidence"],[[a.rank,a.model,f"{a.score:.2f}",f"{a.return_points:.2f}",f"{a.f1_points:.2f}",f"{a.accuracy_points:.2f}",pct(a.mean),f"{a.wins}/{a.completed}",pct(a.accuracy),pct(a.accuracy_reliability),pct(a.MDD),f"{a.CS:.3f}","PASS" if a.stronger_evidence else "FAIL"] for a in rank.itertuples()])
 text+="\n\nMean return, completed trades, MDD andCSabove describe all25archive lookalikes over228hours. Other profile and216/240hour endpoints remain in the immutable combined study. Main return points use the worst of all six conservative bounds with27-hypothesis adjustment, not just the displayed mean. The horizon was fixed earlier and is not today's remaining competition time.\n\n## How opportunity F1 works\n\n"
 text+="For every benchmark coin, evaluate nonoverlapping6-hour blocks after the common one-hour execution delay plus one-minute batch-settlement buffer. A positive opportunity is a fall large enough to profit after both fees and spread. A bot predicts that fall when its actual audited short at block start is at least1%of account equity. Existing held shorts count; dust and cash do not. TP=short+profitablefall;FP=short+nonprofitableblock;FN=no meaningful short+profitablefall. Precision=TP/(TP+FP),recall=TP/(TP+FN),F1=2TP/(2TP+FP+FN). Incomplete endpoints are censored. Zero denominators scorezero.\n\n"
 text+="This measures coverage at fixed decision points. It is distinct from accuracy of new entries and completed-trade profit; it does not inspect every possible intrablock fall or account for position changes inside a block. Future labels are diagnostic only and never feed the bot or select windows.\n\n"
 text+=table(["Rank","Model","TP","FP","Missed falls (FN)","Precision","Recall","F1","Worst-profile F1 lower90","Blocks","Censored"],[[a.rank,a.model,a.tp,a.fp,a.fn,pct(a.precision),pct(a.recall),pct(a.f1),pct(a.f1_lower90),a.blocks,a.censored] for a in rank.itertuples()])
 text+="\n\nCounts and pointF1above are the archive profile. The score uses the smaller lower bound from archive and recent-BTC profiles, resampling start-date quarters20,000times. Repeated and overlapping windows do not become independent experiments.\n\n## Where to look and how to update\n\n"
 text+="leaderboard_short_ranked.csvcontains all components, sample counts, conservative-return rank, raw return/accuracy ranks, F1and unchanged evidence flags. opportunity_profiles.csvhas both contexts; opportunity_cases.csvand opportunity_blocks.csvretain all classifications and censored counts. independent_metric_audit.jsonverifies exposure from actual orders, after-cost labels and F1denominators. manifest.jsonpins all source/evidence files.\n\n"
 text+="The broader13-model return/risk/entry-timing table remains "+str(BASE/"leaderboard_short.md")+". Normal registered-model scoring uses .venv/bin/python -B -m backtest.run --model MODEL --score2in the model's Book worktree and automatically updates /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md. This frozen short rank requires a new equally audited cohort before admitting a new model; it does not silently append scores from different protocols. Publish this version once with .venv/bin/python -B -m research.book.short_ranking.rank --score.\n\n"
 text+="No threshold was relaxed and no live bot or main branch changed. The adaptive gate remains disabled with BCH absent,29/30endpoints. See research/book/short_ranking/PROTOCOL.mdfor every definition and limitation.\n"
 outputs={"leaderboard_short_ranked.csv":rank,"opportunity_profiles.csv":pf,"opportunity_cases.csv":cf,"opportunity_blocks.csv":raw,"censored_blocks.csv":pd.DataFrame(censored_rows)}
 for n,x in outputs.items():x.to_csv(OUT/n,index=False)
 (OUT/"leaderboard_short_ranked.md").write_text(text)
 (OUT/"independent_metric_audit.json").write_text(json.dumps(dict(status="PASS",ledgers=len(audit_rows),classified_blocks=len(raw),audits=audit_rows,maximum_exposure_error=max(a["maximum_exposure_error"] for a in audit_rows)),indent=2))
 (OUT/"manifest.json").write_text(json.dumps(dict(status="PASS",source=source,inputs=before,outputs={n:sha(OUT/n) for n in [*outputs,"leaderboard_short_ranked.md","independent_metric_audit.json"]},models=len(rank),all_history_spent=True,evidence_flags_unchanged=True,production_eligible=False,weights={k:CFG[k] for k in ["return_weight","f1_weight","accuracy_weight"]}),indent=2))
 print(rank[["rank","model","score","mean","completed","accuracy","f1","f1_lower90","stronger_evidence"]].to_string(index=False),flush=True)
if __name__=="__main__":main()
