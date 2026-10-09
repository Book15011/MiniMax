"""Full-minute valuation of the frozen clone; independent signed-cash audit."""
from pathlib import Path
import hashlib,json,sys
import numpy as np,pandas as pd
from src.validation.short_competition import QuoteBook,observed_path,summarize
from prefix_audit import quote_arrays,account_events
ROOT=Path("/home/ubuntu/test/MiniMax");SOURCE=ROOT/"results/book/20261010-short-next-prefix-v3"
OUT=ROOT/"results/book/20261010-clone-prefix-v1"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=json.loads((OUT/"prediction_manifest.json").read_text())
for p,h in m["source_pins"].items():
 if sha(p)!=h:raise ValueError("Frozen clone input changed")
if (OUT/"valuation_audit.json").exists():raise ValueError("Preserve existing valuation")
cfg=json.loads((SOURCE/"prefix_audit.json").read_text())["config"]
assets=m["base"]["assets"];cfg={**cfg,"assets":assets}
raw=pd.read_parquet(SOURCE/"prefix_minutes.parquet");raw=raw[raw.symbol.isin([a+"USDT" for a in assets])]
prices=raw.pivot(index="timestamp",columns="symbol",values="close").sort_index()
quotes=pd.read_parquet(SOURCE/"prefix_quotes.parquet");quotes=quotes[quotes.pair.isin([a+"/USD" for a in assets])]
quotes["ts_utc"]=pd.to_datetime(quotes.ts_utc,utc=True)
book=QuoteBook(prices,quotes,cfg)
ev=pd.read_csv(OUT/"prediction_events.csv");ev["time_utc"]=pd.to_datetime(ev.time_utc,utc=True)
ev["trade_id"]=["C"+str(i+1).zfill(3) for i in range(len(ev))]
fees=dict(zip(ev.trade_id,ev.fee))
events,path,endpoint,cycles=observed_path(ev,book,cfg,fees)
endpoint["fee_status"]="Exact frozen PaperBroker fill fees"
endpoint["accounting"]="Frozen predicted fills, signed-cash valuation; broker cash/gross separately audited in prediction study"
name="frozen_calibrated_reconstruction"
events.to_csv(OUT/"clone_prefix_events.csv",index=False);path.to_csv(OUT/"clone_prefix_equity.csv",index=False)
pd.DataFrame(cycles).to_csv(OUT/"clone_prefix_short_cycles.csv",index=False)
(OUT/"clone_prefix_endpoint.json").write_text(json.dumps(endpoint,indent=2))
summary=summarize(name,events,path,cycles,endpoint,cfg)
pd.DataFrame([summary]).to_csv(OUT/"prefix_comparison.csv",index=False)
# Independent cumulative signed-notional and position reconstruction.
cash=cfg["seed"]+np.cumsum(events.action.map({"Buy Long":-1,"Sell Long":1,"Open Short":1,"Cover Short":-1}).to_numpy()*events.quantity.to_numpy()*events.price_usd.to_numpy()-events.fee.to_numpy())
where=np.searchsorted(pd.DatetimeIndex(events.time_utc).asi8,pd.DatetimeIndex(path.time_utc).asi8,side="right")-1
cashpath=np.where(where>=0,cash[np.maximum(where,0)],cfg["seed"])
q=quote_arrays(path.time_utc,assets,prices,quotes,cfg);equity=cashpath.copy();gross=np.zeros(len(path))
for a in assets:
 long=np.cumsum(np.where((events.asset==a)&(events.action=="Buy Long"),events.quantity,np.where((events.asset==a)&(events.action=="Sell Long"),-events.quantity,0.)))
 short=np.cumsum(np.where((events.asset==a)&(events.action=="Open Short"),events.quantity,np.where((events.asset==a)&(events.action=="Cover Short"),-events.quantity,0.)))
 lp=np.where(where>=0,long[np.maximum(where,0)],0.);sp=np.where(where>=0,short[np.maximum(where,0)],0.)
 assert np.allclose(lp-sp,path[a],rtol=0,atol=1e-8)
 equity+=lp*q[a]["bid"]-sp*q[a]["ask"];gross+=lp*q[a]["bid"]+sp*q[a]["ask"]
assert np.allclose(equity,path.equity,rtol=0,atol=1e-6)
assert np.allclose(gross,path.gross,rtol=0,atol=1e-6)
assert np.allclose(cashpath,path.signed_cash,rtol=0,atol=1e-6)
assert abs((equity[-1]-cfg["fee"]*gross[-1])/cfg["seed"]-1-summary["full_cost_liquidated_return"])<1e-12
assert path.time_utc.iloc[0]==pd.Timestamp(cfg["start"]) and path.time_utc.iloc[-1]==pd.Timestamp(cfg["end"])
proof={"status":"PASS","return":summary["full_cost_liquidated_return"],"MDD":summary["maximum_drawdown"],
 "minute_rows":len(path),"prediction_same_as_original":m["prediction_sha256"]==m["original_prediction_sha256"],
 "rejections":m["rejections"],"source_pins":{str(p):sha(p) for p in [OUT/"prediction_manifest.json",SOURCE/"fine_data_manifest.json",OUT/"clone_prefix_events.csv",OUT/"clone_prefix_equity.csv",Path(__file__)]},
 "limits":"Retrospectively fitted five sessions; frozen five-minute batching retained, while short models use one-hour lag and ten-second order spacing. Minute execution clock afterOct9 00UTC explicitly ticker-assisted; valuation uses recorded quotes. No85% or prospective-edge claim."}
(OUT/"valuation_audit.json").write_text(json.dumps(proof,indent=2))
print(json.dumps(proof,indent=2),flush=True)
