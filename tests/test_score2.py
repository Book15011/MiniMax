"""Fixed-checkpoint score2 arithmetic, compatibility and automatic publication."""
import copy,hashlib,json,logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
import pytest
from backtest.scoring import score2

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

@pytest.fixture
def setup(tmp_path,monkeypatch):
    monkeypatch.setattr(score2,"safe_path",lambda p:Path(p))
    lock=score2.locked
    monkeypatch.setattr(score2,"locked",lambda name:lock(name,tmp_path/"locks"))
    cp=tmp_path/"checkpoint";cp.mkdir()
    cache=tmp_path/"cache";storage=tmp_path/"storage"
    starts=pd.date_range("2020-01-01 12:00",periods=4,freq="30D",tz="UTC")
    eq=np.array([[1,.95,.8,.85,.88],[1,1.1,1.2,1.1,1.08],[1,1,1,1,1],[1,1,1,1,1]],float)
    gross=np.full_like(eq,.5);gross[:,0]=0
    c={"schema_version":1,"tool_version":"same","incumbent":"book_inc","prefix_hours":2,
       "horizon_hours":4,"close_fee":.001,"asof":"2026-10-08 12:00:00+00:00",
       "cache_dir":str(cache),"bootstrap":{"reps":100,"seed":23,"level":.9}}
    base={"tool_version":"same","windows":{"full_run":True},"data":{"panel":"fixed"},
          "inputs_sha256":{"weights":"fixed"},"model":{"candidate":True,"author":"book"},
          "per_window":{"start":list(map(str,starts))},"eligible":True,
          "gates":{"G1":{"hard":True,"pass":True}},
          "return_first":{"full":{"headline_ret":.5,"cs_hit":.3}}}
    def save(name,key,equity=eq):
        s=copy.deepcopy(base);s["model"].update(name=name,run_key=key)
        s["per_window"]["R_liq"]=(equity[:,-1]*(1-.001*gross[:,-1])-1).tolist()
        p=cache/name/key;p.parent.mkdir(parents=True,exist_ok=True)
        np.savez(str(p)+".arrays.npz",equity=equity,gross=gross)
        pd.DataFrame(index=starts).to_parquet(str(p)+".windows.parquet")
        Path(str(p)+".json").write_text(json.dumps({"key":key,"tool_version":"same","model":name}))
        return s
    score=save("book_inc","inc-key");source=tmp_path/"score.json";source.write_text(json.dumps(score))
    pd.DataFrame({"weight":[1/3]*3,"selected":[True,False,True],"distance":[.1,np.nan,.2]},
                 index=starts[:3]).to_parquet(cp/"weighted_windows.parquet")
    v={"integrity_pass":True,"adaptive_pass":False,"active_alpha":0,"weight_mode":"UNIFORM_BASELINE_FALLBACK",
       "current_query_coverage":False,"current_data_confirmed":False,"current_missing_features":["breadth48"],
       "current_query":{"universe_n":30,"breadth_valid_n":29},"statistical_gates":{"direction_not_degraded":False},
       "confirm_crps_improvement":{"mean":.01,"lower":.002,"upper":.02},
       "confirm_brier_degradation":{"mean":-.002,"lower":-.01,"upper":.011},
       "shared_incumbent_transition_validated":False,"case_matcher":"LEGACY_CORE_DIAGNOSTIC"}
    p=cache/"book_inc"/"inc-key"
    files={"frozen_config.json":c,"validation.json":v,
           "input_manifest.json":{"asof":c["asof"],"archive_complete_through":"2026-10-08 00:00:00+00:00"},
           "registered_snapshot.json":[{"model":"book_inc","score_json":str(source),"score_sha256":sha(source)}],
           "cache_inputs.json":{"book_inc":{ext:{"path":str(p)+ext,"sha256":sha(Path(str(p)+ext))}
                                         for ext in [".arrays.npz",".windows.parquet",".json"]}}}
    for name,value in files.items():(cp/name).write_text(json.dumps(value))
    pd.DataFrame({"unused":[0.,0.,0.]}).to_csv(cp/"paper_prefix.csv")
    (cp/"artifact_manifest.json").write_text(json.dumps({p.name:{"sha256":sha(p)} for p in cp.iterdir()}))
    cfg={"book_score2":{"schema_version":1,"checkpoint":str(cp),"registry":str(tmp_path/"registry_2.jsonl"),
                       "leaderboard":str(tmp_path/"leaderboard_2.md"),"csv":str(tmp_path/"leaderboard_2.csv"),
                       "artifacts":str(storage)}}
    return cfg,cp,score,save,eq,gross

