"""Selection ladder: does picking between models beat simply holding one? (docs/STRATEGY_GUIDE.md section 6)

    python -m backtest.selection [--candidates name,name,...] [--step-days 7]

At every test date D (weekly from the SCREEN start) each rung picks a model using only windows that had
ended by D, then is scored on the 14-day window that starts at D (from cash). Pickers:
  history    best candidate on every completed window so far
  recent     best candidate on the 25 most recent non-overlapping completed windows
  lookalike  best candidate on the 25 completed windows whose starting market state is most like D's
             (the validation's CORE features and pick rules; the orchestrator idea)
  <selector> any registered model with method 'selector', scored like any model
References: fixed:<model> (each candidate held throughout), blend (equal mix of the candidates' decisions),
random (average over candidates) and oracle (best candidate at D in hindsight; headroom only).
"Best" = highest median composite A over the reference windows (pre-registered).
A picker passes only if its mean realized composite A beats BOTH the fixed momentum winner and the blend,
with the 90% block-bootstrap interval of the difference above zero, in BOTH SCREEN and CONFIRM.
"""
from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from backtest.compare import rank_models
from backtest.data import load_market
from backtest.evaluate import _ts, evaluate, must_pass, period_masks, simulate_windows, summarize
from backtest.report import num, open_run
from backtest.run import REFERENCE_MODEL
from src.config import load_config, resolve
from src.models import by_method, get
from src.validation.features import CORE_GROUPS
from src.validation.selection import PickRules, active_features, select_lookalikes

PICK_SCORE = "comp_a"
PICKERS = ("history", "recent", "lookalike")


def pick_best(W: dict[str, pd.DataFrame], starts, score: str = PICK_SCORE) -> str | None:
    """Candidate with the highest median `score` over the given window starts (ties: alphabetical)."""
    starts = pd.DatetimeIndex(starts)
    if len(starts) == 0:
        return None
    med = {m: W[m].loc[W[m].index.intersection(starts), score].median() for m in sorted(W)}
    med = {m: v for m, v in med.items() if pd.notna(v)}
    return max(med, key=lambda m: (med[m], -sorted(med).index(m))) if med else None


def completed(index: pd.DatetimeIndex, D: pd.Timestamp, days: int) -> pd.DatetimeIndex:
    return index[index + pd.Timedelta(days=days) <= D]


def recent_starts(done: pd.DatetimeIndex, days: int, n: int) -> list[pd.Timestamp]:
    out, limit = [], None
    for t in sorted(done, reverse=True):
        if limit is None or t <= limit:
            out.append(t)
            limit = t - pd.Timedelta(days=days)
            if len(out) == n:
                break
    return out


