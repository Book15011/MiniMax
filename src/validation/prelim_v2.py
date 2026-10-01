"""Live-like weights v2 (preliminary): the PART 0 code, unchanged, for the round's 12:00 UTC window starts.

    python -m src.validation.prelim_v2 --asof "2026-09-30 00:00" --t-star "2026-10-04 12:00" --grid-hour 12 \
        --out-dir results/book/20261002-return-first/validation_v2_prelim

Runs src.validation.build, then src.validation.live_like, with these inputs changed in memory only (config.yaml,
and so the live bot, keeps its values):
- validation.grid_hour_utc = --grid-hour: the window starts, the state time and the walk-forward test dates;
- validation.live_start = --t-star, the round's start;
- the pool end H = --asof (validation.holdout_days = T* - as-of). The holdout was opened on 2026-10-01 and is
  spent, so the lookalike pool covers every window that ends by the as-of, as the score's pool does;
- the panel is the one already in --panel-dir (the harness panel): nothing is downloaded or rebuilt, and every
  intermediate table goes to --out-dir, never to data/.
Writes validation/validation_set_v2_prelim.json and validation/live_like_v2_prelim.json, with their reports
(reports/validation_set_v2_prelim.md, reports/live_like_v2_prelim.md). The v1 files are not touched; their
pre-registration blocks are copied verbatim into the v2 reports, since the method is the same.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys

import pandas as pd

from src.config import REPO_ROOT, load_config, resolve
from src.data.panel import HourlyPanel
from src.validation import build, live_like

V1_REPORTS = {"build": REPO_ROOT / "reports" / "validation_set_v1.md", "live_like": REPO_ROOT / "reports" / "live_like_v1.md"}
OUT = {"set": REPO_ROOT / "validation" / "validation_set_v2_prelim.json",
       "set_report": REPO_ROOT / "reports" / "validation_set_v2_prelim.md",
       "weights": REPO_ROOT / "validation" / "live_like_v2_prelim.json",
       "weights_report": REPO_ROOT / "reports" / "live_like_v2_prelim.md"}


def patched_config(asof: pd.Timestamp, t_star: pd.Timestamp, hour: int) -> dict:
    cfg = copy.deepcopy(load_config())
    v = cfg["validation"]
    v["grid_hour_utc"] = hour
    v["live_start"] = f"{t_star:%Y-%m-%d %H:%M}"
    v["holdout_days"] = (t_star - asof) / pd.Timedelta(days=1)       # pool end H = the as-of
    return cfg


def seed_report(src, dst) -> None:
    """The v2 report starts as the v1 pre-registration block (the code requires one and keeps it verbatim)."""
    block = build.PREREG_RE.search(src.read_text())
    if block is None:
        raise SystemExit(f"{src} has no pre-registration block")
    dst.write_text(f"(seeded from {src.name})\n\n{block.group(0)}\n")


def retitle(path, old: str, new: str, note: str) -> None:
    s = path.read_text()
    if not s.startswith(old):
        raise SystemExit(f"{path} does not start with {old!r}")
    path.write_text(new + "\n\n" + note + s[len(old):])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--asof", required=True, help='UTC; the last complete hour of the panel, e.g. "2026-09-30 00:00"')
    ap.add_argument("--t-star", required=True, help='UTC; the round start, e.g. "2026-10-04 12:00"')
    ap.add_argument("--grid-hour", type=int, required=True, help="UTC hour of the window starts")
    ap.add_argument("--out-dir", required=True, help="intermediate tables (never under data/)")
    ap.add_argument("--panel-dir", default="data/validation", help="read-only source of the hourly panel")
    a = ap.parse_args(argv)
    out = resolve(a.out_dir)
    if resolve("data") in [out, *out.parents]:
        raise SystemExit("--out-dir must not be under data/")
    asof, t_star = pd.Timestamp(a.asof, tz="UTC"), pd.Timestamp(a.t_star, tz="UTC")
    cfg = patched_config(asof, t_star, a.grid_hour)
    panel_dir = resolve(a.panel_dir)
    inputs = {"method": "src.validation.build + src.validation.live_like, unchanged (PART 0)",
              "grid_hour_utc": a.grid_hour, "T_star": str(t_star), "asof": str(asof), "pool_end_H": str(asof),
              "holdout_days": cfg["validation"]["holdout_days"], "panel": str(panel_dir.relative_to(REPO_ROOT)),
              "panel_last": str(HourlyPanel.load(panel_dir).close.index[-1]), "wrapper": "src.validation.prelim_v2"}

    build.load_config = lambda: cfg
    build.build_hourly_panel = lambda _cfg: HourlyPanel.load(panel_dir)
    build.ARTIFACT, build.REPORT = OUT["set"], OUT["set_report"]
    seed_report(V1_REPORTS["build"], OUT["set_report"])
    rc = build.main(["--asof", str(asof), "--no-refresh", "--out-dir", str(out)])
    if not OUT["set"].exists():
        raise SystemExit("the validation build wrote no artifact")
    va = json.loads(OUT["set"].read_text())
    va["version"] = "validation_set_v2_prelim"
    va["inputs_changed"] = inputs
    OUT["set"].write_text(json.dumps(va, indent=1, default=str))
    note = ("Preliminary v2: the v1 code with " + ", ".join(f"{k} = {v}" for k, v in inputs.items() if k != "method")
            + ". Generated by `python -m src.validation.prelim_v2`.\n")
    retitle(OUT["set_report"], "# Lookalike validation set v1", "# Lookalike validation set v2 (preliminary)",
            note + "The report text below says \"T* − 56d\" wherever it names H: here H is the as-of above.\n")

    live_like.load_config = lambda: cfg
    live_like.ARTIFACT, live_like.REPORT, live_like.VALIDATION = OUT["weights"], OUT["weights_report"], OUT["set"]
    seed_report(V1_REPORTS["live_like"], OUT["weights_report"])
    rc |= live_like.main(["--asof", str(asof), "--work-dir", str(out)])
    art = json.loads(OUT["weights"].read_text())
    art["version"] = "live_like_v2_prelim"
    art["inputs_changed"] = inputs
    art["sha256"] = hashlib.sha256(json.dumps({k: x for k, x in art.items() if k != "sha256"}, sort_keys=True,
                                              default=str).encode()).hexdigest()
    OUT["weights"].write_text(json.dumps(art, indent=1, default=str) + "\n")
    retitle(OUT["weights_report"], "# Live-like weights v1", "# Live-like weights v2 (preliminary)", note)
    print(f"direction test passed: {art['direction']['passed']} (the score refuses weights with a direction factor)")
    print(f"wrote {OUT['set']}, {OUT['weights']} (sha256 {art['sha256'][:12]}); exit {rc}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
