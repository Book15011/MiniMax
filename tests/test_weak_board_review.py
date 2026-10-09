"""Independent synthetic publication and fixed-baseline integrity review."""
import copy
import hashlib
import json
from contextlib import nullcontext
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from backtest.scoring import weak_board


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@pytest.fixture
def board_fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(weak_board, "safe_path", lambda path: Path(path))
    monkeypatch.setattr(weak_board, "locked", lambda name: nullcontext())
    starts = pd.date_range("2020-01-01 12:00", periods=16, freq="QS", tz="UTC")
    root = tmp_path / "checkpoint"; root.mkdir()
    origin = tmp_path / "origin"; origin.mkdir()
    cache = tmp_path / "cache"
    cases = pd.DataFrame({"weak_archived": True, "weak_fresh_btc": True,
                          "positive_control": False, "future_return": .01}, index=starts)
    cases.to_parquet(root / "cases.parquet")
    pd.DataFrame({"BTCUSDT": [100.]}, index=starts[:1]).to_parquet(root / "close_snapshot.parquet")
    sc = {"hours_per_day": 24, "liquidation_cost": .001,
          "composite": {"sortino": .4, "sharpe": .3, "calmar": .3},
          "variants": {"V1": {"returns": "daily", "annualize": 1, "calmar": "mean"}},
          "conventions": {"FLOORED": {"s_daily": .001, "dd_daily": .001,
              "s_hourly": .000204124145231931, "dd_hourly": .000204124145231931, "mdd": .002}}}
    c = {"source_checkpoint": str(origin), "horizons_hours": [216, 228, 240], "primary_hours": 228,
         "short": {"horizons_hours": [1, 3, 6], "minimum_episodes": 30},
         "bootstrap": {"reps": 1000, "seed": 23, "level": .9}, "min_clusters": 12,
         "stress": {"future_down": -.02, "future_rebound": .02}, "lookalikes": {"k": 16}}
    base = {"incumbent": "book_inc", "tool_version": "same", "horizon_hours": 336,
            "close_fee": .001, "cache_dir": str(cache)}
    cfg = {"book_weak_eval": c, "scoring": sc,
           "book_score2": {"schema_version": 2, "checkpoint": str(root),
                          "registry": str(tmp_path / "registry.jsonl"),
                          "leaderboard": str(tmp_path / "leaderboard_2.md"),
                          "csv": str(tmp_path / "leaderboard_2.csv"),
                          "artifacts": str(tmp_path / "saved")}}
    pinned = {}; snapshots = []; source_caches = {}
    def score_model(name, key, shift=0., frozen=True):
        path = cache / name / key; path.parent.mkdir(parents=True, exist_ok=True)
        slope = np.linspace(-.02, .04, len(starts)) + shift
        equity = 100. * (1. + slope[:, None] * np.arange(337)[None, :] / 336.)
        gross = np.full_like(equity, .5); gross[:, 0] = 0.
        np.savez(str(path) + ".arrays.npz", equity=equity, gross=gross)
        pd.DataFrame(index=starts).to_parquet(str(path) + ".windows.parquet")
        pd.DataFrame({"time": [], "symbol": [], "quantity": []}).to_parquet(str(path) + ".trades.parquet")
        Path(str(path) + ".json").write_text(json.dumps({"key": key, "model": name, "tool_version": "same"}))
        score = {"model": {"name": name, "run_key": key, "candidate": True, "author": "book"},
                 "tool_version": "same", "windows": {"full_run": True},
                 "data": {"panel": "fixed"}, "inputs_sha256": {"bars": "fixed"},
                 "gates": {"G1": {"hard": True, "pass": True}}, "eligible": True,
                 "per_window": {"start": list(map(str, starts)),
                               "R_liq": (equity[:, -1] * .9995 / equity[:, 0] - 1.).tolist()},
                 "return_first": {"full": {"headline_ret": .5, "cs_hit": .1}}}
        source = tmp_path / (name + "-" + key + ".json"); source.write_text(json.dumps(score))
        if frozen:
            snapshots.append({"model": name, "score_json": str(source), "score_sha256": digest(source)})
            pinned[name] = {suffix: {"path": str(path) + suffix, "sha256": digest(str(path) + suffix)}
                           for suffix in [".arrays.npz", ".windows.parquet", ".json", ".trades.parquet"]}
            (origin / "cache_inputs.json").write_text(json.dumps(pinned))
            source_caches[name] = {"run_key": key, "files": pinned[name]}
            (root / "source_cache_manifest.json").write_text(json.dumps(source_caches))
        return score, path
    inc, _ = score_model("book_inc", "old")
    candidate, candidate_path = score_model("book_new", "first", .01)
    cp = {"root": root, "c": c, "base": base, "cases": cases,
          "frozen": {"weak": c, "base": base, "scoring": sc}, "snapshots": snapshots,
          "signature": weak_board.signature(inc), "starts": starts, "ix": np.arange(len(starts)),
          "protocol": "synthetic", "metric_hashes": {}, "input": {"fresh_archive_confirmed": False},
          "incumbent_score": inc, "source_caches": source_caches, "validation": {"quarter_clusters": dict.fromkeys(weak_board.PROFILES, 16)}}
    def no_shorts(trades, panel, starts, hours, settings):
        columns = {"onsets": np.zeros(len(starts), int), "terminal_censored": np.zeros(len(starts), int)}
        for h in settings["horizons_hours"]:
            for name in ["valid", "correct", "wrong_direction", "cost_only_loss", "unresolved", "rebound_losses"]:
                columns[f"{name}_{h}h"] = np.zeros(len(starts), int)
        for name in ["closed_episodes", "reweighted_episodes", "cover_proxy_valid", "cover_proxy_wins",
                     "cover_rebound_losses", "barrier_take_profit_sampled", "barrier_stop_loss_sampled",
                     "barrier_censored", "barrier_missing_price", "barrier_intrahour_ambiguous"]:
            columns[name] = np.zeros(len(starts), int)
        columns["precision_6h"] = np.full(len(starts), np.nan)
        columns["mean_proxy_net_6h"] = np.full(len(starts), np.nan)
        return {"windows": pd.DataFrame(columns, index=starts),
                "episodes": pd.DataFrame({"empty": []}), "summary": {"status": "NO_SHORT_ONSETS"}}
    monkeypatch.setattr(weak_board, "short_diagnostics", no_shorts)
    for name, item in [("frozen_config.json", cp["frozen"]), ("registered_snapshot.json", snapshots),
                       ("input_manifest.json", cp["input"]), ("selection_validation.json", cp["validation"])]:
        (root / name).write_text(json.dumps(item))
    manifest = {path.name: {"sha256": digest(path)} for path in root.iterdir()}
    (root / "artifact_manifest.json").write_text(json.dumps(manifest))
    return cfg, cp, candidate, candidate_path, score_model


