"""Frozen check on a newly inspected quote day; all six fixed strategies retained."""
from pathlib import Path
import hashlib,json,yaml
import numpy as np,pandas as pd
from src.config import load_config
from src.models import get
from backtest.data import Market
from backtest.engine import decide
from src.validation.short_competition import QuoteBook,replay_targets,summarize
from research.book.bear_exit.run import NAMES,ROOT
from research.book.price_trend.new_block.audit import sides,audit
from research.book.bear_exit.cutoff import executable_targets
from research.book.bear_exit.audit import terminal_audit
QCFG=yaml.safe_load(Path("research/book/bear_exit/quote_day/config.yaml").read_text());OUT=Path(QCFG["output"])
START=pd.Timestamp(QCFG["start"]);END=pd.Timestamp(QCFG["end"]);ASSETS=QCFG["assets"]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 if (OUT/"comparison.csv").exists():raise ValueError("Preserve prior results")
 freeze=json.loads(Path("research/book/bear_exit/quote_day/freeze.json").read_text())
 if any(sha(p)!=v for p,v in freeze["files"].items()):raise ValueError("Frozen model/quote changed")
 cfg=load_config();accepted=ROOT/"results/book/20261010-short-next-prefix-v3"
 pm=json.loads((accepted/"data_manifest.json").read_text())
 for name in ["hourly_close.parquet","hourly_qv.parquet"]:
  if sha(accepted/name)!=pm["files"][name]["sha256"]:raise ValueError("Prefix panel changed")
 hourly=pd.read_parquet(accepted/"hourly_close.parquet").loc[:START,[a+"USDT" for a in ASSETS]]
 rows=[];audits=[];original_hourly=hourly.copy()
 for tie in ["first","last"]:
  q=pd.read_parquet(ROOT/("results/book/20261010-price-new-block-v2/accepted_quotes-"+tie+".parquet"))
  hourly=original_hourly.copy()
  q.to_parquet(OUT/("accepted_quotes-"+tie+".parquet"),index=False)
  grid=pd.date_range(START,END,freq="min")
  try:bid,ask,last,age=sides(q,grid,ASSETS)
  except ValueError as e:
   (OUT/"coverage_failure.json").write_text(json.dumps(dict(status="FAIL",reason=str(e),frozen=freeze),indent=2));raise
  prices=pd.DataFrame(last,index=grid,columns=[a+"USDT" for a in ASSETS])
  new=prices.loc[prices.index.minute==0].loc[START+pd.Timedelta(hours=1):]
  hourly=pd.concat([hourly,new])
  if hourly.index.duplicated().any():raise ValueError("Duplicate signal observation")
  hourly.to_parquet(OUT/("hourly_close-"+tie+".parquet"))
  qv=pd.read_parquet(accepted/"hourly_qv.parquet").reindex(index=hourly.index,columns=hourly.columns)
  # Membership is fixed for this24hdiagnostic and only price is used by these models.
  uni=pd.Series({START:tuple(hourly.columns)})
  market=Market(hourly,qv,uni,pd.Series(QCFG["halfspread"],index=hourly.columns))
  rules=json.loads((accepted/"exchange_info.json").read_text())["TradePairs"]
  for name in NAMES:
   model=get(name);previous=pd.Series(dtype=float);targets={}
   for t in pd.date_range(START,END-pd.Timedelta(hours=1),freq=str(model.spec.rebalance_hours)+"h"):
    w=decide(model,market,t,cfg["models"][name],previous);targets[t]=w;previous=w
   (OUT/(name+"-"+tie+".targets.json")).write_text(json.dumps({str(t):w.to_dict() for t,w in targets.items()},indent=2))
   for scenario in ["actual","doubled","lag2h"]:
    scenario_quotes=q.copy();fee=QCFG["fee"]
    if scenario=="doubled":
     mid=(q.max_bid+q.min_ask)/2;half=(q.min_ask-q.max_bid)/2
     scenario_quotes["max_bid"]=mid-QCFG["double_multiplier"]*half;scenario_quotes["min_ask"]=mid+QCFG["double_multiplier"]*half;fee=QCFG["fee"]*QCFG["double_multiplier"]
    c=dict(assets=ASSETS,seed=QCFG["seed"],fee=fee,proxy_half_spread=QCFG["halfspread"],quote_max_age=QCFG["quote_age_seconds"],minute_max_age=QCFG["minute_age_seconds"],
       precisions={a:rules[a+"/USD"]["AmountPrecision"] for a in ASSETS},
       price_precisions={a:rules[a+"/USD"]["PricePrecision"] for a in ASSETS},
       min_order=QCFG["min_order"],cash_buffer=QCFG["cash_buffer"],band=model.spec.band,order_spacing_seconds=QCFG["order_spacing_seconds"],start=str(START),end=str(END))
    ev,path,dec,fail,cycles,ep=replay_targets(executable_targets(targets,END,QCFG["stress_lag_minutes"] if scenario=="lag2h" else QCFG["lag_minutes"]),QuoteBook(prices,scenario_quotes,c),c,QCFG["stress_lag_minutes"] if scenario=="lag2h" else QCFG["lag_minutes"])
    if fail:raise ValueError("Replay failure: "+str(fail[:2]))
    if (ev.source!="recorded_roostoo").any():raise ValueError("Proxy execution disallowed in this quote-day check")
    check=audit(ev,path,scenario_quotes,ASSETS,fee,c["seed"],ep)
    terminal=terminal_audit(ev,c["seed"],fee,ep["full_cost_liquidated_equity"])
    audits.append(dict(model=name,scenario=scenario,quote_order=tie,terminal=terminal,**check))
    stem=name+"-"+scenario+"-"+tie
    ev.to_csv(OUT/(stem+".events.csv"),index=False);path.to_parquet(OUT/(stem+".path.parquet"),index=False)
    pd.DataFrame(cycles).to_csv(OUT/(stem+".cycles.csv"),index=False)
    (OUT/(stem+".endpoint.json")).write_text(json.dumps(ep,indent=2))
    p=path.copy();p.loc[p.index[-1],"equity"]=ep["full_cost_liquidated_equity"]
    row=summarize(name,ev,p,cycles,ep,c)
    row.update(scenario=scenario,quote_order=tie,net_short_usd=float(sum((r.quantity*r.price_usd if r.action=="Open Short" else -r.quantity*r.price_usd)-r.fee for r in ev.itertuples() if r.action in ("Open Short","Cover Short"))))
    rows.append(row);print(name,scenario,row["full_cost_liquidated_return"],flush=True)
 if any(sha(p)!=v for p,v in freeze["files"].items()):raise ValueError("Frozen input changed during check")
 controls=[]
 for name in NAMES:
  same_targets=sha(OUT/(name+"-first.targets.json"))==sha(OUT/(name+"-last.targets.json"))
  for scenario in ["actual","doubled","lag2h"]:
   first=next(r for r in rows if r["model"]==name and r["scenario"]==scenario and r["quote_order"]=="first")
   last=next(r for r in rows if r["model"]==name and r["scenario"]==scenario and r["quote_order"]=="last")
   same_events=sha(OUT/(name+"-"+scenario+"-first.events.csv"))==sha(OUT/(name+"-"+scenario+"-last.events.csv"))
   controls.append(dict(model=name,scenario=scenario,targets_identical=same_targets,events_identical=same_events,return_difference=last["full_cost_liquidated_return"]-first["full_cost_liquidated_return"]))
 (OUT/"ordering_sensitivity.json").write_text(json.dumps(controls,indent=2))
 pd.DataFrame(rows).to_csv(OUT/"comparison.csv",index=False)
 (OUT/"audit.json").write_text(json.dumps(dict(status="PASS",ledgers=audits,max_quote_age_seconds=float(age.max()),freeze=freeze,retrospective_spent=True),indent=2))
 text="# Previously inspected October9 quote-day results\n\n"
 text+="Both earliest/latest-file-row controls for the unchanged guard plus three pre-frozen cost/exit candidates, cash start100k, October9 00:00UTC to October10 00:00UTC (08:00HKT to08:00HKT). The data existed before this research protocol: this block and earlier model outcomes were inspected previously. It is spent retrospective evidence, not a prospective trial. One day cannot establish a reliable winner. Actual unsigned as-of bid/ask,0.10%fees,1hlag,1hdecisions, no activityguard. Fixed four-coin membership, no refreshed volume ranking.\n\n"
 text+="Short wins count only naturally completed full episodes after fees. Partial covers remain in their original episode; still-open episodes are censored from accuracy but included in terminal-cost net short PnL and total return. Censored episodes must not be called correct predictions.\n\n"
 text+="|Model|Scenario|Quote order|Return|MDD|Short wins/closed|Censored|Net short $|Orders|\n|---|---|---|---|---|---|---|---|---|\n"
 for r in rows:
  closed=r["short_cycles_completed"];wins=round(closed*r["short_cycle_hit_rate"]) if closed else 0
  text+=f'|{r["model"]}|{r["scenario"]}|{r["quote_order"]}|{r["full_cost_liquidated_return"]:+.3%}|{r["maximum_drawdown"]:.3%}|{wins}/{closed}|{r["short_cycles_censored"]}|{r["net_short_usd"]:+.2f}|{r["strategy_orders"]}|\n'
 text+="\nIndependent accounting and quote-age audits passed for all24ledgers. Doubled scenario charges0.20%fees and doubles each recorded halfspread; lag2h changes executionlagto2h. All three use identical fixed target streams, with whole batches scheduled at/after the terminal mark remaining pending under the strict corrected cutoff rule. Terminal short quantities/cash are independently reconciled in every ledger. No failures or candidates removed. This one-day diagnostic is not inserted into the228hlookalike score. CS requires longer evidence and is shown in the main historical score2 and price-based short tables.\n"
 (OUT/"RESULTS.md").write_text(text)
 Path("research/book/bear_exit/quote_day/RESULTS.md").write_text(text)
if __name__=="__main__":main()
