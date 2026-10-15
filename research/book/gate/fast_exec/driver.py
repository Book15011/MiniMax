"""Thin supervisor around the exact C++ core; no credential loading/order network path."""
from pathlib import Path
import ctypes as C,json,hashlib,hmac,sys,time,os
HERE=Path(__file__).parent
OUT=Path(os.environ.get('MM_FAST_RESULTS','/home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-v1'))
CFG=json.loads((HERE/'config.json').read_text())
class Sized(C.Structure):
    _fields_=[('quantity',C.c_int64),('notional',C.c_int64),('fee',C.c_int64),('status',C.c_int)]
class Core:
    def __init__(self,path=None):
        self.lib=C.CDLL(str(path or OUT/'build/core.so'));L=self.lib
        L.money_parse.argtypes=[C.c_char_p,C.POINTER(C.c_int64)];L.money_parse.restype=C.c_int
        L.size_order.argtypes=[C.c_char_p,C.c_char_p,C.c_int,C.c_int64,C.POINTER(Sized)];L.size_order.restype=C.c_int
        L.gate_order.argtypes=[C.c_int64]*9+[C.c_char_p]*5+[C.c_int,C.c_int64,C.POINTER(Sized)];L.gate_order.restype=C.c_int
        L.rate_new.restype=C.c_void_p;L.rate_free.argtypes=[C.c_void_p]
        L.rate_take.argtypes=[C.c_void_p,C.c_int64,C.c_int,C.c_int,C.c_int,C.c_int];L.rate_take.restype=C.c_int
        L.health_permission.argtypes=[C.c_int64]*14;L.health_permission.restype=C.c_int
        L.state_event.argtypes=[C.POINTER(C.c_int),C.c_int];L.state_event.restype=C.c_int
    def parse(self,x):
        n=C.c_int64()
        if self.lib.money_parse(str(x).encode(),C.byref(n)):raise ValueError('Invalid exact decimal')
        return n.value
    def size(self,r):
        s=Sized()
        if self.lib.size_order(str(r['price']).encode(),str(r['budget']).encode(),r['precision'],r['fee_ppm'],C.byref(s)):raise ValueError('Invalid sizing inputs')
        return s
    def gate(self,r):
        s=Sized()
        values=[r[k] for k in ['now_ms','feed_ms','quote_ms','quote_rtt_ms','clock_uncertainty_ms']]
        values += [CFG[k] for k in ['feed_max_receipt_age_ms','quote_max_receipt_age_ms','quote_max_rtt_ms','clock_max_uncertainty_ms']]
        values += [str(r[k]).encode() for k in ['equity','cash','gross','budget','price']]
        code=self.lib.gate_order(*values,r['precision'],r['fee_ppm'],C.byref(s))
        return code,s
def plain(n):
    return str(n//100000000)+'.'+str(n%100000000).zfill(8)
def sized(s):return {k:plain(getattr(s,k)) for k in ['quantity','notional','fee']}
def prepare(pair,quantity,timestamp):
    coin=pair.removesuffix('/USD')
    if pair!=coin+'/USD' or not coin or not coin.isascii() or not coin.isalnum() or not coin.isupper():raise ValueError('Invalid pair')
    if not timestamp.isdigit() or len(timestamp)!=13:raise ValueError('Invalid timestamp')
    body=f'pair={pair}&quantity={quantity}&side=BUY&timestamp={timestamp}&type=MARKET'
    return {'body':body,'dummy_signature':hmac.new(b'Jefe',body.encode(),hashlib.sha256).hexdigest()}
def ack(d):
    if d.get('Success') is False:return 'REJECTED'
    if d.get('Success') is not True:return 'UNKNOWN'
    s=d.get('OrderDetail',{}).get('Status')
    return s if s in ['FILLED','PENDING','CANCELED'] else 'UNKNOWN'
def book(core,packet):
    d=packet.get('data',packet);symbol=d.get('s','')
    if symbol not in {s+'USDT' for s in CFG['symbols']}:return {'valid':False}
    try:
        b,a=core.parse(d['b']),core.parse(d['a']);bq,aq=core.parse(d['B']),core.parse(d['A'])
        if b<=0 or a<b or bq<=0 or aq<=0 or type(d['u']) is not int or d['u']<=0:return {'valid':False}
        return {'valid':True,'symbol':symbol,'bid':b,'ask':a,'update_id':d['u']}
    except (KeyError,ValueError,TypeError):return {'valid':False}
def execute(core,r):
    cmd=r['cmd']
    if cmd=='health':
        inputs=[r['feed_age_ms'],int(r['quote_needed']),r['quote_p95_ms'],r['order_p95_ms'],r['clock_uncertainty_ms'],r['samples'],r['unresolved_timeouts'],r['opportunity_ms'],CFG['target_filled_ms'],CFG['health_local_budget_ms'],CFG['health_safety_margin_ms'],CFG['health_min_samples'],CFG['feed_max_receipt_age_ms'],CFG['clock_max_uncertainty_ms']]
        code=core.lib.health_permission(*inputs)
        total=r['feed_age_ms']+(r['quote_p95_ms'] if r['quote_needed'] else 0)+r['order_p95_ms']+r['clock_uncertainty_ms']+CFG['health_local_budget_ms']
        return {'allowed':code==0,'reason_code':code,'predicted_total_ms':total,'actual_order_stats_verified':False}
    if cmd=='size':return sized(core.size(r))
    if cmd=='prepare':
        if core.parse(r['quantity'])<=0:raise ValueError('Nonpositive quantity')
        return prepare(r['pair'],r['quantity'],r['timestamp'])
    if cmd=='gate':
        code,s=core.gate(r);return {'allowed':code==0,'rejection_code':code,**sized(s)}
    if cmd=='rate':
        h=core.lib.rate_new()
        if not h:raise MemoryError()
        try:return {'accepted':[bool(core.lib.rate_take(h,t,r['limit'],r['reserve'],r['account_used'],CFG['account_calls_per_minute'])) for t in r['times_ms']]}
        finally:core.lib.rate_free(h)
    if cmd=='lifecycle':
        st=C.c_int(0);accepted=[]
        for e in r['events']:
            result=core.lib.state_event(C.byref(st),{'begin':0,'timeout':1,'pending':2,'filled':3}[e])
            if e=='begin':accepted.append(result==1)
        return {'accepted':accepted,'state':['READY','SUBMITTED','UNKNOWN','PENDING','FILLED'][st.value]}
    if cmd=='ack':return {'state':ack(r['response'])}
    if cmd=='book':return book(core,r['packet'])
    raise ValueError('Unknown operation')
def main():
    core=Core()
    for line in sys.stdin:
        try:r=execute(core,json.loads(line))
        except Exception as e:r={'error':type(e).__name__}
        print(json.dumps(r,separators=(',',':')),flush=True)
if __name__=='__main__':main()
