"""Validate fixed new models, publish normal scores, then audit all cases."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,subprocess,sys,os
import yaml
from research.book.short_forecast import run as study
ROOT=Path('/home/ubuntu/test/MiniMax')
OLDWT=ROOT/'.worktrees/book-book-intraday-short'

def main():
 out=study.OUT;out.mkdir(parents=True,exist_ok=True)
 os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
 if (out/'status.json').exists():raise ValueError('Preserve previous batch')
 status=[]
 tests=[('full_pytest',[sys.executable,'-B','-m','pytest','-q']),('focused_tests',[sys.executable,'-B','-m','pytest','-q','--import-mode=importlib','research/book/short_forecast/test_model.py','research/book/short_forecast/test_audit.py','research/book/short_forecast/test_entry_diagnostics.py','research/book/bear_selective/test_cutoff.py'])]
 validation=[]
 for n,args in tests:
  with (out/(n+'.log')).open('x') as f:code=subprocess.call(args,stdout=f,stderr=subprocess.STDOUT)
  validation.append(dict(job=n,returncode=code));(out/'validation_status.json').write_text(json.dumps(validation,indent=2))
  if code:raise RuntimeError('Tests failed')
 status.append(validation[0])
 # Guard is unchanged and was already published through normal --score2.
 old=yaml.safe_load((OLDWT/'config.yaml').read_text());new=yaml.safe_load(Path('config.yaml').read_text())
 control=study.NAMES[0]
 if control!='book_bear_guard' or old['models'][control]!=new['models'][control]:raise ValueError('Control changed')
 pins={}
 for n in ['src/models/book/_bear_selective.py','src/models/book/book_bear_guard.py']:
  if study.sha(OLDWT/n)!=study.sha(n):raise ValueError('Control source changed')
  pins[n]=study.sha(n)
 records=[json.loads(z) for z in (ROOT/'results/scoring/registry_2.jsonl').read_text().splitlines()]
 rec=[z for z in records if z.get('model')==control][-1]
 for z in rec['artifacts'].values():
  if study.sha(z['path'])!=z['sha256']:raise ValueError('Control score changed')
 (out/'normal_control_reuse.json').write_text(json.dumps(dict(model=control,sources=pins,params=new['models'][control],registry_record=rec),indent=2))
 done={control:dict(job=control,returncode=0,reused=True)}
 def task(n):
  with (out/(n+'.log')).open('x') as f:code=subprocess.call([sys.executable,'-B','-m','backtest.run','--model',n,'--score2'],stdout=f,stderr=subprocess.STDOUT)
  return dict(job=n,returncode=code)
 files=[Path('research/book/short_forecast')/n for n in ['score.py','audit.py','entry_diagnostics.py','control_audit.py']]
 (out/'publisher_helper_freeze.json').write_text(json.dumps(dict(files={str(p.resolve()):study.sha(p) for p in files}),indent=2))
 evaluation_log=(out/'evaluation.log').open('x')
 evaluation=subprocess.Popen([sys.executable,'-B','-c','from research.book.short_forecast.run import evaluate;evaluate()'],stdout=evaluation_log,stderr=subprocess.STDOUT)
 with ThreadPoolExecutor(max_workers=3) as pool:
  for f in as_completed([pool.submit(task,n) for n in study.NAMES[1:]]):
   z=f.result();done[z['job']]=z
   (out/'status.json').write_text(json.dumps(status+[done[n] for n in study.NAMES if n in done],indent=2));print(z,flush=True)
 if len(done)!=len(study.NAMES) or any(z['returncode'] for z in done.values()):raise RuntimeError('Normal scoring failed')
 evaluation_code=evaluation.wait();evaluation_log.close()
 (out/'evaluation_job_status.json').write_text(json.dumps(dict(returncode=evaluation_code),indent=2))
 if evaluation_code:raise RuntimeError('Historical evaluation failed; artifacts preserved')
 code=subprocess.call([sys.executable,'-B','-m','research.book.short_forecast.score','--score'])
 (out/'batch_status.json').write_text(json.dumps(dict(status='PASS' if code==0 else 'FAIL',score_returncode=code),indent=2))
 raise SystemExit(code)
if __name__=='__main__':main()
