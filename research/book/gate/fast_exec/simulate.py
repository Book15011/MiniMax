"""Deterministic admission/fault cases; not a strategy-profit simulator."""
from itertools import product
from pathlib import Path
import json
from .driver import Core,execute,OUT,CFG
def main():
    core=Core();rows=[]
    for window,delay,quote,age,clock in product([0,250,500,750,1000],[50,187,548,1000,4000],[False,True],[10,300],[20,200]):
        r=dict(cmd='health',feed_age_ms=age,quote_needed=quote,quote_p95_ms=delay,order_p95_ms=delay,
            clock_uncertainty_ms=clock,samples=30,unresolved_timeouts=0,opportunity_ms=window)
        result=execute(core,r)
        if result['allowed']:
            assert result['predicted_total_ms']<CFG['target_filled_ms']
            assert result['predicted_total_ms']+CFG['health_safety_margin_ms']<window
            assert age<=CFG['feed_max_receipt_age_ms'] and clock<=CFG['clock_max_uncertainty_ms']
        rows.append({**r,**result})
    for event in ['timeout','pending','filled']:
        r=execute(core,{'cmd':'lifecycle','events':['begin',event,'begin']})
        assert r['accepted']==[True,False]
    summary={'pass':True,'timing_cases':len(rows),'admitted_cases':sum(r['allowed'] for r in rows),
        'expired_or_unqualified_cases':sum(not r['allowed'] for r in rows),'duplicate_order_state_cases':3,
        'profitability_measured':False,'actual_fills':0,'case_frequencies_are_probabilities':False,
        'boundary':'Pure admission contracts at fixed synthetic delays; not network timing or live fill proof'}
    (OUT/'timing_simulation.json').write_text(json.dumps(summary,indent=2))
    (OUT/'timing_simulation_cases.json').write_text(json.dumps(rows,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
