"""Independent behavioral audit of a frozen study worktree; read-only models."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--study-root",required=True)
    ap.add_argument("--expected-commit",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args(argv)
    root=Path(args.study_root).resolve()
    common=root.parent.parent if root.parent.name==".worktrees" else root
    out=Path(args.out).resolve()
    if common not in out.parents:
        raise ValueError("audit output must remain inside remote project")
    commit=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
    if not commit.startswith(args.expected_commit):
        raise ValueError("study HEAD differs from requested audit revision")
    paths=[root/"src/models/book/_short_study.py",root/"config.yaml"]
    names=["book_short_trend","book_short_rebound","book_short_breakdown"]
    paths += [root/"src/models/book"/(name+".py") for name in names]
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    before={str(p):digest(p) for p in paths}
    sys.path.insert(0,str(root))
    import numpy as np
    import pandas as pd
    from src.config import load_config
    from src.contracts import MarketView,check_targets
    from src.models import get
    from backtest.evaluate import model_modules
    from backtest.scoring.evaluate import model_sources

    cfg=load_config()
    coins=cfg["models"][names[0]]["coins"]
    passed=[]; fingerprints={}
    def check(label,fn):
        fn()
        passed.append(label)
    def fixture(name,hour=1,direction=-1,prior=None,rebound=False,volume=True):
        idx=pd.date_range(end=pd.Timestamp("2026-01-20",tz="UTC")+pd.Timedelta(hours=hour),
                          periods=410,freq="h")
        x=np.arange(len(idx))
        px=100*np.exp(direction*.001*x+.0001*np.sin(x))
        if rebound: px[-1]=px[-25:-1].max()*1.01
        close=pd.DataFrame({c:px*(i+1) for i,c in enumerate(coins)},index=idx)
        qv=pd.DataFrame(100.,index=idx,columns=coins)
        if volume:qv.iloc[-24:]=200.
        return MarketView(idx[-1],close,qv,tuple(coins),cfg["models"][name],
                          pd.Series(dtype=float) if prior is None else prior)
    def changed(v,close=None,qv=None,universe=None):
        return MarketView(v.t,v.close if close is None else close,
                          v.quote_volume if qv is None else qv,
                          v.universe if universe is None else universe,v.params,v.prev_targets)
    def assert_empty(w): assert w.empty or float(w.abs().sum())==0
    for name in names:
        model=get(name)
        modules=model_modules(model)
        assert "src.models.book."+name in modules
        assert "src.models.book._short_study" in modules
        source=model_sources(model)
        assert name in source and 'super().__init__' in source
        fingerprints[name]=hashlib.sha256(source.encode()).hexdigest()
        passed.append(name+":wrapper_and_helper_in_cache_fingerprint")
        v=fixture(name)
        w=check_targets(model.targets(v),v,model.spec)
        assert np.isfinite(w.to_numpy()).all()
        assert float(w.abs().sum())<=v.params["gross_cap"]+1e-12
        assert float(w.abs().max())<=v.params["coin_cap"]+1e-12
        passed.append(name+":gross_coin_caps_and_contract")
        future=v.close.iloc[[-1]].copy()
        future.index+=pd.Timedelta(hours=1);future*=1000
        pd.testing.assert_series_equal(w,model.targets(changed(v,close=pd.concat([v.close,future]))))
        passed.append(name+":future_price_unreachable")
        bad=v.close.copy();bad.loc[bad.index[-100],coins[1]]=np.nan
        ww=model.targets(changed(v,close=bad))
        assert coins[1] not in ww and not ww.empty
        assert np.isfinite(ww.to_numpy()).all()
        passed.append(name+":partial_risk_window_missing_coin_excluded")
        assert_empty(model.targets(changed(v,close=v.close.drop(v.close.index[-100]))))
        passed.append(name+":gapped_clock_fails_closed")
        bad=v.close.copy();bad.iloc[-1]=np.nan
        assert_empty(model.targets(changed(v,close=bad)))
        passed.append(name+":missing_current_prices_fail_closed")
        prior=pd.Series(-.1,index=coins)
        off=fixture(name,hour=2,prior=prior)
        pd.testing.assert_series_equal(model.targets(off),prior)
        passed.append(name+":nondecision_hour_retains_prior")
        off=changed(off,universe=tuple(coins[:-1]))
        assert coins[-1] not in model.targets(off)
        passed.append(name+":removed_universe_coin_not_retained")
        sig=np.log(v.close).diff().tail(v.params["vol_hours"]).std()
        assert float((w.abs()*sig*np.sqrt(24)).sum())<=v.params["target_daily_vol"]+1e-12
        passed.append(name+":perfect_correlation_volatility_budget")
    assert len(set(fingerprints.values()))==3
    passed.append("three_distinct_wrapper_constructor_source_fingerprints")

    name=names[2]; model=get(name)
    for hour in [1,7,13,19]:
        w=model.targets(fixture(name,hour=hour))
        assert not w.empty and (w<0).all()
    for hour in [0,2,6,8,12,14,18,20]:
        assert_empty(model.targets(fixture(name,hour=hour)))
    passed.append("breakdown:exact_sixhour_phase_and_no_bootstrap_bypass")
    v=fixture(name);q=v.quote_volume.copy();q.loc[q.index[-1],coins[1]]=np.nan
    w=model.targets(changed(v,qv=q));assert coins[1] not in w and not w.empty
    passed.append("breakdown:missing_volume_blocks_only_affected_fresh_entry")
    q=v.quote_volume.copy();q.loc[q.index[-1],coins[1]]=-1
    w=model.targets(changed(v,qv=q));assert coins[1] not in w and not w.empty
    passed.append("breakdown:negative_volume_blocks_fresh_entry")
    assert_empty(model.targets(fixture(name,volume=False)))
    prior=pd.Series(-.1,index=coins)
    w=model.targets(fixture(name,volume=False,prior=prior))
    assert not w.empty and (w<0).all()
    passed.append("breakdown:existing_short_persists_without_new_volume_confirmation")
    assert_empty(model.targets(fixture(name,prior=prior,rebound=True,hour=7)))
    passed.append("breakdown:rebound_exit_precedes_reweight_or_entry")

    name=names[1];model=get(name)
    assert_empty(model.targets(fixture(name,hour=7,prior=prior,rebound=True)))
    assert_empty(model.targets(fixture(name,hour=13,prior=pd.Series(dtype=float))))
    passed.append("rebound:exit_then_no_intraday_reentry")
    for name in names[:2]:
        w=get(name).targets(fixture(name,direction=1,prior=prior))
        assert not w.empty and (w>0).all()
        passed.append(name+":daily_short_to_long_flip_uses_new_causal_trend")
    for name in names[:2]:
        assert_empty(get(name).targets(fixture(name,hour=12)))
        passed.append(name+":first_cash_start_offphase_stays_cash")

    if before!={str(p):digest(p) for p in paths}:
        raise ValueError("study source changed during audit")
    finalcommit=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
    if finalcommit!=commit:
        raise ValueError("study HEAD changed during audit")
    report={"study_root":str(root),"commit":commit,"checks_passed":len(passed),
            "checks":passed,"source_hashes":before,"source_fingerprints":fingerprints,
            "status":"PASS","future_profit_or_live_execution_validated":False}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":"PASS","checks":len(passed),"commit":commit,"output":str(out)}))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
