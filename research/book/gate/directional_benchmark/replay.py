"""Pure received-quote simulator; explicit lower-bound maker eligibility, no live execution."""
from collections import deque
from decimal import Decimal as D
import math
import numpy as np
from .broker import Portfolio,Order,role,sized
def simulate(times,bids,asks,coins,signals,rules,cfg,kind="A",maker=False,delay=6,fraction=1):
    t=np.asarray(times,float);bids=np.asarray(bids,float);asks=np.asarray(asks,float)
    if np.any(np.diff(t)<=0):raise ValueError("time ordering")
    p=Portfolio(D(str(cfg["paper_starting_equity"])));initial=p.cash
    lookup={c:i for i,c in enumerate(coins)};pending=[];calls=deque();peak=float(initial);dd=0;navs=[];fills=[];errors=[]
    counts={"signals":0,"submitted":0,"expired":0,"quota_rejected":0,"size_or_cash_rejected":0,"terminal_positions":0,"maker_fills":0,"taker_fills":0,"cancels":0}
    lastentry={};maxgross=0;maxcalls=0;nextentry=-math.inf;mark=None
    signal_times=sorted(signals);signal_cursor=0;lastmarks={}
    def quotes(i):
        for c in p.positions:
            j=lookup.get(c)
            if j is not None and np.isfinite(bids[i,j]) and np.isfinite(asks[i,j]) and bids[i,j]>0 and asks[i,j]>=bids[i,j]:
                lastmarks[c]=(t[i],D(str(bids[i,j])),D(str(asks[i,j])))
            elif c not in lastmarks or t[i]-lastmarks[c][0]>cfg["maximum_quote_age_seconds"]:raise ValueError("unpriced holding "+c)
        return {c:(x[1],x[2]) for c,x in lastmarks.items() if c in p.positions}
    def budget(now,reduction=False,cancel=False):
        nonlocal maxcalls
        while calls and now-calls[0]>=60:calls.popleft()
        n=1 if cancel else 2
        cap=cfg["max_process_calls_per_minute"]-cfg["sampled_public_calls_per_minute"]-(0 if reduction else cfg["reserve_exit_calls"])
        if len(calls)+n>cap:counts["quota_rejected"]+=1;return False
        calls.extend([now]*n);maxcalls=max(maxcalls,len(calls)+cfg["sampled_public_calls_per_minute"]);return True
    def valid(i,c):
        j=lookup.get(c)
        return j is not None and np.isfinite(bids[i,j]) and np.isfinite(asks[i,j]) and bids[i,j]>0 and asks[i,j]>=bids[i,j] and c+"/USD" in rules
    def queue(i,c,side,qty,reduction=False):
        if any(o["coin"]==c for o in pending):return
        if not valid(i,c):errors.append("missing_pair_or_quote:"+c);return
        pr=rules[c+"/USD"]["AmountPrecision"]
        if type(pr) is not int or not 0<=pr<=8:errors.append("unsupported_precision:"+c);return
        if qty<=0:return
        if not budget(t[i],reduction):return
        use_maker=maker and side>0 and not reduction
        pending.append({"coin":c,"side":side,"quantity":qty,"precision":pr,"signal_time":t[i],"due":t[i]+delay,
          "limit":D(str(bids[i,lookup[c]])) if use_maker else None,"arrived":False,"reduction":reduction})
        counts["submitted"]+=1
    for i,now in enumerate(t):
        try:mark=quotes(i)
        except ValueError as e:errors.append(str(e));break
        # Submitted orders are never resent. Eligibility uses later observed ask/bid, never a future high.
        for o in list(pending):
            if now<o["due"]:continue
            c=o["coin"]
            if not valid(i,c):continue
            j=lookup[c];bid,ask=D(str(bids[i,j])),D(str(asks[i,j]))
            if o["limit"] is not None and o["arrived"] and now-o["due"]>cfg["entry_ttl_seconds"]:
                if budget(now,True,True):pending.remove(o);counts["expired"]+=1;counts["cancels"]+=1
                continue
            if not o["arrived"]:
                o["arrived"]=True;o["role"]="TAKER" if o["limit"] is None else role(o["side"],o["limit"],bid,ask)
            if o["role"]=="RESTING" and ask>o["limit"]:continue
            fee=D(str(cfg["maker_fee"] if o["role"]=="RESTING" else cfg["taker_fee"]))
            price=o["limit"] if o["role"]=="RESTING" else ask if o["side"]>0 else bid
            qty=o["quantity"]
            if o["role"]=="RESTING":qty=(qty*D(str(fraction))).quantize(D(10)**-o["precision"],rounding="ROUND_DOWN")
            if qty*price<D(str(cfg["minimum_order_usd"])):pending.remove(o);counts["size_or_cash_rejected"]+=1;continue
            before=p.positions.get(c,(D(0),D(0)))[0]
            try:p.fill(Order(c,o["side"],qty),price,fee)
            except ValueError:counts["size_or_cash_rejected"]+=1;pending.remove(o);continue
            fill={**p.fills[-1],"time":now,"signal_time":o["signal_time"],"role":o["role"],"terminal":False}
            fills.append(fill);counts["maker_fills" if o["role"]=="RESTING" else "taker_fills"]+=1
            pending.remove(o);after=p.positions.get(c,(D(0),D(0)))[0]
            if before==0 and after!=0:lastentry[c]=now
            if after==0:lastentry.pop(c,None);nextentry=now+cfg["cooldown_seconds"]
            if fraction<1 and o["role"]=="RESTING":
                if budget(now,True,True):counts["cancels"]+=1
                else:errors.append("partial_cancel_budget_unavailable")
        try:mark=quotes(i)
        except ValueError as e:errors.append(str(e));break
        nav=p.nav(mark);gross=p.gross(mark)
        if nav<=0 or gross>nav+D(".00000001"):errors.append("gross_or_equity_violation")
        maxgross=max(maxgross,float(gross/nav) if nav>0 else math.inf)
        liquid=float(nav-gross*D(str(cfg["taker_fee"])))
        peak=max(peak,liquid);dd=max(dd,1-liquid/peak);navs.append((now,liquid))
        if kind=="A" and p.positions:
            for c,(q,e) in list(p.positions.items()):
                if now-lastentry.get(c,now)>=cfg["hold_seconds"]:queue(i,c,-1 if q>0 else 1,abs(q),True)
        while signal_cursor<len(signal_times) and signal_times[signal_cursor]<=now:
            stamp=signal_times[signal_cursor];weights=signals[stamp];signal_cursor+=1
            if stamp<t[0] or now-stamp>cfg["maximum_quote_age_seconds"]:continue
            if kind=="A" and (p.positions or pending or now<nextentry):continue
            counts["signals"]+=bool(weights)
            # A target change cancels outstanding entries first; actual inventory remains in the ledger.
            if kind=="B":
                for o in list(pending):
                    if not o["reduction"]:
                        if budget(now,True,True):pending.remove(o);counts["cancels"]+=1
            reductions=[];increases=[]
            for c in sorted(set(weights)|set(p.positions)):
                if not valid(i,c):errors.append("missing_target_quote:"+c);continue
                j=lookup[c];bid,ask=D(str(bids[i,j])),D(str(asks[i,j]))
                q,e=p.positions.get(c,(D(0),D(0)));want=D(str(weights.get(c,0)))
                held=q*(bid if q>0 else ask)/nav if nav else D(0)
                band=D(".05") if kind=="B" else D(0)
                if want!=0 and abs(want-held)<=band:continue
                if q and (want==0 or (want>0)!=(q>0) or abs(want)<abs(held)):
                    target=abs(want)*nav/(bid if q>0 else ask) if want and (want>0)==(q>0) else D(0)
                    precision=rules[c+"/USD"]["AmountPrecision"];amount=max(D(0),abs(q)-target).quantize(D(10)**-precision,rounding="ROUND_DOWN")
                    reductions.append((c,-1 if q>0 else 1,amount,True))
                    # Flips wait for a later target; no proceeds of unfilled reductions are spent.
                    continue
                if want:
                    side=1 if want>0 else -1;price=ask if side>0 else bid
                    remaining=max(D(0),abs(want)*nav-abs(q)*price)
                    remaining=min(remaining,p.free_cash())
                    amount=sized(remaining,price,rules[c+"/USD"]["AmountPrecision"],cfg["taker_fee"])
                    increases.append((c,side,amount,False))
            for c,sd,q,red in reductions+increases:queue(i,c,sd,q,red)
    terminal_complete=True
    if not navs:terminal_complete=False
    elif t[-1]-navs[-1][0]>cfg["maximum_quote_age_seconds"]:terminal_complete=False
    if terminal_complete:
        try:
            mark=quotes(len(t)-1)
            for c,(q,e) in list(p.positions.items()):
                bid,ask=mark[c];price=bid if q>0 else ask
                p.fill(Order(c,-1 if q>0 else 1,abs(q)),price,D(str(cfg["taker_fee"])))
                fills.append({**p.fills[-1],"time":t[-1],"signal_time":t[-1],"role":"TAKER","terminal":True});counts["terminal_positions"]+=1
        except ValueError as e:errors.append(str(e));terminal_complete=False
    if terminal_complete:navs[-1]=(navs[-1][0],float(p.cash))
    return {"return":float(p.cash/initial-1) if terminal_complete else None,"net_usd":float(p.cash-initial) if terminal_complete else None,
      "mdd":dd,"max_gross":maxgross,"fees_usd":float(p.fees),"complete":terminal_complete and not errors,"errors":sorted(set(errors)),
      "max_modeled_calls_per_minute":maxcalls,"terminal_liquidation_is_price_mark_not_verified_fill":True,
      **counts,"fills":fills,"nav":navs,"unfilled_at_end":len(pending),"actual_orders":0}
