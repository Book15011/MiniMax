"""Compare variants of one model on the harness windows: python -m research.baitoey.sweep <grid.yaml> [--confirm]

A grid file names a registered model and a list of variants. Each variant overrides model parameters
(its config.yaml block) and/or the spec's `rebalance_hours` and `band`. Every variant is scored exactly like
backtest.run (same windows, costs, lag, activity guard). By default only SCREEN is shown: pick settings there,
and open CONFIRM once (--confirm) after freezing them.

Output: a markdown table printed and saved to results/baitoey/<YYYYMMDD>-sweep-<grid name>/table.md.
"""
from __future__ import annotations

import argparse
import copy
import dataclasses
import logging
from datetime import datetime, timezone
from pathlib import Path

import yaml

from backtest.data import load_market
from backtest.evaluate import evaluate, period_masks, summarize
from src.config import REPO_ROOT, load_config
from src.models import get

SPEC_KEYS = ("rebalance_hours", "band")
COLS = [("med", "Median", "pct"), ("p10", "Worst 10%", "pct"), ("worst", "Worst", "pct"), ("pos", "> 0", "share"),
        ("mdd_med", "Median max DD", "pct"), ("comp_a", "Comp. A", "num"), ("comp_b", "Comp. B", "num"),
        ("active_ok", "≥ 10 active days", "share"), ("turn_day", "Turnover/day", "num"),
        ("fees", "Fees/window", "pct"), ("orders_day_max", "Max orders/day", "int")]


def fmt(x, kind: str) -> str:
    return {"pct": f"{x:+.2%}", "share": f"{x:.0%}", "num": f"{x:+.2f}", "int": f"{int(x)}"}[kind]


def score(model, market, cfg: dict, params: dict, spec_over: dict, log) -> tuple:
    model = copy.copy(model)
    model.spec = dataclasses.replace(model.spec, **spec_over)
    model.spec.validate()
    cfg = copy.deepcopy(cfg)
    # spec overrides go into params too, so the harness cache key changes with them
    cfg["models"][model.spec.name] = {**params, "_spec": spec_over} if spec_over else params
    return evaluate(model, market, cfg, use_cache=True, log=log), cfg


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("grid", type=Path)
    ap.add_argument("--confirm", action="store_true", help="also show CONFIRM (only after settings are frozen)")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    log = logging.getLogger("sweep")

    grid = yaml.safe_load(a.grid.read_text())
    cfg = load_config()
    base_model = get(grid["model"])
    base_params = cfg["models"][grid["model"]]
    market = load_market(cfg)
    periods = ["SCREEN"] + (["CONFIRM"] if a.confirm else [])
    need = cfg["harness"]["min_active_days"]

    rows = []
    for ref in grid.get("references", []):
        ev = evaluate(get(ref), market, cfg, use_cache=True, log=log)
        rows.append((f"ref: {ref}", ev, cfg))
    for v in [{"name": "base"}] + grid["variants"]:
        over = {k: val for k, val in v.items() if k != "name"}
        spec_over = {k: over.pop(k) for k in SPEC_KEYS if k in over}
        unknown = set(over) - set(base_params)
        if unknown:
            raise SystemExit(f"variant {v['name']}: unknown parameters {sorted(unknown)}")
        ev, vcfg = score(base_model, market, cfg, {**base_params, **over}, spec_over, log)
        rows.append((v["name"], ev, vcfg))
        log.info("scored %s", v["name"])

    out = [f"# Sweep: {a.grid.stem} ({grid['model']})", ""]
    for period in periods:
        out += [f"## {period}", "", "| Variant | " + " | ".join(c[1] for c in COLS) + " |",
                "|---|" + "---|" * len(COLS)]
        for name, ev, vcfg in rows:
            mask = period_masks(ev.windows, vcfg, False)[period]
            s = summarize(ev.windows[mask.to_numpy()], need)
            out.append(f"| {name} | " + " | ".join(fmt(s[k], kind) for k, _, kind in COLS) + " |")
        out.append("")
    text = "\n".join(out)
    print(text)
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    root = REPO_ROOT.parent.parent if REPO_ROOT.parent.name == ".worktrees" else REPO_ROOT  # shared checkout
    dest = root / "results" / "baitoey" / f"{day}-sweep-{a.grid.stem}"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "table.md").write_text(text)
    (dest / "grid.yaml").write_text(a.grid.read_text())
    log.info("saved %s", dest / "table.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
