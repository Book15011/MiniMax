"""Require byte-identical benchmark execution across the corrected cohorts."""
from pathlib import Path
import hashlib,json
import pandas as pd
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def compare_pairs(pairs):
 rows=[]
 for old,new in pairs:
  a,b=sha(old),sha(new)
  if a!=b:raise ValueError('Control artifact differs: '+str(new))
  rows.append(dict(prior=str(old),current=str(new),sha256=a))
 return rows

def audit(out,study):
 freeze=json.loads((out/'publisher_helper_freeze.json').read_text())
 if any(sha(Path(p))!=h for p,h in freeze['files'].items()):raise ValueError('Publication helper changed after its freeze')
 prior=Path('/home/ubuntu/test/MiniMax/results/book/20261010-bear-selective-v2')
 m=json.loads((prior/'evaluation_manifest.json').read_text())
 if m['status']!='PASS' or sha(prior/'window_results.csv')!=m['window_results_sha256']:raise ValueError('Prior corrected control evidence changed')
 f=pd.read_csv(out/'window_results.csv');cases=pd.read_parquet(out/'cases.parquet')
 control=study['models'][0]
 x=f[f.model==control]
 expected=len(cases)*len(study['horizons'])*len(study['costs'])+len(study['costs'])
 if len(x)!=expected or x.duplicated(['case','scenario','hours']).any():raise ValueError('Incomplete control replay')
 pairs=[]
 for z in x.itertuples():
  relative=Path('cases')/z.case/(control+'-'+z.scenario+'-'+str(z.hours))
  for suffix in ['.events.csv','.cycles.csv','.path.parquet','.endpoint.json']:
   pairs.append((Path(str(prior/relative)+suffix),Path(str(out/relative)+suffix)))
 rows=compare_pairs(pairs)
 proof=dict(status='PASS',control=control,ledgers=len(x),artifacts=len(rows),all_identical=True,prior_manifest_sha256=sha(prior/'evaluation_manifest.json'),source_sha256=sha(__file__),file_pairs=rows)
 (out/'control_reproduction_audit.json').write_text(json.dumps(proof,indent=2))
 return proof
