"""Frozen check on a newly inspected quote day; all six fixed strategies retained."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
from src.config import load_config
from src.models import get
from backtest.data import Market
from backtest.engine import decide
from src.validation.short_competition import QuoteBook,replay_targets,summarize
from research.book.price_trend.run import NAMES,ROOT
from research.book.price_trend.new_block.audit import sides,audit
OUT=ROOT/"results/book/20261010-price-new-block-v1"
START=pd.Timestamp("2026-10-09T00:00Z");END=pd.Timestamp("2026-10-10T00:00Z");ASSETS=["BTC","ETH","BNB","XRP"]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 if (OUT/"comparison.csv").exists():raise ValueError("Preserve prior results")
 freeze=json.loads(Path("research/book/price_trend/new_block/freeze.json").read_text())
 if any(sha(p)!=v for p,v in freeze["files"].items()):raise ValueError("Frozen model/quote changed")
 cfg=load_config();accepted=ROOT/"results/book/20261010-short-next-prefix-v3"
 pm=json.loads((accepted/"data_manifest.json").read_text())
 for name in ["hourly_close.parquet","hourly_qv.parquet"]:
  if sha(accepted/name)!=pm["files"][name]["sha256"]:raise ValueError("Prefix panel changed")
 hourly=pd.read_parquet(accepted/"hourly_close.parquet").loc[:START,[a+"USDT" for a in ASSETS]]
 quotes=[]
 for day in ["20261008","20261009"]:
  for chunk in pd.read_csv(ROOT/("results/book/scalp/quotes/"+day+".csv"),chunksize=200000):
   x=chunk[chunk.pair.isin([a+"/USD" for a in ASSETS])].copy()
   x["ts_utc"]=pd.to_datetime(x.ts_utc,utc=True)
   x=x[(x.ts_utc>=START-pd.Timedelta(seconds=60))&(x.ts_utc<=END)]
   quotes.append(x)
 q=pd.concat(quotes,ignore_index=True).sort_values(["ts_utc","pair"])
 if q.duplicated(["pair","ts_utc"]).any():raise ValueError("Duplicate quote")
 q.to_parquet(OUT/"accepted_quotes.parquet",index=False)
 grid=pd.date_range(START,END,freq="min")
 try:bid,ask,last,age=sides(q,grid,ASSETS)
 except ValueError as e:
  (OUT/"coverage_failure.json").write_text(json.dumps(dict(status="FAIL",reason=str(e),frozen=freeze),indent=2));raise
 prices=pd.DataFrame(last,index=grid,columns=[a+"USDT" for a in ASSETS])
 new=prices.loc[prices.index.minute==0].loc[START+pd.Timedelta(hours=1):]
 hourly=pd.concat([hourly,new])
 if hourly.index.duplicated().any():raise ValueError("Duplicate signal observation")
 hourly.to_parquet(OUT/"hourly_close.parquet")
 qv=pd.read_parquet(accepted/"hourly_qv.parquet").reindex(index=hourly.index,columns=hourly.columns)
 # Membership is fixed for this24hdiagnostic and only price is used by these models.
 uni=pd.Series({START:tuple(hourly.columns)})
 market=Market(hourly,qv,uni,pd.Series(.0005,index=hourly.columns))
 rules=json.loads((accepted/"exchange_info.json").read_text())["TradePairs"]
 rows=[];audits=[]
 for name in NAMES:
  model=get(name);previous=pd.Series(dtype=float);targets={}
  for t in pd.date_range(START,END-pd.Timedelta(hours=1),freq="4h"):
   w=decide(model,market,t,cfg["models"][name],previous);targets[t]=w;previous=w
  (OUT/(name+".targets.json")).write_text(json.dumps({str(t):w.to_dict() for t,w in targets.items()},indent=2))
  for scenario in ["actual","doubled","lag2h"]:
   scenario_quotes=q.copy();fee=.001
   if scenario=="doubled":
    mid=(q.max_bid+q.min_ask)/2;half=(q.min_ask-q.max_bid)/2
    scenario_quotes["max_bid"]=mid-2*half;scenario_quotes["min_ask"]=mid+2*half;fee=.002
   c=dict(assets=ASSETS,seed=100000.,fee=fee,proxy_half_spread=.0005,quote_max_age=30,minute_max_age=60,
      precisions={a:rules[a+"/USD"]["AmountPrecision"] for a in ASSETS},
      price_precisions={a:rules[a+"/USD"]["PricePrecision"] for a in ASSETS},
      min_order=1.,cash_buffer=.001,band=model.spec.band,order_spacing_seconds=10.,start=str(START),end=str(END))
   ev,path,dec,fail,cycles,ep=replay_targets(targets,QuoteBook(prices,scenario_quotes,c),c,120 if scenario=="lag2h" else 60)
   if fail:raise ValueError("Replay failure: "+str(fail[:2]))
   if (ev.source!="recorded_roostoo").any():raise ValueError("Proxy execution disallowed in this quote-day check")
   check=audit(ev,path,scenario_quotes,ASSETS,fee,c["seed"],ep);audits.append(dict(model=name,scenario=scenario,**check))
   stem=name+"-"+scenario
   ev.to_csv(OUT/(stem+".events.csv"),index=False);path.to_parquet(OUT/(stem+".path.parquet"),index=False)
   pd.DataFrame(cycles).to_csv(OUT/(stem+".cycles.csv"),index=False)
   (OUT/(stem+".endpoint.json")).write_text(json.dumps(ep,indent=2))
   p=path.copy();p.loc[p.index[-1],"equity"]=ep["full_cost_liquidated_equity"]
   row=summarize(name,ev,p,cycles,ep,c)
   row.update(scenario=scenario,net_short_usd=float(sum((r.quantity*r.price_usd if r.action=="Open Short" else -r.quantity*r.price_usd)-r.fee for r in ev.itertuples() if r.action in ("Open Short","Cover Short"))))
   rows.append(row);print(name,scenario,row["full_cost_liquidated_return"],flush=True)
 if any(sha(p)!=v for p,v in freeze["files"].items()):raise ValueError("Frozen input changed during check")
 pd.DataFrame(rows).to_csv(OUT/"comparison.csv",index=False)
 (OUT/"audit.json").write_text(json.dumps(dict(status="PASS",ledgers=audits,max_quote_age_seconds=float(age.max()),freeze=freeze,retrospective_newly_inspected=True),indent=2))
 text="# Newly inspected October9 quote-day results\n\n"
 text+="All six pre-frozen candidates, cash start100k, October9 00:00UTC to October10 00:00UTC (08:00HKT to08:00HKT). The data existed before this research protocol: this is a newly inspected retrospective block, not a prospective trial. One day cannot establish a reliable winner. Actual unsigned as-of bid/ask,0.10%fees,1hlag,4hdecisions, no activityguard. Fixed four-coin membership, no refreshed volume ranking.\n\n"
 text+="Short wins count only naturally completed full episodes after fees. Partial covers remain in their original episode; still-open episodes are censored from accuracy but included in terminal-cost net short PnL and total return. Censored episodes must not be called correct predictions.\n\n"
 text+="|Model|Scenario|Return|MDD|Short wins/closed|Censored|Net short $|Orders|\n|---|---|---|---|---|---|---|---|\n"
 for r in rows:
  closed=r["short_cycles_completed"];wins=round(closed*r["short_cycle_hit_rate"]) if closed else 0
  text+=f'|{r["model"]}|{r["scenario"]}|{r["full_cost_liquidated_return"]:+.3%}|{r["maximum_drawdown"]:.3%}|{wins}/{closed}|{r["short_cycles_censored"]}|{r["net_short_usd"]:+.2f}|{r["strategy_orders"]}|\n'
 text+="\nIndependent accounting and quote-age audits passed for all18ledgers. Doubled scenario charges0.20%fees and doubles each recorded halfspread; lag2h changes executionlagto2h. All three use identical fixed targets. No failures or candidates removed. This one-day diagnostic is not inserted into the228hlookalike score. CS requires longer evidence and is shown in the main historical score2 and price-based short tables.\n"
 (OUT/"RESULTS.md").write_text(text)
 Path("research/book/price_trend/new_block/RESULTS.md").write_text(text)
if __name__=="__main__":main()
