"""Replay spent public packets to verify one-trigger-per-burst semantics."""
from pathlib import Path
from collections import deque
import json
from .driver import OUT,Core,book,CFG
from .signal import BurstDetector
def main():
    core=Core();current=BurstDetector();history={};ids={};old=0;new=0;n=0
    for line in (OUT/'shadow_stream.jsonl').open():
        r=json.loads(line);b=book(core,r['packet'])
        if not b['valid']:continue
        s=b['symbol'];at=r['receive_mono_ns'];bid=b['bid']
        if b['update_id']<=ids.get(s,0):continue
        ids[s]=b['update_id'];n+=1
        q=history.setdefault(s,deque())
        while q and at-q[0][0]>CFG['burst_max_reference_age_ms']*1_000_000:q.popleft()
        ref=None
        for t,p in q:
            if at-t>=CFG['burst_horizon_ms']*1_000_000:ref=(t,p)
            else:break
        q.append((at,bid))
        if ref and (bid-ref[1])*10000>=ref[1]*CFG['burst_min_bps']:old+=1
        z=current.update(s,b['update_id'],at,bid)
        if z:
            assert z['reference_mono_ns']<=at-CFG['burst_horizon_ms']*1_000_000;new+=1
    result={'valid_unique_updates':n,'original_repeated_threshold_updates':old,'episode_triggers_after_fix':new,
        'method':'Same spent stream; same burst threshold and horizon; trigger only on entering a qualifying episode',
        'new_market_test':False,'profit_or_accuracy_measured':False,'lowered_thresholds':False}
    (OUT/'episode_replay.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
