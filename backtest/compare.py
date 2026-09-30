"""Compare every model in one method and pick the winner by the pre-registered rule.

    python -m backtest.compare --method momentum [--no-cache]

Writes reports/compare/<method>/<YYYYMMDD-HHMM>.md and .log. The rule (docs/STRATEGY_GUIDE.md section 5):
1. Must-pass on SCREEN + CONFIRM windows: activity, worst fortnight better than BTC hold, no look-ahead.
2. In each of SCREEN and CONFIRM, rank passing models on four scores (higher is better): median composite A,
   median composite B, worst-10% return, share of positive windows. Period score = mean rank.
3. Combined = mean of the two period scores. Lowest wins; ties go to the better CONFIRM score, then lower turnover.
"""
from __future__ import annotations

import argparse
import time

import pandas as pd

from backtest.data import load_market
from backtest.evaluate import evaluate, must_pass, period_masks, summarize
from backtest.report import num, open_run, pct
from backtest.run import REFERENCE_MODEL
from src.config import load_config
from src.contracts import METHODS
from src.models import by_method, get

SCORES = (("comp_a", "median comp. A"), ("comp_b", "median comp. B"), ("p10", "worst 10%"), ("pos", "share > 0"))
PERIODS = ("SCREEN", "CONFIRM")
RULE = """1. Must-pass on SCREEN + CONFIRM windows: activity (>= min_active_days in every window), worst fortnight
   better than BTC hold's, decisions reproducible (no look-ahead, no hidden state).
2. In each of SCREEN and CONFIRM, rank the passing models on four scores (higher is better): median composite A,
   median composite B, worst-10% return, share of positive windows. Period score = mean of the four ranks.
3. Combined = mean of the two period scores. Lowest wins; ties go to the better CONFIRM score, then lower turnover."""


def rank_models(summ: dict[str, dict[str, dict]], passing: list[str]) -> pd.DataFrame:
    """summ[model][period] -> summary dict. Returns per-model period scores, combined score and rank."""
    rows = {}
    for period in PERIODS:
        tab = pd.DataFrame({m: {k: summ[m][period][k] for k, _ in SCORES} for m in passing}).T
        ranks = tab.rank(ascending=False, method="average")
        rows[period] = ranks.mean(axis=1)
    out = pd.DataFrame(rows)
    out["combined"] = out[list(PERIODS)].mean(axis=1)
    out["turn"] = [summ[m]["CONFIRM"]["turn_day"] for m in out.index]
    out = out.sort_values(["combined", "CONFIRM", "turn"])
    out["place"] = range(1, len(out) + 1)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--method", required=True, choices=METHODS)
    ap.add_argument("--no-cache", action="store_true")
    a = ap.parse_args(argv)
    cfg = load_config()
    models = by_method(a.method)
    md, lg, log = open_run(cfg, f"compare/{a.method}")
    if not models:
        md.write_text(f"# Compare: {a.method}\n\nNo registered models in this method yet.\n")
        log.info("no models in method %s", a.method)
        return 0
    t0 = time.time()
    market = load_market(cfg)
    ref = evaluate(get(REFERENCE_MODEL), market, cfg, use_cache=True, log=log)
    need = cfg["harness"]["min_active_days"]
    evs, summ, checks = {}, {}, {}
    for name, model in sorted(models.items()):
        ev = evaluate(model, market, cfg, use_cache=not a.no_cache, log=log)
        evs[name] = ev
        masks = period_masks(ev.windows, cfg, False)
        summ[name] = {p: summarize(ev.windows[m.to_numpy()], need) for p, m in masks.items()}
        checks[name] = must_pass(ev, ref, cfg)
    passing = [m for m in evs if all(ok for _, ok, _ in checks[m])]
    ranking = rank_models(summ, passing) if passing else pd.DataFrame()
    winner = ranking.index[0] if len(ranking) else None

    lines = [f"# Compare: {a.method}", "",
             f"{len(evs)} model(s) · {len(passing)} pass the must-pass checks · "
             f"winner: **{winner or 'none'}**", "",
             "## Must-pass (SCREEN + CONFIRM)", "", "| Model | Author | " + " | ".join(c for c, _, _ in checks[next(iter(evs))]) + " |",
             "|---|---|" + "---|" * len(checks[next(iter(evs))])]
    for m in evs:
        lines.append(f"| {m} | {evs[m].spec.author} | " + " | ".join(("PASS" if ok else "**FAIL**: " + d) for _, ok, d in checks[m]) + " |")
    for period in PERIODS + ("LOOKALIKE25", "RECENT25"):
        lines += ["", f"## {period}", "", "| Model | n | Median | Worst 10% | Worst | > 0 | Median comp. A | Median comp. B | Median max DD | Turnover/day |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for m in evs:
            s = summ[m].get(period, {"n": 0})
            if not s.get("n"):
                lines.append(f"| {m} | 0 | | | | | | | | |")
                continue
            lines.append(f"| {m} | {s['n']} | {pct(s['med'])} | {pct(s['p10'])} | {pct(s['worst'])} | {s['pos']:.0%} | "
                         f"{num(s['comp_a'])} | {num(s['comp_b'])} | {pct(s['mdd_med'])} | {s['turn_day']:.2f} |")
    lines += ["", "## Ranking (lower is better; ranks among passing models)", ""]
    if len(ranking):
        lines += ["| Place | Model | SCREEN score | CONFIRM score | Combined |", "|---|---|---|---|---|"]
        for m, r in ranking.iterrows():
            lines.append(f"| {int(r.place)} | {m} | {r.SCREEN:.2f} | {r.CONFIRM:.2f} | {r.combined:.2f} |")
    else:
        lines.append("No model passes the must-pass checks, so this method has no winner.")
    lines += ["", "## Rule (pre-registered in docs/STRATEGY_GUIDE.md section 5)", "", RULE, "",
              f"Runtime {time.time() - t0:.0f} s."]
    md.write_text("\n".join(lines) + "\n")
    log.info("winner for %s: %s", a.method, winner)
    log.info("report: %s", md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
