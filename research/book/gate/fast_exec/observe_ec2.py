"""Concurrent public EC2 observation: independently timestamped WS and rate-paced REST.
No credentials, signed calls, orders, retries, bot imports or interpolated price samples.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse,base64,hashlib,json,time,threading,platform
import requests
from .driver import CFG,OUT
from .ws import read_frame,client_frame
from .public_auth import PublicAuth
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--seconds',type=int,default=600)
    a=p.parse_args()
    if not 60<=a.seconds<=1800:raise ValueError('Bounded observation:60..1800s')
    a.out.mkdir(parents=True,exist_ok=True)
    files=[a.out/x for x in ['binance_books.jsonl','roostoo_quotes.jsonl','observer_summary.json']]
    if any(x.exists() for x in files):raise FileExistsError('Never overwrite observations')
    stop=threading.Event();counts={'binance_books':0,'roostoo_calls':0,'roostoo_failures':0};errors=[]
    session=requests.Session();session.auth=PublicAuth();offset=0.;last_call=-float('inf')
    def fetch(path,sink):
        nonlocal last_call
        budget_start=time.monotonic_ns()
        wait=max(0,CFG['public_sample_interval_ms']/1000-(time.monotonic()-last_call))
        if stop.wait(wait):return None
        start=time.monotonic_ns();wall=time.time_ns();last_call=time.monotonic()
        params={'timestamp':int(time.time()*1000+offset)} if path=='/v3/ticker' else None
        row={'path':path,'send_mono_ns':start,'send_unix_ns':wall,'budget_wait_ms':(start-budget_start)/1e6}
        counts['roostoo_calls']+=1
        try:
            r=session.get('https://mock-api.roostoo.com'+path,params=params,timeout=(2,4),allow_redirects=False)
            raw=r.json();end=time.monotonic_ns()
            good=r.status_code==200 and isinstance(raw,dict) and (raw.get('Success') is True if path=='/v3/ticker' else 'ServerTime' in raw)
            row.update(receive_mono_ns=end,receive_unix_ns=time.time_ns(),network_ms=(end-start)/1e6,
                       http_status=r.status_code,success=good,server_time=raw.get('ServerTime'))
            if path=='/v3/ticker':
                selected=['BTC']+CFG['symbols']
                row['quotes']={s:raw.get('Data',{}).get(s+'/USD') for s in selected}
        except Exception as e:
            end=time.monotonic_ns();row.update(receive_mono_ns=end,receive_unix_ns=time.time_ns(),
                network_ms=(end-start)/1e6,success=False,error=type(e).__name__)
        counts['roostoo_failures']+=int(not row['success'])
        sink.write(json.dumps(row,separators=(',',':'))+'\n');sink.flush();return row
    def roo():
        nonlocal offset
        with files[1].open('x') as sink:
            for _ in range(3):
                row=fetch('/v3/serverTime',sink)
                if row and row['success']:offset=row['server_time']-(row['send_unix_ns']+row['receive_unix_ns'])/2e6
            while not stop.is_set():fetch('/v3/ticker',sink)
    pool=ThreadPoolExecutor(max_workers=1);future=pool.submit(roo);r=None
    start=time.monotonic();deadline=start+a.seconds
    try:
        symbols=['BTC']+CFG['symbols']
        names='/'.join(s.lower()+'usdt@bookTicker' for s in symbols)
        key=base64.b64encode(__import__('os').urandom(16)).decode()
        r=requests.get('https://data-stream.binance.vision:443/stream?streams='+names,
            headers={'Connection':'Upgrade','Upgrade':'websocket','Sec-WebSocket-Key':key,'Sec-WebSocket-Version':'13'},stream=True,timeout=5,auth=PublicAuth())
        expected=base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
        if r.status_code!=101 or r.headers.get('Sec-WebSocket-Accept')!=expected:raise ValueError('Stream handshake failed')
        reader=r.raw._fp.fp;sock=reader.raw._sock;fragment=None
        with files[0].open('x') as sink:
            while time.monotonic()<deadline:
                if future.done():future.result();raise RuntimeError('Quote recorder stopped')
                fin,op,data=read_frame(reader);received=time.monotonic_ns()
                if op==9:sock.sendall(client_frame(10,data));continue
                if op==10:continue
                if op==8:raise EOFError('Feed closed')
                if op==1:
                    if fragment is not None:raise ValueError('Overlapping fragments')
                    fragment=data
                elif op==0:
                    if fragment is None:raise ValueError('Unexpected continuation')
                    fragment+=data
                else:raise ValueError('Unexpected opcode')
                if len(fragment)>1_000_000:raise ValueError('Message too large')
                if not fin:continue
                packet=json.loads(fragment);fragment=None;d=packet.get('data',{})
                if d.get('s') not in {s+'USDT' for s in symbols}:continue
                counts['binance_books']+=1
                sink.write(json.dumps({'receive_mono_ns':received,'receive_unix_ns':time.time_ns(),'data':d},separators=(',',':'))+'\n')
    except Exception as e:errors.append(type(e).__name__+': '+str(e))
    finally:
        stop.set();pool.shutdown(wait=True)
        try:future.result()
        except Exception as e:errors.append('Quote worker:'+type(e).__name__)
        session.close()
        if r is not None:r.close()
    result={'status':'COMPLETE' if not errors else 'FAILED','errors':errors,'counts':counts,'seconds':time.monotonic()-start,
        'host':platform.node(),'host_role':'EC2 when run by the operator; not remotely attested','source_event_timestamp_available':False,
        'roostoo_quote_generation_time_known':False,'requests_are_independently_timed':True,'rate_wait_excluded_from_network_ms':True,
        'orders':0,'signed_calls':0,'failures_retained':True}
    files[2].write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
