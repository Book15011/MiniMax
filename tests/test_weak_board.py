"""Conditional score2 integration must preserve compatibility and immutable evidence."""
import numpy as np
import pandas as pd
import pytest
from backtest.scoring import weak_board
def test_profile_score_is_minimum_across_horizons_and_baselines():
    a=np.array([[.03,.02,-.01],[.01,.01,.01]])
    b=np.array([[.02,.01,.0],[.02,-.03,.01]])
    assert weak_board.selection_score(a,b).tolist()==pytest.approx([-.01,-.03])
def test_source_signature_is_revision_and_data_specific():
    from backtest.scoring.score2 import signature
    a={"data":{"prices":"a"},"inputs_sha256":{"v":"1"}}
    b={"data":{"prices":"b"},"inputs_sha256":{"v":"1"}}
    assert signature(a)!=signature(b)
def test_all_rows_get_visible_experimental_rank_without_activation():
    frame=pd.DataFrame({"model":["slow","cash","good"],"selection_score":[-.02,0,.01],
                        "CS":[.1,0,.4],"original_eligible":[True,True,False]})
    result=weak_board.rank_frame(frame)
    assert result.model.tolist()==["good","cash","slow"]
    assert result["rank"].tolist()==[1,2,3]
    assert not result.production_eligible.any()
def test_schema2_dispatch_does_not_run_legacy_checkpoint(monkeypatch):
    from backtest.scoring import score2
    cfg={"book_score2":{"schema_version":2}}
    monkeypatch.setattr(weak_board,"load_checkpoint",lambda cfg:"new")
    assert score2.load_checkpoint(cfg)=="new"
def test_publish_failure_precedes_registry_and_board_mutation(tmp_path,monkeypatch):
    from backtest.scoring.score2 import sha
    cfg={"book_score2":{"registry":str(tmp_path/"registry"),"leaderboard":str(tmp_path/"board"),"csv":str(tmp_path/"csv")}}
    for k in ["registry","leaderboard","csv"]:pd.Series([k]).to_csv(cfg["book_score2"][k])
    before={k:sha(tmp_path/{"registry":"registry","leaderboard":"board","csv":"csv"}[k]) for k in ["registry","leaderboard","csv"]}
    monkeypatch.setattr(weak_board,"save_score",lambda *a:(_ for _ in ()).throw(ValueError("bad evidence")))
    with pytest.raises(ValueError,match="bad evidence"):weak_board.publish_scores([{}],cfg,{})
    assert before=={k:sha(tmp_path/{"registry":"registry","leaderboard":"board","csv":"csv"}[k]) for k in before}
