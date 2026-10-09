import numpy as np
import pandas as pd
import pytest

from research.book.short_validation.run import (
    select_test_cases, summarize, paired_summaries, ledger_metrics, validate_arrays,
)

def daily_starts():
    return pd.date_range("2022-07-01 12:00", "2026-06-30 12:00", freq="D", tz="UTC")

def test_fixed_cases_have_eight_folds_and_no_cross_boundary_or_overlap():
    cases = select_test_cases(daily_starts(), 228)
    assert list(cases.fold.unique()) == [
        "2022H2", "2023H1", "2023H2", "2024H1",
        "2024H2", "2025H1", "2025H2", "2026H1",
    ]
    assert (cases.endpoint <= cases.fold_end).all()
    assert (cases.index[1:] - cases.index[:-1] >= pd.Timedelta(days=14)).all()
    assert cases.index[0] == pd.Timestamp("2022-07-01 12:00", tz="UTC")

def test_missing_fixed_start_fails_instead_of_changing_schedule():
    starts = daily_starts().delete(0)
    with pytest.raises(ValueError, match="missing fixed"):
        select_test_cases(starts, 228)

def test_case_selection_rejects_naive_duplicate_and_wrong_horizon():
    starts = daily_starts()
    with pytest.raises(ValueError, match="aware"):
        select_test_cases(starts.tz_localize(None), 228)
    with pytest.raises(ValueError, match="unique"):
        select_test_cases(starts.append(starts[:1]), 228)
    with pytest.raises(ValueError, match="228"):
        select_test_cases(starts, 240)

def test_array_validation_rejects_missing_clock_steps_and_nonpositive_money():
    eq = np.ones((2, 337)); gr = np.zeros_like(eq)
    validate_arrays(eq, gr, 2, 336)
    with pytest.raises(ValueError, match="dimensions"):
        validate_arrays(eq[:, :-1], gr[:, :-1], 2, 336)
    eq[0, 5] = 0
    with pytest.raises(ValueError, match="positive"):
        validate_arrays(eq, gr, 2, 336)
    eq[0, 5] = 1; gr[0, 3] = np.nan
    with pytest.raises(ValueError, match="finite"):
        validate_arrays(eq, gr, 2, 336)

def test_shortened_activity_excludes_endpoint_and_strategy_wins_guard_bucket():
    t0 = pd.Timestamp("2022-07-01 12:00", tz="UTC")
    rows = []
    for hour, kind, before, after in [
        (1, "guard", 0., .01), (2, "decision", .01, -.2),
        (5, "guard", -.2, -.19), (228, "decision", -.19, 0.),
        (230, "decision", 0., .3),
    ]:
        rows.append(dict(window_start=t0, hour=hour, time_utc=t0+pd.Timedelta(hours=hour),
                         kind=kind, w_before=before, w_after=after,
                         fee_usd=1., spread_usd=.5))
    result = ledger_metrics(pd.DataFrame(rows), pd.DatetimeIndex([t0]), 228, 100000)
    r = result.iloc[0]
    assert r.active_days == 2
    assert r.strategy_days == 1
    assert r.guard_only_days == 1
    assert r.orders == 5  # sign flip is two orders; endpoint order is included in costs
    assert r.turnover == pytest.approx(.01+.21+.01+.19)
    assert r.fees_e0 == pytest.approx(4/100000)
    assert r.spread_e0 == pytest.approx(2/100000)

def test_summary_tail_fraction_and_drawdown_sign():
    rows = pd.DataFrame({
        "return": [-.3, -.2, .1, .2, .4], "mdd": [.3, .2, .1, .1, .05],
        "CS": [0]*5, "CS_UTC": [0]*5, "active_days": [1]*5,
        "strategy_days": [1]*5, "guard_only_days": [0]*5,
        "turnover": [1]*5, "fees_e0": [.001]*5, "spread_e0": [.0001]*5,
    })
    s = summarize(rows)
    assert s["return_mean"] == pytest.approx(.04)
    assert s["tail10_mean"] == -.3
    assert s["mdd_worst"] == .3

def test_pairing_refuses_incomplete_or_duplicate_cases():
    t = pd.Timestamp("2022-07-01 12:00", tz="UTC")
    data = pd.DataFrame([
        dict(model="candidate", window_start=t, fold="2022H2", **{"return": .1}),
        dict(model="cash", window_start=t, fold="2022H2", **{"return": 0.}),
    ])
    result = paired_summaries(data, ["candidate"], ["cash"])
    assert set(result.fold) == {"2022H2", "ALL"}
    assert (result.delta_mean == .1).all()
    bad = data.copy(); bad.loc[1, "window_start"] += pd.Timedelta(days=14)
    with pytest.raises(ValueError, match="paired case"):
        paired_summaries(bad, ["candidate"], ["cash"])
    with pytest.raises(ValueError, match="duplicate"):
        paired_summaries(pd.concat([data, data.iloc[:1]]), ["candidate"], ["cash"])

def test_published_cache_attestation_detects_tampering(tmp_path):
    import json
    from research.book.short_validation.run import published_pin, sha
    source = tmp_path/"score.json"
    source.write_text("{}")
    item = {"path":str(source),"sha256":sha(source)}
    entry = {"protocol":"p","model":"candidate","run_key":"a"*16,
             "cache_inputs":{".arrays.npz":{"path":"cache","sha256":"good"}},
             "artifacts":{"score.json":item},"source_sha256":sha(source)}
    registry = tmp_path/"registry.jsonl"
    registry.write_text(json.dumps(entry)+"\n")
    cp = {"protocol":"p","registry":str(registry)}
    good = entry["cache_inputs"]
    assert len(published_pin("candidate","a"*16,cp,good)) == 1
    with pytest.raises(ValueError,match="cache changed"):
        published_pin("candidate","a"*16,cp,{".arrays.npz":{"path":"cache","sha256":"bad"}})
    source.write_text('{"changed":true}')
    with pytest.raises(ValueError,match="score changed"):
        published_pin("candidate","a"*16,cp,good)

def test_liquidation_is_charged_once_with_same_existing_risk_math():
    from backtest.scoring.weak_risk import remainder_risk
    from src.config import load_config
    eq=np.ones((1,337)); gross=np.ones_like(eq)
    risk=remainder_risk(eq,gross,pd.DatetimeIndex(["2022-07-01 12:00"],tz="UTC"),
                        0,228,load_config()["scoring"])
    assert risk["return"][0] == pytest.approx(-.001)
    assert risk["mdd"][0] == pytest.approx(.001)
