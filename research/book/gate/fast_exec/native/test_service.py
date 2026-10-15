"""Standalone native service regression tests; all transport fixtures stay on loopback."""
import json,os,subprocess,hashlib,hmac,socket,threading,struct,time
from decimal import Decimal,ROUND_DOWN,ROUND_CEILING
from pathlib import Path
import pytest
BIN=Path(os.environ.get("MM_NATIVE_BIN","/home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-native-v2/build/fast_exec_native"))
CFG=Path(__file__).parents[1]/"config.json"
def call(rows):
    p=subprocess.run([str(BIN),"protocol",str(CFG)],input="".join(json.dumps(r)+"\n" for r in rows),text=True,capture_output=True,timeout=10)
    assert p.returncode==0,p.stderr
    return [json.loads(x) for x in p.stdout.splitlines()]
def test_native_dependencies():
    r=call([{"cmd":"version"}])[0]
    assert r["runtime"]=="C++17" and r["orders_network_enabled"] is False
    assert "libcurl" in r["transport"]
def test_decimal_sizing_and_hmac():
    rows=[{"cmd":"size","price":str(Decimal(17+i)/Decimal(13))[:10],"budget":str(Decimal(10000+i)/100),"precision":i%9,"fee_ppm":1000} for i in range(120)]
    result=call(rows)
    for r,o in zip(rows,result):
        p,b=Decimal(r["price"]),Decimal(r["budget"]);q=Decimal(o["quantity"])
        step=Decimal(10)**-r["precision"]
        assert q%step==0
        exact=q*p;unit=Decimal("0.00000001")
        n=exact.quantize(unit,rounding=ROUND_CEILING);fee=(n*Decimal(".001")).quantize(unit,rounding=ROUND_CEILING)
        assert n==Decimal(o["notional"]) and fee==Decimal(o["fee"]) and n+fee<=b
        extra=((q+step)*p).quantize(unit,rounding=ROUND_CEILING)
        assert extra+(extra*Decimal(".001")).quantize(unit,rounding=ROUND_CEILING)>b
    r=call([{"cmd":"prepare","pair":"AVNT/USD","quantity":"1.20000000","timestamp":"1792000000000"}])[0]
    body="pair=AVNT/USD&quantity=1.20000000&side=BUY&timestamp=1792000000000&type=MARKET"
    assert r["body"]==body and r["dummy_signature"]==hmac.new(b"Jefe",body.encode(),hashlib.sha256).hexdigest()
def test_invalid_money_and_json():
    for price in ["0","1e-4","-2","1.000000001","99999999999999999999999999"]:
        assert "error" in call([{"cmd":"size","price":price,"budget":"100","precision":8,"fee_ppm":1000}])[0]
    p=subprocess.run([str(BIN),"protocol",str(CFG)],input='{"cmd":"version"} junk\n{"cmd":"version"}\n',text=True,capture_output=True)
    r=[json.loads(x) for x in p.stdout.splitlines()]
    assert "error" in r[0] and r[1]["runtime"]=="C++17"
def test_order_timeout_partial_duplicate_cancel():
    r=call([
      {"cmd":"begin","id":"a","quantity":"2","now_ms":100,"expiry_ms":500},
      {"cmd":"begin","id":"b","quantity":"2","now_ms":100,"expiry_ms":500},
      {"cmd":"timeout","id":"a"},
      {"cmd":"begin","id":"b","quantity":"2","now_ms":101,"expiry_ms":500},
      {"cmd":"ack","id":"a","status":"PARTIAL","filled":"1","success":True},
      {"cmd":"begin","id":"b","quantity":"2","now_ms":102,"expiry_ms":500},
      {"cmd":"ack","id":"a","status":"CANCELED","filled":"1","success":True},
      {"cmd":"ack","id":"a","status":"CANCELED","filled":"1","success":True}])
    assert r[0]["accepted"] and not r[1]["accepted"] and not r[3]["accepted"] and not r[5]["accepted"]
    assert r[2]["state"]=="UNKNOWN" and r[4]["state"]=="PARTIAL"
    assert r[6]["state"]=="CANCELED" and r[7]["duplicate"]
    assert r[7]["filled"]=="1.00000000" and r[7]["sends"]==1
