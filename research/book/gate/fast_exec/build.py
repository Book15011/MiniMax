"""Build isolated native core without installing packages or modifying the bot."""
from pathlib import Path
import subprocess,json,hashlib,os,sys,shlex
HERE=Path(__file__).parent
OUT=Path(os.environ.get('MM_FAST_RESULTS','/home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-v1'))
def main():
    d=OUT/'build';d.mkdir(parents=True,exist_ok=True)
    cmd=['g++','-std=c++17','-O3','-Wall','-Wextra','-Werror','-fPIC','-shared',str(HERE/'core.cpp'),'-o',str(d/'core.so')]
    r=subprocess.run(cmd,capture_output=True,text=True)
    (OUT/'build.log').write_text(r.stdout+r.stderr)
    if r.returncode:print(r.stdout+r.stderr);raise SystemExit(r.returncode)
    script='#!/bin/sh\nexec '+shlex.quote(sys.executable)+' -B -m '+shlex.quote(__package__+'.driver')+'\n'
    (d/'fast_exec').write_text(script);(d/'fast_exec').chmod(0o755)
    info={'native_core':'C++17','supervisor':'Python3.10','compiler':subprocess.check_output(['g++','--version'],text=True).splitlines()[0],
        'flags':cmd[1:8],'source_sha256':hashlib.sha256((HERE/'core.cpp').read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256((d/'core.so').read_bytes()).hexdigest(),
        'commit':json.loads((HERE/'source_manifest.json').read_text())['commit'] if (HERE/'source_manifest.json').exists() else subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'standalone_cpp_networking_built':False,
        'dependency_failure':'Official package/raw header downloads timed out; no system installation or custom TLS/crypto implementation.'}
    (OUT/'build_manifest.json').write_text(json.dumps(info,indent=2));print(json.dumps(info,indent=2))
if __name__=='__main__':main()
