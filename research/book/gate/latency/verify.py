"""Independent cash/position reconstruction using saved quotes and round trips."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd,yaml
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT.parents[1]/"results/book/20261015-latency-gate-v1"
CFG=yaml.safe_load(Path(__file__).with_name("config.yaml").read_text())
def main():
    historical=json.loads((OUT/"historical_complete.json").read_text())
    prospective=json.loads((OUT/"prospective_complete.json").read_text())
    digest=hashlib.sha256(Path(__file__).with_name("core.py").read_bytes()).hexdigest()
    assert historical["source_sha256"]==prospective["source_sha256"]==digest
    R=np.load(OUT/"roostoo_history.npz",allow_pickle=False)
    F={kind:np.load(OUT/f"prospective_{kind}_inputs.npz",allow_pickle=False) for kind in prospective["sources"]}
    errors={"net_return":0.,"fees_usd":0.,"ledger_usd":0.,"trade_pnl_usd":0.,"drawdown":0.}
    checked=trades=0
    for p in sorted((OUT/"traces").glob("*.json")):
        meta=json.loads(p.read_text());s=meta["summary"];tr=meta["trips"]
        raw=np.load(p.with_suffix(".npz"),allow_pickle=False);t=raw["times"];E=raw["equity"]
        if s["source_family"]=="archive_tradeclose_roostoo_quotes":
            rt=R["times"]+s["clock_offset"];B,A=R["bid"],R["ask"]
        else:
            kind=s["source_family"].split("_")[1];rt=F[kind]["times"];B,A=F[kind]["bid"],F[kind]["ask"]
        ix=np.searchsorted(rt,t);assert np.array_equal(rt[ix],t)
        B,A=B[ix],A[ix];cash_change=np.zeros(len(t));holding=np.zeros(len(t))
        fees=0.;pnls=[];rate=CFG["signal"]["taker"]*(2 if s["scenario"]=="double_fees" else 1)
        for r in tr:
            j=CFG["symbols"].index(r["coin"]);i=int(np.searchsorted(t,r["entry_time"]));k=int(np.searchsorted(t,r["exit_time"]))
            q=r["qty"];sd=r["side"];entry=A[i,j] if sd>0 else B[i,j];exit=B[k,j] if sd>0 else A[k,j]
            assert entry==r["entry_price"] and exit==r["exit_price"]
            valid=np.isfinite(B[:,j])&np.isfinite(A[:,j])&(B[:,j]>0)&(A[:,j]>=B[:,j])
            eligible=np.flatnonzero(valid&(t>=r["signal_time"]+s["order_delay"])&(t>r["signal_time"]))
            assert len(eligible) and eligible[0]==i,"Not the first eligible delayed quote"
            enfee=q*entry*rate;exfee=q*exit*rate;fees+=enfee+exfee
            pnl=sd*q*(exit-entry)-enfee-exfee;pnls.append(pnl)
            errors["trade_pnl_usd"]=max(errors["trade_pnl_usd"],abs(pnl-r["net_pnl"]))
            cash_change[i]+=-sd*q*entry-enfee;cash_change[k]+=sd*q*exit-exfee
            marks=B[i:k,j] if sd>0 else A[i:k,j]
            holding[i:k]=sd*q*marks-q*marks*rate
            assert i<=k and r["entry_time"]>r["signal_time"]
        nav=CFG["signal"]["capital"]+cash_change.cumsum()+holding
        expected=np.r_[CFG["signal"]["capital"],nav]
        assert len(expected)==len(E)
        if s["terminal_priced"]:
            errors["ledger_usd"]=max(errors["ledger_usd"],float(np.nanmax(np.abs(expected-E))))
            net=nav[-1]/CFG["signal"]["capital"]-1
            errors["net_return"]=max(errors["net_return"],abs(net-s["return"]))
            assert abs(sum(pnls)/CFG["signal"]["capital"]-s["return"])<1e-10
        if s["complete_marks"]:
            dd=float((1-expected/np.maximum.accumulate(expected)).max())
            errors["drawdown"]=max(errors["drawdown"],abs(dd-s["mdd"]))
        errors["fees_usd"]=max(errors["fees_usd"],abs(fees-s["fees_usd"]))
        if pnls:assert np.isclose((np.array(pnls)>0).mean(),s["win_rate"],atol=1e-12)
        assert s["trades"]==len(tr) and not s["production_eligible"] and not s["actual_fill_verified"]
        checked+=1;trades+=len(tr)
    assert checked==historical["runs"]+prospective["runs"]
    assert errors["ledger_usd"]<1e-6 and errors["fees_usd"]<1e-6 and errors["trade_pnl_usd"]<1e-6
    assert errors["net_return"]<1e-10 and errors["drawdown"]<1e-10
    audit={"status":"PASS","runs":checked,"simulated_roundtrips":trades,"max_errors":errors,
           "source_sha256":digest,"actual_execution_verified":False,"independent_researcher_review":False}
    (OUT/"independent_verification.json").write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2))
if __name__=="__main__":main()
