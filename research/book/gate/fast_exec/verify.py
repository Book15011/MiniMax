"""Independent saved-observation pacing, duration and admission checks."""
from collections import deque,Counter
import json
from .driver import OUT,CFG
def main():
    public=[json.loads(x) for x in (OUT/'public_matrix.jsonl').read_text().splitlines()]
    shadow=[json.loads(x) for x in (OUT/'shadow_requests.jsonl').read_text().splitlines()]
    intents=[json.loads(x) for x in (OUT/'shadow_intents.jsonl').read_text().splitlines()]
    requests=sorted(public+shadow,key=lambda r:r['start_mono_ns']);queue=deque();maximum=0;issues=[]
    for r in requests:
        at=r['start_mono_ns']
        while queue and at-queue[0]>=60_000_000_000:queue.popleft()
        queue.append(at);maximum=max(maximum,len(queue))
        if r['end_mono_ns']<at:issues.append('negative duration')
        if abs((r['end_mono_ns']-at)/1e6-r['elapsed_ms'])>1e-6:issues.append('elapsed mismatch')
    if maximum>CFG['process_calls_per_minute']:issues.append('rolling request budget exceeded')
    gaps=[(b['start_mono_ns']-a['start_mono_ns'])/1e6 for a,b in zip(public,public[1:])]
    if min(gaps)<CFG['public_sample_interval_ms']-.1:issues.append('matrix pacing violated')
    for r in intents:
        if r['eligible'] and r['preparation_ms']>=CFG['target_filled_ms']-CFG['reserved_order_ack_ms']:issues.append('late intent allowed')
        if r['actual_fill'] or r['production_eligible']:issues.append('unsupported execution claim')
    result={'pass':not issues,'issues':issues,'public_matrix_requests':len(public),'shadow_requests':len(shadow),
        'total_public_roostoo_requests':len(requests),'maximum_requests_any_rolling_minute':maximum,
        'minimum_matrix_request_start_gap_ms':min(gaps),'public_matrix_failures':sum(not r['success'] for r in public),
        'shadow_intents_checked':len(intents),'shadow_reasons':dict(Counter(r['reason'] for r in intents)),
        'orders':0,'signed_calls':0,'actual_fills_verified':False,'independent_researcher_review':False}
    (OUT/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    if issues:raise SystemExit(1)
if __name__=='__main__':main()
