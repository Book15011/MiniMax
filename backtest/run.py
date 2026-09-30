"""Score one model: python -m backtest.run --model <name> [--holdout] [--no-cache] | --list

Writes reports/<name>/<YYYYMMDD-HHMM>.md (commit it) and a .log next to it (never committed).
"""
from __future__ import annotations

import argparse
import time

from backtest.data import load_market
from backtest.evaluate import evaluate
from backtest.report import open_run, write_model_report
from src.config import load_config
from src.models import discover, get

REFERENCE_MODEL = "team_btc_hold"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", help="registered model name")
    ap.add_argument("--list", action="store_true", help="list registered models")
    ap.add_argument("--holdout", action="store_true", help="open the sealed holdout (only for the frozen launch model)")
    ap.add_argument("--no-cache", action="store_true", help="recompute even if a cached result matches")
    a = ap.parse_args(argv)
    if a.list or not a.model:
        for name, m in sorted(discover().items(), key=lambda kv: (kv[1].spec.method, kv[0])):
            print(f"{m.spec.method:10s} {name:28s} {m.spec.author:8s} {m.spec.description}")
        return 0
    cfg = load_config()
    model = get(a.model)
    md, lg, log = open_run(cfg, a.model)
    t0 = time.time()
    market = load_market(cfg)
    log.info("data: %s", market.notes)
    ev = evaluate(model, market, cfg, holdout=a.holdout, use_cache=not a.no_cache, log=log)
    ref = evaluate(get(REFERENCE_MODEL), market, cfg, holdout=a.holdout, use_cache=True, log=log)
    out = write_model_report(ev, ref, market.notes, cfg, md, time.time() - t0)
    for c, ok, d in out["checks"]:
        log.info("must-pass %-30s %s  %s", c, "PASS" if ok else "FAIL", d)
    log.info("report: %s", md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
