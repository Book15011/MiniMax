"""Pure causal paper model. No filesystem, clock, network or account imports."""
import numpy as np
import pandas as pd
from research.book.gate.simulator_edge.money import quantity

def causal_asof(target,available,values,max_age):
    target=np.asarray(target,float);available=np.asarray(available,float);values=np.asarray(values,float)
    if len(available)==0:return np.full((len(target),values.shape[1]),np.nan)
    if np.any(np.diff(available)<0):raise ValueError("availability must be sorted")
    pos=np.searchsorted(available,target,side="right")-1
    safe=np.maximum(pos,0);out=values[safe].copy()
    out[(pos<0)|(target-available[safe]>max_age)]=np.nan
    return out

def gaps(t,bid,ask,external_bid,external_ask,p):
    mid=(bid+ask)/2;emid=(external_bid+external_ask)/2
    valid=np.isfinite(mid)&np.isfinite(emid)&(bid>0)&(ask>=bid)&(external_bid>0)&(external_ask>=external_bid)
    ratio=np.divide(mid,emid,out=np.full_like(mid,np.nan),where=valid)
    ix=pd.to_datetime(t,unit="s",utc=True)
    basis=pd.DataFrame(ratio,index=ix).rolling(str(p["basis_seconds"])+"s",closed="left",
                                              min_periods=p["min_basis_observations"]).median().to_numpy()
    basis[np.asarray(t)<t[0]+p["basis_seconds"]]=np.nan
    long=external_bid*basis/ask-1;short=bid/(external_ask*basis)-1
    long[~valid]=np.nan;short[~valid]=np.nan
    return long,short,basis

