"""Bounded public GET-only capture; no account/execution imports."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,time,subprocess
import requests,yaml
from src.config import load_config
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT.parents[1]/"results/book/20261015-latency-gate-v1"
CFG=yaml.safe_load(Path(__file__).with_name("config.yaml").read_text())
def fetch(source,url,params):
    begin=time.monotonic_ns();wall=time.time()
    row={"source":source,"send_mono_ns":begin,"send_unix":wall}
    try:
        r=requests.get(url,params=params,timeout=CFG["capture"]["request_timeout_seconds"])
        row.update(receive_mono_ns=time.monotonic_ns(),receive_unix=time.time(),http_status=r.status_code)
        if r.status_code==200:
            body=r.json()
            row["success"]=not isinstance(body,dict) or body.get("Success",True) is not False
            if row["success"]:row["data"]=body
            else:row["error"]="public_success_false"
        else:row["success"]=False;row["error"]="http_"+str(r.status_code)
    except (requests.RequestException,ValueError) as e:
        row.update(receive_mono_ns=time.monotonic_ns(),receive_unix=time.time(),success=False,error=type(e).__name__)
    return row
def main():
    OUT.mkdir(exist_ok=True);c=CFG["capture"];roostoo=load_config()["exchange"]["base_url"].rstrip("/")
    paths={s:OUT/(s+"_capture.jsonl") for s in ["binance","roostoo"]}
    assert not any(p.exists() for p in paths.values()),"Never append over an earlier capture"
    external="https://data-api.binance.vision/api/v3/ticker/bookTicker"
    params={"symbols":json.dumps([s+"USDT" for s in CFG["symbols"]],separators=(",",":"))}
    start=time.monotonic();deadline=start+c["duration_seconds"];due={"binance":start,"roostoo":start}
    counts={s:0 for s in paths};fail={s:0 for s in paths}
    pending={};pool=ThreadPoolExecutor(max_workers=2)
    with paths["binance"].open("w") as eb,paths["roostoo"].open("w") as rb:
        handles={"binance":eb,"roostoo":rb}
        while time.monotonic()<deadline or pending:
            now=time.monotonic()
            for source,f in list(pending.items()):
                if f.done():
                    row=f.result();handles[source].write(json.dumps(row,separators=(",",":"))+"\n");handles[source].flush()
                    counts[source]+=1;fail[source]+=int(not row["success"]);del pending[source]
            if now<deadline:
                for source in paths:
                    if now>=due[source] and source not in pending:
                        gap=c["external_interval_seconds"] if source=="binance" else c["roostoo_interval_seconds"]
                        due[source]=now+gap
                        pending[source]=pool.submit(fetch,source,external if source=="binance" else roostoo+"/v3/ticker",
                                                    params if source=="binance" else {"timestamp":int(time.time()*1000)})
            time.sleep(.05)
    pool.shutdown()
    summary={"status":"CAPTURE_COMPLETE","counts":counts,"failures":fail,"duration_mono_seconds":time.monotonic()-start,
             "git_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
             "public_only":True,"orders":0,"actual_fills_verified":False}
    (OUT/"capture_complete.json").write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
if __name__=="__main__":main()
