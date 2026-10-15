"""Audit native runs and calculate explicitly conditional 50-hour fee scenarios."""
from pathlib import Path
from collections import Counter,deque
from decimal import Decimal
import json,subprocess,itertools,hashlib,os
from ..signal import BurstDetector
HERE=Path(__file__).parent
ROOT=Path("/home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-native-v2")
BIN=ROOT/"build/fast_exec_native"
CFG=HERE.parent/"config.json"
def batch(rows):
    p=subprocess.run([str(BIN),"protocol",str(CFG)],input="".join(json.dumps(r,separators=(",",":"))+"\n" for r in rows),capture_output=True,text=True,timeout=30)
    if p.returncode:raise RuntimeError(p.stderr)
    result=[json.loads(x) for x in p.stdout.splitlines()]
    if len(result)!=len(rows):raise AssertionError("missing native response")
    return result
def deterministic_cases():
    base={"cmd":"decision","now_ms":1000,"feed_ms":1000,"quote_ms":1000,"quote_rtt_ms":187,
      "uncertainty_ms":0,"order_p95_ms":187,"order_samples":30,"verified_order_stats":True,"opportunity_ms":500,
      "equity":"100000","cash":"100000","gross":"0","budget":"10","price":"1","external_bid":"1.004","precision":4,"account_ms":1000}
    cases=[];truth=[]
    for opportunity,delay,age,clock,verified in itertools.product([0,250,500,750,1000],[50,187,548,999,1000],[0,100,251],[0,50,101],[False,True]):
        total=age+delay+clock+5
        cases.append({**base,"opportunity_ms":opportunity,"order_p95_ms":delay,"feed_ms":1000-age,"uncertainty_ms":clock,"verified_order_stats":verified})
        truth.append(bool(verified and age<=250 and clock<=100 and opportunity>0 and total<1000 and total+50<opportunity))
    result=batch(cases);mismatch=[i for i,(r,t) in enumerate(zip(result,truth)) if r.get("allowed")!=t]
    record={"scope":"deterministic admission scenarios; frequencies are NOT market probabilities","cases":len(cases),
      "admitted":sum(x.get("allowed",False) for x in result),"rejected":sum(not x.get("allowed",False) for x in result),"oracle_mismatches":mismatch,
      "orders":0,"actual_order_latency_distribution_available":False}
    (ROOT/"admission_cases.json").write_text(json.dumps([{"input":a,"result":r,"expected":t} for a,r,t in zip(cases,result,truth)]))
    (ROOT/"admission_summary.json").write_text(json.dumps(record,indent=2))
    assert not mismatch,record
    return record
def capture(folder):
    path=ROOT/folder/"events.jsonl"
    detector=BurstDetector();latest={};calls=[];rtts=[];reason=Counter();books=0;expected=0;mismatch=[];errors=[];positions=[];replay_inputs=[];recorded_flags=[]
    for line in path.open():
        r=json.loads(line)
        if r.get("kind")=="book":
            d=r["packet"]["data"];symbol=d["s"];now=r["receive_mono_ns"]
            assert d["u"]>latest.get(symbol,0),"noncausal update"
            latest[symbol]=d["u"];bid=int(Decimal(d["b"])*100000000)
            signal=detector.update(symbol,d["u"],now,bid) is not None
            if bool(r["burst_episode"])!=signal:mismatch.append(books)
            expected+=signal;books+=1
            replay_inputs.append({"cmd":"book","now_ns":now,"packet":r["packet"]});recorded_flags.append(bool(r["burst_episode"]))
        elif r.get("kind")=="public_request":
            calls.append(r["send_mono_ns"])
            if r.get("success"):rtts.append(r["rtt_ns"]/1000000)
        elif r.get("kind")=="decision":reason[r["reason"]]+=1
        elif r.get("kind")=="feed_error":
            errors.append(r);detector=BurstDetector();latest={}
    # Per-source clock data; never force global log arrival ordering between threads.
    calls.sort();left=0;maximum=0
    for right,stamp in enumerate(calls):
        while stamp-calls[left]>=60000000000:left+=1
        maximum=max(maximum,right-left+1)
    rtts.sort()
    p=lambda q:rtts[min(len(rtts)-1,(len(rtts)*q+99)//100-1)] if rtts else None
    replayed=batch(replay_inputs)
    replay_mismatch=[i for i,(r,flag) in enumerate(zip(replayed,recorded_flags)) if not r.get("valid") or r.get("signal")!=flag]
    summary=json.loads((ROOT/folder/"summary.json").read_text())
    report={"folder":folder,"books":books,"python_expected_episodes":expected,"native_recorded_episodes":summary["burst_episodes"],
      "episode_disagreement_indices":mismatch,"native_replay_disagreement_indices":replay_mismatch,"requests":len(calls),"max_requests_rolling_minute":maximum,
      "minimum_request_spacing_ms":min((b-a)/1000000 for a,b in zip(calls,calls[1:])) if len(calls)>1 else None,
      "successful_public_rtt_median_ms":p(50),"successful_public_rtt_p95_ms":p(95),"feed_errors":errors,
      "decision_reasons":dict(reason),"orders":summary["orders"],"audit_ok":summary["audit_ok"],
      "quote_generation_time_known":False,"subsecond_roostoo_lag_identified":False,
      "source_sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    assert maximum<=15
    assert books==summary["books"] and expected==summary["burst_episodes"] and not mismatch and not replay_mismatch
    assert summary["orders"]==0 and summary["signed_calls"]==0
    (ROOT/folder/"independent_audit.json").write_text(json.dumps(report,indent=2))
    return report
def fee_scenarios():
    fee=Decimal(".001");friction=Decimal(".0005");budget=Decimal("1000");account=Decimal("100000")
    cases=[]
    for completed,retained_gap in itertools.product([0,10,50,100],[Decimal("-.001"),Decimal("0"),Decimal(".001"),Decimal(".003"),Decimal(".005")]):
        gross=retained_gap-friction
        pnl=budget*((1+gross)*(1-fee)/(1+fee)-1)*completed
        cases.append({"completed_round_trips_in_50h":completed,"assumed_entry_cash_budget_usd":str(budget),
          "assumed_account_equity_usd":str(account),"retained_gross_gap_before_additional_friction_bps":str(retained_gap*10000),
          "additional_round_trip_friction_bps":"5","entry_fee_bps":"10","exit_fee_bps":"10",
          "net_cash_gain_usd":str(pnl),"account_return_pct":str(pnl/account*100)})
    result={"status":"CONDITIONAL_SENSITIVITY_NOT_AN_EXPECTED_RETURN","hours":50,"cases":cases,
      "no_trade_incremental_return_pct":"0","forecast_return_pct":None,
      "break_even_retained_gross_gap_bps":str(((1+fee)/(1-fee)-1+friction)*10000),
      "unknown_penalty_not_applied":"20% reported penalty formula/trigger unknown; account drawdown penalty differs from haircut on positive profits",
      "why_no_forecast":"No verified EC2 order fills, tradable opportunity rate, joint feed/order timing or realized gap-retention distribution. A selected historical minute high is not a causal exit."}
    (ROOT/"return_50h_scenarios.json").write_text(json.dumps(result,indent=2))
    return result
def main():
    r={"admission":deterministic_cases(),"prospective":capture("prospective_final"),"return_50h":fee_scenarios()}
    (ROOT/"audit_summary.json").write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!="return_50h"},indent=2))
if __name__=="__main__":main()
