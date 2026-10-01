"""Append-only registry of scoring runs and the leaderboard regenerated from it (docs/EVALUATION.md section 4).

- registry: scoring.registry (JSONL, one line per run, never rewritten). Appends take the same lock file as
  `scripts/lock scoring-registry -- ...` (run/locks/scoring-registry.lock, flock), but wait for it instead of
  failing, so concurrent runs queue up.
- leaderboard: full runs only (every pool window, every gate), with the current tool version only. A run whose
  numbers are identical to another's (same run key) is shown once. Each person's run count sits next to their
  best score, so the number of attempts behind a score stays visible.
"""
from __future__ import annotations

import fcntl
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from backtest.scoring.competition import all_variants
from src.config import REPO_ROOT, resolve

LOCK_NAME = "scoring-registry"


def locks_dir() -> Path:
    common = REPO_ROOT / ".git"
    if common.is_file():                       # inside a worktree: .git is a file pointing at the common dir
        gitdir = Path(common.read_text().split(":", 1)[1].strip())
        root = gitdir.parent.parent.parent     # <root>/.git/worktrees/<name> -> <root>
    else:
        root = REPO_ROOT
    return root / "run" / "locks"


@contextmanager
def locked(name: str = LOCK_NAME, lock_dir: str | Path | None = None):
    d = Path(lock_dir) if lock_dir else locks_dir()
    d.mkdir(parents=True, exist_ok=True)
    with open(d / f"{name}.lock", "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            (d / f"{name}.info").write_text(f"pid={os.getpid()} user={os.environ.get('MM_MEMBER', '?')} "
                                            f"since={datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ} cmd=registry append\n")
            yield
        finally:
            (d / f"{name}.info").unlink(missing_ok=True)
            fcntl.flock(fh, fcntl.LOCK_UN)


def append(path: str | Path, entry: dict, lock_dir: str | Path | None = None) -> None:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n"
    with locked(lock_dir=lock_dir):
        with open(p, "a") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())


def read(path: str | Path) -> tuple[list[dict], int]:
    """Entries, and the number of unreadable lines (should be 0)."""
    p = resolve(path)
    if not p.exists():
        return [], 0
    out, bad = [], 0
    for line in p.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            bad += 1
    return out, bad


def entry_from(score: dict, runner: str, outputs: dict) -> dict:
    sel = {c: {v: score["headline"][c][v]["headline"] for v in score["headline"][c]} for c in score["headline"]}
    return {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "runner": runner,
            "model": score["model"]["name"], "author": score["model"]["author"], "method": score["model"]["method"],
            "run_key": score["model"]["run_key"], "tool_version": score["tool_version"],
            "scoring_version": score["scoring_version"], "full": bool(score["windows"]["full_run"]),
            "primary": score["primary"]["headline"], "live_like": score["primary"]["live_like"],
            "recency": score["primary"]["recency"], "headline": sel,
            "gates": {g: v["pass"] for g, v in score["gates"].items()}, "eligible": score["eligible"],
            "median_R": score["summary"]["median_R"], "worst10_R": score["summary"]["worst10_R"],
            "worst_R": score["summary"]["worst_R"], "commit": (score.get("code") or {}).get("commit"),
            "robust_min": (score.get("robustness") or {}).get("min"), "robust": (score.get("robustness") or {}).get("pass"),
            "rel_other_bars": (score.get("gate_sensitivity") or {}).get("rel_headline", {}), **outputs}


def current(entries: list[dict], tool_version: str) -> list[dict]:
    """Full runs of this tool version, one per run key (the latest)."""
    seen: dict[str, dict] = {}
    for e in entries:
        if e.get("full") and e.get("tool_version") == tool_version:
            seen[e["run_key"]] = e
    return list(seen.values())


def rank(entries: list[dict], value: float, conv: str, variant: str) -> tuple[int, int]:
    vals = [e["headline"][conv][variant] for e in entries]
    return 1 + sum(v > value for v in vals), len(vals)


def leaderboard(entries: list[dict], tool_version: str, conventions: list[str], variants: list[str],
                primary: dict) -> str:
    rows = sorted(current(entries, tool_version), key=lambda e: -e["primary"])
    runs_by: dict[str, int] = {}
    for e in entries:
        if e.get("full") and e.get("tool_version") == tool_version:
            runs_by[e["author"]] = runs_by.get(e["author"], 0) + 1
    pc, pv = primary["convention"], primary["variant"]
    head = [f"# Scoring leaderboard (tool version `{tool_version}`)", "",
            f"Full runs only, this tool version only; identical results shown once. Sorted by HEADLINE "
            f"{pv} {pc} (primary). Regenerated after every registered run; see docs/EVALUATION.md.", "",
            "| # | Model | Author | Method | Eligible | Gates failed | " +
            " | ".join(f"{v} {c}" for c in conventions for v in variants) + " | Live-like | Recency | Robust (min layer) | REL, median bar | Median R | Worst R |",
            "|---|---|---|---|---|---|" + "---|" * (len(conventions) * len(variants)) + "---|---|---|---|---|---|"]
    for k, e in enumerate(rows, 1):
        failed = ", ".join(g for g, ok in e["gates"].items() if not ok) or "none"
        vals = " | ".join(f"{e['headline'][c][v]:+.3f}" for c in conventions for v in variants)
        head.append(f"| {k} | {e['model']} | {e['author']} | {e['method']} | {'yes' if e['eligible'] else 'no'} | "
                    f"{failed} | {vals} | {e['live_like']:+.3f} | {e['recency']:+.3f} | "
                    f"{('yes ' if e.get('robust') else 'no ') + format(e['robust_min'], '+.2f') if e.get('robust_min') is not None else '—'} | "
                    f"{format(e['rel_other_bars']['median'], '+.3f') if (e.get('rel_other_bars') or {}).get('median') is not None else '—'} | "
                    f"{e['median_R'] * 100:+.2f}% | {e['worst_R'] * 100:+.2f}% |")
    head += ["", "## Runs per person", "", "| Person | Full runs (this version) | Best eligible HEADLINE | Best HEADLINE (any) |",
             "|---|---|---|---|"]
    for person in sorted(runs_by):
        mine = [e for e in rows if e["author"] == person]
        best = max(mine, key=lambda e: e["primary"])
        elig = [e for e in mine if e["eligible"]]
        be = max(elig, key=lambda e: e["primary"]) if elig else None
        be_txt = f"{be['primary']:+.3f} ({be['model']})" if be else "—"
        head.append(f"| {person} | {runs_by[person]} | {be_txt} | {best['primary']:+.3f} ({best['model']}) |")
    return "\n".join(head) + "\n"


def write_leaderboard(cfg: dict, tool_version: str) -> Path:
    sc = cfg["scoring"]
    entries, _ = read(sc["registry"])
    md = leaderboard(entries, tool_version, list(sc["conventions"]), all_variants(sc), sc["primary"])
    out = resolve(sc["leaderboard"])
    out.parent.mkdir(parents=True, exist_ok=True)
    with locked():
        out.write_text(md)
    return out
