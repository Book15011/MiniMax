"""Bounded event-triggered public shadow prototype. Cannot place orders or read credentials."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import base64,hashlib,json,time,math,ctypes as C,subprocess
import requests
from .driver import CFG,OUT,Core,book
from .native_http import NativeHTTP
from .signal import BurstDetector,decision
from .ws import read_frame,client_frame
from .public_auth import PublicAuth
def main():
    paths=[OUT/'shadow_stream.jsonl',OUT/'shadow_requests.jsonl',OUT/'shadow_intents.jsonl']
    if any(p.exists() for p in paths):raise FileExistsError('Never overwrite a shadow run')
    core=Core();limiter=core.lib.rate_new();http=NativeHTTP(http2=True);pool=ThreadPoolExecutor(max_workers=1)
    counters={'frames':0,'valid_books':0,'burst_events':0,'requests':0,'budget_or_pacing_rejections':0,'busy_rejections':0,
        'eligible_intents':0,'ineligible_candidates':0}
    latest={};detector=BurstDetector();last_call=-math.inf;offset=0.;uncertainty=math.inf;info={};pending=None
    received=[];r=None;sock=None;status='COMPLETE';error=None;started=time.monotonic()
    request_sink=paths[1].open('x');intent_sink=paths[2].open('x');stream_sink=paths[0].open('x')
    def query(url,initial=False):
        nonlocal last_call
        now=time.monotonic()
        if initial:time.sleep(max(0,CFG['public_sample_interval_ms']/1000-(now-last_call)));now=time.monotonic()
        elif now-last_call<CFG['public_sample_interval_ms']/1000:
            counters['budget_or_pacing_rejections']+=1;return None
        if not core.lib.rate_take(limiter,int(now*1000),CFG['process_calls_per_minute'],CFG['reserve_exit_calls'],0,CFG['account_calls_per_minute']):
            counters['budget_or_pacing_rejections']+=1;return None
        last_call=now;counters['requests']+=1
        row=http.get(url);request_sink.write(json.dumps(row,separators=(',',':'))+'\n');request_sink.flush()
        return row
    def quote():
        return query('https://mock-api.roostoo.com/v3/ticker?timestamp='+str(int(time.time()*1000+offset)))
    def finish(task):
        symbol,start,burst,future=task
        q=future.result()
        if q is None:return
        now=time.monotonic_ns();b=latest.get(symbol)
        if b is None:return
        result=decision(core,symbol,start,now,b,q,uncertainty,info,int(time.time()*1000+offset))
        result.update(symbol=symbol,signal_start_mono_ns=start,processed_mono_ns=now,burst=burst)
        counters['eligible_intents' if result['eligible'] else 'ineligible_candidates']+=1
        if len(received)<CFG['max_shadow_intent_records']:received.append(result)
        intent_sink.write(json.dumps(result,separators=(',',':'))+'\n');intent_sink.flush()
    try:
        for _ in range(3):
            row=query('https://mock-api.roostoo.com/v3/serverTime',True)
            if row and row['success'] and row['elapsed_ms']/2<uncertainty:
                uncertainty=row['elapsed_ms']/2
                offset=row['body']['ServerTime']-(row['send_unix_ns']+row['receive_unix_ns'])/2e6
        row=query('https://mock-api.roostoo.com/v3/exchangeInfo',True)
        if row and row['success']:info=row['body'].get('TradePairs',{})
        names='/'.join(s.lower()+'usdt@bookTicker' for s in CFG['symbols'])
        url='https://data-stream.binance.vision:443/stream?streams='+names
        key=base64.b64encode(__import__('os').urandom(16)).decode()
        r=requests.get(url,headers={'Connection':'Upgrade','Upgrade':'websocket','Sec-WebSocket-Key':key,'Sec-WebSocket-Version':'13'},stream=True,timeout=5,auth=PublicAuth())
        expected=base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
        if r.status_code!=101 or r.headers.get('Sec-WebSocket-Accept')!=expected:raise ValueError('Public stream handshake failed')
        reader=r.raw._fp.fp;sock=reader.raw._sock;fragment=None
        end=time.monotonic()+CFG['shadow_seconds']
        while time.monotonic()<end:
            if pending is not None and pending[3].done():finish(pending);pending=None
            fin,op,payload=read_frame(reader);now=time.monotonic_ns();counters['frames']+=1
            if op==9:sock.sendall(client_frame(10,payload));continue
            if op==10:continue
            if op==8:raise EOFError('Feed closed; no further signals')
            if op==1:
                if fragment is not None:raise ValueError('Overlapping fragments')
                fragment=payload
            elif op==0:
                if fragment is None:raise ValueError('Unexpected continuation')
                fragment+=payload
            else:raise ValueError('Unexpected data opcode')
            if len(fragment)>1_000_000:raise ValueError('Message too large')
            if not fin:continue
            packet=json.loads(fragment);fragment=None
            b=book(core,packet)
            if not b['valid']:continue
            b.update(receive_mono_ns=now,receive_unix_ns=time.time_ns());counters['valid_books']+=1
            old=latest.get(b['symbol'])
            if old and b['update_id']<=old['update_id']:continue
            latest[b['symbol']]=b
            burst=detector.update(b['symbol'],b['update_id'],now,b['bid'])
            if burst:
                counters['burst_events']+=1
                if pending is None:pending=(b['symbol'],now,burst,pool.submit(quote))
                else:counters['busy_rejections']+=1
            # Raw packet buffering is after signal scheduling, not before it.
            stream_sink.write(json.dumps({'receive_mono_ns':now,'packet':packet},separators=(',',':'))+'\n')
        if pending is not None:finish(pending);pending=None
    except Exception as e:status='FAILED';error=type(e).__name__+': '+str(e)
    finally:
        pool.shutdown(wait=True);http.close();core.lib.rate_free(limiter)
        if r is not None:r.close()
        for sink in [request_sink,intent_sink,stream_sink]:sink.close()
    result={'status':status,'error':error,'counters':counters,'elapsed_seconds':time.monotonic()-started,
        'clock_offset_ms':offset,'clock_uncertainty_ms':uncertainty,'verified_metadata_symbols':len(info),
        'networking':'Native libcurl C ABI; Python supervisor; existing tested public RFC6455 reader',
        'orders':0,'signed_calls':0,'credentials_loaded':False,'actual_fills_verified':False,'production_eligible':False,
        'order_ack_budget_ms':CFG['reserved_order_ack_ms'],'intents_are_independent_counterfactuals':True,
        'portfolio_returns_or_f1':None,'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()}
    (OUT/'shadow_summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
