"""Recorded-quote research only. No API, credential, client or live execution imports."""
from pathlib import Path
from decimal import Decimal,ROUND_DOWN
import hashlib,json
import numpy as np
import pandas as pd
import yaml
from research.book.gate.simulator_edge.money import quantity,resting_hit
ROOT=Path(__file__).resolve().parents[4];MAIN=ROOT.parents[1]
OUT=MAIN/"results/book/20261015-simulator-edge-v1"
NAMES=["tick_mm","taker_tick","rev5_mm","rev5_mt","rev5_tm","rev5_tt","tick_rev1","tick_rev2","tick_rev3",
       "mom5_tt","break60_tt","bidask5_tt","last_low_tt","spread_compress_tt","market60_tt","short_mom5_proxy","short_fade_proxy"]
def features(b,a,l,rules,p):
    n=int(p["lookback_minutes"]*60/p["sample_seconds"]);h=int(p["breakout_lookback_minutes"]*60/p["sample_seconds"])
    r5=b/b.shift(n)-1;r60=b/b.shift(h)-1;spread=(a-b)/b;hurdle=spread+p["entry_hurdle"]
    steps=pd.Series({c:10.**(-rules[c]["PricePrecision"]) for c in b.columns})
    tickmove=-(b-b.shift(1))/steps
    f={"mom5_tt":r5.where(r5>hurdle),"rev5_tt":(-r5).where(-r5>hurdle)}
    for k in ["rev5_mm","rev5_mt","rev5_tm"]:f[k]=f["rev5_tt"]
    for k in [1,2,3]:f["tick_rev"+str(k)]=tickmove.where(tickmove>=k)*(steps/b)
    priorhi=b.shift(1).rolling(h,min_periods=h).max()
    f["break60_tt"]=(b/priorhi-1).where(b>priorhi)
    f["bidask5_tt"]=r5.where((r5>hurdle)&(a>a.shift(n)))
    f["last_low_tt"]=(1-l/b).where(l<=b)
    m=int(p["spread_lookback_minutes"]*60/p["sample_seconds"])
    median=spread.shift(1).rolling(m,min_periods=m).median()
    f["spread_compress_tt"]=(median-spread).where((spread<median)&(spread.shift(1)>median))
    leader=[c for c in ["BTC/USD","ETH/USD"] if c in b]
    leader_up=(r60[leader].mean(axis=1)>p["entry_hurdle"]) if leader else pd.Series(False,index=b.index)
    f["market60_tt"]=r5.where((r5>hurdle)&np.broadcast_to(leader_up.to_numpy()[:,None],r5.shape))
    f["short_mom5_proxy"]=(-r5).where(-r5>hurdle)
    f["short_fade_proxy"]=(-r5).where((-r5>hurdle)&(r60>0))
    tick=b.rdiv(steps,axis="columns")
    tick.loc[:,[c for c in b.columns if c not in ["BONK/USD","PEPE/USD","STO/USD"]]]=np.nan
    f["tick_mm"]=tick;f["taker_tick"]=tick
    return {k:v.replace([np.inf,-np.inf],np.nan).to_numpy() for k,v in f.items()}
