"""Reproducible source/config evidence; no strategy outcome evaluation."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess

import yaml

from backtest.evaluate import model_modules
from src.models.book.book_cashshort_confirm import MODEL as CONFIRM
from src.models.book.book_cashshort_pullback import MODEL as PULLBACK

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "results/book/20261009-conditional-short-research"
PIN = "0b2c2630da058eab8abb0c8881cdbcbb1b54a1ff"
NEW = {"book_cashshort_confirm", "book_cashshort_pullback"}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    base_cfg = yaml.safe_load(git("show", "320984e:config.yaml"))
    candidate_cfg = dict(cfg)
    candidate_cfg["models"] = {k: v for k, v in cfg["models"].items() if k not in NEW}
    assert candidate_cfg == base_cfg, "Existing configuration or field changed"
    old = ROOT / ("results/scoring/score2/603da2948b68ee0f5c8a/baitoey_ovl_brk_dual/"
                  "f30fa79cde92399a-dd87f9f0d65673f9/score.json")
    record = json.loads(old.read_text())
    for name in NEW:
        assert cfg["models"][name]["long_base"] == record["model"]["params"]
    files = ["src/models/baitoey/_overlays.py",
             "src/models/baitoey/baitoey_vt_dual.py",
             "src/models/baitoey/baitoey_ovl_brk_dual.py",
             "src/models/baitoey/_volume_signals.py",
             "src/models/baitoey/baitoey_vt_mom.py",
             "src/models/baselines/team_rot_ew.py"]
    hashes = {}
    for path in files:
        raw = (ROOT / path).read_bytes()
        assert raw == git("show", f"{PIN}:{path}"), f"Unpinned helper {path}"
        hashes[path] = digest(raw)
    models = {}
    for model in (CONFIRM, PULLBACK):
        deps = model_modules(model)
        models[model.spec.name] = {
            "modules": deps,
            "source_sha256": {name: digest((ROOT / (name.replace(".", "/") + ".py")).read_bytes())
                              for name in deps},
            "params": cfg["models"][model.spec.name],
        }
    board = ROOT / "results/book/20261009-short-study-v2/leaderboard_snapshot/leaderboard_2.csv"
    evidence = {
        "scope": "source/config audit only; candidate performance unverified",
        "worktree_base_commit": "320984e",
        "original_metric_protocol": "603da2948b68ee0f5c8a",
        "original_broad_query": "FAILED 29/30; BCH absent; never relaxed",
        "pinned_own_team_commit": PIN,
        "existing_config_unchanged_except_two_new_models": True,
        "exact_published_backbone_params": True,
        "baseline_score_sha256": digest(old.read_bytes()),
        "frozen_53row_board_sha256": digest(board.read_bytes()),
        "pinned_source_sha256": hashes,
        "models": models,
    }
    (OUT / "source_audit.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({k: v for k, v in evidence.items() if k not in {"models", "pinned_source_sha256"}},
                     indent=2))


if __name__ == "__main__":
    main()
