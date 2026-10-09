"""Read-only causal accounting attribution of published model caches."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from src.config import load_config,resolve
from backtest.data import load_market
from backtest.scoring.score2 import load_checkpoint
from backtest.scoring.weak_stats import tail_mean
from research.book.short_validation.run import load_cache,input_hashes,sha

MODELS={
"baitoey_ovl_brk_dual":"f30fa79cde92399a",
"baitoey_vt_dual":"457a15537cb2cb75",
"book_vt_dual":"5ccb581e175dacbe",
"pol_switch_vt_tl_e20v45":"0ec3cf0ca1185b36",
"book_short_trend":"e758f48cfbbba861",
"book_short_rebound":"41ce2438da8f9330",
"book_short_breakdown":"8b75f0d5cd989604",
}
TOP="baitoey_ovl_brk_dual"


def attribute_path(prices,columns,trades,equity,gross,net,e0,close_fee):
    """Reconstruct every cached hour before accepting long/short PnL attribution.

    Each hour earns price PnL on the previous hour's post-fill weights.
    Current-hour fills cannot earn the price move that occurred before them.
    Ordinary fee/spread amounts are subtracted in original-capital units.
    """
    px=np.asarray(prices,float);eq=np.asarray(equity,float)
    gr=np.asarray(gross,float);nt=np.asarray(net,float)
    hours=len(eq)-1
    if px.shape!=(hours+1,len(columns)) or gr.shape!=eq.shape or nt.shape!=eq.shape:
        raise ValueError("attribution dimensions mismatch")
    if not np.isfinite(eq).all() or (eq<=0).any() or abs(eq[0]-1)>1e-12:
        raise ValueError("invalid starting or cached equity")
    if not np.isfinite(e0) or e0<=0 or not np.isfinite(close_fee) or close_fee<0:
        raise ValueError("invalid money settings")
    if trades.duplicated(["hour","series"]).any():
        raise ValueError("duplicate asset fill within clock hour")
    by_hour={int(h):v for h,v in trades.groupby("hour")}
    pos={c:i for i,c in enumerate(columns)}
    w=np.zeros(len(columns));value=1.
    long_pnl=short_pnl=fees=spread=long_turn=short_turn=guard_turn=strategy_turn=0.
    lsexposure=[]
    max_eq_error=max_weight_error=0.
    for h in range(1,hours+1):
        valid=np.isfinite(px[h])&np.isfinite(px[h-1])&(px[h-1]>0)
        r=np.zeros(len(columns))
        r[valid]=px[h,valid]/px[h-1,valid]-1
        parts=value*w*r
        long_pnl+=float(parts[w>0].sum())
        short_pnl+=float(parts[w<0].sum())
        pr=float(w@r)
        if pr!=0:
            value*=1+pr
            w=w*(1+r)/(1+pr)
        fill=by_hour.get(h)
        if fill is not None:
            for row in fill.itertuples():
                if row.series not in pos:
                    raise ValueError("fill asset missing from price panel")
                i=pos[row.series]
                err=abs(w[i]-float(row.w_before))
                max_weight_error=max(max_weight_error,err)
                if err>1e-10:
                    raise ValueError("ledger before-weight does not reproduce")
                long_turn+=abs(max(row.w_after,0)-max(row.w_before,0))
                short_turn+=abs(min(row.w_after,0)-min(row.w_before,0))
                if row.kind=="guard":guard_turn+=abs(row.w_after-row.w_before)
                else:strategy_turn+=abs(row.w_after-row.w_before)
                w[i]=float(row.w_after)
            fee=float(fill.fee_usd.sum()/e0)
            sp=float(fill.spread_usd.sum()/e0)
            if fee<0 or sp<0:
                raise ValueError("negative execution cost")
            fees+=fee;spread+=sp;value-=fee+sp
        error=abs(value-eq[h]);max_eq_error=max(max_eq_error,error)
        if error>1e-10:
            raise ValueError("cached equity path does not reproduce")
        if abs(np.abs(w).sum()-gr[h])>1e-10 or abs(w.sum()-nt[h])>1e-10:
            raise ValueError("cached exposure path does not reproduce")
        lsexposure.append([np.maximum(w,0).sum(),np.maximum(-w,0).sum()])
    liquidation=value*close_fee*gr[-1]
    result=long_pnl+short_pnl-fees-spread-liquidation
    expected=eq[-1]*(1-close_fee*gr[-1])-1
    identity_error=abs(result-expected)
    if identity_error>1e-10:
        raise ValueError("long-short-cost identity failed")
    exposure=np.asarray(lsexposure)
    return {"return":expected,"long_pnl":long_pnl,"short_pnl":short_pnl,
            "fees":fees,"spread":spread,"liquidation":liquidation,
            "long_mean":float(exposure[:,0].mean()),"short_mean":float(exposure[:,1].mean()),
            "gross_mean":float(exposure.sum(axis=1).mean()),
            "net_mean":float((exposure[:,0]-exposure[:,1]).mean()),
            "long_turnover":long_turn,"short_turnover":short_turn,
            "guard_turnover":guard_turn,"strategy_turnover":strategy_turn,
            "max_equity_error":max_eq_error,"max_before_weight_error":max_weight_error,
            "identity_error":identity_error}


def run(out_dir):
    cfg=load_config();cp=load_checkpoint(cfg)
    cp["registry"]=str(resolve(cfg["book_score2"]["registry"]).resolve())
    before=input_hashes(cfg,cp)
    market=load_market(cfg)
    grid=pd.date_range(market.close.index[0],market.close.index[-1],freq="h")
    prices=market.close.reindex(grid).ffill()
    cases=cp["cases"]
    support=cases[["weak_archived","weak_fresh_btc","positive_control"]].any(axis=1)
    cases=cases.loc[support]
    frames=[];sources={}
    for name,key in MODELS.items():
        original=cp["source_caches"].get(name)
        fixed=original is not None and original["run_key"]==key
        eq,gross,trades,source=load_cache(name,key,cp,fixed=fixed)
        sources[name]=source
        path=resolve(cp["base"]["cache_dir"]).resolve()/name/key
        with np.load(Path(str(path)+".arrays.npz"),allow_pickle=False) as arr:
            net=arr["net"].copy()
        columns=list(trades.series.unique())
        if not set(columns)<=set(prices.columns):
            raise ValueError("traded assets missing from historical panel")
        px=prices.reindex(columns=columns).to_numpy(float)
        grouped={t:g for t,g in trades.groupby("window_start")}
        for start,case in cases.iterrows():
            row=cp["starts"].get_loc(start);i=grid.get_loc(start)
            fills=grouped.get(start,trades.iloc[:0])
            fills=fills.loc[(fills.hour>0)&(fills.hour<=228)]
            values=attribute_path(px[i:i+229],columns,fills,eq[row,:229],gross[row,:229],
                                  net[row,:229],cfg["scoring"]["e0"],cfg["scoring"]["liquidation_cost"])
            frames.append({"model":name,"run_key":key,"window_start":start,**case.to_dict(),**values})
    windows=pd.DataFrame(frames)
    summaries=[];paired=[]
    for profile in ["weak_archived","weak_fresh_btc","positive_control"]:
        for name in MODELS:
            part=windows.loc[(windows.model==name)&windows[profile]]
            for scenario in ["all","future_down","future_rebound"]:
                sub=part
                if scenario!="all":
                    if "future_return" not in sub:
                        raise ValueError("saved240h BTC outcome absent")
                    future=sub["future_return"]
                    threshold=cp["c"]["stress"]["future_down" if scenario=="future_down" else "future_rebound"]
                    sub=sub.loc[future<=threshold] if scenario=="future_down" else sub.loc[future>=threshold]
                if sub.empty:continue
                record={"profile":profile,"model":name,"scenario":scenario,"n":len(sub)}
                for column in ["return","long_pnl","short_pnl","fees","spread","liquidation","long_mean",
                               "short_mean","gross_mean","net_mean","long_turnover","short_turnover",
                               "guard_turnover","strategy_turnover"]:
                    record[column+"_mean"]=float(sub[column].mean())
                record.update(return_median=float(sub["return"].median()),
                              return_p10=float(sub["return"].quantile(.1)),
                              return_tail10=tail_mean(sub["return"],.1),
                              return_worst=float(sub["return"].min()))
                summaries.append(record)
        top=windows.loc[(windows.model==TOP)&windows[profile]].set_index("window_start")["return"]
        for name in MODELS:
            sub=windows.loc[(windows.model==name)&windows[profile]].set_index("window_start")
            delta=sub["return"]-top.reindex(sub.index)
            paired.append({"profile":profile,"model":name,"baseline":TOP,"n":len(delta),
                           "paired_mean":float(delta.mean()),"paired_median":float(delta.median()),
                           "paired_p10":float(delta.quantile(.1)),"paired_wins":float((delta>0).mean())})
    after=input_hashes(cfg,cp)
    if before!=after:raise ValueError("source inputs changed")
    for source in sources.values():
        for item in list(source["files"].values())+source["score_sources"]:
            if sha(item["path"])!=item["sha256"]:raise ValueError("cache changed during attribution")
    out=Path(out_dir).resolve()
    root=resolve("results/book").resolve()
    if root not in out.parents:raise ValueError("dedicated Book output directory required")
    out.mkdir(parents=True,exist_ok=True)
    windows.to_csv(out/"window_attribution.csv",index=False)
    summary=pd.DataFrame(summaries)
    summary.to_csv(out/"profile_attribution.csv",index=False)
    pd.DataFrame(paired).to_csv(out/"paired_top.csv",index=False)
    manifest={"protocol":cp["protocol"],"primary_metric_changed":False,"source_inputs":before,
              "model_keys":MODELS,"cache_sources":sources,"cases":len(cases),"source_sha256":sha(__file__),
              "all_hourly_paths_reproduced":True,"attribution_is_retrospective":True,
              "outputs":{p.name:sha(p) for p in out.glob("*.csv")}}
    (out/"attribution_manifest.json").write_text(json.dumps(manifest,indent=2,default=str))
    print(summary.loc[(summary.profile=="weak_archived")&(summary.scenario=="all"),
        ["model","return_mean","long_pnl_mean","short_pnl_mean","fees_mean","spread_mean",
         "long_mean_mean","short_mean_mean","long_turnover_mean","short_turnover_mean"]].to_string(index=False))
    print("case_columns",list(cases.columns))

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",required=True)
    a=ap.parse_args(argv);run(a.out)
if __name__=="__main__":main()
