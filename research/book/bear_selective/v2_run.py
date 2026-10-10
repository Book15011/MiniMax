"""Correct the endpoint convention; reuse proven unchanged normal scores."""
from pathlib import Path
import json,subprocess,sys,time
import yaml
from research.book.bear_selective import run as study
ROOT=Path('/home/ubuntu/test/MiniMax')
PRIOR=ROOT/'results/book/20261010-bear-selective-v1'
OLDWT=ROOT/'.worktrees/book-book-intraday-short'

def main():
 out=study.OUT;out.mkdir(parents=True,exist_ok=True)
 if (out/'status.json').exists():raise ValueError('Preserve previous batch')
 prior=json.loads((PRIOR/'status.json').read_text())
 if len(prior)!=5 or any(z['returncode'] for z in prior):raise ValueError('Normal score incomplete')
 oldcfg=yaml.safe_load((OLDWT/'config.yaml').read_text());newcfg=yaml.safe_load(Path('config.yaml').read_text())
 same=['src/models/book/_bear_selective.py']+['src/models/book/'+n+'.py' for n in study.NAMES]
 proofs={}
 for n in same:
  a=study.sha(OLDWT/n);b=study.sha(n)
  if a!=b:raise ValueError('Model changed: '+n)
  proofs[n]=a
 if any(oldcfg['models'][n]!=newcfg['models'][n] for n in study.NAMES):raise ValueError('Model params changed')
 registry=[json.loads(z) for z in (ROOT/'results/scoring/registry_2.jsonl').read_text().splitlines()]
 records={}
 for n in study.NAMES:
  z=[r for r in registry if r.get('model')==n][-1]
  for a in z['artifacts'].values():
   if study.sha(a['path'])!=a['sha256']:raise ValueError('Published score artifact changed')
  records[n]=z
 (out/'normal_score_reuse.json').write_text(json.dumps(dict(source_status_path=str(PRIOR/'status.json'),source_status_sha256=study.sha(PRIOR/'status.json'),unchanged_model_sources=proofs,unchanged_model_parameters={n:newcfg['models'][n] for n in study.NAMES},published_registry_records=records,reason='Normal --score2 jobs already passed. Only supplemental endpoint eligibility changes.'),indent=2))
 rows=[]
 for name,args in [('full_pytest',[sys.executable,'-B','-m','pytest','-q']),('focused_tests',[sys.executable,'-B','-m','pytest','-q','--import-mode=importlib','research/book/bear_selective/test_model.py','research/book/bear_selective/test_cutoff.py','research/book/bear_selective/test_audit.py','research/book/bear_selective/test_entry_diagnostics.py'])]:
  with (out/(name+'.log')).open('x') as f:code=subprocess.call(args,stdout=f,stderr=subprocess.STDOUT)
  rows.append(dict(job=name,returncode=code));(out/'validation_status.json').write_text(json.dumps(rows,indent=2))
  if code:raise RuntimeError('Tests failed')
 status=[rows[0]]+[dict(job=n,returncode=0,reused_from=str(PRIOR/'status.json')) for n in study.NAMES]
 (out/'status.json').write_text(json.dumps(status,indent=2))
 # Let the older failed-version process finish and preserve its full diagnostics.
 while subprocess.run(['tmux','has-session','-t','mm-book-bear-selective-resume'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:time.sleep(10)
 if (PRIOR/'evaluation_manifest.json').exists():raise ValueError('Unexpected successful prior version')
 failure=json.loads((PRIOR/'evaluation_progress.json').read_text())
 if not failure['failures']:raise ValueError('Expected failed endpoint evidence missing')
 (out/'previous_failure_reference.json').write_text(json.dumps(dict(path=str(PRIOR),progress_sha256=study.sha(PRIOR/'evaluation_progress.json'),failed_cases=len(failure['failures']),reason='Hourly decision plus lag could start an order batch exactly at cutoff; later spaced orders crossed it. v2 excludes entire batches starting at cutoff.',rules_unchanged=True),indent=2))
 study.evaluate()
 code=subprocess.call([sys.executable,'-B','-m','research.book.bear_selective.score','--score'])
 (out/'batch_status.json').write_text(json.dumps(dict(status='PASS' if code==0 else 'FAIL',score_returncode=code),indent=2))
 raise SystemExit(code)
if __name__=='__main__':main()
