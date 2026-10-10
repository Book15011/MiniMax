"""Publish a readable current view; preserve every original score and evidence artifact."""
from pathlib import Path
import hashlib,json,os
import numpy as np,pandas as pd
ROOT=Path("/home/ubuntu/test/MiniMax")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 source=ROOT/"results/book/20261010-short-ranked-v1";combined=ROOT/"results/book/20261010-short-combined-v3"
 proof=json.loads((source/"manifest.json").read_text())
 if proof["status"]!="PASS" or not proof["evidence_flags_unchanged"]:raise ValueError("Unverified scoring parent")
 for n,h in proof["outputs"].items():
  if sha(source/n)!=h:raise ValueError("Original score changed")
 x=pd.read_csv(source/"leaderboard_short_ranked.csv");raw=x.copy()
 original=pd.read_csv(combined/"leaderboard_short.csv").set_index("model")
 x=x.rename(columns={"censored":"opportunity_censored"})
 x["episode_censored"]=[int(original.loc[n,"censored"]) for n in x.model]
 x["f1_rank"]=x.f1_lower90.rank(method="min",ascending=False).astype(int)
 for c in raw.columns:
  pd.testing.assert_series_equal(raw[c],x["opportunity_censored" if c=="censored" else c],check_names=False,check_exact=True)
 text=(source/"leaderboard_short_ranked.md").read_text()
 replacements={"up to50":"up to 50","up to30":"up to 30","up to20":"up to 20","these13models":"these 13 models","quarter-cluster90%":"quarter-cluster 90%","Wilson90%":"Wilson 90%","quarter-cluster and Wilson90%":"quarter-cluster and Wilson 90%","and25from50have":"and 25 from 50 have","same50%raw":"same 50% raw","all25archive":"all 25 archive","over228hours":"over 228 hours","andCSabove":"and CS above","Other profile and216/240hour":"Other profile and 216/240-hour","with27-hypothesis":"with 27-hypothesis","nonoverlapping6-hour":"nonoverlapping 6-hour","least1%of":"least 1% of","scorezero":"score zero","quarters20,000times":"quarters 20,000 times","leaderboard_short_ranked.csvcontains":"leaderboard_short_ranked.csv contains","opportunity_profiles.csvhas":"opportunity_profiles.csv has","opportunity_cases.csvand opportunity_blocks.csvretain":"opportunity_cases.csv and opportunity_blocks.csv retain","independent_metric_audit.jsonverifies":"independent_metric_audit.json verifies","manifest.jsonpins":"manifest.json pins","broader13-model":"broader 13-model","--score2in":"--score2 in","absent,29/30endpoints":"absent, 29/30 endpoints","PROTOCOL.mdfor":"PROTOCOL.md for"}
 for a,b in replacements.items():text=text.replace(a,b)
 text+="\n\n## F1 rank, shown separately\n\nThis rank sorts the worse-profile F1 lower bound. A model can cover more falls and still lose after trading costs; compare the return and evidence columns before selecting it.\n\n"
 text+="| F1 rank | Model | Archive F1 | Worst-profile F1 lower bound | Mean portfolio return | Wins / completed |\n|---|---|---|---|---|---|\n"
 for z in x.sort_values(["f1_rank","model"]).itertuples():
  text+=f"| {z.f1_rank} | {z.model} | {z.f1:.2%} | {z.f1_lower90:.2%} | {z.mean:+.3%} | {z.wins}/{z.completed} |\n"
 text+="\nThe CSV names opportunity_censored for incomplete six-hour labels and episode_censored for strategy positions still open at the portfolio endpoint. The original score file used censored for opportunity labels; the original portfolio counts remain preserved in the combined study. All original score components, ranks, returns and evidence flags reproduce exactly in this view.\n"
 scoring=ROOT/"results/scoring";core=[scoring/n for n in ["leaderboard_2.csv","short_leaderboard_2.csv","registry_2.jsonl","leaderboard.md"] if (scoring/n).exists()]
 before={str(p):sha(p) for p in core}
 md=scoring/"leaderboard_short_ranked.md";csv=scoring/"leaderboard_short_ranked.csv"
 for p in [md,csv]:
  if p.exists():raise ValueError("Existing published current view; preserve before updating")
 md.write_text(text);x.to_csv(csv,index=False)
 board=scoring/"leaderboard_2.md";old=board.read_text();oldsha=sha(board)
 marker="<!-- book-short-rank-guide -->"
 guide=marker+"\n\nFor the short-strategy comparison, start with "+str(md)+". It combines 50% conservative after-cost return, 30% opportunity F1 and 20% sample-aware completed accuracy, with trade counts and unchanged reliability flags. The detailed 13-model return/risk and executed-entry timing study remains "+str(combined/"leaderboard_short.md")+". Normal --score2 continues to update the registered-model table below; the short study admits a new model only after an equal-protocol audited batch.\n\n"
 if marker not in old:
  head,sep,body=old.partition("\n");new=head+"\n\n"+guide+body.lstrip("\n")
  if sha(board)!=oldsha:raise ValueError("Leaderboard changed while preparing guide")
  tmp=board.with_suffix(".md.book-tmp");tmp.write_text(new);os.replace(tmp,board)
 after={str(p):sha(p) for p in core}
 if before!=after:raise ValueError("Core numeric/registry files changed concurrently; inspect proof")
 (source/"presentation_audit.json").write_text(json.dumps(dict(status="PASS",source_manifest_sha256=sha(source/"manifest.json"),original_columns_exact=True,added_columns=["f1_rank","episode_censored"],renamed_columns={"censored":"opportunity_censored"},core_files_unchanged=before,normal_board_before=oldsha,normal_board_after=sha(board),outputs={str(p):sha(p) for p in [md,csv]}),indent=2))
 print(json.dumps(dict(status="PASS",leaderboard=str(md),models=len(x)),indent=2))
if __name__=="__main__":main()
