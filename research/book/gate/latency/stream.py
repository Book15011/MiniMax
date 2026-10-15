"""Bounded public RFC6455 book capture; no credentials/account/order methods."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import base64,hashlib,json,os,struct,time
import requests,yaml
from src.config import load_config
from research.book.gate.latency.collect import fetch
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT.parents[1]/"results/book/20261015-latency-gate-v1"
CFG=yaml.safe_load(Path(__file__).with_name("config.yaml").read_text())
def read_frame(stream):
    def exact(n):
        data=b""
        while len(data)<n:
            chunk=stream.read(n-len(data))
            if not chunk:raise EOFError("truncated public frame")
            data+=chunk
        return data
    a,b=exact(2);fin=bool(a&128);opcode=a&15
    if a&112 or b&128:raise ValueError("unsupported or masked server frame")
    size=b&127
    if size==126:size=struct.unpack("!H",exact(2))[0]
    elif size==127:size=struct.unpack("!Q",exact(8))[0]
    if size>1_000_000 or (opcode>=8 and (size>125 or not fin)):raise ValueError("invalid public frame size")
    return fin,opcode,exact(size)
def client_frame(opcode,payload,mask=None):
    if len(payload)>125:raise ValueError("control frame too large")
    mask=os.urandom(4) if mask is None else mask
    return bytes([128|opcode,128|len(payload)])+mask+bytes(x^mask[i%4] for i,x in enumerate(payload))
def main():
    paths=[OUT/"binance_stream.jsonl",OUT/"roostoo_stream.jsonl"]
    assert not any(p.exists() for p in paths),"Never overwrite an earlier capture"
    names="/".join(s.lower()+"usdt@bookTicker" for s in CFG["symbols"])
    url="https://data-stream.binance.vision:443/stream?streams="+names
    key=base64.b64encode(os.urandom(16)).decode();r=None;sock=None;pending=None;counts={"stream":0,"roostoo":0,"roostoo_failures":0}
    begin=time.monotonic();deadline=begin+600;due=begin;status="CAPTURE_COMPLETE";error=None
    pool=ThreadPoolExecutor(max_workers=1);roostoo=load_config()["exchange"]["base_url"].rstrip("/")
    try:
        r=requests.get(url,headers={"Connection":"Upgrade","Upgrade":"websocket","Sec-WebSocket-Key":key,
                                   "Sec-WebSocket-Version":"13"},stream=True,timeout=8)
        if r.status_code!=101:raise ValueError("public websocket HTTP "+str(r.status_code))
        expected=base64.b64encode(hashlib.sha1((key+"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        if r.headers.get("Sec-WebSocket-Accept")!=expected:raise ValueError("websocket accept mismatch")
        reader=r.raw._fp.fp;sock=reader.raw._sock;fragment=b""
        with paths[0].open("w") as eb,paths[1].open("w") as rb:
            while time.monotonic()<deadline:
                now=time.monotonic()
                if pending is not None and pending.done():
                    row=pending.result();rb.write(json.dumps(row,separators=(",",":"))+"\n");rb.flush()
                    counts["roostoo"]+=1;counts["roostoo_failures"]+=int(not row["success"]);pending=None
                if now>=due and pending is None:
                    due=now+6
                    pending=pool.submit(fetch,"roostoo",roostoo+"/v3/ticker",{"timestamp":int(time.time()*1000)})
                fin,op,payload=read_frame(reader);received=time.monotonic_ns()
                if op==9:sock.sendall(client_frame(10,payload));continue
                if op==10:continue
                if op==8:raise EOFError("public server closed stream")
                if op==1:fragment=payload
                elif op==0:fragment+=payload
                else:continue
                if fin:
                    body=json.loads(fragment);fragment=b""
                    if "data" in body and body["data"].get("s") in {s+"USDT" for s in CFG["symbols"]}:
                        row={"receive_mono_ns":received,"receive_unix":time.time(),"data":body["data"]}
                        eb.write(json.dumps(row,separators=(",",":"))+"\n");counts["stream"]+=1
                        if counts["stream"]%100==0:eb.flush()
            if pending is not None:
                row=pending.result();rb.write(json.dumps(row,separators=(",",":"))+"\n")
                counts["roostoo"]+=1;counts["roostoo_failures"]+=int(not row["success"])
    except Exception as e:
        status="CAPTURE_FAILED";error=type(e).__name__
    finally:
        pool.shutdown(wait=True)
        if sock is not None:
            try:sock.sendall(client_frame(8,struct.pack("!H",1000)))
            except OSError:pass
        if r is not None:r.close()
    summary={"status":status,"error":error,"counts":counts,"elapsed_seconds":time.monotonic()-begin,
             "public_only":True,"orders":0,"certificate_verified":True,"event_timestamp_known":False}
    (OUT/"stream_complete.json").write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
if __name__=="__main__":main()