def test_source_terminal_accounting_is_reproduced_before_shorter_scores(board_fixture):
    cfg, cp, score, path, factory = board_fixture
    row, evidence, _, _ = weak_board.evaluate_score(score, cp)
    with np.load(str(path) + ".arrays.npz") as cached:
        eq, gross = cached["equity"], cached["gross"]
        expected = eq[:, 228] * (1. - .001 * gross[:, 228]) / eq[:, 0] - 1.
    np.testing.assert_allclose(evidence["return"][:, 1], expected, rtol=0., atol=1e-14)
    broken = copy.deepcopy(score); broken["per_window"]["R_liq"][0] += .01
    with pytest.raises(ValueError, match="accounting"):
        weak_board.evaluate_score(broken, cp)


def test_original_registered_internal_path_cannot_change_with_same_terminal_return(board_fixture):
    cfg, cp, score, path, factory = board_fixture
    arrays_path = str(path) + ".arrays.npz"
    with np.load(arrays_path) as cached:
        eq, gross = cached["equity"].copy(), cached["gross"].copy()
    eq[0, 100] *= .8
    np.savez(arrays_path, equity=eq, gross=gross)
    with pytest.raises(ValueError, match="cache"):
        weak_board.evaluate_score(score, cp)


def test_republished_incumbent_name_keeps_original_revision_as_baseline(board_fixture):
    cfg, cp, score, path, factory = board_fixture
    revised, _ = factory("book_inc", "new-revision", .03, frozen=False)
    original = weak_board.evaluate_score(cp["incumbent_score"], cp)[1]
    revised_ev = weak_board.evaluate_score(revised, cp)[1]
    entries = [weak_board.save_score(score, cfg, cp), weak_board.save_score(revised, cfg, cp)]
    frame, _, _, _, _, evidence = weak_board.make_frame(entries, cp)
    row = frame.loc[frame.model == "book_inc"].iloc[0]
    expected = (revised_ev["return"][:, 1] - original["return"][:, 1]).mean()
    assert row.delta_vs_incumbent == pytest.approx(expected, abs=1e-14)
    assert expected > 0. and evidence["family_models"] == 3


@pytest.mark.parametrize("change", ["digest", "eligibility", "candidate", "headline"])
def test_saved_source_and_registry_row_must_agree(board_fixture, change):
    cfg, cp, score, path, factory = board_fixture
    entry = weak_board.save_score(score, cfg, cp)
    if change == "digest": entry["source_sha256"] = "0" * 64
    elif change == "eligibility": entry["row"]["original_eligible"] = False
    elif change == "candidate": entry["row"]["candidate"] = False
    elif change == "headline": entry["row"]["original_headline_ret"] = 1.
    with pytest.raises(ValueError, match="source|row|identity"):
        weak_board.read_evidence(entry, cp)


