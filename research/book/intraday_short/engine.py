"""Pure causal hypotheses and directional cash-start minute paper replay."""
from __future__ import annotations
from copy import deepcopy
import numpy as np
import pandas as pd
from src.execution.planner import Holdings,Quote,plan_orders,equity,current_weights,SHORT_OPEN,SHORT_CLOSE
from src.execution.paper import PaperBroker
FAMILIES=("volume_breakout","failed_rebound","bounce_fade","relative_weakness","flow_breakout")
def features(data,cfg):
 close=pd.DataFrame({s:z.close for s,z in data.items()})
 qv=pd.DataFrame({s:z.quote_volume for s,z in data.items()})
 low=pd.DataFrame({s:z.low for s,z in data.items()})
 buy=pd.DataFrame({s:z.taker_buy_quote for s,z in data.items()})
 if not close.index.is_unique or close.isna().any().any():raise ValueError("Incomplete prices")
 ret15=close/close.shift(cfg["signal_minutes"])-1;ret60=close/close.shift(cfg["breakout_minutes"])-1
 r=np.log(close).diff();sigma=r.rolling(cfg["breakout_minutes"],min_periods=cfg["breakout_minutes"]).std()*np.sqrt(cfg.get("risk_horizon_minutes",180))
 ema=close.ewm(span=cfg["ema_minutes"],adjust=False,min_periods=cfg["ema_minutes"]).mean()
 ema60=close.ewm(span=60,adjust=False,min_periods=60).mean()
 ret48=close/close.shift(cfg["warmup_minutes"])-1
 weak=(ret48.BTCUSDT<0)&(close.BTCUSDT<ema.BTCUSDT)
 # Breadth means positive one-hour return, with all selected endpoints required.
 weak &= (ret60>0).mean(axis=1)<=cfg.get("breadth_max",.4)
 ready=close.rolling(cfg["warmup_minutes"]+1,min_periods=cfg["warmup_minutes"]+1).count().eq(cfg["warmup_minutes"]+1)
 common=ready&(close<ema)&(sigma>=cfg["sigma_floor"])
 volume15=qv.rolling(cfg["signal_minutes"],min_periods=cfg["signal_minutes"]).sum()
 prior_volume=volume15.shift(cfg["signal_minutes"]).rolling(cfg.get("volume_baseline_minutes",240),min_periods=cfg.get("volume_baseline_minutes",240)).mean()
 prior_low=low.shift(1).rolling(cfg["breakout_minutes"],min_periods=cfg["breakout_minutes"]).min()
 breakout=(close<prior_low*(1-cfg["break_buffer"]))&(ret15<0)&(volume15>prior_volume*cfg["volume_multiple"])
 failed=(close.shift(cfg["signal_minutes"])/close.shift(3*cfg["signal_minutes"])-1>cfg["rebound_prior"])&(ret15<cfg["rebound_fail"])&(close.shift(cfg["signal_minutes"])>=ema60.shift(cfg["signal_minutes"]))&(close<ema60)
 bounce=(ret60.shift(cfg["signal_minutes"])>cfg["bounce_move"])&(ret15<0)
 relative=(ret60<cfg["relative_move"])&(ret60.sub(ret60.BTCUSDT,axis=0)<cfg["relative_excess"])&(ret15<0)
 flow=buy.rolling(cfg["signal_minutes"],min_periods=cfg["signal_minutes"]).sum()/volume15.replace(0,np.nan)
 raw=dict(zip(FAMILIES,[breakout,failed,bounce,relative,breakout&(flow<cfg["flow_max"])]))
 signals={name:(mask&common).mul(weak,axis=0).astype(bool) for name,mask in raw.items()}
 return {"close":close,"sigma":sigma,"strength":-ret60/sigma.replace(0,np.nan),"weak":weak,"signals":signals}
def choose_entries(signal,strength,active,cooldown,eq,minute,cfg,sigma=None,current_gross=0):
 out={};budget=max(0,cfg["max_short_gross"]-current_gross)
 candidates=sorted([s for s in signal.index if signal[s] and s not in active and minute>=cooldown.get(s,-1)],key=lambda s:(-float(strength.get(s,0) if pd.notna(strength.get(s,0)) else 0),s))
 for s in candidates:
  if len(active)+len(out)>=cfg["max_positions"]:break
  stop=max(cfg["stop_floor"],cfg["stop_sigma"]*float(sigma.get(s,0))) if sigma is not None else cfg["stop_floor"]
  weight=min(cfg["max_coin"],cfg["risk_fraction"]/stop,budget)
  if weight*eq<10:continue
  out[s]=weight;budget-=weight
 return out