def test_malformed_ack_is_not_a_fill():
    r=call([{"cmd":"begin","id":"a","quantity":"2","now_ms":0,"expiry_ms":500},
      {"cmd":"ack","id":"wrong","status":"FILLED","filled":"2","success":True},
      {"cmd":"ack","id":"a","status":"FILLED","filled":"1","success":True},
      {"cmd":"ack","id":"a","status":"FILLED","filled":"2","success":False}])
    assert r[1]["state"]=="UNKNOWN" and r[2]["state"]=="UNKNOWN" and r[3]["state"]=="UNKNOWN"
    assert all(x["filled"]=="0.00000000" for x in r)
def test_expired_and_future_inputs():
    assert not call([{"cmd":"begin","id":"a","quantity":"2","now_ms":500,"expiry_ms":500}])[0]["accepted"]
    base={"cmd":"decision","now_ms":1000,"feed_ms":990,"quote_ms":995,"quote_rtt_ms":187,"uncertainty_ms":10,
     "order_p95_ms":187,"order_samples":30,"verified_order_stats":True,"opportunity_ms":500,"equity":"100000","cash":"100000",
     "gross":"0","budget":"10","price":"1","external_bid":"1.004","precision":4,"account_ms":1000}
    r=call([base,{**base,"verified_order_stats":False},{**base,"order_p95_ms":548},{**base,"feed_ms":1001},
      {**base,"account_ms":-10000},{**base,"external_bid":"1.001"}])
    assert r[0]["allowed"]
    assert all(not x["allowed"] for x in r[1:])
def test_quota_reserves_exits_and_account_caps():
    rows=[{"cmd":"quota","now_ms":i,"account_used":0,"exit":False} for i in range(18)]
    rows += [{"cmd":"quota","now_ms":20+i,"account_used":0,"exit":True} for i in range(4)]
    r=call(rows)
    assert sum(x["accepted"] for x in r[:18])==17
    assert sum(x["accepted"] for x in r[18:])==3
    assert not call([{"cmd":"quota","now_ms":0,"account_used":30,"exit":True}])[0]["accepted"]
def test_feed_duplicate_and_crossed():
    b={"cmd":"book","now_ms":0,"packet":{"data":{"s":"AVNTUSDT","u":1,"b":"1","a":"1.01","B":"10","A":"10"}}}
    r=call([b,b,{**b,"packet":{"data":{**b["packet"]["data"],"u":2,"a":".9"}}}])
    assert r[0]["valid"] and not r[1]["valid"] and not r[2]["valid"]

def test_state_reconciliation_and_exactly_once_fill():
    r=call([{"cmd":"begin","id":"a","quantity":"2","now_ms":0,"expiry_ms":500},
      {"cmd":"ack","id":"a","status":"PARTIAL","filled":"1","success":True},
      {"cmd":"ack","id":"a","status":"PARTIAL","filled":"0.5","success":True},
      {"cmd":"ack","id":"a","status":"FILLED","filled":"2","success":True},
      {"cmd":"ack","id":"a","status":"FILLED","filled":"2","success":True},
      {"cmd":"begin","id":"a","quantity":"2","now_ms":1,"expiry_ms":500}])
    assert r[2]["state"]=="UNKNOWN" and r[2]["filled"]=="1.00000000"
    assert r[3]["state"]=="FILLED" and r[4]["duplicate"] and r[4]["sends"]==1
    assert not r[5]["accepted"]
def test_single_burst_episode():
    def b(i,t,p):return {"cmd":"book","now_ms":t,"packet":{"s":"AVNTUSDT","u":i,"b":p,"a":p,"B":"10","A":"10"}}
    r=call([b(1,0,"1"),b(2,1000,"1.002"),b(3,1001,"1.002"),b(4,2002,"1.002"),b(5,3002,"1.004")])
    assert [x["signal"] for x in r]==[False,True,False,False,True]
