from research.book.gate.fast_exec.signal import BurstDetector,fee_room,decision
from research.book.gate.fast_exec.driver import Core
def test_burst_is_past_only_and_ignores_duplicate_updates():
    d=BurstDetector()
    assert not d.update('AVNTUSDT',1,0,10000000)
    assert not d.update('AVNTUSDT',1,1_100_000_000,10100000)
    r=d.update('AVNTUSDT',2,1_100_000_000,10100000)
    assert r and r['burst_bps']==100.
def test_no_signal_without_an_old_enough_reference_or_after_gap():
    d=BurstDetector()
    assert not d.update('AVNTUSDT',1,0,10000000)
    assert not d.update('AVNTUSDT',2,500_000_000,10100000)
    assert not d.update('AVNTUSDT',3,5_000_000_000,11000000)
def test_fee_room_uses_both_taker_sides_and_extra_costs():
    assert not fee_room(10020000,10000000)
    assert fee_room(10040000,10000000)
def test_subsecond_target_counts_quote_wait_and_reserves_ack_budget():
    c=Core()
    q={'success':True,'body':{'Data':{'AVNT/USD':{'MinAsk':1.0,'MaxBid':.999}}},'elapsed_ms':100,'end_mono_ns':1_000_000_000}
    b={'bid':101000000,'receive_mono_ns':1_000_000_000}
    info={'AVNT/USD':{'CanTrade':True,'AmountPrecision':4}}
    r=decision(c,'AVNTUSDT',0,1_000_000_000,b,q,20,info,1792040000000)
    assert not r['eligible'] and r['reason']=='preparation_deadline'
    r=decision(c,'AVNTUSDT',900_000_000,1_000_000_000,b,q,20,info,1792040000000)
    assert r['eligible'] and r['preparation_ms']==100
def test_untradable_coin_and_stale_feed_block_intent():
    c=Core();q={'success':True,'body':{'Data':{'AVNT/USD':{'MinAsk':1.0,'MaxBid':.999}}},'elapsed_ms':100,'end_mono_ns':1_000_000_000}
    b={'bid':101000000,'receive_mono_ns':1_000_000_000}
    assert not decision(c,'AVNTUSDT',900_000_000,1_000_000_000,b,q,20,{},1792040000000)['eligible']
    b['receive_mono_ns']=500_000_000
    assert not decision(c,'AVNTUSDT',900_000_000,1_000_000_000,b,q,20,{'AVNT/USD':{'CanTrade':True,'AmountPrecision':4}},1792040000000)['eligible']

def test_burst_fires_once_per_episode_and_rearms_after_condition_clears():
    d=BurstDetector()
    d.update('AVNTUSDT',1,0,10000000)
    assert d.update('AVNTUSDT',2,1_100_000_000,10100000)
    assert not d.update('AVNTUSDT',3,1_200_000_000,10100000)
    assert not d.update('AVNTUSDT',4,2_300_000_000,10100000)
    assert d.update('AVNTUSDT',5,3_400_000_000,10200000)
