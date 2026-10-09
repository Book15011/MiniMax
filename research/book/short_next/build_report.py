"""Publish the human research report only after this frozen batch completes."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
ROOT=Path("/home/ubuntu/test/MiniMax");R=ROOT/"results/book";W=Path.cwd()
FINAL=R/"20261010-short-next-final"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p):return json.loads(Path(p).read_text())
required=[
 ("20261010-transition-short/status.json",lambda x:len(x)==2 and all(r["returncode"]==0 for r in x)),
 ("20261010-transition-cost/status.json",lambda x:len(x)==2 and all(r["returncode"]==0 for r in x)),
 ("20261010-short-next-prefix-v3-audit-v2/audit.json",lambda x:x["passed"]),
 ("20261010-transition-prefix-v1-audit/audit.json",lambda x:x["passed"]),
 ("20261010-hourly-archive-audit/audit.json",lambda x:x["status"]=="PASS"),
 ("20261010-clone-prediction-read-guard/proof.json",lambda x:x["status"]=="PASS"),
 ("20261010-clone-prediction-read-guard/test_status.json",lambda x:len(x)==2 and all(r["returncode"]==0 for r in x))]
for rel,condition in required:
 if not condition(js(R/rel)):raise ValueError("Required evidence incomplete: "+rel)
for date in ("20261009-short-next","20261010-transition-short"):
 assert js(R/date/"before_hashes.json")==js(R/date/"after_hashes.json")
if FINAL.exists():raise ValueError("Preserve existing final snapshot")
FINAL.mkdir(parents=True)
sources=[ROOT/"results/scoring"/n for n in ("leaderboard_2.md","leaderboard_2.csv","short_leaderboard_2.csv","registry_2.jsonl")]
before={str(p):sha(p) for p in sources}
for p in sources:(FINAL/p.name).write_bytes(p.read_bytes())
if before!={str(p):sha(p) for p in sources}:raise ValueError("Concurrent board change; snapshot rejected")
board=pd.read_csv(FINAL/"leaderboard_2.csv")
short=pd.read_csv(FINAL/"short_leaderboard_2.csv")
names=["baitoey_ovl_brk_dual","book_cashshort_pullback","book_cashshort_confirm","book_transition_short"]
b=board.set_index("model")
for name in names:assert name in b.index
selected=b.loc[names]
assert (selected.original_eligible==True).all()
primary=["| Model | Rank | Mean weak 228h | Fresh BTC mean | Conservative selection score | CS | Mean MDD | Stronger evidence |","|---|---:|---:|---:|---:|---:|---:|---|"]
for name,row in selected.iterrows():
 primary.append(f"| {name} | {int(row['rank'])} | {row.return_mean:+.3%} | {row.fresh_mean:+.3%} | {row.selection_score:+.3%} | {row.CS:.3f} | {row.mdd_mean:.3%} | {'YES' if row.strengthened_evidence else 'NO'} |")
st=["| Model/profile | Onsets | Windows firing | Correct1h / valid | Correct6h / valid | 6h precision90% range | Window-mean6h unit proxy |","|---|---:|---:|---:|---:|---:|---:|"]
for row in short[short.model.isin(names[1:]+["book_short_breakdown"])].itertuples():
 st.append(f"| {row.model}/{row.profile} | {row.onsets} | {row.windows_with_onsets}/{row.total_windows} | {row.correct_1h}/{row.valid_1h} | {row.correct_6h}/{row.valid_6h} | {row.precision_6h_lower90:.1%} to {row.precision_6h_upper90:.1%} | {row.window_mean_proxy_net_6h:+.3%} |")
pref=pd.concat([pd.read_csv(R/"20261010-short-next-prefix-v3/prefix_comparison.csv"),pd.read_csv(R/"20261010-transition-prefix-v1/prefix_comparison.csv").query("model!='observed_literal_ledger'")],ignore_index=True)
pt=["| Model | Full-cost return | MDD | Orders | Short-opening orders | Completed / censored short cycles | Profitable completed cycles |","|---|---:|---:|---:|---:|---:|---:|"]
for row in pref.itertuples():
 hit="unknown" if pd.isna(row.short_cycle_hit_rate) else f"{row.short_cycle_hit_rate:.1%}"
 pt.append(f"| {row.model} | {row.full_cost_liquidated_return:+.4%} | {row.maximum_drawdown:.4%} | {row.strategy_orders} | {row.short_entry_orders} | {row.short_cycles_completed}/{row.short_cycles_censored} | {hit} |")
chron=pd.concat([pd.read_csv(R/"20261010-short-next-chronological/fold_summary.csv"),pd.read_csv(R/"20261010-transition-chronological/fold_summary.csv").query("model=='book_transition_short'")],ignore_index=True)
ct=["| Model | Mean | Median | P10 | Worst | Mean MDD | Mean CS |","|---|---:|---:|---:|---:|---:|---:|"]
for row in chron[(chron.fold=="ALL")&chron.model.isin(names)].itertuples():
 ct.append(f"| {row.model} | {row.return_mean:+.3%} | {row.return_median:+.3%} | {row.return_p10:+.3%} | {row.return_worst:+.3%} | {row.mdd_mean:.3%} | {row.CS_mean:.3f} |")
cost=pd.concat([pd.read_csv(R/"20261010-short-next-cost/summary.csv"),pd.read_csv(R/"20261010-transition-cost/summary.book_transition_short.csv")],ignore_index=True)
kt=["| Model/scenario | Mean | Median | P10 | Worst | Mean MDD | Mean CS |","|---|---:|---:|---:|---:|---:|---:|"]
for row in cost.itertuples():
 kt.append(f"| {row.model}/{row.scenario} | {row.mean:+.3%} | {row.median:+.3%} | {row.p10:+.3%} | {row.worst:+.3%} | {row.mean_MDD:.3%} | {row.mean_CS:.3f} |")
text=(W/"research/book/short_next/REPORT_TEMPLATE.md").read_text()
newcost=cost[cost.model=="book_transition_short"].set_index("scenario")
oldcost=cost[cost.model=="baitoey_ovl_brk_dual"].set_index("scenario")
gap1=newcost.loc["original","mean"]-oldcost.loc["original","mean"]
gap2=newcost.loc["doubled","mean"]-oldcost.loc["doubled","mean"]
assessment=f"On the same 160 cost-test paths, the transition model's mean return differed from the strongest long model by {gap1*100:+.3f} percentage points at ordinary costs and {gap2*100:+.3f} points at doubled costs. These paired descriptive comparisons are separate from the primary ranking."
text=text.replace("__ASSESSMENT__",assessment)
text=text.replace("__PRIMARY__",chr(10).join(primary)).replace("__SHORT__",chr(10).join(st)).replace("__PREFIX__",chr(10).join(pt)).replace("__CHRON__",chr(10).join(ct)).replace("__COST__",chr(10).join(kt))
(W/"research/book/short_next/RESULTS.md").write_text(text)
(FINAL/"README.md").write_text(text)
manifest={"protocol":"603da2948b68ee0f5c8a","source_worktree":str(W),"model_keys":{n:str(b.loc[n,"run_key"]) for n in names},"publication_rows":len(board),"board_source_hashes":before,
 "required_evidence":{rel:sha(R/rel) for rel,_ in required},
 "snapshot_hashes":{p.name:sha(p) for p in FINAL.iterdir() if p.is_file()},
 "report_source_sha256":sha(__file__),"all_history_spent":True,"cloning_85_met":False,"live_change":False}
(FINAL/"manifest.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps({"report":str(W/"research/book/short_next/RESULTS.md"),"snapshot":str(FINAL),"primary":selected[["rank","return_mean","selection_score","strengthened_evidence"]].to_dict("index")},indent=2),flush=True)