def simulate(t,bid,ask,long_gap,short_gap,rules,coins,candidate,p,delay,start,end,fee_multiplier=1):
    t=np.asarray(t,float)
    if np.any(np.diff(t)<=0):raise ValueError("quotes must be strictly increasing")
    keep=(t>=start)&(t<=end);t=t[keep]
    bid,ask,long_gap,short_gap=[np.asarray(x,float)[keep] for x in [bid,ask,long_gap,short_gap]]
    if len(t)==0:raise ValueError("empty interval")
    fee=p["taker"]*fee_multiplier;cash=float(p["capital"]);q=0.;side=0;j=None;opened=None
    pending=None;next_entry=-np.inf;trips=[];fees=0.;attempts=fills=expired=0
    equity=[];gross=[];orders=[];entry_wait=[];exit_wait=[]
    def valid(i,k):
        return np.isfinite([bid[i,k],ask[i,k]]).all() and 0<bid[i,k]<=ask[i,k]
    def close(i,terminal=False):
        nonlocal cash,q,side,j,opened,fees,next_entry
        px=bid[i,j] if side>0 else ask[i,j];f=q*px*fee
        cash+=side*q*px-f;fees+=f
        trips.append({**opened,"exit_time":float(t[i]),"exit_price":float(px),"exit_fee":f,
                      "net_pnl":cash-opened["cash_before"],"terminal":terminal})
        orders.append(float(t[i]));q=0.;side=0;j=None;opened=None
        next_entry=t[i]+p["cooldown_seconds"]
    for i,now in enumerate(t):
        if pending is not None and now>=pending["due"] and i>pending["i"]:
            if pending["kind"]=="entry":
                k=pending["coin"]
                if valid(i,k):
                    sd=pending["side"];px=ask[i,k] if sd>0 else bid[i,k]
                    exp=p["long_exposure"] if sd>0 else p["short_exposure"]
                    qty=quantity(cash*exp,px,rules[coins[k]]["AmountPrecision"],fee)
                    if qty*px>=rules[coins[k]].get("MiniOrder",p["min_order"]):
                        before=cash;f=qty*px*fee;cash-=sd*qty*px+f;fees+=f
                        q=qty;side=sd;j=k;fills+=1;orders.append(float(now));entry_wait.append(now-pending["signal_time"])
                        opened={"coin":coins[j],"side":side,"qty":q,"entry_time":float(now),"entry_price":float(px),
                                "entry_fee":f,"cash_before":before,"entry_cash_after":cash,
                                "signal_time":pending["signal_time"],"signal_gap":pending["gap"]}
                    pending=None
            elif valid(i,j):
                exit_wait.append(now-pending["signal_time"]);close(i);pending=None
        if q and pending is None and valid(i,j):
            gap=long_gap[i,j] if side>0 else short_gap[i,j]
            px=bid[i,j] if side>0 else ask[i,j]
            adverse=side*(px/opened["entry_price"]-1)
            if (np.isfinite(gap) and gap<=0) or now-opened["entry_time"]>=p["hold_seconds"] or adverse<=-p["stop_fraction"]:
                pending={"kind":"exit","due":now+delay,"i":i,"signal_time":float(now)}
        if not q and pending is None and now>=next_entry:
            best=None
            for sd in candidate["directions"]:
                signals=long_gap[i] if sd>0 else short_gap[i]
                for k in range(len(coins)):
                    g=signals[k]
                    if valid(i,k) and np.isfinite(g) and g>=candidate["threshold"]:
                        key=(float(g),-k,sd)
                        if best is None or key>best[0]:best=(key,k,sd)
            if best is not None:
                _,k,sd=best;attempts+=1
                pending={"kind":"entry","coin":k,"side":sd,"gap":best[0][0],"due":now+delay,"i":i,"signal_time":float(now)}
        if q:
            nav=cash+side*q*(bid[i,j] if side>0 else ask[i,j])-q*(bid[i,j] if side>0 else ask[i,j])*fee if valid(i,j) else np.nan
            notional=q*(bid[i,j] if side>0 else ask[i,j]) if valid(i,j) else np.nan
            equity.append(nav);gross.append(notional/nav if nav>0 else np.nan)
        else:equity.append(cash);gross.append(0.)
    if pending and pending["kind"]=="entry":expired+=1
    terminal_priced=not q or valid(len(t)-1,j)
    if q and terminal_priced:close(len(t)-1,True);equity[-1]=cash;gross[-1]=0.
    E=np.asarray([p["capital"]]+equity,float);G=np.asarray([0.]+gross,float)
    net=None if not terminal_priced else cash/p["capital"]-1
    dd=float((1-E/np.maximum.accumulate(E)).max()) if np.isfinite(E).all() else None
    pnl=np.array([x["net_pnl"] for x in trips]);wins=pnl[pnl>0];loss=pnl[pnl<0]
    maxcalls=0
    for k,s in enumerate(orders):
        maxcalls=max(maxcalls,2+int(np.sum((np.array(orders)>=s)&(np.array(orders)<s+60))))
    return {"candidate":candidate["name"],"return":net,"mdd":dd,"trades":len(trips),"entry_attempts":attempts,"entry_fills":fills,
            "expired_entries":expired,"fill_rate":fills/attempts if attempts else None,
            "win_rate":float((pnl>0).mean()) if len(pnl) else None,
            "avg_win_usd":float(wins.mean()) if len(wins) else None,
            "avg_loss_usd":float(loss.mean()) if len(loss) else None,"ev_usd":float(pnl.mean()) if len(pnl) else None,
            "fees_usd":fees,"terminal_priced":terminal_priced,"complete_marks":bool(np.isfinite(E).all()),
            "max_marked_gross":float(np.nanmax(G)),"max_modeled_order_calls_per_minute":maxcalls,
            "mean_entry_wait_seconds":float(np.mean(entry_wait)) if entry_wait else None,
            "mean_exit_wait_seconds":float(np.mean(exit_wait)) if exit_wait else None,
            "actual_fill_verified":False,"capacity_verified":False,"latency_penalty":True,
            "production_eligible":False,"trips":trips,"_equity":E,"_times":t}

def penalized_round(gain,treatment,current=-.16):
    equity=(1+current)*(1+gain);r=equity-1
    if treatment=="none":return r
    if treatment=="subtract_20pp":return r-.2
    if treatment=="equity_haircut20":return .8*equity-1
    if treatment=="round_profit_haircut20":return .8*r if r>0 else r
    if treatment=="incremental_profit_haircut20":return (1+current)*(1+(gain*.8 if gain>0 else gain))-1
    raise ValueError(treatment)
