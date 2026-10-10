"""Combine only audited equal-protocol hourly short cohorts; no new fitting or replay."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np,pandas as pd
from research.book.intraday_short.report import clustered_interval,eligible
ROOT=Path('/home/ubuntu/test/MiniMax')
PARENTS=[ROOT/'results/book/20261010-bear-selective-v2',ROOT/'results/book/20261010-bear-exit-v1']
OUT=ROOT/'results/book/20261010-short-combined-v1'
PROFILES=('weak_archived','weak_fresh_btc')
HORIZONS=(216,228,240)
HYPOTHESES=21
CONTROL='book_bear_guard'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def merge_cohorts(a,b,keys=('case','scenario','hours')):
 if set(a.columns)!=set(b.columns):raise ValueError('Cohort columns differ')
 if a.duplicated(['model',*keys]).any() or b.duplicated(['model',*keys]).any():raise ValueError('Duplicate cohort rows')
 shared=set(a.model)&set(b.model)
 if shared!={CONTROL}:raise ValueError('Unexpected shared model')
 left=a[a.model==CONTROL].sort_values(list(keys)).reset_index(drop=True)
 right=b[b.model==CONTROL].sort_values(list(keys)).reset_index(drop=True)[left.columns]
 try:pd.testing.assert_frame_equal(left,right,check_exact=True)
 except AssertionError as exc:raise ValueError('Control differs between cohorts') from exc
 return pd.concat([a,b[b.model!=CONTROL][a.columns]],ignore_index=True)
def parent(p):
 for n in ['evaluation_manifest.json','report_manifest.json','independent_execution_audit.json','terminal_short_quantity_audit.json','entry_diagnostics_manifest.json']:
  d=json.loads((p/n).read_text())
  if d['status']!='PASS':raise ValueError('Parent evidence failed: '+str(p/n))
 m=json.loads((p/'evaluation_manifest.json').read_text())
 if sha(p/'window_results.csv')!=m['window_results_sha256']:raise ValueError('Parent outcomes changed')
 if json.loads((p/'evaluation_before.json').read_text())!=json.loads((p/'evaluation_after.json').read_text()):raise ValueError('Parent freeze differs')
 for n in ['independent_execution_audit.json','terminal_short_quantity_audit.json']:
  if json.loads((p/n).read_text())['ledgers']!=2460:raise ValueError('Parent ledger count differs')
 status=json.loads((p/'status.json').read_text())
 if len(status)!=5 or any(z['returncode'] for z in status):raise ValueError('Parent tests/normal scoring incomplete')
 e=json.loads((p/'entry_diagnostics_manifest.json').read_text())
 if e['input_result_sha256']!=sha(p/'window_results.csv'):raise ValueError('Entry marks use different results')
 return pd.read_csv(p/'window_results.csv')
def summary(x):
 n=int(x.completed.sum());w=int(x.wins.sum())
 return dict(n=len(x),mean=float(x['return'].mean()),median=float(x['return'].median()),p10=float(x['return'].quantile(.1)),worst=float(x['return'].min()),CS=float(x.CS.mean()),MDD=float(x.maximum_drawdown.mean()),completed=n,wins=w,accuracy=w/n if n else np.nan,censored=int(x.censored.sum()),firing=int(((x.completed+x.censored)>0).sum()),mean_gross=float(x.mean_gross_ratio.mean()))
def table(headers,rows):
 return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join('---' for _ in headers)+'|']+['| '+' | '.join(map(str,r))+' |' for r in rows])
def pct(x):return 'unknown' if pd.isna(x) else f'{x:+.3%}'
def rate(x):return 'unknown' if pd.isna(x) else f'{x:.2%}'
def build():
 if (OUT/'manifest.json').exists():raise ValueError('Preserve published combined cohort')
 before={}
 for p in PARENTS:
  for n in ['evaluation_manifest.json','report_manifest.json','window_results.csv','cases.parquet','independent_execution_audit.json','terminal_short_quantity_audit.json','evaluation_before.json','evaluation_after.json','status.json','entry_accuracy_1h_3h_6h.csv','entry_diagnostics_manifest.json','executed_entry_markouts.csv']:
   before[str(p/n)]=sha(p/n)
 proof=PARENTS[1]/'control_reproduction_audit.json';before[str(proof)]=sha(proof)
 guard=json.loads(proof.read_text())
 if guard['status']!='PASS' or guard['ledgers']!=615 or guard['artifacts']!=2460 or not guard['all_identical']:raise ValueError('Guard control reproduction failed')
 a,b=map(parent,PARENTS)
 if sha(PARENTS[0]/'cases.parquet')!=sha(PARENTS[1]/'cases.parquet'):raise ValueError('Lookalike cases differ')
 f=merge_cohorts(a,b);models=sorted(f.model.unique())
 if len(models)!=7 or len(f)!=4305 or any(f.groupby('model').size()!=615):raise ValueError('Combined coverage changed')
 cases=pd.read_parquet(PARENTS[0]/'cases.parquet');profiles=[];rows=[]
 for name in models:
  lows=[];alows=[];gates=[]
  for profile in PROFILES:
   starts=set(map(str,cases.index[cases[profile]]))
   for hours in HORIZONS:
    x=f[(f.model==name)&(f.scenario=='original')&(f.hours==hours)&f.start.isin(starts)]
    if len(x)!=25:raise ValueError('Lost a lookalike case')
    lo,hi=clustered_interval(x,'return',alpha=.1/(HYPOTHESES*6))
    al,ah=clustered_interval(x,'accuracy')
    stress=f[(f.model==name)&(f.scenario=='doubled')&(f.hours==hours)&f.start.isin(starts)]['return'].mean()
    control=f[(f.model==name)&(f.scenario=='original')&(f.hours==228)&f.start.isin(set(map(str,cases.index[cases.positive_control])))]['return'].mean()
    quarters=pd.to_datetime(x.start,utc=True).dt.tz_localize(None).dt.to_period('Q').nunique()
    z=dict(model=name,profile=profile,hours=hours,**summary(x),lower_family90=lo,upper_family90=hi,accuracy_lower90=al,accuracy_upper90=ah,doubled_mean=stress,control_mean=control,quarters=quarters)
    passed=eligible(lo,z['completed'],quarters,z['firing'],stress,z['median'],control)
    z['stronger_evidence']=passed;profiles.append(z);lows.append(lo);gates.append(passed)
    if hours==228:alows.append(al)
  primary=next(z for z in profiles if z['model']==name and z['profile']=='weak_archived' and z['hours']==228)
  rows.append({**primary,'selection_lower90':min(lows),'worst_profile_accuracy_lower90':min(alows),'stronger_evidence':all(gates)})
 rank=pd.DataFrame(rows).sort_values(['selection_lower90','model'],ascending=[False,True])
 rank['rank']=range(1,8);rank['accuracy_rank']=rank.worst_profile_accuracy_lower90.rank(method='min',ascending=False)
 rank['return_rank']=rank['mean'].rank(method='min',ascending=False)
 entries=[]
 for p in PARENTS:entries.append(pd.read_csv(p/'entry_accuracy_1h_3h_6h.csv').drop(columns=['accuracy_rank_6h']))
 en=merge_cohorts(*entries,keys=('profile',))
 en['accuracy_rank_6h']=en.groupby('profile')['6h_accuracy'].rank(method='min',ascending=False)
 scenarios=[]
 for profile in PROFILES:
  for label,mask in [('future_down',cases.future_return<=-.02),('future_rebound',cases.future_return>=.02),('future_neutral',cases.future_return.between(-.02,.02,inclusive='neither'))]:
   starts=set(map(str,cases.index[cases[profile]&mask]));sr=[]
   for name in models:
    x=f[(f.model==name)&(f.scenario=='original')&(f.hours==228)&f.start.isin(starts)]
    sr.append(dict(profile=profile,future_label=label,model=name,**summary(x)))
   for place,z in enumerate(sorted(sr,key=lambda z:(-z['mean'],z['model'])),1):scenarios.append({**z,'scenario_return_rank':place})
 sc=pd.DataFrame(scenarios)
 text='# Combined short leaderboard: seven comparable hourly models\n\n'
 text+='Read Evidence first. All seven fail the reliable-profit checks; rank 1 is an experiment priority, not a validated live replacement. Clone trade agreement is a separate objective. This table reuses 4,305 audited outcomes from two completed cohorts; it performs no new fitting or trade replay. The shared guard is counted once and all 615 control ledgers reproduced exactly across the cohorts.\n\n'
 text+='All rows use the same 25 archive lookalikes, 228-hour cash-start portfolios, 25% gross / 10% coin intended caps, hourly decisions, one-hour lag, 0.10% fees and 0.05% halfspread each side. Recent-BTC lookalikes, 216/240-hour horizons, doubled costs and two-hour lag remain in the files. All 25 cases, including cash and later rebounds, count. Realised exposure can differ. The 228-hour horizon was frozen earlier; it is not the remaining competition time today.\n\n'
 text+='Conservative rank sorts the worst of six profile/horizon quarter-cluster lower bounds on mean return, using 20,000 resamples and the same 21-hypothesis correction for every row. Completed accuracy is net-profitable fully closed short episodes / completed episodes, including partial covers within an episode. Forced endpoint closes are censored from accuracy and included in return with full closing costs. Accuracy rank sorts the worst-profile 90% lower bound at 228 hours. Return rank sorts archive mean return. CS retains 0.4 Sortino + 0.3 Sharpe + 0.3 Calmar; MDD uses minute equity.\n\n'
 text+=table(['Rank','Model','Lower return','Return rank','Mean return','Median','P10','Worst','Wins/closed','Accuracy','Accuracy rank','Censored','MDD','CS','Mean gross','Evidence'],[[z.rank,z.model,pct(z.selection_lower90),int(z.return_rank),pct(z.mean),pct(z.median),pct(z.p10),pct(z.worst),f'{z.wins}/{z.completed}',rate(z.accuracy),int(z.accuracy_rank),z.censored,rate(z.MDD),f'{z.CS:.3f}',rate(z.mean_gross),'PASS' if z.stronger_evidence else 'FAIL'] for z in rank.itertuples()])
 text+='\n\nEvidence requires all six lower return bounds > 0, at least 30 completed episodes, 12 quarters and 12 firing windows in each context, positive doubled-cost mean, nonnegative median and positive-control mean >= -1%. Thresholds were not relaxed. Retrospective passes would still need future evaluation. Full model definitions and individual ledgers remain in the two source cohorts.\n\n## Short entry timing, ranked separately\n\n'
 text+='These labels start at the first simulated executed short fill after lag/band/rounding. They hypothetically hold that entry unchanged for 1/3/6 hours and charge entry/exit fees and spread, regardless of the strategy actual exit. They measure entry timing rather than completed-strategy profit. Horizons outside the window are censored. The descriptive rank uses 6-hour accuracy; it does not change the evidence flag.\n\n'
 primary=en[en.profile=='weak_archived'].sort_values(['accuracy_rank_6h','model'])
 text+=table(['6h rank','Model','Firing windows','1h wins/n','3h wins/n','6h wins/n','6h accuracy','6h mean after-cost mark','6h censored'],[[int(z['accuracy_rank_6h']),z['model'],f"{z['firing_windows']}/25",f"{z['1h_wins']}/{z['1h_count']}",f"{z['3h_wins']}/{z['3h_count']}",f"{z['6h_wins']}/{z['6h_count']}",rate(z['6h_accuracy']),pct(z['6h_mean_markout']),z['6h_censored']] for z in primary.to_dict('records')])
 text+='\n\n## When the historical market subsequently fell, rebounded or stayed neutral\n\nFuture BTC 240-hour return labels: down <= -2%, rebound >= +2%, neutral between. Strategy outcomes still use the 228-hour endpoint. These labels use future information and are diagnostic only: they never select the main windows, enter strategies, change the main rank or estimate the next market direction. Conditional ranks alone must not select a live model.\n\n'
 for label in ['future_down','future_rebound','future_neutral']:
  x=sc[(sc.profile=='weak_archived')&(sc.future_label==label)].sort_values('scenario_return_rank')
  text+=f'### {label}\n\n'
  text+=table(['Conditional return rank','Model','Windows','Mean return','Wins/closed','Accuracy','MDD','CS'],[[z.scenario_return_rank,z.model,z.n,pct(z.mean),f'{z.wins}/{z.completed}',rate(z.accuracy),rate(z.MDD),f'{z.CS:.3f}'] for z in x.itertuples()])+'\n\n'
 text+='## Read and reproduce\n\nleaderboard_short.csv has the primary ranks; entry_accuracy_1h_3h_6h.csv has both timing profiles; scenario_summary.csv retains all conditional groups and profiles; profile_summary.csv contains all six contexts. window_results.csv retains every unique outcome. manifest.json pins both parent reports, audit proofs, inputs and outputs. This presentation does not combine the earlier minute-exit or 100%-gross cohorts as equal-protocol models.\n\n'
 text+='Normal registered-model scoring remains .venv/bin/python -B -m backtest.run --model MODEL --score2 in Book worktree, which automatically updates /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md. The combined frozen study is a separate cohort and does not automatically admit a new model. A new strategy needs a new frozen batch with the same cases/execution and appropriate expanded hypothesis adjustment before joining a new combined version. This report can be generated once with .venv/bin/python -B -m research.book.bear_exit.combine --score; publication refuses overwrite.\n\n'
 text+='All history is spent research. Supplemental replay omits the daily activity guard; normal --score2 includes it. Historical spreads are proxies. Archived modern coin selection and present precision rules limit inference. The adaptive BCH-absent 29/30 coverage failure remains unchanged. No main merge, competition API or live bot change occurred.\n'
 if any(sha(p)!=h for p,h in before.items()):raise ValueError('Parent evidence changed while combining')
 OUT.mkdir(parents=True,exist_ok=True)
 outputs={'window_results.csv':f,'leaderboard_short.csv':rank,'profile_summary.csv':pd.DataFrame(profiles),'entry_accuracy_1h_3h_6h.csv':en,'scenario_summary.csv':sc}
 for n,x in outputs.items():x.to_csv(OUT/n,index=False)
 (OUT/'leaderboard_short.md').write_text(text)
 Path('research/book/bear_exit/COMBINED_RESULTS.md').write_text(text)
 files={n:sha(OUT/n) for n in [*outputs,'leaderboard_short.md']}
 (OUT/'manifest.json').write_text(json.dumps(dict(status='PASS',all_history_spent=True,source_sha256=sha(__file__),inputs=before,outputs=files,unique_models=7,unique_ledgers=len(f),family_hypotheses=HYPOTHESES,shared_control='EXACT',production_eligible=False),indent=2))
 print(rank[['rank','model','mean','accuracy','stronger_evidence']].to_string(index=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--score',required=True,action='store_true');p.parse_args();build()
