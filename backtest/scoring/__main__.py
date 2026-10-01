"""Scoring commands (docs/EVALUATION.md). Score one model with the harness's run command:

    python -m backtest.run --model <name> --score

Team-level commands:

    python -m backtest.scoring field [--no-cache]            score CASH and the 6 field benchmarks (reference rows)
    python -m backtest.scoring compare <a> <b> [--no-cache]  HEADLINE_RET difference a - b with a month-bootstrap interval
    python -m backtest.scoring leaderboard                    regenerate the leaderboard from the registry
"""
from __future__ import annotations

import argparse
import time

import numpy as np

from backtest.data import load_market
from backtest.report import open_run, stamp
from backtest.scoring import registry
from backtest.scoring.evaluate import tool_version
from backtest.scoring.report import score_and_publish
from backtest.scoring.returnfirst import BARS, month_multiplicity, tie_test
from backtest.scoring.score import score_model
from src.config import load_config
from src.models import get

REFERENCE_ROWS = ("team_cash",)


def cmd_field(cfg: dict, use_cache: bool) -> int:
    ts = stamp()
    market = load_market(cfg)
    for name in REFERENCE_ROWS + tuple(cfg["scoring"]["field"]):
        md, _lg, log = open_run(cfg, name, ts)
        log.info("data: %s", market.notes)
        score_and_publish(get(name), market, cfg, md.with_name(f"{md.stem}-score.md"), log, use_cache=use_cache)
    return 0


def cmd_compare(cfg: dict, a: str, b: str, use_cache: bool) -> int:
    """HEADLINE_RET(a) - HEADLINE_RET(b) on the full pool, with the leaderboard's paired month bootstrap."""
    sc = cfg["scoring"]
    md, _lg, log = open_run(cfg, "compare/headline")
    t0 = time.time()
    market = load_market(cfg)
    sa, ca = score_model(get(a), market, cfg, use_cache=use_cache, log=log)
    sb, cb = score_model(get(b), market, cfg, use_cache=use_cache, log=log)
    starts = ca["starts"]
    w = ca["w_final"].reindex(starts).to_numpy()
    if not np.allclose(w, cb["w_final"].reindex(starts).to_numpy(), rtol=0, atol=1e-15):
        raise SystemExit("the two runs have different weights: score both with the same tool version")
    inds = {n: c["rf_cols"].loc[starts, [f"hit_{k}" for k in BARS]].to_numpy(dtype=float) for n, c in ((a, ca), (b, cb))}
    t = sc["tie"]
    res = tie_test(inds, w, b, month_multiplicity(starts, int(t["reps"]), int(t["seed"])), float(t["level"]))[a]
    verdict = ("a is better (interval above 0)" if res["lo"] > 0 else "b is better (interval below 0)" if res["hi"] < 0
               else "no clear difference (interval includes 0)")
    L = [f"# Compare: {a} vs {b}", "",
         f"HEADLINE_RET: {a} {sa['primary']['headline']:.3f} ({'eligible' if sa['eligible'] else 'not eligible'}) · "
         f"{b} {sb['primary']['headline']:.3f} ({'eligible' if sb['eligible'] else 'not eligible'})", "",
         f"**Difference a - b = {res['diff']:+.3f}, {float(t['level']):.0%} interval [{res['lo']:+.3f}, {res['hi']:+.3f}]**: "
         f"{verdict}.", "",
         f"Paired bootstrap over calendar months of the window start: {int(t['reps'])} draws, seed {int(t['seed'])}, "
         f"{len(starts)} windows; each draw recomputes both HEADLINE_RETs with the drawn windows' final weights.", "",
         "| | a | b |", "|---|---|---|"]
    for k in BARS:
        L.append(f"| HIT {k} | {sa['return_first']['full']['hit'][k]:.3f} | {sb['return_first']['full']['hit'][k]:.3f} |")
    L.append(f"| CS_HIT | {sa['return_first']['full']['cs_hit']:.3f} | {sb['return_first']['full']['cs_hit']:.3f} |")
    for g in sa["gates"]:
        L.append(f"| {g} ({'hard' if sa['gates'][g]['hard'] else 'report-only'}) | "
                 f"{'PASS' if sa['gates'][g]['pass'] else 'FAIL'} | {'PASS' if sb['gates'][g]['pass'] else 'FAIL'} |")
    L += ["", f"Tool version `{sa['tool_version']}` · run keys `{sa['model']['run_key']}` / `{sb['model']['run_key']}` · "
          f"runtime {time.time() - t0:.0f} s."]
    md.write_text("\n".join(L) + "\n")
    log.info("compare %s - %s = %+.4f [%+.4f, %+.4f]; report %s", a, b, res["diff"], res["lo"], res["hi"], md)
    return 0


def cmd_leaderboard(cfg: dict) -> int:
    market = load_market(cfg)
    out = registry.write_leaderboard(cfg, tool_version(cfg, market))
    print(out.read_text())
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m backtest.scoring", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("field", help="score CASH and the field benchmarks")
    f.add_argument("--no-cache", action="store_true")
    c = sub.add_parser("compare", help="HEADLINE difference of two models with a bootstrap interval")
    c.add_argument("a")
    c.add_argument("b")
    c.add_argument("--no-cache", action="store_true")
    sub.add_parser("leaderboard", help="regenerate the leaderboard")
    a = ap.parse_args(argv)
    cfg = load_config()
    if a.cmd == "field":
        return cmd_field(cfg, not a.no_cache)
    if a.cmd == "compare":
        return cmd_compare(cfg, a.a, a.b, not a.no_cache)
    return cmd_leaderboard(cfg)


if __name__ == "__main__":
    raise SystemExit(main())
