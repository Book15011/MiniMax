"""Native correctness tests, fixed fake signing key; no network or credentials."""
from pathlib import Path
from decimal import Decimal,ROUND_DOWN,ROUND_UP
import subprocess,json,random,hmac,hashlib
import pytest
from research.book.gate.fast_exec.driver import OUT
BIN=OUT/'build/fast_exec'
def native(rows):
    r=subprocess.run([str(BIN),'--worker'],input=''.join(json.dumps(x)+'\n' for x in rows),capture_output=True,text=True,check=True)
    return [json.loads(x) for x in r.stdout.splitlines()]
def size(price='1.23456789',budget='1000',precision=4,fee=1000):
    return dict(cmd='size',price=price,budget=budget,precision=precision,fee_ppm=fee)
def test_native_quantity_matches_independent_decimal_oracle():
    rng=random.Random(20261015);cases=[]
    for i in range(400):
        cases.append(size(str(Decimal(rng.randrange(1000,10**10))/10**8),str(Decimal(rng.randrange(100,10**8))/100),rng.randrange(0,9),rng.choice([0,500,1000,5000])))
    results=native(cases)
    for c,r in zip(cases,results):
        px=Decimal(c['price']);b=Decimal(c['budget']);fee=Decimal(c['fee_ppm'])/10**6
        step=Decimal(1).scaleb(-c['precision'])
        qty=(b/(px*(1+fee))).quantize(step,rounding=ROUND_DOWN)
        # Enforce conservatively rounded dollar cost with eight fractional places.
        unit=Decimal('0.00000001')
        while qty>0:
            n=(qty*px).quantize(unit,rounding=ROUND_UP)
            charge=(n*fee).quantize(unit,rounding=ROUND_UP)
            if n+charge<=b:break
            qty-=step
        assert Decimal(r['quantity'])==qty
        assert Decimal(r['notional'])+Decimal(r['fee'])<=b
def test_invalid_decimal_precision_and_overflow_are_rejected():
    bad=['-1','nan','1e-6','1.000000001','9999999999999999999999999','.','1.','']
    assert all('error' in r for r in native([size(price=x) for x in bad]+[size(precision=9)]))
def test_canonical_request_and_hmac_match_existing_documented_contract():
    c=dict(cmd='prepare',pair='AVNT/USD',quantity='123.4500',timestamp='1792040000000')
    r=native([c])[0]
    expected='pair=AVNT/USD&quantity=123.4500&side=BUY&timestamp=1792040000000&type=MARKET'
    assert r['body']==expected
    assert r['dummy_signature']==hmac.new(b'Jefe',expected.encode(),hashlib.sha256).hexdigest()
def test_unknown_order_never_retries_and_pending_is_not_filled():
    rows=[dict(cmd='lifecycle',events=['begin','timeout','begin']),dict(cmd='lifecycle',events=['begin','pending','begin']),dict(cmd='lifecycle',events=['begin','filled','begin'])]
    r=native(rows)
    assert r[0]['accepted']==[True,False] and r[0]['state']=='UNKNOWN'
    assert r[1]['accepted']==[True,False] and r[1]['state']=='PENDING'
    assert r[2]['accepted']==[True,False] and r[2]['state']=='FILLED'
def test_rolling_budget_reserves_exits_and_rejects_account_exhaustion():
    r=native([dict(cmd='rate',times_ms=[0]*21,limit=20,reserve=3,account_used=0),dict(cmd='rate',times_ms=[0],limit=20,reserve=3,account_used=28),dict(cmd='rate',times_ms=[0]*17+[60000],limit=20,reserve=3,account_used=0)])
    assert sum(r[0]['accepted'])==17
    assert r[1]['accepted']==[False]
    assert sum(r[2]['accepted'])==18
def test_stale_future_and_slow_prices_block_decision():
    base=dict(cmd='gate',now_ms=1000,feed_ms=950,quote_ms=950,quote_rtt_ms=100,clock_uncertainty_ms=20,equity='1000',cash='1000',gross='0',price='1',budget='100',precision=4,fee_ppm=1000)
    rows=[base,{**base,'feed_ms':700},{**base,'quote_ms':700},{**base,'feed_ms':1001},{**base,'quote_rtt_ms':301},{**base,'clock_uncertainty_ms':101},{**base,'gross':'999.99'}]
    r=native(rows)
    assert r[0]['allowed']
    assert all(not x['allowed'] for x in r[1:])
def test_order_ack_requires_success_and_filled_status_not_quantity():
    rows=[dict(cmd='ack',response={'Success':True,'OrderDetail':{'Status':'FILLED','FilledQuantity':1}}),dict(cmd='ack',response={'Success':True,'OrderDetail':{'Status':'PENDING'}}),dict(cmd='ack',response={'Success':True,'OrderDetail':{'Status':'CANCELED','FilledQuantity':100}}),dict(cmd='ack',response={'Success':False}),dict(cmd='ack',response={})]
    r=native(rows)
    assert [x['state'] for x in r]==['FILLED','PENDING','CANCELED','REJECTED','UNKNOWN']
def test_book_decoder_rejects_crossed_invalid_and_unknown_symbols():
    good={'stream':'avntusdt@bookTicker','data':{'u':123,'s':'AVNTUSDT','b':'0.1338','a':'0.1339','B':'100','A':'100'}}
    r=native([dict(cmd='book',packet=good),dict(cmd='book',packet={**good,'data':{**good['data'],'b':'0.2'}}),dict(cmd='book',packet={**good,'data':{**good['data'],'s':'OTHERUSDT'}})])
    assert r[0]['valid'] and not r[1]['valid'] and not r[2]['valid']

def test_invalid_native_state_event_cannot_mark_an_order_filled():
    import ctypes as C
    from research.book.gate.fast_exec.driver import Core
    core=Core();state=C.c_int(1)
    assert core.lib.state_event(C.byref(state),99)==-1
    assert state.value==1
def test_zero_depth_book_is_rejected():
    from research.book.gate.fast_exec.driver import Core,book
    p={'u':1,'s':'AVNTUSDT','b':'1','a':'1.01','B':'100','A':'0'}
    assert book(Core(),p)['valid'] is False

def test_latency_permission_is_independent_from_model_direction_and_uses_tail_budget():
    base=dict(cmd='health',feed_age_ms=10,quote_needed=False,quote_p95_ms=187,order_p95_ms=187,clock_uncertainty_ms=20,
        samples=30,unresolved_timeouts=0,opportunity_ms=500)
    r=native([base,{**base,'order_p95_ms':548},{**base,'samples':3},{**base,'unresolved_timeouts':1},{**base,'quote_needed':True},{**base,'opportunity_ms':0}])
    assert r[0]['allowed'] and not r[1]['allowed']
    assert not r[2]['allowed'] and not r[3]['allowed']
    assert r[4]['allowed'] and not r[5]['allowed']
