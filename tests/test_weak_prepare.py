"""Preparation rejects ticker gaps and keeps fresh-cash state matching causal."""
from pathlib import Path
import zipfile
import numpy as np
import pandas as pd
import pytest
from research.book.weak_eval.prepare import (
    archive_frame, build_states, join_panels, require_query_coverage, exclude_irrelevant_offgrid, reference_breadth, apply_verified_archives, require_verified_reference,
)


def frames():
    ix=pd.date_range("2026-10-07 22:00",periods=6,freq="h",tz="UTC")
    return pd.DataFrame({"BTCUSDT":range(100,106)},index=ix,dtype=float)


def feature_cfg():
    return {"features":{"FAST":["btc_ret48"],"BREADTH":["breadth48"]},
            "minimum_hour_coverage":.98,"min_breadth_coins":20,"breadth_hours":48}


def test_join_never_overwrites_immutable_history_or_uses_ticker_only_future():
    x=frames();h=x.iloc[:2].copy();l=x.copy();l.iloc[0,0]=999
    result,q=join_panels(h,h*10,l,l*10,x.index[4],x.index[3])
    assert result.iloc[0,0]==100
    assert result.index.max()==x.index[3]
    assert q.index.equals(result.index)


def test_join_rejects_timezone_naive_and_duplicate_bars():
    x=frames();bad=x.copy();bad.index=bad.index.tz_localize(None)
    with pytest.raises(ValueError,match="UTC"):join_panels(bad,bad,x,x,x.index[-1],x.index[-1])
    bad=pd.concat([x,x.iloc[:1]])
    with pytest.raises(ValueError,match="unique"):join_panels(x,x,bad,bad,x.index[-1],x.index[-1])


def test_state_build_uses_actual_cash_start_not_four_day_future(monkeypatch):
    calls=[]
    def fake(close,qv,times,validation,cfg):
        times=pd.DatetimeIndex(times);calls.append((times.copy(),cfg["state_grid_hour_utc"]))
        return pd.DataFrame({"btc_ret48":-.01,"breadth48":.1,"universe_n":30,"breadth_valid_n":30},index=times)
    monkeypatch.setattr("research.book.weak_eval.prepare.build_features",fake)
    x=frames();starts=pd.DatetimeIndex([x.index[0],x.index[1]])
    out=build_states(x,x,starts,x.index[2],{},feature_cfg())
    assert len(calls)==3
    assert calls[0][0][0]==starts[0]
    assert calls[1][0][0]==starts[1]
    assert calls[2][0][0]==x.index[2]
    assert out["historical_features"].index.equals(starts)


def test_query_coverage_preserves_29_of_30_failure():
    q=pd.Series({"btc_ret48":-.02,"breadth48":np.nan,"universe_n":30,"breadth_valid_n":29})
    with pytest.raises(ValueError,match="29/30"):require_query_coverage(q,feature_cfg())
    q["breadth48"]=.1
    with pytest.raises(ValueError,match="29/30"):require_query_coverage(q,feature_cfg())


def test_query_coverage_requires_finite_features_and_minimum_universe():
    q=pd.Series({"btc_ret48":np.nan,"breadth48":.1,"universe_n":30,"breadth_valid_n":30})
    with pytest.raises(ValueError,match="finite"):require_query_coverage(q,feature_cfg())
    q=pd.Series({"btc_ret48":-.01,"breadth48":.1,"universe_n":10,"breadth_valid_n":10})
    with pytest.raises(ValueError,match="universe"):require_query_coverage(q,feature_cfg())


def make_zip(tmp_path,missing=False,duplicate=False,microseconds=True):
    day=pd.Timestamp("2026-10-08",tz="UTC")
    times=pd.date_range(day,periods=24,freq="h")
    if missing:times=times[:-1]
    if duplicate:times=times.append(times[-1:])
    rows=[]
    for t in times:
        unit=1000000 if microseconds else 1000
        a=int(t.timestamp()*unit);b=int((t+pd.Timedelta(hours=1)).timestamp()*unit)-1
        rows.append(f"{a},100,102,99,101,1,{b},101,1,0,0,0")
    path=tmp_path/"BTCUSDT-1h-2026-10-08.zip"
    with zipfile.ZipFile(path,"w") as z:z.writestr("data.csv","\n".join(rows))
    return path,day


