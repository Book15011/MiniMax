"""Finite public connection matrix and whole-supervisor preparation benchmark."""
from pathlib import Path
import argparse,json,time,subprocess,platform,statistics,math
from decimal import Decimal,ROUND_DOWN
import requests
from .driver import CFG,OUT,Core,book,prepare,sized
from .native_http import NativeHTTP,L
from .public_auth import PublicAuth
def stats(x):
    x=sorted(x)
    def q(p):return x[min(len(x)-1,math.ceil(p*len(x))-1)] if x else None
    return {'n':len(x),'median':statistics.median(x) if x else None,'p95':q(.95),'p99':q(.99),'max':max(x) if x else None}
def micro(out,core_path=None):
    core=Core(core_path)
    packet=json.dumps({'stream':'avntusdt@bookTicker','data':{'u':123,'s':'AVNTUSDT','b':'0.1338','a':'0.1339','B':'10000','A':'10000'}})
    fixture=dict(now_ms=1000,feed_ms=950,quote_ms=950,quote_rtt_ms=100,clock_uncertainty_ms=20,
        equity=CFG['paper_equity'],cash=CFG['paper_equity'],gross='0',price='0.1339',budget=CFG['paper_order_budget'],precision=4,fee_ppm=CFG['entry_fee_ppm'])
    native=[];py=[];checksum=0
    for i in range(CFG['microbenchmark_iterations']):
        t=time.perf_counter_ns()
        b=book(core,json.loads(packet));health=core.lib.health_permission(50,0,187,187,20,30,0,500,CFG['target_filled_ms'],CFG['health_local_budget_ms'],CFG['health_safety_margin_ms'],CFG['health_min_samples'],CFG['feed_max_receipt_age_ms'],CFG['clock_max_uncertainty_ms']);code,s=core.gate(fixture)
        if not b['valid'] or code or health:raise AssertionError('Positive fixture rejected')
        prepared=prepare('AVNT/USD',sized(s)['quantity'],'1792040000000')
        checksum+=len(prepared['body'])
        native.append((time.perf_counter_ns()-t)/1000)
        t=time.perf_counter_ns()
        quantity=(Decimal(fixture['budget'])/(Decimal(fixture['price'])*Decimal('1.001'))).quantize(Decimal('0.0001'),rounding=ROUND_DOWN)
        checksum+=int(quantity>0)
        py.append((time.perf_counter_ns()-t)/1000)
    result={'boundary':'JSON decode, book validation, native latency permission, native risk and sizing, decimal output, canonical body, dummy HMAC; no network or actual fill',
        'complete_supervisor_prepare_us':stats(native),'decimal_size_only_us':stats(py),
        'complete_prepare_deadline_misses':sum(x>CFG['local_prepare_target_us'] for x in native),
        'target_prepare_us':CFG['local_prepare_target_us'],'iterations':CFG['microbenchmark_iterations'],'checksum':checksum,
        'comparison_is_same_scope':False,'performance_guarantee':False}
    (out/'microbenchmark.json').write_text(json.dumps(result,indent=2))
def public(out,host_role="unknown"):
    path=out/'public_matrix.jsonl'
    if path.exists():raise FileExistsError('Never overwrite captures')
    variants=['python_fresh_h1','native_warm_h2','native_cold_h1','python_reused_h1','native_warm_h1','native_cold_h2']
    native={v:NativeHTTP(http2=v.endswith('h2'),cold='cold' in v) for v in variants if v.startswith('native')}
    py=requests.Session();py.auth=PublicAuth();due=time.monotonic();offset=0.;rows=[]
    def pace():
        nonlocal due
        time.sleep(max(0,due-time.monotonic()));due=time.monotonic()+CFG['public_sample_interval_ms']/1000
    try:
        with path.open('x') as sink:
            for i in range(3):
                pace();r=native['native_warm_h1'].get('https://mock-api.roostoo.com/v3/serverTime')
                r.update(variant='clock',sample=i);sink.write(json.dumps(r)+'\n');sink.flush()
                if r['success'] and r['body'].get('ServerTime'):
                    offset=r['body']['ServerTime']-(r['send_unix_ns']+r['receive_unix_ns'])/2e6
            for i in range(CFG['public_samples_per_variant']):
                # Rotate order deterministically to reduce fixed time-of-session confounding.
                order=variants[i%len(variants):]+variants[:i%len(variants)]
                for v in order:
                    pace();url='https://mock-api.roostoo.com/v3/ticker?timestamp='+str(int(time.time()*1000+offset))
                    if v.startswith('native'):r=native[v].get(url)
                    else:
                        t=time.monotonic_ns();wall=time.time_ns()
                        try:
                            h=py if v=='python_reused_h1' else requests.Session()
                            h.auth=PublicAuth()
                            response=h.get(url,timeout=(CFG['connect_timeout_ms']/1000,CFG['request_timeout_ms']/1000),allow_redirects=False)
                            body=response.json()
                            r={'start_mono_ns':t,'end_mono_ns':time.monotonic_ns(),'send_unix_ns':wall,'receive_unix_ns':time.time_ns(),
                                'http_status':response.status_code,'success':response.status_code==200 and body.get('Success',True) is not False,
                                'http_version':response.raw.version,'body':body}
                            if h is not py:h.close()
                        except requests.RequestException as e:
                            r={'start_mono_ns':t,'end_mono_ns':time.monotonic_ns(),'send_unix_ns':wall,'success':False,'error':type(e).__name__}
                        r['elapsed_ms']=(r['end_mono_ns']-t)/1e6
                    r.update(variant=v,sample=i);rows.append(r);sink.write(json.dumps(r)+'\n');sink.flush()
        summary={}
        for v in variants:
            z=[r for r in rows if r['variant']==v];good=[r['elapsed_ms'] for r in z if r['success']]
            summary[v]={'attempts':len(z),'successes':len(good),'failures':len(z)-len(good),'successful_public_GET_ms':stats(good),
                'all_attempts_above_1s':sum(r['elapsed_ms']>=CFG['target_filled_ms'] for r in z),
                'actual_http_versions':sorted({r.get('http_version') for r in z if r.get('http_version') is not None}),
                'native_new_connections':sum(r.get('new_connections',0) for r in z)}
        result={'status':'PUBLIC_GET_ONLY','host':platform.node(),'libcurl':L.curl_version().decode(),'variants':summary,
            'clock_offset_ms_last_probe':offset,'order_ack_or_fill_measured':False,'signed_calls':0,'orders':0,'ec2_measurement':host_role=='ec2','host_role':host_role,'host_role_source':'Explicit CLI label; not attested',
            'small_sample_percentiles_descriptive_only':True}
        (out/'public_summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
    finally:
        py.close()
        for h in native.values():h.close()
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=OUT);p.add_argument('--core',type=Path);p.add_argument('--micro-only',action='store_true');p.add_argument('--host-role',choices=['lab','ec2','unknown'],default='unknown')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);micro(a.out,a.core)
    if not a.micro_only:public(a.out,a.host_role)
if __name__=='__main__':main()
