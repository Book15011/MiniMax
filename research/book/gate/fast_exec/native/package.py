"""Make a small source-only native EC2 handoff, remotely; never package the repo."""
from pathlib import Path
import tarfile,io,json,hashlib
HERE=Path(__file__).parent
ROOT=Path("/home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-native-v2")
def main():
    selected=sorted(HERE.glob("*.hpp"))+[HERE/"service.cpp",HERE/"build.py",HERE/"test_service.py",HERE/"README.md",HERE/"ABI_SOURCES.md"]
    selected += [HERE.parent/x for x in ["core.cpp","config.json","signal.py","driver.py"]]
    selected += [HERE/"ec2_native_public.sh",HERE/"EC2_HANDOFF.md"]
    target=ROOT/"fast_exec_native_ec2.tar.gz";hashes={}
    with tarfile.open(target,"w:gz") as tar:
        for source in selected:
            name="fast_exec/"+str(source.relative_to(HERE.parent))
            if source.name in ["ec2_native_public.sh","EC2_HANDOFF.md"]:name="fast_exec/"+source.name
            data=source.read_bytes()
            if source.name=="test_service.py":data=data.replace(b"from research.book.gate.fast_exec.signal",b"from fast_exec.signal")
            info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o755 if source.suffix==".sh" else 0o644
            tar.addfile(info,io.BytesIO(data));hashes[name]=hashlib.sha256(data).hexdigest()
    manifest={"bundle":str(target),"sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"bytes":target.stat().st_size,
      "files_sha256":hashes,"secrets":False,"orders_network_enabled":False,"test_import_namespace_relocated":True,
      "runtime":"C++17; Python is only build/test convenience"}
    (ROOT/"native_package_manifest.json").write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
if __name__=="__main__":main()