@pytest.mark.parametrize("microseconds",[True,False])
def test_archive_requires_full_closed_grid_and_converts_time_units(tmp_path,microseconds):
    p,day=make_zip(tmp_path,microseconds=microseconds)
    f=archive_frame(p,day)
    assert len(f)==24
    assert f.index.min()==day+pd.Timedelta(hours=1)
    assert f.index.max()==day+pd.Timedelta(days=1)
    assert f["close"].eq(101).all()


@pytest.mark.parametrize("missing,duplicate",[(True,False),(False,True)])
def test_archive_rejects_incomplete_or_duplicate_day(tmp_path,missing,duplicate):
    p,day=make_zip(tmp_path,missing,duplicate)
    with pytest.raises(ValueError,match="24"):archive_frame(p,day)


def test_future_prices_are_clipped_before_building_query(monkeypatch):
    def fake(close,qv,times,validation,cfg):
        assert close.index.max()<=max(times)
        return pd.DataFrame({"btc_ret48":-.01,"breadth48":.1,"universe_n":30,"breadth_valid_n":30},index=pd.DatetimeIndex(times))
    monkeypatch.setattr("research.book.weak_eval.prepare.build_features",fake)
    x=frames()
    build_states(x,x,pd.DatetimeIndex([x.index[0]]),x.index[2],{},feature_cfg())


def test_prepare_freezes_two_profiles_and_rejects_definition_changes(tmp_path,monkeypatch):
    from research.book.weak_eval.prepare import prepare
    import copy,json
    hist=tmp_path/"hist";live=tmp_path/"live";hist.mkdir();live.mkdir()
    ix=pd.date_range("2026-09-01 12:00",periods=30,freq="D",tz="UTC")
    symbols=["BTCUSDT","BCHUSDT"]+[f"C{i}USDT" for i in range(28)]
    hp=pd.DataFrame(100.,index=ix,columns=symbols);hq=hp*10
    lp=pd.DataFrame(101.,index=pd.date_range(ix[-1],pd.Timestamp("2026-10-09 00:00Z"),freq="h"),columns=symbols)
    lp.loc[pd.Timestamp("2026-10-09 00:00Z"),"BCHUSDT"]=np.nan
    lq=lp*10
    hp.to_parquet(hist/"panel_close_1h.parquet");hq.to_parquet(hist/"panel_quote_volume_1h.parquet")
    lp.to_parquet(live/"close_1h.parquet");lq.to_parquet(live/"qv_1h.parquet")
    (live/"store_meta.json").write_text(json.dumps({"complete_through":"2026-10-08 00:00Z","ticker_only":["2026-10-09 00:00Z"]}))
    monkeypatch.setattr("research.book.weak_eval.prepare.safe_path",lambda x:Path(x))
    def fake(close,qv,times,validation,cfg):
        times=pd.DatetimeIndex(times);fresh=times==pd.Timestamp("2026-10-09 00:00Z")
        return pd.DataFrame({"btc_ret48":-.01,"breadth48":np.where(fresh,np.nan,.1),
             "universe_n":30,"breadth_valid_n":np.where(fresh,29,30)},index=times)
    monkeypatch.setattr("research.book.weak_eval.prepare.build_features",fake)
    cfg={"book_weak_eval":{"asof":"2026-10-09 00:00Z","reference_asof":"2026-10-08 00:00Z",
         "out_dir":str(tmp_path/"out"),"historical_panel":str(hist),"live_panel":str(live)},
         "book_regime_eval":feature_cfg(),"validation":{"universe":{"exclude":[],"stablecoins":[],
             "leveraged_regex":".*UPUSDT$","min_history_days":0,"volume_days":30,"top_n":30}}}
    result=prepare(cfg,ix[:3],archive_evidence=[{"status":"HTTP404"}])
    assert result["query"].breadth_valid_n==30
    assert result["fresh_query"].breadth_valid_n==29
    assert np.isnan(result["fresh_query"].breadth48)
    assert result["input_manifest"]["reference_age_hours"]==24
    assert result["input_manifest"]["fresh_archive_confirmed"] is False
    repeated=prepare(cfg,ix[:3])
    pd.testing.assert_frame_equal(result["historical_features"],repeated["historical_features"],check_freq=False)
    changed=copy.deepcopy(cfg);changed["book_regime_eval"]["minimum_hour_coverage"]=.9
    with pytest.raises(ValueError,match="definition"):prepare(changed,ix[:3])
    (tmp_path/"out"/"query_features.parquet").write_bytes(b"corrupt")
    with pytest.raises(ValueError,match="snapshot changed"):prepare(cfg,ix[:3])


