"""APT-metadata-verified Ubuntu headers, extracted privately; no system changes."""
from pathlib import Path
import subprocess,json,hashlib,time
import requests
OUT=Path('/home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-v1')
def main():
    d=OUT/'deps';d.mkdir(exist_ok=True);rows=[]
    for package in ['libcurl4-openssl-dev','libssl-dev','libboost1.74-dev','nlohmann-json3-dev']:
        fields={}
        for line in subprocess.check_output(['apt-cache','show','--no-all-versions',package],text=True).splitlines():
            if ': ' in line:
                k,v=line.split(': ',1)
                if k in ['Package','Version','Filename','SHA256','Size']:fields[k]=v
        row={"package":package,"metadata":fields,"status":"FAILED"}
        try:
            url="https://archive.ubuntu.com/ubuntu/"+fields["Filename"];row["url"]=url
            r=requests.get(url,timeout=(10,25));r.raise_for_status()
            digest=hashlib.sha256(r.content).hexdigest()
            if digest!=fields["SHA256"] or len(r.content)!=int(fields["Size"]):raise ValueError("APT metadata integrity mismatch")
            p=d/Path(fields["Filename"]).name;p.write_bytes(r.content)
            subprocess.run(['dpkg-deb','-x',str(p),str(d/'root')],check=True,capture_output=True)
            row.update(status="OK",sha256=digest,bytes=len(r.content))
        except Exception as e:row["error"]=type(e).__name__+": "+str(e)
        rows.append(row);(d/'https_manifest.json').write_text(json.dumps(rows,indent=2));print(row,flush=True)
if __name__=="__main__":main()