def test_fixed_prefix_and_terminal_fee_without_production_rank(setup):
    cfg,_,s,_,eq,gross=setup
    row,ret,prefix,_=score2.evaluate_score(s,score2.load_checkpoint(cfg))
    expected=eq[:3,-1]*(1-.001*gross[:3,-1])/eq[:3,2]-1
    np.testing.assert_allclose(ret,expected,atol=1e-14)
    np.testing.assert_allclose(prefix,eq[:3,2]-1)
    assert row["score2_mean"]==pytest.approx(expected.mean())
    assert row["score2_p10"]==pytest.approx(expected.min())
    assert row["rank"] is None and not row["production_eligible"]

@pytest.mark.parametrize("change",["partial","tool","data","windows","accounting","hard-gate"])
def test_incompatible_scores_rejected(setup,change):
    cfg,_,s,*_=setup;s=copy.deepcopy(s)
    if change=="partial":s["windows"]["full_run"]=False
    if change=="tool":s["tool_version"]="other"
    if change=="data":s["data"]={"panel":"different"}
    if change=="windows":s["per_window"]["start"].reverse()
    if change=="accounting":s["per_window"]["R_liq"][0]+=.01
    if change=="hard-gate":s["gates"]["G1"]["pass"]=False
    with pytest.raises(ValueError):score2.evaluate_score(s,score2.load_checkpoint(cfg))

def test_changed_checkpoint_rejected(setup):
    cfg,cp,*_=setup;p=cp/"validation.json";p.write_text(p.read_text()+" ")
    with pytest.raises(ValueError,match="checkpoint"):score2.load_checkpoint(cfg)

def test_separate_board_idempotence_and_reading_instructions(setup):
    cfg,_,s,save,*_=setup
    original=Path(cfg["book_score2"]["leaderboard"]).with_name("leaderboard.md");original.write_text("untouched")
    score2.publish(s,cfg)
    new=save("book_next","next");score2.publish(new,cfg);score2.publish(new,cfg)
    entries=[json.loads(x) for x in Path(cfg["book_score2"]["registry"]).read_text().splitlines()]
    assert len(entries)==2 and original.read_text()=="untouched"
    text=Path(cfg["book_score2"]["leaderboard"]).read_text()
    assert all(x in text for x in ["book_inc","book_next","How to read","29/30","DISABLED","NOT_VALIDATED"])
    frame=pd.read_csv(cfg["book_score2"]["csv"])
    assert len(frame)==2 and frame["rank"].isna().all() and not frame.production_eligible.any()

def test_failed_publication_preserves_previous_files(setup):
    cfg,_,s,*_=setup;score2.publish(s,cfg)
    lb=Path(cfg["book_score2"]["leaderboard"]);reg=Path(cfg["book_score2"]["registry"])
    before=lb.read_bytes(),reg.read_bytes();s["tool_version"]="wrong"
    with pytest.raises(ValueError):score2.publish(s,cfg)
    assert before==(lb.read_bytes(),reg.read_bytes())

def test_model_revision_replaces_display_preserving_history(setup):
    cfg,_,s,save,eq,_=setup;score2.publish(s,cfg)
    revised=eq.copy();revised[:,-1]*=1.01
    score2.publish(save("book_inc","revision",revised),cfg)
    frame=pd.read_csv(cfg["book_score2"]["csv"])
    assert len(frame)==1 and frame.iloc[0].run_key=="revision" and frame.iloc[0].attempts==2
    assert frame.iloc[0].delta_vs_incumbent==pytest.approx(.01*(eq[:3,-1]*(1-.0005)/eq[:3,2]).mean())