def test_checkpoint_manifest_cannot_omit_consumed_frozen_input(board_fixture):
    cfg, cp, score, path, factory = board_fixture
    root = cp["root"]
    manifest = json.loads((root / "artifact_manifest.json").read_text())
    del manifest["cases.parquet"]
    (root / "artifact_manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="manifest"):
        weak_board.load_checkpoint(cfg)


def test_checkpoint_settings_must_stay_frozen(board_fixture):
    cfg, cp, *_ = board_fixture
    cfg = copy.deepcopy(cfg); cfg["scoring"]["liquidation_cost"] = .002
    with pytest.raises(ValueError, match="settings"):
        weak_board.load_checkpoint(cfg)


@pytest.mark.parametrize("failed_file", ["leaderboard_2.md", "short_leaderboard_2.csv", "comparison_validation.json"])
def test_io_failure_does_not_publish_partial_registry_or_tables(tmp_path, monkeypatch, failed_file):
    monkeypatch.setattr(weak_board, "safe_path", lambda path: Path(path))
    monkeypatch.setattr(weak_board, "locked", lambda name: nullcontext())
    root = tmp_path / "research"; root.mkdir()
    cfg = {"book_score2": {"registry": str(tmp_path / "registry.jsonl"),
                           "leaderboard": str(tmp_path / "leaderboard_2.md"),
                           "csv": str(tmp_path / "leaderboard_2.csv")}}
    for key, path in cfg["book_score2"].items():
        Path(path).write_text("" if key == "registry" else "old " + key)
    tracked = [Path(path) for path in cfg["book_score2"].values()]
    tracked += [tmp_path / "short_leaderboard_2.csv"]
    tracked += [root / name for name in ["comparison_validation.json", "model_windows.csv",
                                       "sensitivity.csv", "leave_quarter_out.csv", "all_models.csv", "short_table.csv"]]
    before = {path: path.read_bytes() if path.exists() else None for path in tracked}
    entry = {"protocol": "synthetic", "model": "new", "run_key": "new", "source_sha256": "hash"}
    monkeypatch.setattr(weak_board, "save_score", lambda *args: entry)
    frame = pd.DataFrame({"model": ["new"], "selection_score": [.01], "CS": [.1]})
    monkeypatch.setattr(weak_board, "make_frame",
                        lambda *args: (frame, frame, frame, frame, frame, {"ok": True}))
    monkeypatch.setattr(weak_board, "render", lambda *args: "new board")
    actual = weak_board.os.replace
    failed_once = False
    def fail(source, destination):
        nonlocal failed_once
        if Path(destination).name == failed_file and not failed_once:
            failed_once = True
            raise OSError("synthetic publication failure")
        return actual(source, destination)
    monkeypatch.setattr(weak_board.os, "replace", fail)
    with pytest.raises(OSError, match="synthetic"):
        weak_board.publish_scores([{}], cfg, {"root": root})
    after = {path: path.read_bytes() if path.exists() else None for path in tracked}
    assert after == before
    assert not list(tmp_path.rglob("*.staged.*"))


def test_republishing_older_revision_makes_requested_revision_current(board_fixture, monkeypatch):
    cfg, cp, original, path, factory = board_fixture
    monkeypatch.setattr(weak_board, "render", lambda cp, frame, short, evidence: frame.to_csv(index=False))
    weak_board.publish_scores([original], cfg, cp)
    revised, _ = factory("book_new", "second", .02, frozen=False)
    weak_board.publish_scores([revised], cfg, cp)
    board, frame = weak_board.publish_scores([original], cfg, cp)
    assert frame.loc[frame.model == "book_new", "run_key"].iloc[0] == original["model"]["run_key"]
    entries = [json.loads(line) for line in Path(cfg["book_score2"]["registry"]).read_text().splitlines()]
    assert len(entries) == 3 and entries[-1]["run_key"] == original["model"]["run_key"]
    # Repeating the currently selected identity stays idempotent.
    weak_board.publish_scores([original], cfg, cp)
    repeated = Path(cfg["book_score2"]["registry"]).read_text().splitlines()
    assert len(repeated) == 3


def test_per_run_report_rejects_a_different_revision_row(board_fixture, monkeypatch, tmp_path):
    cfg, cp, score, path, factory = board_fixture
    monkeypatch.setattr(weak_board, "load_checkpoint", lambda cfg: cp)
    wrong = pd.DataFrame({"model": [score["model"]["name"]], "run_key": ["different"],
                          "rank": [1], "selection_score": [.01], "return_mean": [.02],
                          "return_p10": [-.01], "CS": [.1]})
    monkeypatch.setattr(weak_board, "publish_scores", lambda *args: (Path(cfg["book_score2"]["leaderboard"]), wrong))
    report = tmp_path / "per_run.md"
    with pytest.raises(ValueError, match="revision|run|identity"):
        weak_board.publish(score, cfg, report_path=report)
    assert not report.exists()
