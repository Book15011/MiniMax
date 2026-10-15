"""Build one standalone native process with installed supported C libraries; no system changes."""
from pathlib import Path
import subprocess,json,hashlib,os
HERE=Path(__file__).parent
OUT=Path(os.environ.get("MM_NATIVE_RESULTS","/home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-native-v2"))
def main():
    (OUT/"build").mkdir(parents=True,exist_ok=True)
    command=["g++","-std=c++17","-O3","-Wall","-Wextra","-Werror","-Wno-misleading-indentation","-pthread",str(HERE/"service.cpp"),
             "-Wl,-z,relro,-z,now","-l:libcurl.so.4","-l:libjson-c.so.5","-l:libcrypto.so.3","-o",str(OUT/"build/fast_exec_native")]
    r=subprocess.run(command,capture_output=True,text=True)
    (OUT/"build.log").write_text(r.stdout+r.stderr)
    if r.returncode:print(r.stdout+r.stderr);raise SystemExit(r.returncode)
    sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob("*.hpp"))+[HERE/"service.cpp",HERE.parent/"core.cpp",HERE.parent/"config.json"]}
    info={"runtime":"standalone C++17","python_in_runtime":False,"build_command":command,"source_commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
      "working_tree_dirty":bool(subprocess.check_output(["git","status","--porcelain"],text=True).strip()),
      "source_sha256":sources,"binary_sha256":hashlib.sha256((OUT/"build/fast_exec_native").read_bytes()).hexdigest(),
      "dependencies":"system public libcurl4, json-c5, OpenSSL3; opaque ABI declarations in abi.hpp",
      "signed_order_transport":False,"live_gateway_integration":False}
    (OUT/"build_manifest.json").write_text(json.dumps(info,indent=2));print(json.dumps(info,indent=2))
if __name__=="__main__":main()
