"""Retrospective fee/rebound attribution; never enters model selection."""
from pathlib import Path
import hashlib,json,yaml
import numpy as np,pandas as pd
from research.book.bear_selective.diagnostics.pnl import liquidation_curve
CFG=yaml.safe_load(Path("research/book/bear_selective/diagnostics/config.yaml").read_text())
ROOT=Path("/home/ubuntu/test/MiniMax");SOURCE=ROOT/"results/book/20261010-price-trend-v1";OUT=Path(CFG["output"])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 if (OUT/"input_before.json").exists():raise ValueError("Preserve previous diagnostic")
 cases=pd.read_parquet(SOURCE/"cases.parquet")
 selected=cases.index[np.logical_or.reduce([cases[p].to_numpy() for p in CFG["profiles"]])]
 manifest=ROOT/"results/book/20261010-intraday-short-v2/data_manifest.json"
 m=json.loads(manifest.read_text());data={};files=[manifest,SOURCE/"cases.parquet",Path(__file__),Path("research/book/bear_selective/diagnostics/pnl.py"),Path("research/book/bear_selective/diagnostics/config.yaml")]
 for symbol,z in m["datasets"].items():
  p=Path(z["path"])
  if sha(p)!=z["sha256"]:raise ValueError("Market input changed")
  data[symbol.removesuffix("USDT")]=pd.read_parquet(p,columns=["close"]).close;files.append(p)
 for t in selected:
  for name in CFG["models"]:
   stem=SOURCE/"cases"/t.strftime("%Y%m%dT%H%M")/(name+"-original-"+str(CFG["hours"]))
   files.extend([Path(str(stem)+".cycles.csv"),Path(str(stem)+".events.csv")])
 before={str(p.resolve()):sha(p) for p in files};(OUT/"input_before.json").write_text(json.dumps(before,indent=2))
 rows=[]
 for t in selected:
  for name in CFG["models"]:
   stem=SOURCE/"cases"/t.strftime("%Y%m%dT%H%M")/(name+"-original-"+str(CFG["hours"]))
   try:cycles=pd.read_csv(str(stem)+".cycles.csv")
   except pd.errors.EmptyDataError:continue
   ev=pd.read_csv(str(stem)+".events.csv");ev["time_utc"]=pd.to_datetime(ev.time_utc,utc=True)
   for c in cycles[cycles.status=="completed"].itertuples():
    start=pd.Timestamp(c.start);end=pd.Timestamp(c.end)
    fills=ev[(ev.asset==c.asset)&(ev.time_utc>=start)&(ev.time_utc<=end)]
    minutes=pd.date_range(start.ceil("min"),end.floor("min"),freq="min")
    grid=minutes.union(pd.DatetimeIndex(fills.time_utc)).sort_values()
    prices=data[c.asset];ix=prices.index.searchsorted(grid,side="right")-1
    if (ix<0).any() or ((grid-prices.index[ix]).total_seconds()>CFG["max_price_age_seconds"]).any():raise ValueError("Missing price")
    mid=pd.Series(prices.iloc[ix].to_numpy(),index=grid)
    curve=liquidation_curve(mid,fills,CFG["fee"],CFG["halfspread"])
    error=abs(curve.iloc[-1]-c.net_pnl)
    if error>CFG["money_tolerance_usd"]:raise ValueError("Cycle net PnL mismatch")
    fees=fills.fee.sum();gross=c.net_pnl+fees;notional=(fills.loc[fills.action=="Open Short","quantity"]*fills.loc[fills.action=="Open Short","price_usd"]).sum()
    rows.append(dict(case=str(t),model=name,asset=c.asset,start=str(start),end=str(end),hours=(end-start).total_seconds()/3600,
      net_pnl=c.net_pnl,gross_pnl=gross,fees=fees,opened_notional=notional,win=c.net_pnl>0,gross_win=gross>CFG["money_tolerance_usd"],
      fee_only_loss=(gross>CFG["money_tolerance_usd"] and c.net_pnl<=0),profit_surrender=(curve.max()>CFG["money_tolerance_usd"] and c.net_pnl<=0),
      max_sampled_net_profit=curve.max(),worst_sampled_net_pnl=curve.min(),net_return_on_total_opened_notional=c.net_pnl/notional,
      max_sampled_net_return_on_total_opened_notional=curve.max()/notional,reconciliation_error=error))
 out=pd.DataFrame(rows);out.to_csv(OUT/"completed_cycle_diagnostics.csv",index=False);summary=[]
 for profile in CFG["profiles"]:
  starts=set(map(str,cases.index[cases[profile]]))
  for name in CFG["models"]:
   x=out[(out.model==name)&out["case"].isin(starts)]
   summary.append(dict(profile=profile,model=name,completed=len(x),net_wins=int(x.win.sum()),gross_wins=int(x.gross_win.sum()),
      fee_only_losses=int(x.fee_only_loss.sum()),profitable_then_losing=int(x.profit_surrender.sum()),
      net_profit_usd=float(x.net_pnl.sum()),fees_usd=float(x.fees.sum()),median_hold_hours=float(x.hours.median())))
 summary=pd.DataFrame(summary);summary.to_csv(OUT/"summary.csv",index=False)
 after={p:sha(p) for p in before};(OUT/"input_after.json").write_text(json.dumps(after,indent=2))
 if before!=after:raise ValueError("Inputs changed")
 (OUT/"status.json").write_text(json.dumps(dict(status="PASS",completed_unique_cycles=len(out),max_pnl_error=float(out.reconciliation_error.max()),hindsight_only=True),indent=2))
 text="# Why earlier completed shorts lost\n\nEvery naturally completed short episode of all six original price models in both fixed25windowweak profiles at228h. These are spent retrospective diagnostics. Separate profiles can overlap; never add them as independent trials.\n\n"
 text+="Gross wins remove only explicit fees from actual fill PnL; spread stays charged. Fee-only loss means gross profit>0but net<=0. Profitable-then-losing means at least one sampled full-cost liquidation value was positive before actual completion at a loss. This latter value uses hindsight and immediate liquidation; it is not an achievable exit signal under1hdelay or a backtest of an exit rule. Multiple entries/partial covers use actual quantities and fees. All completed endpoint PnLs reconcile independently. Censored open shorts are excluded from this question, but remain included in the original portfolio returns.\n\n"
 text+="|Profile|Model|Net wins/closed|Gross wins|Fee-only losses|Profitable then losing|Median hold h|Fees USD|\n|---|---|---|---|---|---|---|---|\n"
 for z in summary.itertuples():text+=f"|{z.profile}|{z.model}|{z.net_wins}/{z.completed}|{z.gross_wins}|{z.fee_only_losses}|{z.profitable_then_losing}|{z.median_hold_hours:.2f}|{z.fees_usd:.2f}|\n"
 text+="\nThese measures diagnose possible cost/exit weaknesses. They neither enter the scoring formula nor justify selecting a model without the unchanged return/risk evidence checks. Full observations: completed_cycle_diagnostics.csv.\n"
 (OUT/"RESULTS.md").write_text(text);Path("research/book/bear_selective/diagnostics/RESULTS.md").write_text(text)
 print(summary.to_string(index=False),flush=True)
if __name__=="__main__":main()
