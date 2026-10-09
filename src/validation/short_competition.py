"""Retrospective same-period comparison using unchanged project planner/PaperBroker.

No signed APIs, model fitting, score changes or live actions. Observed fills are a
conditional literal ledger; predicted fills are simulations, never actual fills.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,importlib
from pathlib import Path
from decimal import Decimal
import numpy as np
import pandas as pd
import yaml
from src.api.rules import PairRule
from src.contracts import MarketView,check_targets
from src.execution.planner import Holdings,Quote,plan_orders,equity,current_weights
from src.execution.paper import PaperBroker
from src.validation.observed_baseline import ledger,closed_minutes,weights_from_hourly

ACTIONS={"BUY":"Buy Long","SELL":"Sell Long","SHORT_OPEN":"Open Short","SHORT_CLOSE":"Cover Short"}

def hourly_archives(a):
    """Only complete 60-minute hours produce usable close/volume observations."""
    p=a.pivot(index="timestamp",columns="symbol",values="close").sort_index()
    q=a.pivot(index="timestamp",columns="symbol",values="quote_volume").sort_index()
    pc=p.resample("h",label="right",closed="right").count()
    qc=q.resample("h",label="right",closed="right").count()
    return (p.resample("h",label="right",closed="right").last().where(pc==60),
            q.resample("h",label="right",closed="right").sum(min_count=60).where(qc==60))

class QuoteBook:
    def __init__(self,prices,quotes,cfg):
        self.cfg=cfg;self.assets=cfg["assets"];self.p=prices.sort_index()
        self.pt=self.p.index.asi8
        self.q={}
        for a in self.assets:
            x=quotes.loc[quotes.pair==a+"/USD"].copy()
            x["ts_utc"]=pd.to_datetime(x.ts_utc,utc=True)
            x=x.sort_values("ts_utc")
            self.q[a]=(pd.DatetimeIndex(x.ts_utc).asi8,x)
    def at(self,t):
        t=pd.Timestamp(t);j=np.searchsorted(self.pt,t.value,side="right")-1
        row=self.p.iloc[j] if j>=0 else None
        age=(t.value-self.pt[j])/1e9 if j>=0 else np.inf
        result={};meta={}
        for a in self.assets:
            idx,x=self.q[a];k=np.searchsorted(idx,t.value,side="right")-1
            qa=(t.value-idx[k])/1e9 if k>=0 else np.inf
            if k>=0 and qa<=self.cfg["quote_max_age"]:
                r=x.iloc[k];bid=float(r.max_bid);ask=float(r.min_ask)
                source="recorded_roostoo";stamp=str(r.ts_utc);source_age=qa
            else:
                mark=float(row.get(a+"USDT",np.nan)) if row is not None else np.nan
                if age>self.cfg["minute_max_age"]:return None,None
                bid=mark*(1-self.cfg["proxy_half_spread"]);ask=mark*(1+self.cfg["proxy_half_spread"])
                source="verified_archive_proxy";stamp=str(self.p.index[j]);source_age=age
            if not np.isfinite(bid) or not np.isfinite(ask) or bid<=0 or ask<bid:return None,None
            pair=a+"/USD";result[pair]=Quote(bid,ask)
            meta[pair]={"source":source,"quote_time":stamp,"age_seconds":source_age,"bid":bid,"ask":ask}
        return result,meta

class ShortCycles:
    def __init__(self):self.active={};self.done=[]
    def fill(self,event,pnl=0.,closed=False):
        a=event["asset"]
        if event["action"]=="Open Short":
            if a not in self.active:
                self.active[a]={"asset":a,"start":str(event["time_utc"]),"opened_quantity":0.,
                                "covered_quantity":0.,"net_pnl":0.,"entry_orders":0}
            r=self.active[a];r["opened_quantity"]+=event["quantity"]
            r["entry_orders"]+=1;r["net_pnl"]-=event["fee"]
        elif event["action"]=="Cover Short":
            r=self.active[a];r["covered_quantity"]+=event["quantity"]
            r["net_pnl"]+=float(pnl)-event["fee"]
            if closed:
                self.done.append({**r,"end":str(event["time_utc"]),"status":"completed",
                                  "profitable":r["net_pnl"]>0})
                del self.active[a]
    def finish(self,t):
        return self.done+[{**r,"end":str(t),"status":"censored","profitable":None} for r in self.active.values()]

def rules_for(cfg):
    return {a+"/USD":PairRule(a+"/USD",int(cfg["price_precisions"].get(a,4)),
            int(cfg["precisions"][a]),Decimal(str(cfg["min_order"]))) for a in cfg["assets"]}

def state_row(h,t,q):
    eq=equity(h,q)
    gross=sum(qty*q[a].bid for a,qty in h.spot.items() if a in q)+sum(pos.qty*q[a].ask for a,pos in h.shorts.items() if a in q)
    return {"time_utc":t,"cash":h.usd_free,"equity":eq,"gross":gross,
            "gross_ratio":gross/eq,"locked_collateral":sum(x.collateral for x in h.shorts.values()),
            **{a.split("/")[0]:h.spot.get(a,0)-(h.shorts[a].qty if a in h.shorts else 0) for a in q}}

def paths_from_states(states,book,cfg,extra=()):
    start=pd.Timestamp(cfg["start"]);end=pd.Timestamp(cfg["end"])
    grid=pd.DatetimeIndex(sorted(set(pd.date_range(start,end,freq="min"))|set(extra)|{start,end}))
    ix=np.array([t.value for t,_ in states],dtype=np.int64);rows=[];missing=[]
    for t in grid:
        q,_=book.at(t)
        if q is None:missing.append({"time_utc":str(t),"phase":"valuation","reason":"missing_or_stale_quote"});continue
        j=np.searchsorted(ix,t.value,side="right")-1
        rows.append(state_row(states[j][1],t,q))
    return pd.DataFrame(rows),missing

def replay_targets(weights,book,cfg,lag_minutes):
    """Execute precomputed causal targets after fixed lag with the shared planner."""
    start=pd.Timestamp(cfg["start"]);end=pd.Timestamp(cfg["end"])
    h=Holdings(float(cfg["seed"]));rules=rules_for(cfg);broker=PaperBroker(h,rules,cfg["fee"])
    states=[(start,copy.deepcopy(h))];events=[];decisions=[];failures=[];cycles=ShortCycles()
    for t,w in sorted(weights.items()):
        t=pd.Timestamp(t);execution=t+pd.Timedelta(minutes=lag_minutes)
        if t<start or execution>end:continue
        q,meta=book.at(execution)
        if q is None:
            failures.append({"time_utc":str(execution),"phase":"planning","reason":"missing_or_stale_quote"});continue
        target={s.removesuffix("USDT")+"/USD":float(v) for s,v in w.items()}
        orders,notes=plan_orders(target,h,q,rules,float(cfg["band"]),float(cfg["fee"]),
                                 float(cfg["cash_buffer"]),float(cfg["min_order"]),exact=False)
        decisions.append({"time_utc":str(t),"execution_utc":str(execution),"targets":target,"notes":notes,"orders":len(orders)})
        for n,o in enumerate(orders):
            ft=execution+pd.Timedelta(seconds=n*cfg["order_spacing_seconds"])
            if ft>end:
                failures.append({"time_utc":str(ft),"phase":"execution","reason":"order_beyond_cutoff","pair":o.pair});continue
            fq,fm=book.at(ft)
            if fq is None:
                failures.append({"time_utc":str(ft),"phase":"execution","reason":"missing_or_stale_quote","pair":o.pair});continue
            f=broker.execute([o],fq)[0]
            if f["status"]!="FILLED":
                failures.append({"time_utc":str(ft),"phase":"execution","reason":f.get("reason","rejected"),"pair":o.pair});continue
            e={"asset":o.pair.split("/")[0],"action":ACTIONS[o.kind],"quantity":f["qty"],"price_usd":f["price"],
               "fee":f["fee"],"time_utc":ft,"decision_utc":t,"source":fm[o.pair]["source"],
               "source_time":fm[o.pair]["quote_time"],"source_age_seconds":fm[o.pair]["age_seconds"],"phase":"strategy"}
            events.append(e);cycles.fill(e,f.get("pnl",0.),o.pair not in h.shorts)
            states.append((ft,copy.deepcopy(h)))
    path,missing=paths_from_states(states,book,cfg,[t for t,_ in states])
    failures+=missing
    q,endpoint=book.at(end)
    if q is None:raise ValueError("Endpoint has no trustworthy quote")
    marked=equity(h,q);censored=cycles.finish(end)
    full_fee=cfg["fee"]*(sum(qty*q[a].bid for a,qty in h.spot.items())+sum(pos.qty*q[a].ask for a,pos in h.shorts.items()))
    orders,notes=plan_orders({},h,q,rules,0.,cfg["fee"],0.,cfg["min_order"],exact=True)
    terminal_fees=0.
    for o in orders:
        f=broker.execute([o],q)[0]
        if f["status"]!="FILLED":
            failures.append({"time_utc":str(end),"phase":"terminal","reason":f.get("reason","rejected"),"pair":o.pair});continue
        terminal_fees+=f["fee"]
        events.append({"asset":o.pair.split("/")[0],"action":ACTIONS[o.kind],"quantity":f["qty"],"price_usd":f["price"],
                       "fee":f["fee"],"time_utc":end,"decision_utc":end,"source":endpoint[o.pair]["source"],
                       "source_time":endpoint[o.pair]["quote_time"],"source_age_seconds":endpoint[o.pair]["age_seconds"],"phase":"terminal"})
    leftover={a:qty for a,qty in h.spot.items() if qty}
    summary={"marked_equity":marked,"liquidated_equity":equity(h,q),"terminal_fees":terminal_fees,
             "full_cost_liquidated_equity":marked-full_fee,"full_terminal_fee_estimate":full_fee,
             "residual_dust_fee_estimate":max(0.,full_fee-terminal_fees),
             "terminal_notes":notes,"remaining_spot_dust":leftover,"endpoint_quotes":endpoint,
             "pending_decisions_after_cutoff":sum(pd.Timestamp(t)+pd.Timedelta(minutes=lag_minutes)>end for t in weights)}
    columns=["asset","action","quantity","price_usd","fee","time_utc","decision_utc","source","source_time","source_age_seconds","phase"]
    return pd.DataFrame(events,columns=columns),path,decisions,failures,censored,summary

def observed_path(events,book,cfg,fee_overrides=None):
    """Literal signed-cash FIFO ledger; retain impossible recorded capital use."""
    ev=events.sort_values(["time_utc","trade_id"]).reset_index(drop=True).copy()
    states=ledger(ev,cfg["seed"],cfg["fee"]);offset=0.;rows=[];tracker=ShortCycles()
    previous_realized=0.
    for i,r in ev.iterrows():
        fee=float(r.quantity)*float(r.price_usd)*cfg["fee"]
        override=(fee_overrides or {}).get(r.trade_id,fee);offset+=override-fee
        st=states[i];st["cash"]-=offset;st["fees"]+=offset
        row=r.to_dict();row["fee"]=override;row["phase"]="observed";rows.append(row)
        pnl=st["gross_realized"]-previous_realized
        if r.action in ("Open Short","Cover Short"):
            tracker.fill(row,pnl,st["short"].get(r.asset,0)<=1e-12)
        previous_realized=st["gross_realized"]
    start=pd.Timestamp(cfg["start"]);end=pd.Timestamp(cfg["end"])
    ix=pd.DatetimeIndex(ev.time_utc).asi8;path=[]
    for t in sorted(set(pd.date_range(start,end,freq="min"))|set(ev.time_utc)|{end}):
        q,meta=book.at(t)
        if q is None:raise ValueError("Missing observed valuation quote")
        j=np.searchsorted(ix,pd.Timestamp(t).value,side="right")-1
        st=states[j] if j>=0 else {"cash":cfg["seed"],"long":{},"short":{},"fees":0.}
        eq=st["cash"]+sum(v*q[a+"/USD"].bid for a,v in st["long"].items())-sum(v*q[a+"/USD"].ask for a,v in st["short"].items())
        gross=sum(v*q[a+"/USD"].bid for a,v in st["long"].items())+sum(v*q[a+"/USD"].ask for a,v in st["short"].items())
        path.append({"time_utc":t,"signed_cash":st["cash"],"equity":eq,"gross":gross,"gross_ratio":gross/eq,
                     **{a:st["long"].get(a,0)-st["short"].get(a,0) for a in cfg["assets"]}})
    p=pd.DataFrame(path);last=p.iloc[-1];terminal=last.gross*cfg["fee"]
    summary={"marked_equity":float(last.equity),"liquidated_equity":float(last.equity-terminal),"terminal_fees":float(terminal),
             "full_cost_liquidated_equity":float(last.equity-terminal),"full_terminal_fee_estimate":float(terminal),
             "fees":float(states[-1]["fees"]),"minimum_signed_cash":min(float(s["cash"]) for s in states),
             "observed_capital_violations":int(sum(s["cash_negative"] or s["gross_exceeds_equity"] for s in states)),
             "initial_signed_cash_deficit":max(0.,-float(states[4]["cash"])) if len(states)>=5 else max(0.,-float(states[-1]["cash"])),
             "accounting":"literal signed-cash FIFO; signed_cash is not free collateral; no scaling of supplied fills",
             "liquidation":"estimated close of all balances at endpoint bid/ask less0.1% fee; sub-dollar dust analytical",
             "endpoint_quotes":book.at(end)[1]}
    return pd.DataFrame(rows),p,summary,tracker.finish(end)

def summarize(name,events,path,cycles,endpoint,cfg):
    strategy=events[events.phase!="terminal"]
    completed=[x for x in cycles if x["status"]=="completed"]
    returns=path.equity/float(cfg["seed"])-1
    draw=path.equity/path.equity.cummax()-1
    return {"model":name,"marked_return":endpoint["marked_equity"]/cfg["seed"]-1,
            "liquidated_return":endpoint["liquidated_equity"]/cfg["seed"]-1,
            "full_cost_liquidated_return":endpoint["full_cost_liquidated_equity"]/cfg["seed"]-1,
            "maximum_drawdown":float(-draw.min()),"minimum_marked_return":float(returns.min()),
            "strategy_orders":len(strategy),"fees":float(strategy.fee.sum()),"terminal_fees":endpoint["terminal_fees"],
            "notional_turnover_seed":float((strategy.quantity*strategy.price_usd).sum()/cfg["seed"]),
            "short_entry_orders":int((strategy.action=="Open Short").sum()),
            "short_cycles_completed":len(completed),"short_cycles_censored":sum(x["status"]=="censored" for x in cycles),
            "short_cycle_hit_rate":sum(x["profitable"] for x in completed)/len(completed) if completed else None,
            "completed_short_net_pnl":sum(x["net_pnl"] for x in completed),
            "mean_gross_ratio":float(path.gross_ratio.mean()),"maximum_gross_ratio":float(path.gross_ratio.max())}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",default="results/book/20261009-short-competition");a=ap.parse_args()
    out=Path(a.out);manifest=json.loads((out/"data_manifest.json").read_text())
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    for name,r in manifest["files"].items():
        if sha(out/name)!=r["sha256"]:raise ValueError("Frozen input changed: "+name)
    raw=pd.read_parquet(out/"archive_minutes.parquet")
    q=pd.read_parquet(out/"quotes.parquet");q["ts_utc"]=pd.to_datetime(q.ts_utc,utc=True)
    h,v=hourly_archives(raw)
    p=raw.pivot(index="timestamp",columns="symbol",values="close").sort_index()
    # Publisher archives take precedence; quotes fill only the unavailable final partial day.
    p=p.combine_first(closed_minutes(q)).sort_index()
    qh=closed_minutes(q).resample("h",label="right",closed="right").last()
    h=h.combine_first(qh).sort_index();v=v.reindex(index=h.index,columns=h.columns)
    cfg=yaml.safe_load(Path("config.yaml").read_text())
    basic={"assets":["BNB","BTC","ETH","SOL","XRP"],"seed":100000.,"fee":.001,"band":.03,"min_order":1.,
           "cash_buffer":.001,"precisions":{"BNB":3,"BTC":5,"ETH":4,"SOL":3,"XRP":1},
           "price_precisions":{"BNB":2,"BTC":2,"ETH":2,"SOL":2,"XRP":4},"minute_max_age":120,
           "quote_max_age":30,"proxy_half_spread":.0001,"order_spacing_seconds":10.,
           "start":"2026-10-04T12:00Z","end":"2026-10-09T01:15Z"}
    book=QuoteBook(p,q,basic);results=[];target_manifest={};failure_counts={}
    for name in ["book_short_trend","book_short_rebound","book_short_breakdown"]:
        model=importlib.import_module("src.models.book."+name).MODEL;pars=cfg["models"][name]
        weights={};prev=pd.Series(dtype=float)
        for t in pd.date_range(basic["start"],pd.Timestamp(basic["end"]).floor("h"),freq="h"):
            view=MarketView(t,h.loc[:t],v.loc[:t],tuple(pars["coins"]),pars,prev)
            w=check_targets(model.targets(view),view,model.spec);weights[t]=w;prev=w
        e,path,dec,fail,cycles,end=replay_targets(weights,book,basic,60)
        e.to_csv(out/(name+"_events.csv"),index=False);path.to_csv(out/(name+"_equity.csv"),index=False)
        pd.DataFrame(cycles).to_csv(out/(name+"_short_cycles.csv"),index=False)
        pd.DataFrame(fail,columns=["time_utc","phase","reason","pair"]).to_csv(out/(name+"_failures.csv"),index=False)
        (out/(name+"_decisions.json")).write_text(json.dumps(dec,indent=2))
        (out/(name+"_endpoint.json")).write_text(json.dumps(end,indent=2))
        results.append(summarize(name,e,path,cycles,end,basic))
        failure_counts[name]=len(fail)
        target_manifest[name]={"params":pars,"model_source_sha256":sha("src/models/book/"+name+".py"),
                               "source_helper_sha256":sha("src/models/book/_short_study.py"),
                               "target_rows":len(weights),"first_target_time":str(next(iter(weights))),
                               "execution_lag_minutes":60,"initial_forced_equal":False,
                               "model_helper_commit":"317a600","model_wrapper_commit":"02b06ff"}
    # Preserve the original frozen replica recipe and its original price-to-signal panel.
    clone=yaml.safe_load((out/"original_replica_config.yaml").read_text())
    clone_h=pd.read_parquet(out/"original_clone_warmup_hourly.parquet")
    clone_p=closed_minutes(q).combine_first(raw[raw.timestamp>=pd.Timestamp("2026-09-30T00:00Z")].pivot(index="timestamp",columns="symbol",values="close")).sort_index()
    clone_h=clone_p.resample("h",label="right",closed="right").last().combine_first(clone_h)
    wt=weights_from_hourly(clone_h,clone)
    first=pd.Timestamp(clone["first_decision"])
    if clone["initial_equal"]:wt[first]=pd.Series(clone["initial_gross"]/len(clone["assets"]),index=[x+"USDT" for x in clone["assets"]])
    cc={**basic,**clone}
    e,path,dec,fail,cycles,end=replay_targets(wt,book,cc,int(clone["delay_minutes"]))
    name="original_frozen_clone"
    e.to_csv(out/(name+"_events.csv"),index=False);path.to_csv(out/(name+"_equity.csv"),index=False)
    pd.DataFrame(cycles).to_csv(out/(name+"_short_cycles.csv"),index=False)
    pd.DataFrame(fail,columns=["time_utc","phase","reason","pair"]).to_csv(out/(name+"_failures.csv"),index=False)
    (out/(name+"_endpoint.json")).write_text(json.dumps(end,indent=2))
    results.append(summarize(name,e,path,cycles,end,basic));failure_counts[name]=len(fail)
    target_manifest[name]={"config_sha256":sha(out/"original_replica_config.yaml"),
                           "execution_lag_minutes":int(clone["delay_minutes"]),"initial_forced_equal":bool(clone["initial_equal"]),
                           "recipe":"original frozen causal predictor, no fit, historical price preference preserved"}
    obs=pd.read_csv(out/"observed_trades_corrected.csv")
    obs["time_utc"]=[pd.Timestamp(str(r.date)+" "+str(r.time),tz="Asia/Hong_Kong").tz_convert("UTC") for _,r in obs.iterrows()]
    e,path,end,cycles=observed_path(obs,book,basic,{"T001":19.98})
    name="observed_literal_ledger"
    e.to_csv(out/(name+"_events.csv"),index=False);path.to_csv(out/(name+"_equity.csv"),index=False)
    pd.DataFrame(cycles).to_csv(out/(name+"_short_cycles.csv"),index=False)
    (out/(name+"_endpoint.json")).write_text(json.dumps(end,indent=2))
    results.append(summarize(name,e,path,cycles,end,basic))
    pd.DataFrame(results).to_csv(out/"comparison.csv",index=False)
    warm=h.loc[pd.Timestamp(basic["start"])-pd.Timedelta(hours=193):pd.Timestamp(basic["start"])]
    provenance={"basic_config":basic,"model_configs":target_manifest,"data_manifest_sha256":sha(out/"data_manifest.json"),
                "runner_sha256":sha(__file__),"full_config_sha256":sha("config.yaml"),
                "shared_source_sha256":{n:sha(n) for n in ["src/execution/planner.py","src/execution/paper.py","src/api/rules.py","src/contracts.py","src/validation/observed_baseline.py"]},"git_commit":__import__("subprocess").check_output(["git","rev-parse","HEAD"],text=True).strip(),
                "source_hourly_close_first":str(h.index.min()),"source_hourly_close_last":str(h.index.max()),
                "warmup_before_start_rows":len(warm),"warmup_close_missing":int(warm.isna().sum().sum()),
                "warmup_volume_missing":int(v.reindex(warm.index).isna().sum().sum()),
                "failure_counts":failure_counts,
                "warnings":["Retrospective single competition prefix; not model-selection or clone validation",
                            "Hourly decisions plus1h lag; simulated fine-price fills, not actual market executions",
                            "Original clone retains5minlag/equal bootstrap; reference trades have their actual recorded times",
                            "Proxy1bp halfspread before recorded quotes, actual as-of recorded bid/ask thereafter",
                            "Short hit rate counts completed organic cycles only; terminal liquidation does not convert censoring into hits",
                            "Actual recorded opening orders overdraw100k account; preserve the given evidence",
                            "No activity-guard trades injected; same pure model/planner but not full live runner simulation"]}
    (out/"provenance.json").write_text(json.dumps(provenance,indent=2))
    print(pd.DataFrame(results).to_string(index=False))
    print("execution/valuation failures",failure_counts)
if __name__=="__main__":main()