def test_concurrent_publishers_keep_every_model(setup):
    cfg,_,_,save,*_=setup
    scores=[save("book_new"+str(i),"key"+str(i)) for i in range(3)]
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(lambda s:score2.publish(s,cfg),scores))
    assert set(pd.read_csv(cfg["book_score2"]["csv"]).model)=={"book_new0","book_new1","book_new2"}

@pytest.mark.parametrize("both",[False,True])
def test_cli_only_updates_primary_when_requested(tmp_path,monkeypatch,both):
    from backtest import run
    from backtest.scoring import report
    score={"model":{"name":"book_test"}};calls=[]
    monkeypatch.setattr(run,"load_config",lambda:{})
    monkeypatch.setattr(run,"get",lambda name:name)
    monkeypatch.setattr(run,"load_market",lambda cfg:type("M",(),{"notes":{}})())
    monkeypatch.setattr(run,"open_run",lambda *a:(tmp_path/"run.md",None,logging.getLogger("score2-test")))
    monkeypatch.setattr(run,"evaluate",lambda *a,**kw:object())
    monkeypatch.setattr(run,"write_model_report",lambda *a:{"checks":[]})
    monkeypatch.setattr(report,"score_and_publish",lambda *a,**kw:calls.append(("primary",kw.get("register"))) or score)
    monkeypatch.setattr(score2,"load_checkpoint",lambda cfg:{})
    monkeypatch.setattr(score2,"publish",lambda s,cfg,**kw:calls.append(("secondary",s)) or Path("leaderboard_2.md"))
    args=["--model","book_test","--score2"]+(["--score"] if both else [])
    assert run.main(args)==0 and calls==[("primary",both),("secondary",score)]

def test_score2_disallows_holdout():
    from backtest import run
    with pytest.raises(SystemExit) as e:run.main(["--model","book_test","--score2","--holdout"])
    assert e.value.code==2


def test_ineligible_full_model_is_visible_but_not_production_eligible(setup):
    cfg,_,s,*_=setup
    s["eligible"]=False;s["gates"]["G1"]["pass"]=False
    score2.publish(s,cfg)
    row=pd.read_csv(cfg["book_score2"]["csv"]).iloc[0]
    assert not row.original_eligible and not row.production_eligible
    assert row.failed_hard_gates=="G1"

def test_published_vector_tampering_blocks_refresh(setup):
    cfg,_,s,*_=setup;score2.publish(s,cfg)
    registry=Path(cfg["book_score2"]["registry"])
    entry=json.loads(registry.read_text().splitlines()[0])
    vector=Path(entry["returns"]);vector.write_bytes(vector.read_bytes()+b"x")
    board=Path(cfg["book_score2"]["leaderboard"]);before=board.read_bytes()
    with pytest.raises(ValueError,match="artifacts changed"):score2.refresh(cfg)
    assert board.read_bytes()==before

def test_missing_checkpoint_fails_before_any_backtest(monkeypatch):
    from backtest import run
    monkeypatch.setattr(run,"load_config",lambda:{})
    monkeypatch.setattr(run,"load_market",lambda cfg:pytest.fail("backtest should not start"))
    with pytest.raises(SystemExit) as e:run.main(["--model","book_test","--score2"])
    assert e.value.code==2


def test_paper_prefix_not_attributed_to_a_changed_model_revision(setup,monkeypatch):
    cfg,_,score,save,*_=setup
    monkeypatch.setattr(score2,"PAPER_MODELS",{"book_inc":"unused"})
    cp=score2.load_checkpoint(cfg)
    original=score2.evaluate_score(score,cp)[0]
    assert "paper_prefix_return" in original
    revised=score2.evaluate_score(save("book_inc","different-revision"),cp)[0]
    assert "paper_prefix_return" not in revised
    assert revised["paper_identity_status"]=="NO_PAPER_FOR_THIS_REVISION"