def test_offgrid_source_rows_outside_all_feature_warmup_are_explicitly_excluded():
    x=frames()
    extra=x.iloc[:1].copy();extra.index=extra.index-pd.Timedelta(days=1000)+pd.Timedelta(minutes=28)
    bad=pd.concat([extra,x]).sort_index()
    p,q,rows=exclude_irrelevant_offgrid(bad,bad,x.index[0]-pd.Timedelta(days=201))
    pd.testing.assert_frame_equal(p,x,check_freq=False)
    assert len(rows)==1
    assert rows[0]["reason"]=="off-grid timestamp outside all candidate feature warmup"
    with pytest.raises(ValueError,match="usable feature history"):
        exclude_irrelevant_offgrid(bad,bad,bad.index[0]-pd.Timedelta(hours=1))


def test_recent_breadth_never_replaces_missing_reference_coin():
    t=pd.Timestamp("2026-10-09 00:00Z")
    symbols=["BTCUSDT","BCHUSDT"]+[f"C{i}USDT" for i in range(28)]
    p=pd.DataFrame(100.,index=pd.DatetimeIndex([t-pd.Timedelta(hours=48),t]),columns=symbols+["REPLACEMENTUSDT"])
    p.loc[t,"BCHUSDT"]=np.nan
    result=reference_breadth(p,symbols,t,{"breadth_hours":48,"minimum_hour_coverage":.98,"min_breadth_coins":20,"breadth_hours":48})
    assert result["universe_n"]==30
    assert result["breadth_valid_n"]==29
    assert np.isnan(result["breadth48"])
    assert np.isnan(result["alt_minus_btc48"])


def test_verified_public_override_uses_copies_and_rejects_changed_archive(tmp_path):
    import json,hashlib
    p,day=make_zip(tmp_path)
    raw=tmp_path/"public_archive"/"BTCUSDT";raw.mkdir(parents=True)
    new=raw/p.name;p.rename(new)
    digest=hashlib.sha256(new.read_bytes()).hexdigest()
    record={"file":"BTCUSDT/"+new.name,"symbol":"BTCUSDT","period":"2026-10-08","status":"ok","sha256":digest}
    (tmp_path/"archive_downloads.jsonl").write_text(json.dumps(record)+"\n")
    x=frames();original=x.copy()
    a,b,proof=apply_verified_archives(x,x,tmp_path,day+pd.Timedelta(days=1))
    pd.testing.assert_frame_equal(x,original)
    assert a.loc[day+pd.Timedelta(hours=1),"BTCUSDT"]==101
    assert b.loc[day+pd.Timedelta(hours=1),"BTCUSDT"]==101
    assert len(proof["records"])==1
    new.write_bytes(b"changed")
    with pytest.raises(ValueError,match="checksum"):apply_verified_archives(x,x,tmp_path,day+pd.Timedelta(days=1))


def test_reference_requirements_include_volatility_midnight_anchor_and_new_universe_coins():
    t=pd.Timestamp("2026-10-08 00:00Z");symbols=["BTCUSDT","BCHUSDT"]
    records=[{"symbol":s,"period":d} for s in symbols for d in ["2026-10-05","2026-10-06","2026-10-07"]]
    records += [{"symbol":"BTCUSDT","period":t.strftime("%Y-%m-%d")} for t in pd.date_range("2026-09-30","2026-10-04",freq="D")]
    proof={"records":records}
    result=require_verified_reference(proof,symbols,t,{"volatility_hours":[168,720]})
    assert result["btc_days"][0]=="2026-09-30"
    assert result["all_required_archives_verified"]
    with pytest.raises(ValueError,match="NEWUSDT"):
        require_verified_reference(proof,symbols+["NEWUSDT"],t,{"volatility_hours":[168,720]})
    with pytest.raises(ValueError,match="2026-09-30"):
        require_verified_reference({"records":[r for r in records if r["period"]!="2026-09-30"]},symbols,t,{"volatility_hours":[168,720]})