def run(name,b,a,l,signals,rules,p,t0,t1,*,buy_rule="ask",fee_mult=1.,lag_mult=1,partial=False):
    t=b.index.asi8/1e9;B,A,L=b.to_numpy(),a.to_numpy(),l.to_numpy();cols=list(b.columns)
    lo=int(b.index.searchsorted(t0));hi=int(b.index.searchsorted(t1,side="right"))-1
    fe=p["maker"]*fee_mult;ft=p["taker"]*fee_mult;lag=int(p["lag_samples"]*lag_mult)
    entryM=name in ["tick_mm","rev5_mm","rev5_mt"];exitM=name in ["tick_mm","taker_tick","rev5_mm","rev5_tm"]
    side=-1 if name.startswith("short") else 1
    tick=name in ["tick_mm","taker_tick"]
    hold=(p["tick_hold_seconds"] if tick else
          60*(p["tick_reversal_hold_minutes"] if name.startswith("tick_rev") else p["breakout_hold_minutes"] if name=="break60_tt" else p["leader_hold_minutes"] if name=="market60_tt" else p["hold_minutes"]))
    cash=float(p["capital"]);q=0.;j=None;pending=None;next_entry=-np.inf;trips=[];equity=[cash];callcounts=[]
    attempts=fills=orders=0;costs=spread_cost=0.;opened=None
    def valid(i,j):return j is not None and np.isfinite([B[i,j],A[i,j],L[i,j]]).all() and 0<B[i,j]<=A[i,j]
    def mark(i):
        if not q:return cash
        if not valid(i,j):return equity[-1]
        return cash+q*B[i,j]*(1-ft) if side>0 else cash-q*A[i,j]*(1+ft)
    def open_at(i,px,rate):
        nonlocal cash,q,fills,orders,costs,spread_cost,opened
        fraction=p["partial_fill_fraction"] if partial and entryM else 1.
        qty=quantity(cash*p["exposure"]*fraction,px,rules[cols[j]]["AmountPrecision"],rate)
        if qty*px<rules[cols[j]].get("MiniOrder",p.get("min_order",1)):return False
        before=cash;fee=qty*px*rate
        cash+=(-qty*px-fee) if side>0 else (qty*px-fee)
        q=qty;costs+=fee;spread_cost+=qty*(A[i,j]-B[i,j])/2 if rate==ft else 0.
        opened={"entry_time":float(t[i]),"entry_price":float(px),"qty":qty,"entry_fee":fee,"cash_before":before,
                "entry_maker":bool(rate==fe),"coin":cols[j],"exit_cashflow":0.,"exit_fees":0.,"terminal":False}
        fills+=1;orders+=1;return True
    def close_at(i,px,rate,part=1.,terminal=False):
        nonlocal cash,q,orders,costs,spread_cost,opened,next_entry,j
        qty=q if part==1 else float((Decimal(str(q))*Decimal(str(part))).quantize(Decimal(1).scaleb(-rules[cols[j]]["AmountPrecision"]),rounding=ROUND_DOWN))
        if qty<=0:qty=q
        fee=qty*px*rate;flow=(qty*px-fee) if side>0 else (-qty*px-fee)
        cash+=flow;q=max(0.,q-qty);costs+=fee;spread_cost+=qty*(A[i,j]-B[i,j])/2 if rate==ft else 0.;orders+=1
        opened["exit_cashflow"]+=flow;opened["exit_fees"]+=fee
        if q<=10.**(-rules[cols[j]]["AmountPrecision"])*1e-6:
            q=0.;profit=cash-opened["cash_before"]
            trips.append({**opened,"exit_time":float(t[i]),"exit_price":float(px),"net_pnl":float(profit),
                          "net_return":float(profit/(opened["entry_price"]*opened["qty"])),"terminal":terminal})
            opened=None;j=None;next_entry=t[i]+p["pause_seconds"]
    for i in range(lo,hi+1):
        calls=1
        if pending is not None:
            calls+=1
            if valid(i,j) and i>=pending["live"]:
                px=pending["limit"];kind=pending["kind"];market=pending["market"]
                crossing=(A[i,j]<=px) if kind=="entry" else (B[i,j]>=px)
                if market:
                    px=(A[i,j] if side>0 else B[i,j]) if kind=="entry" else (B[i,j] if side>0 else A[i,j])
                    if kind=="entry":open_at(i,px,ft)
                    else:close_at(i,px,ft)
                    pending=None;calls+=1
                elif i==pending["live"] and crossing:
                    if kind=="entry":open_at(i,A[i,j],ft)
                    else:close_at(i,B[i,j],ft)
                    pending=None;calls+=1
                else:
                    hit=(A[i,j]<=px if buy_rule=="ask" else L[i,j]<=px and B[i,j]<=px) if kind=="entry" else B[i,j]>=px
                    pending["count"]=pending["count"]+1 if hit else 0
                    if resting_hit("BUY" if kind=="entry" else "SELL",px,B[i,j],A[i,j],L[i,j],buy_rule,pending["count"],p["maker_confirm_samples"]):
                        if kind=="entry":
                            open_at(i,px,fe);pending=None
                        else:
                            close_at(i,px,fe,p["partial_fill_fraction"] if partial else 1.)
                            pending={"kind":"exit","market":True,"limit":0.,"live":i+lag,"expiry":np.inf,"count":0} if q else None
                        calls+=1
            if pending is not None and t[i]>=pending["expiry"]:
                if pending["kind"]=="exit":
                    pending={"kind":"exit","market":True,"limit":0.,"live":i+lag,"expiry":np.inf,"count":0};calls+=2
                else:
                    pending=None;j=None;next_entry=t[i]+p["pause_seconds"];calls+=1
        if q and pending is None and valid(i,j):
            st=10.**(-rules[cols[j]]["PricePrecision"])
            stopped=tick and B[i,j]<=opened["entry_price"]-p["stop_ticks"]*st
            matured=t[i]>=opened["entry_time"]+hold
            if tick or matured or stopped:
                maker=exitM and not stopped
                limit=opened["entry_price"]+st if tick else A[i,j]
                pending={"kind":"exit","market":not maker,"limit":limit,"live":i+lag,
                         "expiry":t[i]+p["maker_expiry_seconds"] if maker else np.inf,"count":0};calls+=1
        elif q and pending is not None and pending["kind"]=="exit" and not pending["market"] and valid(i,j) and tick:
            st=10.**(-rules[cols[j]]["PricePrecision"])
            if B[i,j]<=opened["entry_price"]-p["stop_ticks"]*st:
                pending={"kind":"exit","market":True,"limit":0.,"live":i+lag,"expiry":np.inf,"count":0};calls+=2
        if not q and pending is None and t[i]>=next_entry:
            if tick or int(round(t[i]))%p["decision_seconds"]==0:
                score=signals[name][i].copy();valids=np.isfinite(B[i])&np.isfinite(A[i])&(B[i]>0)&(A[i]>=B[i])
                score[~valids]=-np.inf
                if np.isfinite(score).any():
                    j=int(np.argmax(np.where(np.isfinite(score),score,-np.inf)))
                    pending={"kind":"entry","market":not entryM,"limit":B[i,j],"live":i+lag,
                             "expiry":t[i]+p["maker_expiry_seconds"] if entryM else np.inf,"count":0}
                    attempts+=1;calls+=1
        equity.append(mark(i));callcounts.append(calls)
    # All outstanding buys cancel; all filled inventory is charged a bid/ask terminal exit.
    terminal_missing=False
    if q:
        if valid(hi,j):close_at(hi,B[hi,j] if side>0 else A[hi,j],ft,terminal=True)
        else:terminal_missing=True
    equity[-1]=cash if not q else equity[-1]
    e=np.asarray(equity);pn=np.array([x["net_pnl"] for x in trips]);rr=np.array([x["net_return"] for x in trips])
    rolling=pd.Series(callcounts).rolling(int(60/p["sample_seconds"]),min_periods=1).sum()
    maxcalls=int(rolling.max()+p["reserve_calls_per_minute"])
    assert maxcalls<=p["total_calls_per_minute"]
    win=pn[pn>0];loss=pn[pn<0]
    return {"return":float(e[-1]/p["capital"]-1),"mdd":float(-(e/np.maximum.accumulate(e)-1).min()),
            "trades":len(trips),"entry_attempts":attempts,"entry_fills":fills,"fill_rate":fills/attempts if attempts else None,
            "win_rate":float((pn>0).mean()) if len(pn) else None,"avg_win_usd":float(win.mean()) if len(win) else None,
            "avg_loss_usd":float(loss.mean()) if len(loss) else None,"ev_usd":float(pn.mean()) if len(pn) else None,
            "ev_return":float(rr.mean()) if len(rr) else None,"total_costs":float(costs),"crossed_spread_cost":float(spread_cost),
            "orders":orders,"max_calls_minute":maxcalls,"terminal_price_missing":terminal_missing,"trips":trips,
            "actual_fill_verified":False,"quantity_precision_applied":True,"assumed_partial_fills":partial}
