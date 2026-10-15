"""Download verified Ubuntu development packages into ignored research outputs; no system install."""
from pathlib import Path
import subprocess,json,hashlib
OUT=Path('/home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-v1')
def main():
 d=OUT/'deps';d.mkdir(parents=True,exist_ok=True);rows=[]
 packages=['libcurl4-openssl-dev','libssl-dev','libboost1.74-dev','nlohmann-json3-dev']
 for package in packages:
  r=subprocess.run(['apt-get','download',package],cwd=d,capture_output=True,text=True,timeout=150)
  (d/(package+'.log')).write_text(r.stdout+r.stderr)
  row={'package':package,'returncode':r.returncode}
  files=sorted(d.glob(package+'_*.deb'))
  if r.returncode==0 and len(files)==1:
   p=files[0];row.update(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
   x=subprocess.run(['dpkg-deb','-x',str(p),str(d/'root')],capture_output=True,text=True)
   row['extract_returncode']=x.returncode
  rows.append(row);(d/'manifest.json').write_text(json.dumps(rows,indent=2));print(row,flush=True)
if __name__=='__main__':main()
