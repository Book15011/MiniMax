"""Export only the isolated research prototype as a portable remote artifact."""
from pathlib import Path
import json,hashlib,subprocess,tarfile,shutil
from .driver import HERE,OUT
def main():
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    dest=OUT/'portable';package=dest/'fast_exec';package.mkdir(parents=True,exist_ok=True)
    names=['core.cpp','driver.py','build.py','native_http.py','benchmark.py','signal.py','shadow.py','ws.py','observe_ec2.py','public_auth.py','config.json','PILOT_SPEC.json',
           'test_native.py','test_http.py','test_signal.py','PLAN.md','CPP_EXECUTION_PLAN.md','RESEARCH.md','README.md']
    hashes={}
    for name in names:
        p=HERE/name
        if not p.exists():continue
        text=p.read_text()
        if name.startswith('test_'):text=text.replace('research.book.gate.fast_exec','fast_exec')
        (package/name).write_text(text);hashes[name]=hashlib.sha256(text.encode()).hexdigest()
    (package/'__init__.py').write_text('')
    (package/'source_manifest.json').write_text(json.dumps({'commit':commit,'sha256':hashes,'test_import_namespace_relocated':True},indent=2))
    for name in ['ec2_public_observer.sh','ec2_cpp_prereq_check.sh']:
        shutil.copy2(HERE/name,dest/name);(dest/name).chmod(0o755)
    archive=OUT/'fast_exec_public_ec2.tar.gz'
    with tarfile.open(archive,'w:gz') as t:
        t.add(package,arcname='fast_exec')
        for name in ['ec2_public_observer.sh','ec2_cpp_prereq_check.sh']:t.add(dest/name,arcname=name)
    manifest={'source_commit':commit,'archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'size_bytes':archive.stat().st_size,'contains_credentials':False,'contains_live_bot_or_data':False,'orders_enabled':False}
    (OUT/'portable_manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