def load():
    p=yaml.safe_load(Path(__file__).with_name("config.yaml").read_text())["quote"]
    snapshot=json.loads((OUT/"public_exchange_snapshot.json").read_text())
    rules={k:v for k,v in snapshot["exchangeInfo"]["TradePairs"].items() if v.get("CanTrade")}
    hashes={};pieces=[]
    for day in range(7,15):
        file=MAIN/f"results/book/scalp/quotes/202610{day:02}.csv";hashes[str(file)]=hashlib.sha256(file.read_bytes()).hexdigest()
        for ch in pd.read_csv(file,chunksize=300000):
            ch=ch[ch.pair.isin(rules)].copy();pieces.append(ch)
    raw=pd.concat(pieces,ignore_index=True);raw["ts"]=pd.to_datetime(raw.ts_utc,utc=True)+pd.Timedelta(seconds=p["offset_seconds"])
    for c in ["max_bid","min_ask","last_price"]:raw[c]=pd.to_numeric(raw[c],errors="coerce")
    invalid=~(np.isfinite(raw[["max_bid","min_ask","last_price"]]).all(axis=1)&(raw.max_bid>0)&(raw.min_ask>=raw.max_bid)&(raw.last_price>0))
    bad=int(invalid.sum());raw=raw[~invalid]
    exact=int(raw.duplicated(["ts","pair","max_bid","min_ask","last_price"]).sum());raw=raw.drop_duplicates(["ts","pair","max_bid","min_ask","last_price"])
    conflict=raw.duplicated(["ts","pair"],keep=False);conflicts=int(conflict.sum());raw=raw[~conflict]
    frames={}
    for field in ["max_bid","min_ask","last_price"]:
        x=raw.pivot(index="ts",columns="pair",values=field).sort_index().resample(str(p["sample_seconds"])+"s",label="right",closed="right").last()
        frames[field]=x.ffill(limit=p["stale_samples"]).sort_index(axis=1)
    meta={"input_hashes":hashes,"invalid_rows":bad,"exact_duplicates_removed":exact,"conflicting_rows_quarantined":conflicts,
          "pairs_recorded":len(frames["max_bid"].columns),"current_trade_pairs":len(rules),"quote_clock_offset_seconds":p["offset_seconds"],
          "no_depth_or_24h_activity":True,"historical_listing_membership_verified":False}
    (OUT/"quote_data_audit.json").write_text(json.dumps(meta,indent=2))
    return frames["max_bid"],frames["min_ask"],frames["last_price"],rules,p

