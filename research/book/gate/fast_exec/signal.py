"""Frozen upward-burst hypothesis and deadline gates; no trading I/O."""
from collections import deque
from .driver import CFG,plain,prepare
class BurstDetector:
    def __init__(self):self.history={};self.ids={};self.active={}
    def update(self,symbol,update,now,bid):
        if update<=self.ids.get(symbol,0):return None
        self.ids[symbol]=update
        q=self.history.setdefault(symbol,deque())
        while q and now-q[0][0]>CFG['burst_max_reference_age_ms']*1_000_000:q.popleft()
        ref=None
        for t,p in q:
            if now-t>=CFG['burst_horizon_ms']*1_000_000:ref=(t,p)
            else:break
        q.append((now,bid))
        if ref is None or (bid-ref[1])*10000<ref[1]*CFG['burst_min_bps']:
            self.active[symbol]=False;return None
        if self.active.get(symbol,False):return None
        self.active[symbol]=True
        return {'reference_mono_ns':ref[0],'reference_bid':ref[1],'burst_bps':(bid-ref[1])/ref[1]*10000}
def fee_room(bid,ask):
    return bid>0 and ask>0 and (bid-ask)*10000>=ask*CFG['gap_min_bps'] and bid*(1000000-CFG['exit_fee_ppm'])>ask*(1000000+CFG['entry_fee_ppm']+CFG['extra_cost_ppm'])
def decision(core,symbol,start,now,b,q,clock_uncertainty,info,timestamp):
    result={'eligible':False,'preparation_ms':(now-start)/1e6,'actual_fill':False,'production_eligible':False}
    if now<start or now-start>=(CFG['target_filled_ms']-CFG['reserved_order_ack_ms'])*1_000_000:
        return {**result,'reason':'preparation_deadline'}
    pair=symbol.removesuffix('USDT')+'/USD';meta=info.get(pair,{})
    if meta.get('CanTrade') is not True or type(meta.get('AmountPrecision')) is not int or not 0<=meta['AmountPrecision']<=8:
        return {**result,'reason':'missing_or_unsupported_pair_metadata'}
    if not q.get('success'):return {**result,'reason':'quote_request_failed'}
    try:
        ask=core.parse(q['body']['Data'][pair]['MinAsk'])
        if not fee_room(b['bid'],ask):return {**result,'reason':'insufficient_net_fee_room'}
        request=dict(now_ms=now//1_000_000,feed_ms=b['receive_mono_ns']//1_000_000,quote_ms=q['end_mono_ns']//1_000_000,
            quote_rtt_ms=int(q['elapsed_ms']+.999),clock_uncertainty_ms=int(clock_uncertainty+.999),
            equity=CFG['paper_equity'],cash=CFG['paper_equity'],gross='0',price=plain(ask),
            budget=CFG['paper_order_budget'],precision=meta['AmountPrecision'],fee_ppm=CFG['entry_fee_ppm'])
        code,s=core.gate(request)
        if code:return {**result,'reason':'native_freshness_or_risk_gate','rejection_code':code}
        return {**result,'eligible':True,'reason':'shadow_intent_only','quantity':plain(s.quantity),
            'pair':pair,**prepare(pair,plain(s.quantity),str(timestamp))}
    except (ValueError,KeyError,TypeError):return {**result,'reason':'invalid_quote'}