class Fixture:
    def __init__(self,handler):
        self.sock=socket.socket();self.sock.bind(("127.0.0.1",0));self.sock.listen();self.port=self.sock.getsockname()[1]
        self.error=None
        def run():
            try:
                c,_=self.sock.accept()
                with c:c.settimeout(5);handler(c)
            except BaseException as e:self.error=e
            finally:self.sock.close()
        self.thread=threading.Thread(target=run,daemon=True);self.thread.start()
    def finish(self):
        self.thread.join(6)
        assert not self.thread.is_alive()
        if self.error:raise self.error
def request(c):
    data=b""
    while b"\r\n\r\n" not in data:data+=c.recv(1024)
    return data.decode()
def test_native_http_and_no_redirect():
    seen=[]
    def handler(c):
        seen.append(request(c));body=b'{"Success":true}'
        c.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: "+str(len(body)).encode()+b"\r\nConnection: close\r\n\r\n"+body)
    f=Fixture(handler)
    p=subprocess.run([str(BIN),"http-fixture",str(CFG),f"http://127.0.0.1:{f.port}/fixture"],capture_output=True,text=True,timeout=6)
    f.finish();r=json.loads(p.stdout)
    assert r["curl_code"]==0 and r["http_status"]==200 and len(seen)==1 and "GET /fixture" in seen[0]
    assert "RST" not in seen[0] and "Authorization" not in seen[0]
    def redirect(c):
        request(c);c.sendall(b"HTTP/1.1 302 Found\r\nLocation: http://127.0.0.1:1/fixture\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
    f=Fixture(redirect)
    p=subprocess.run([str(BIN),"http-fixture",str(CFG),f"http://127.0.0.1:{f.port}/fixture"],capture_output=True,text=True,timeout=6)
    f.finish();assert json.loads(p.stdout)["http_status"]==302
def ws_handshake(c,bad=False):
    req=request(c);key=[x.split(": ",1)[1] for x in req.split("\r\n") if x.lower().startswith("sec-websocket-key:")][0]
    import base64
    accept=base64.b64encode(hashlib.sha1((key+"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest())
    if bad:accept=b"bad"
    c.sendall(b"HTTP/1.1 101 Switching Protocols\r\nConnection: Upgrade\r\nUpgrade: websocket\r\nSec-WebSocket-Accept: "+accept+b"\r\n\r\n")
def run_ws(handler):
    f=Fixture(handler)
    p=subprocess.run([str(BIN),"ws-fixture",str(CFG),f"http://127.0.0.1:{f.port}/fixture"],capture_output=True,text=True,timeout=6)
    f.finish();assert p.returncode==0,p.stderr
    return [json.loads(x) for x in p.stdout.splitlines()]
def test_native_websocket_fragment_ping_and_multiple_messages():
    def handler(c):
        ws_handshake(c)
        c.sendall(b'\x01\x05{"x":'+b'\x89\x02ok'+b'\x80\x021}')
        # Masked client pong; a control frame can interrupt a text message.
        pong=c.recv(1024);assert pong[0]==138 and pong[1]&128
        length=pong[1]&127;mask=pong[2:6];payload=pong[6:6+length]
        assert bytes(x^mask[i%4] for i,x in enumerate(payload))==b"ok"
        c.sendall(b'\x81\x07{"x":2}'+b'\x88\x00')
    r=run_ws(handler)
    assert [x["x"] for x in r if "x" in x]==[1,2]
    assert r[-1]["messages"]==2
@pytest.mark.parametrize("frame",[b"\x81\x80",b"\x09\x00",b"\x82\x00",b"\x80\x00",b"\x81\x7e\x00\x01x",b"\x81\x7f\x80"+b"\x00"*7])
def test_native_websocket_rejects_bad_frames(frame):
    def handler(c):ws_handshake(c);c.sendall(frame)
    r=run_ws(handler);assert r[-1]["messages"]==0 and "error" in r[-1]
def test_native_websocket_handshake_must_be_valid():
    def handler(c):ws_handshake(c,bad=True)
    r=run_ws(handler);assert r[-1]["messages"]==0 and "validation" in r[-1]["error"]
