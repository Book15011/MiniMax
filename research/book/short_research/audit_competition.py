"""Independent signed-cash and fill-causality audit for saved competition artifacts."""
from pathlib import Path
from decimal import Decimal
import json,hashlib
import pandas as pd

out=Path("/home/ubuntu/test/MiniMax/results/book/20261009-short-competition")
names=["book_short_trend","book_short_rebound","book_short_breakdown","original_frozen_clone","observed_literal_ledger"]
report={"checks":[],"source":"independent signed cash from event notional and fees; no planner/broker math imported"}
def check(name,passed,**values):report["checks"].append({"name":name,"passed":bool(passed),**values})
for name in names:
    ev=pd.read_csv(out/(name+"_events.csv"))
    endpoint=json.loads((out/(name+"_endpoint.json")).read_text())
    q=endpoint["endpoint_quotes"];stage=ev[ev.phase!="terminal"]
    def recompute(rows):
        cash=Decimal("100000");long={};short={}
        for _,r in rows.iterrows():
            a=r.asset;qty=Decimal(str(r.quantity));value=qty*Decimal(str(r.price_usd));cash-=Decimal(str(r.fee))
            if r.action=="Buy Long":cash-=value;long[a]=long.get(a,Decimal(0))+qty
            if r.action=="Sell Long":cash+=value;long[a]=long.get(a,Decimal(0))-qty
            if r.action=="Open Short":cash+=value;short[a]=short.get(a,Decimal(0))+qty
            if r.action=="Cover Short":cash-=value;short[a]=short.get(a,Decimal(0))-qty
        eq=cash+sum(v*Decimal(str(q[a+"/USD"]["bid"])) for a,v in long.items())-sum(v*Decimal(str(q[a+"/USD"]["ask"])) for a,v in short.items())
        gross=sum(v*Decimal(str(q[a+"/USD"]["bid"])) for a,v in long.items())+sum(v*Decimal(str(q[a+"/USD"]["ask"])) for a,v in short.items())
        return float(eq),float(gross)
    marked,gross=recompute(stage)
    common=marked-.001*gross
    check(name+" marked equity independent cash",abs(marked-endpoint["marked_equity"])<1e-6,error_usd=marked-endpoint["marked_equity"])
    check(name+" common full liquidation independent cash",abs(common-endpoint["full_cost_liquidated_equity"])<1e-6,error_usd=common-endpoint["full_cost_liquidated_equity"])
    if name!="observed_literal_ledger":
        actual,_=recompute(ev)
        check(name+" practical liquidation independent cash",abs(actual-endpoint["liquidated_equity"])<1e-6,error_usd=actual-endpoint["liquidated_equity"])
        age=pd.to_datetime(stage.time_utc,utc=True)-pd.to_datetime(stage.source_time,utc=True)
        check(name+" quote source never future",bool((age.dt.total_seconds()>=0).all()))
        lag=pd.to_datetime(stage.time_utc,utc=True)-pd.to_datetime(stage.decision_utc,utc=True)
        minimum=300 if name=="original_frozen_clone" else 3600
        check(name+" declared execution lag",bool((lag.dt.total_seconds()>=minimum).all()))
    if name.startswith("book_short") or name=="original_frozen_clone":
        previous=out/"revisions/wrapper-v1"
        for suffix in ["_events.csv","_short_cycles.csv"]:
            p=out/(name+suffix);old=previous/(name+suffix)
            same=hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256(old.read_bytes()).hexdigest()
            check(name+suffix+" wrapper identity",same)
        current=pd.read_csv(out/(name+"_equity.csv"));old=pd.read_csv(previous/(name+"_equity.csv"))
        check(name+" equity path wrapper identity",current.equity.equals(old.equity))
# Existing frozen clone's original published execution fields must remain identical.
old=pd.read_csv("/home/ubuntu/test/MiniMax/results/book/20261009-observed-baseline/broker_events.csv")
new=pd.read_csv(out/"original_frozen_clone_events.csv");new=new[new.phase=="strategy"].reset_index(drop=True)
columns=["asset","action","quantity","price_usd","time_utc","decision_utc","fee"]
check("original frozen clone old execution fields identity",old[columns].equals(new[columns]))
provenance=json.loads((out/"provenance.json").read_text())
check("complete close warmup",provenance["warmup_close_missing"]==0,rows=provenance["warmup_before_start_rows"])
check("complete volume warmup",provenance["warmup_volume_missing"]==0)
check("no execution or valuation failures",sum(provenance["failure_counts"].values())==0)
a=pd.read_csv(out/"comparison.csv");old=pd.read_csv(out/"revisions/wrapper-v1/comparison.csv")
fields=["marked_return","liquidated_return","maximum_drawdown","strategy_orders","fees","terminal_fees","notional_turnover_seed"]
check("first pass primary metrics unchanged",a[fields].equals(old[fields]))
check("no completed short hit-rate invented",bool(a.short_cycle_hit_rate.isna().all()) and bool((a.short_cycles_completed==0).all()))
report["passed"]=all(x["passed"] for x in report["checks"])
report["count"]=len(report["checks"])
(out/"independent_audit.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
if not report["passed"]:raise SystemExit(1)
