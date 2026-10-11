"""Fixed offline diagnostic: complete bars, frozen costs, no network or orders."""
from pathlib import Path
import hashlib
import importlib.util
import json

import numpy as np
import pandas as pd

from src.config import load_config
from src.models import get
from backtest.engine import Costs,Simulator,compute_targets,decision_times

ROOT=Path("/home/ubuntu/test/MiniMax/.worktrees/book-book-high-recovery")
MAIN=ROOT.parents[1]
T0=pd.Timestamp("2026-10-12 00:00",tz="UTC")
T1=pd.Timestamp("2026-10-15 00:00",tz="UTC")

def ready(last):
    return pd.Timestamp(last)>=T1

def data_problem(close,qv,complete):
    """No scores from an incomplete clock, even if a future placeholder exists."""
    if not ready(complete):
        return "Store complete_through has not reached the frozen endpoint"
    for frame in (close,qv):
        if not frame.index.is_unique or not frame.index.is_monotonic_increasing:
            return "Input clock is duplicated or unsorted"
        if frame.index.tz is None:
            return "Input clock has no timezone"
        expected=pd.date_range(T0,T1,freq="h")
        if not expected.isin(frame.index).all():
            return "Frozen period has missing hourly rows"
    if "BTCUSDT" not in close:
        return "BTC clock missing"
    btc=close.loc[T0:T1,"BTCUSDT"].to_numpy()
    if not np.isfinite(btc).all() or not (btc>0).all():
        return "Frozen BTC clock contains invalid prices"
    return None

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    out=MAIN/"results/book/20261012-high-forward-v1"
    out.mkdir(exist_ok=True)
    if (out/"complete.json").exists():
        print("Frozen forward results already exist; unchanged.")
        return
    freeze=json.loads(Path(__file__).with_name("forward_freeze.json").read_text())
    assert pd.Timestamp(freeze["start"])==T0 and pd.Timestamp(freeze["end"])==T1
    assert digest(Path(__file__))==freeze["forward_evaluator_sha256"],"Forward evaluator changed"
    cfg=load_config()
    assert digest(ROOT/"config.yaml")==freeze["config_sha256"],"Configuration changed"
    for name,params in freeze["params"].items():
        assert cfg["models"][name]==params,"Parameters changed"
    for rel,expected in freeze["source_sha256"].items():
        assert digest(ROOT/rel)==expected,"Source changed: "+rel
    reader=MAIN/"results/book/paper-live/paper_live.py"
    assert digest(reader)==freeze["market_reader_sha256"],"Market reader changed"
    store=MAIN/"results/book/shadow/h1"
    paths=[store/n for n in ["close_1h.parquet","qv_1h.parquet","store_meta.json"]]
    before={str(path):digest(path) for path in paths}
    close=pd.read_parquet(paths[0])
    qv=pd.read_parquet(paths[1])
    complete=pd.Timestamp(json.loads(paths[2].read_text())["complete_through"])
    problem=data_problem(close,qv,complete)
    def wait(reason):
        (out/"waiting.json").write_text(json.dumps({
            "status":"WAITING","reason":reason,"available_through":str(close.index[-1]),
            "complete_through":str(complete),"required_through":str(T1),"scores_produced":False
        },indent=2))
        print("WAITING:",reason,"; no scores produced.")
    if problem:
        wait(problem)
        return
    spec=importlib.util.spec_from_file_location("book_forward_market_reader",reader)
    pl=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pl)
    pl.STORE=store
    mk=pl.load_market(cfg)
    mk.close=mk.close.loc[:T1]
    mk.quote_volume=mk.quote_volume.loc[:T1]
    mk.universe_by_day=mk.universe_by_day.loc[:T1]
    # Fix spread assumptions rather than discovering a newer snapshot after the test.
    mk.half_spread=pd.Series(freeze["half_spread"],dtype=float).reindex(mk.close.columns)
    h=cfg["harness"]
    prepared=[]
    for name in freeze["names"]:
        model=get(name)
        grid=decision_times(mk.close.index,model.spec.rebalance_hours,h["grid_hour_utc"],T0,T1)
        times=pd.DatetimeIndex([T0]+[t for t in grid if t>T0])
        targets=compute_targets(model,mk,times,freeze["params"][name])
        assert np.isfinite(targets.to_numpy()).all(),"Nonfinite weights"
        assert (targets.abs().sum(axis=1)<=1+1e-10).all(),"Gross exposure exceeds 100%"
        held=targets.columns[targets.abs().max()>1e-12]
        prices=mk.close.loc[T0:T1,held].to_numpy()
        if not np.isfinite(prices).all() or not (prices>0).all():
            wait("A potentially held coin has unavailable prices after allowed fill")
            return
        assert np.isfinite(mk.half_spread.reindex(held)).all(),"Frozen spread missing"
        prepared.append((name,model,targets))
    assert before=={str(path):digest(path) for path in paths},"Store changed while loading"
    rows=[]
    arrays={}
    for name,model,targets in prepared:
        sim=Simulator(
            mk,targets,model.spec.band,Costs(h["fees"]["taker"],h["fees"]["short"]),
            h["execution_lag_hours"],h["grid_hour_utc"],h["activity_guard_offset_hours"],
            h["keep_alive_weight"],guard_utc_day=h["guard_utc_day"])
        result=sim.run(sim.index.get_loc(T0),int((T1-T0)/pd.Timedelta(hours=1)),trace=True)
        equity,gross=result.equity,result.trace["gross"]
        assert np.isfinite(equity).all() and np.isfinite(gross).all()
        arrays[name]=(equity,gross)
        rows.append({
            "model":name,"return":float(equity[-1]*(1-cfg["scoring"]["liquidation_cost"]*gross[-1])-1),
            "mdd":float(-(equity/np.maximum.accumulate(equity)-1).min()),
            "actual_account":False,"production_eligible":False})
    assert before=={str(path):digest(path) for path in paths},"Store changed during scoring"
    # Publish only after the complete cohort passes all input and integrity checks.
    mk.close.to_parquet(out/"close_snapshot.parquet")
    mk.quote_volume.to_parquet(out/"qv_snapshot.parquet")
    mk.universe_by_day.to_frame("universe").to_parquet(out/"universe_snapshot.parquet")
    for name,(equity,gross) in arrays.items():
        np.savez_compressed(out/f"{name}.npz",equity=equity,gross=gross)
    pd.DataFrame(rows).to_csv(out/"results.csv",index=False)
    (out/"complete.json").write_text(json.dumps({
        "status":"PASS","period":[str(T0),str(T1)],"single_path_only":True,
        "actual_account":False,"production_eligible":False,
        "source_commit":freeze["source_commit"],"input_hashes":before,
        "freeze_sha256":digest(Path(__file__).with_name("forward_freeze.json"))
    },indent=2))

if __name__=="__main__":
    main()