def replay(close,signal,sigma,weak,cfg,rules,endpoints=None,strength=None):
 if close.isna().any().any() or (close<=0).any().any():raise ValueError("Invalid/missing quote")
 if not close.index.equals(signal.index) or not close.index.equals(sigma.index):raise ValueError("Grid mismatch")
 if not close.index.equals(pd.date_range(close.index[0],close.index[-1],freq="min")):raise ValueError("Minute coverage")
 endpoints=endpoints or [len(close)-1]
 prices=close.to_numpy();symbols=list(close.columns);pairs=[s.removesuffix("USDT")+"/USD" for s in symbols]
 svals=signal.to_numpy();vol=sigma.to_numpy();weakvals=weak.to_numpy()
 strength=signal.astype(float) if strength is None else strength
 strengthvals=strength.fillna(0).to_numpy()
 h=Holdings(float(cfg["seed"]));broker=PaperBroker(h,rules,cfg["fee"]);active={};cooldown={};pending={};events=[];cycles=[];open_min={};E=np.empty(len(close));G=np.empty(len(close))
 signed_cash=float(cfg["seed"]);signed_pos={p:0. for p in pairs};maxerr=0.;rejected=0
 def quotes(i):return {p:Quote(float(prices[i,j])*(1-cfg["halfspread"]),float(prices[i,j])*(1+cfg["halfspread"])) for j,p in enumerate(pairs)}
 def fill(i,actions):
  nonlocal signed_cash,maxerr,rejected
  q=quotes(i);eq=equity(h,q);targets=current_weights(h,q,eq)
  reasons={s:r for kind,s,r in actions}
  for kind,s,reason in actions:
   p=s.removesuffix("USDT")+"/USD"
   targets[p]=0 if kind=="close" else -active[s]["weight"]
  orders,notes=plan_orders(targets,h,q,rules,band=0.,fee=cfg["fee"],cash_buffer=.01,min_trade_usd=10)
  fills=broker.execute(orders,q)
  for f in fills:
   o=f["order"];s=o.pair.replace("/USD","USDT")
   if f["status"]!="FILLED":rejected+=1;raise ValueError("Rejected paper order")
   if o.kind not in (SHORT_OPEN,SHORT_CLOSE):raise ValueError("Short-only contract")
   qty,price,fee=f["qty"],f["price"],f["fee"]
   signed_cash+=(qty*price if o.kind==SHORT_OPEN else -qty*price)-fee
   signed_pos[o.pair]+=(-qty if o.kind==SHORT_OPEN else qty)
   event={"minute":i,"time":str(close.index[i]),"symbol":s,"kind":o.kind,"price":price,"qty":qty,"fee":fee,"reason":reasons.get(s,"unexpected")}
   events.append(event)
   if o.kind==SHORT_OPEN:
    stop=active[s]["stop"];active[s].update(entry=price,qty=qty,fee=fee,minute=i,stop=stop)
    open_min[s]=i
   else:
    a=active.pop(s);net=a["qty"]*(a["entry"]-price)-a["fee"]-fee
    cycles.append({"symbol":s,"entry_minute":a["minute"],"exit_minute":i,"entry_price":a["entry"],"exit_price":price,"qty":a["qty"],"net":net,"reason":reasons.get(s,"unexpected"),"censored":reasons.get(s)=="terminal"})
    cooldown[s]=i+cfg["cooldown_minutes"]
  maxerr=max(maxerr,abs(equity(h,q)-(signed_cash+sum(signed_pos[p]*q[p].ask for p in pairs))))
  if any(kind=="open" and s not in open_min for kind,s,_ in actions):raise ValueError("Intended opening did not fill")
 for i in range(len(close)):
  if i in pending:fill(i,pending.pop(i))
  asks=prices[i]*(1+cfg["halfspread"])
  eq=h.usd_free;gross=0.
  for j,p in enumerate(pairs):
   if p in h.shorts:
    pos=h.shorts[p];eq+=pos.collateral+pos.qty*(pos.entry-asks[j]);gross+=pos.qty*asks[j]
  indep=signed_cash+sum(signed_pos[p]*asks[j] for j,p in enumerate(pairs))
  maxerr=max(maxerr,abs(eq-indep))
  if eq<=0 or h.usd_free<-1e-6:raise ValueError("Invalid cash/equity")
  E[i]=eq;G[i]=gross/eq
  if i in endpoints:
   pass
  due=i+cfg["lag_minutes"]
  if due>=len(close):continue
  inflight={s for acts in pending.values() for _,s,_ in acts}
  closes=[]
  for j,s in enumerate(symbols):
   if s not in active or s in inflight or "entry" not in active[s]:continue
   a=active[s];move=prices[i,j]/a["entry"]-1
   reason=None
   if gross/eq>=1:reason="gross_guard"
   elif move>=a["stop"]:reason="stop"
   elif move<=-cfg["take_multiple"]*a["stop"]:reason="take"
   elif i-a["minute"]>=cfg["max_hold_minutes"]:reason="timeout"
   elif close.index[i].minute%cfg["signal_minutes"]==0 and not weakvals[i]:reason="regime_clear"
   if reason:closes.append(("close",s,reason))
  if closes:pending.setdefault(due,[]).extend(closes)
  if close.index[i].minute%cfg["signal_minutes"]==0 and weakvals[i] and not closes:
   candidates=choose_entries(pd.Series(svals[i],index=symbols),pd.Series(strengthvals[i],index=symbols),active,cooldown,eq,i,cfg,pd.Series(vol[i],index=symbols),gross/eq)
   actions=[]
   for s,w in candidates.items():
    if s in inflight:continue
    j=symbols.index(s);active[s]={"weight":w,"stop":max(cfg["stop_floor"],cfg["stop_sigma"]*float(vol[i,j]))}
    actions.append(("open",s,"signal"))
   if actions:pending.setdefault(due,[]).extend(actions)
 windows=[]
 for end in endpoints:
  ce=[c for c in cycles if c["exit_minute"]<=end]
  ee=[e for e in events if e["minute"]<=end]
  outstanding=[e for e in ee if e["kind"]==SHORT_OPEN and not any(c["symbol"]==e["symbol"] and c["entry_minute"]==e["minute"] for c in ce)]
  terminalfee=sum(e["qty"]*prices[end,symbols.index(e["symbol"])]*(1+cfg["halfspread"])*cfg["fee"] for e in outstanding)
  path=E[:end+1].copy();path[-1]-=terminalfee
  completed=[c for c in ce if not c["censored"]]
  terminalnet=sum(e["qty"]*(e["price"]-prices[end,symbols.index(e["symbol"])]*(1+cfg["halfspread"]))-e["fee"]-e["qty"]*prices[end,symbols.index(e["symbol"])]*(1+cfg["halfspread"])*cfg["fee"] for e in outstanding)
  net=sum(c["net"] for c in completed)+terminalnet
  if abs(path[-1]-cfg["seed"]-net)>1e-6:raise ValueError("Independent cycle PnL mismatch")
  windows.append({"end_minute":end,"return":path[-1]/cfg["seed"]-1,"MDD":float((1-path/np.maximum.accumulate(path)).max()),"completed":len(completed),"censored":len(outstanding),"wins":sum(c["net"]>0 for c in completed),"onsets":sum(e["kind"]==SHORT_OPEN for e in ee),"net_short_usd":net,"fees":sum(e["fee"] for e in ee)+terminalfee,"orders":len(ee)+len(outstanding),"mean_gross":G[:end+1].mean(),"max_gross":G[:end+1].max(),"turnover":(sum(e["qty"]*e["price"] for e in ee)+sum(e["qty"]*prices[end,symbols.index(e["symbol"])]*(1+cfg["halfspread"]) for e in outstanding))/cfg["seed"],"CS":np.nan,"CS_UTC":np.nan})
 if h.shorts:
  fill(len(close)-1,[("close",p.replace("/USD","USDT"),"terminal") for p in list(h.shorts)])
  E[-1]=equity(h,quotes(len(close)-1));G[-1]=0.
 if maxerr>1e-6:raise ValueError("Signed cash audit")
 return {"events":pd.DataFrame(events,columns=["minute","time","symbol","kind","price","qty","fee","reason"]),"cycles":pd.DataFrame(cycles),"windows":pd.DataFrame(windows),"equity":E,"gross":G,"audit":{"status":"PASS","max_equity_error":maxerr,"rejected":rejected}}