def main():
    b,a,l,rules,p=load();f=features(b,a,l,rules,p)
    source_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    config_hash=hashlib.sha256(Path(__file__).with_name("config.yaml").read_bytes()).hexdigest()
    rows=[];tripframes=[];paths=[]
    periods=[("calibration","2026-10-08","2026-10-13"),("validation","2026-10-13","2026-10-14"),("recent_check","2026-10-14","2026-10-15")]
    for name in NAMES:
        for split,t0,t1 in periods:
            z=run(name,b,a,l,f,rules,p,pd.Timestamp(t0,tz="UTC"),pd.Timestamp(t1,tz="UTC"))
            trip=z.pop("trips")
            rows.append({"candidate":name,"source":"roostoo_quotes","split":split,"scenario":"strict_base","hours":(pd.Timestamp(t1)-pd.Timestamp(t0)).total_seconds()/3600,**z})
            if trip:
                df=pd.DataFrame(trip);df["candidate"]=name;df["split"]=split;tripframes.append(df)
        for sc,opts in [("extra_delay",{"lag_mult":2}),("double_fees",{"fee_mult":2.}),("partial_maker",{"partial":True}),("optimistic_last",{"buy_rule":"last"})]:
            z=run(name,b,a,l,f,rules,p,pd.Timestamp("2026-10-14",tz="UTC"),pd.Timestamp("2026-10-15",tz="UTC"),**opts)
            z.pop("trips");rows.append({"candidate":name,"source":"roostoo_quotes","split":"recent_check","scenario":sc,"hours":24,**z})
        for hour in [68,72]:
            for start in pd.date_range("2026-10-08 16:00","2026-10-11 16:00",freq="D",tz="UTC"):
                z=run(name,b,a,l,f,rules,p,start,start+pd.Timedelta(hours=hour));z.pop("trips")
                paths.append({"candidate":name,"start":str(start),"hours":hour,**z,"disjoint_anchor":start.day in [8,11]})
        print("DONE quote",name,flush=True)
    pd.DataFrame(rows).to_csv(OUT/"quote_summary.csv",index=False)
    pd.DataFrame(paths).to_csv(OUT/"quote_windows.csv",index=False)
    if tripframes:pd.concat(tripframes,ignore_index=True).to_parquet(OUT/"quote_trips.parquet",index=False)
    audit=json.loads((OUT/"quote_data_audit.json").read_text())
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==h for path,h in audit["input_hashes"].items())
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==source_hash
    assert hashlib.sha256(Path(__file__).with_name("config.yaml").read_bytes()).hexdigest()==config_hash
    (OUT/"quote_complete.json").write_text(json.dumps({"status":"PASS","candidates":len(NAMES),"rows":len(rows),"windows":len(paths),
      "source_sha256":source_hash,"config_sha256":config_hash,"input_hashes_unchanged":True,"production_eligible":False},indent=2))
if __name__=="__main__":main()
