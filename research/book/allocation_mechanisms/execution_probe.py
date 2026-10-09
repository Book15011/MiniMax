"""Shared-broker execution evaluation of research-directed allocation mechanisms."""
import argparse,hashlib,itertools,json,sys
from pathlib import Path
import numpy as np,pandas as pd,yaml
from probe import CFG,portfolio_features,bounded_weights
sys.path.insert(0,CFG["source_worktree"])
from src.validation.observed_study import load_market,score_parts
from src.validation.observed_baseline import broker_replay,match_events,weights_from_hourly

def mechanism_weights(hourly,times,params):
 cols=[a+"USDT" for a in CFG["assets"]];h=hourly[cols]
 if params["kind"]=="single":
  v=portfolio_features(h,times,params["family"],int(params["lookback"]),int(params["lag"]),int(params["vol_window"]),params["shrink"],params["transform"],int(params["fast"]))
 else:
  raw=portfolio_features(h,times,"ema",int(params["lookback"]),int(params["lag"]),int(params["vol_window"]),1.,"raw",int(params["fast"]))
  vol=np.stack([h.loc[:t-pd.Timedelta(hours=int(params["lag"]))].pct_change(fill_method=None).tail(int(params["vol_window"])).std().values for t in times])
  v=np.clip(raw/params["forecast_clip"],-1,1)/vol**int(params["power"])
 w=bounded_weights(v,params["k"],params["cap"],CFG["gross_limit"])
 return {t:pd.Series(row,index=cols) for t,row in zip(times,w)}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--predict-only",action="store_true");args=ap.parse_args()
 out=Path(CFG["output"]);base=yaml.safe_load(Path(CFG["corrected_config"]).read_text())
 q,p,h=load_market(base)
 q=q.loc[(q.ts_utc.dt.hour==CFG["execution"]["quote_hour_utc"])&q.ts_utc.dt.minute.between(CFG["execution"]["quote_minute_minimum"],CFG["execution"]["quote_minute_maximum"])]
 times=[pd.Timestamp(str(d)+"T%02d:00Z"%CFG["decision_hour_utc"]) for d in CFG["dates"]]
 if args.predict_only:
  frozen=json.loads((out/"execution_selection_freeze.json").read_text())
  cfg={**base,**frozen["execution"],"initial_equal":False};wt=mechanism_weights(h,times,frozen["params"])
  ev,path,dec=broker_replay(p,cfg,q,wt);ev.to_csv(out/"prediction_without_log_events.csv",index=False)
  print(json.dumps({"predicted":len(ev),"sha256":hashlib.sha256((out/"prediction_without_log_events.csv").read_bytes()).hexdigest()}));return
 e=pd.read_csv(base["input"]);e["time_utc"]=[pd.Timestamp(r.date+" "+r.time,tz="Asia/Hong_Kong").tz_convert("UTC") for _,r in e.iterrows()]
 tr=e.loc[e.date<=base["train_last_date"]]
 short=[]
 for table,kind in (("mechanism_shortlist.csv","single"),("twostage_shortlist.csv","two")):
  tab=pd.read_csv(out/table)
  for _,r in tab.iterrows():
   pars={k:(v.item() if hasattr(v,"item") else v) for k,v in r.to_dict().items() if k not in ("candidate","train_mae","later_mae","all_mae","train_sign","later_sign")}
   pars["kind"]=kind;short.append((kind+"-"+str(int(r.candidate)),pars,float(r.train_mae)))
 (out/"execution_protocol.json").write_text(json.dumps({"shortlist_count":len(short),"variants":CFG["execution"],"selection":"training strict F1 then action-only F1 then smaller train target MAE then smaller delay/band and candidate order","later_status":"previously seen retrospective diagnostic, never used to select parameters","no_initial_bootstrap":True},indent=2))
 cutoff=pd.Timestamp(CFG["execution"]["train_last_timestamp"]);trainp=p.loc[p.index<=cutoff]
 trainq=q.loc[q.ts_utc<=cutoff];traint=[t for t in times if t<=cutoff]
 trials=[];best=None;per_model={}
 for number,(ident,pars,mae) in enumerate(short):
  wt=mechanism_weights(h,traint,pars)
  for delay,band in itertools.product(CFG["execution"]["delays_minutes"],CFG["execution"]["rebalance_bands"]):
   cfg={**base,"end":str(cutoff),"delay_minutes":delay,"band":band,"initial_equal":False}
   ev,path,dec=broker_replay(trainp,cfg,trainq,wt)
   m=match_events(tr,ev,base["match_seconds"],base["match_quantity_relative"]);dm=match_events(tr,ev,base["match_seconds"],base["match_quantity_relative"],False)
   row=dict(candidate=ident,delay_minutes=delay,band=band,target_train_mae=mae,matched=m["matched"],predicted=m["predicted"],precision=m["precision"],recall=m["recall"],f1=m["f1"],direction_f1=dm["f1"])
   trials.append(row);key=(m["f1"],dm["f1"],-mae,-delay,-band,-number)
   record=(key,pars,{"delay_minutes":delay,"band":band},row)
   if best is None or key>best[0]:best=record
   if ident not in per_model or key>per_model[ident][0]:per_model[ident]=record
 pd.DataFrame(trials).to_csv(out/"execution_training_trials.csv",index=False)
 frozen={"params":best[1],"execution":best[2],"selection":best[3],"trained_through":str(cutoff),"input_sha256":hashlib.sha256(Path(base["input"]).read_bytes()).hexdigest(),"target_grid_config_sha256":hashlib.sha256((Path(__file__).parent/"config.yaml").read_bytes()).hexdigest(),"later_status":"previously seen retrospective diagnostic"}
 (out/"execution_selection_freeze.json").write_text(json.dumps(frozen,indent=2))
 cfg={**base,**best[2],"initial_equal":False};wt=mechanism_weights(h,times,best[1]);ev,path,dec=broker_replay(p,cfg,q,wt)
 ev.to_csv(out/"selected_events.csv",index=False);path.to_csv(out/"selected_equity.csv",index=False);(out/"selected_decisions.json").write_text(json.dumps(dec,indent=2))
 scores=score_parts(e,ev,cfg);scores["selection"]=frozen;scores["return_at_cutoff"]=float(path.iloc[-1].equity/base["seed"]-1)
 pairs={x["observed_index"]:x["predicted_index"] for x in scores["all"]["pairs"]}
 comparison=[]
 for i,r in e.iterrows():
  j=pairs.get(i);v=ev.iloc[j] if j is not None else None
  comparison.append(dict(trade_id=r.trade_id,date=r.date,asset=r.asset,action=r.action,observed_quantity=r.quantity,observed_time=str(r.time_utc),matched=j is not None,predicted_quantity=float(v.quantity) if v is not None else None,predicted_time=str(v.time_utc) if v is not None else ""))
 pd.DataFrame(comparison).to_csv(out/"selected_event_comparison.csv",index=False)
 (out/"selected_metrics.json").write_text(json.dumps(scores,indent=2))
 later=[];bestmodels=[]
 # All fixed mechanism comparisons are descriptive, not a later-based selection.
 for ident,(key,pars,execpars,row) in per_model.items():
  c={**base,**execpars,"initial_equal":False};v=mechanism_weights(h,times,pars);orders,equity,dec=broker_replay(p,c,q,v)
  metrics=score_parts(e,orders,c)
  later.append(dict(candidate=ident,training_matches=metrics["training"]["matched"],training_f1=metrics["training"]["f1"],later_matches=metrics["validation"]["matched"],later_precision=metrics["validation"]["precision"],later_recall=metrics["validation"]["recall"],later_f1=metrics["validation"]["f1"],all_matches=metrics["all"]["matched"],all_precision=metrics["all"]["precision"],all_recall=metrics["all"]["recall"],all_f1=metrics["all"]["f1"],delay_minutes=execpars["delay_minutes"],band=execpars["band"]))
  bestmodels.append(dict(candidate=ident,params=pars,execution=execpars))
 pd.DataFrame(later).to_csv(out/"all_shortlist_retrospective_diagnostics.csv",index=False)
 (out/"all_shortlist_frozen_parameters.json").write_text(json.dumps(bestmodels,indent=2))
 origwt=weights_from_hourly(h,base);oe,op,od=broker_replay(p,base,q,origwt)
 original=score_parts(e,oe,base);(out/"original_frozen_metrics.json").write_text(json.dumps(original,indent=2))
 print(json.dumps({"selection":best[3],"all":{k:v for k,v in scores["all"].items() if k not in ("pairs","direction_only")},"training":{k:v for k,v in scores["training"].items() if k not in ("pairs","direction_only")},"later":{k:v for k,v in scores["validation"].items() if k not in ("pairs","direction_only")},"return":scores["return_at_cutoff"],"original_all_matches":original["all"]["matched"]},indent=2))
if __name__=="__main__":main()