def block_boot_ci(x: np.ndarray, block: int = 4, reps: int = 2000, seed: int = 20261003) -> tuple[float, float]:
    """90% interval of the mean of a serially dependent series (moving-block bootstrap)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < block + 1:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=(reps, nb))
    idx = np.minimum((starts[:, :, None] + np.arange(block)).reshape(reps, -1)[:, :n], n - 1)
    means = x[idx].mean(axis=1)
    return float(np.percentile(means, 5)), float(np.percentile(means, 95))


def blend_targets(evs: dict) -> pd.DataFrame:
    """Equal mix of the candidates' actual decisions (hourly union of decision times, carried forward)."""
    tgs = [ev.targets for ev in evs.values()]
    times = tgs[0].index
    for t in tgs[1:]:
        times = times.union(t.index)
    cols = sorted(set().union(*[set(t.columns) for t in tgs]))
    parts = [t.reindex(columns=cols).fillna(0.0).reindex(times).ffill().fillna(0.0) for t in tgs]
    return sum(parts) / len(parts)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidates", default="", help="comma-separated model names (default: every momentum and trend model)")
    ap.add_argument("--step-days", type=int, default=7)
    ap.add_argument("--no-cache", action="store_true")
    a = ap.parse_args(argv)
    cfg = load_config()
    h, v = cfg["harness"], cfg["validation"]
    days = h["window_days"]
    md, lg, log = open_run(cfg, "selection")
    t_run = time.time()
    market = load_market(cfg)

    names = [x for x in a.candidates.split(",") if x] or sorted({**by_method("momentum"), **by_method("trend")})
    selectors = sorted(by_method("selector"))
    if len(names) < 2:
        md.write_text("# Selection ladder\n\nNeeds at least two candidate models.\n")
        log.info("fewer than two candidates: %s", names)
        return 0
    evs = {n: evaluate(get(n), market, cfg, use_cache=not a.no_cache, log=log) for n in names}
    sel_evs = {n: evaluate(get(n), market, cfg, use_cache=not a.no_cache, log=log) for n in selectors}
    ref = evaluate(get(REFERENCE_MODEL), market, cfg, use_cache=True, log=log)
    W = {n: ev.windows for n, ev in evs.items()}
    starts = W[names[0]].index
    band = min(ev.spec.band for ev in evs.values())
    W_blend = simulate_windows(market, blend_targets(evs), band, cfg, starts)
    log.info("blend of %s simulated on %d windows", names, len(starts))

    # the fixed reference: the momentum winner by the section 5 rule (else the best candidate on SCREEN)
    need = h["min_active_days"]
    mom = [n for n in names if evs[n].spec.method == "momentum"]
    summ = {n: {p: summarize(evs[n].windows[m.to_numpy()], need) for p, m in period_masks(evs[n].windows, cfg, False).items()}
            for n in mom}
    passing = [n for n in mom if all(ok for _, ok, _ in must_pass(evs[n], ref, cfg))]
    if passing:
        fixed = rank_models(summ, passing).index[0]
    else:
        screen = starts[period_masks(W[names[0]], cfg, False)["SCREEN"].to_numpy()]
        fixed = pick_best({n: W[n] for n in (mom or names)}, screen)
    log.info("fixed reference: %s", fixed)

    feats = pd.read_parquet(resolve(h["panel_dir"]) / "features.parquet")
    act = active_features(CORE_GROUPS)
    rules = PickRules(v["k"], v["min_separation_days"], v["span_days"], v["max_per_span"], v["horizon_days"])
    screen_lo = _ts(h["periods"]["SCREEN"][0], h["grid_hour_utc"])
    tests = [D for D in pd.date_range(screen_lo, starts[-1], freq=f"{a.step_days}D") if D in starts]
    rows, picks = [], {p: [] for p in PICKERS}
    for D in tests:
        done = completed(starts, D, days)
        choice = {"history": pick_best(W, done), "recent": pick_best(W, recent_starts(done, days, v["k"]))}
        pool = done.intersection(feats.index)
        pool = pool[feats.loc[pool, act].notna().all(axis=1).to_numpy()]
        look = None
        if D in feats.index and feats.loc[D, act].notna().all() and len(pool) >= v["k"]:
            sel, _ = select_lookalikes(feats.loc[pool, act], feats.loc[D, act], CORE_GROUPS, rules)
            if len(sel) == v["k"]:
                look = pick_best(W, sel["t0"])
        choice["lookalike"] = look
        row = {"D": D}
        for n in names:
            row[f"fixed:{n}"] = W[n].loc[D, PICK_SCORE]
        row["blend"] = W_blend.loc[D, PICK_SCORE]
        row["random"] = float(np.mean([W[n].loc[D, PICK_SCORE] for n in names]))
        row["oracle"] = float(max(W[n].loc[D, PICK_SCORE] for n in names))
        for p, m in choice.items():
            row[p] = W[m].loc[D, PICK_SCORE] if m else np.nan
            picks[p].append(m)
        for s, ev in sel_evs.items():
            row[s] = ev.windows.loc[D, PICK_SCORE]
        rows.append(row)
    R = pd.DataFrame(rows).set_index("D")

    periods = {}
    for name, (lo, hi) in h["periods"].items():
        lo_t, hi_t = _ts(lo, h["grid_hour_utc"]), _ts(hi, h["grid_hour_utc"])
        periods[name] = R[(R.index >= lo_t) & (R.index <= hi_t)]

    rungs = [f"fixed:{n}" for n in names] + ["blend", "random", "oracle"]
    testees = [p for p in PICKERS] + selectors
    verdict = {}
    lines = ["# Selection ladder", "",
             f"Candidates: {', '.join(names)} · selectors: {', '.join(selectors) or 'none registered'} · "
             f"fixed reference: **{fixed}** · test dates every {a.step_days} days · score: realized composite A "
             "of the window starting at each test date.", ""]
    for pname, P in periods.items():
        lines += [f"## {pname} ({len(P)} test dates)", "",
                  "| Rung | Mean comp. A | Median comp. A | vs fixed (90% CI) | vs blend (90% CI) |", "|---|---|---|---|---|"]
        for r in rungs + testees:
            if r not in P or P[r].isna().all():
                continue
            x = P[r].dropna()
            cells = [f"| {r} | {num(x.mean())} | {num(x.median())} |"]
            for base in (f"fixed:{fixed}", "blend"):
                if r in testees:
                    d = (P[r] - P[base]).dropna().to_numpy()
                    lo_ci, hi_ci = block_boot_ci(d)
                    cells.append(f" {num(d.mean())} [{num(lo_ci)}, {num(hi_ci)}] |")
                    verdict.setdefault(r, []).append(bool(lo_ci > 0))
                else:
                    cells.append(" |")
            lines.append("".join(cells))
        lines.append("")
    lines += ["## Verdict", "", "| Picker | Passes? |", "|---|---|"]
    for r in testees:
        ok = verdict.get(r, [])
        lines.append(f"| {r} | {'**PASS**' if ok and all(ok) and len(ok) == 2 * len(periods) else 'no'} |")
    lines += ["", "## What each picker chose", "", "| Picker | " + " | ".join(names) + " | none |",
              "|---|" + "---|" * (len(names) + 1)]
    for p in PICKERS:
        c = pd.Series(picks[p]).value_counts(dropna=False)
        lines.append(f"| {p} | " + " | ".join(str(int(c.get(n, 0))) for n in names) + f" | {int(c.get(None, 0))} |")
    lines += ["", "## Rule", "", (__doc__ or "").split("Pickers:")[1].strip(), "", f"Runtime {time.time() - t_run:.0f} s."]
    md.write_text("\n".join(lines) + "\n")
    log.info("verdict: %s", {r: all(v) for r, v in verdict.items()})
    log.info("report: %s", md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
