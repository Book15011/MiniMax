"""Lock-in vs the top-20 cut, by market scenario (analysis, not a model change).

For every scored 14-day round of pol_switch_vt_tl_e20v45: the hourly equity path, the end-of-round lock-in as the live
bot runs it (from day 10, once equity is +3% above the start: sell at the next hour at fee + median half-spread,
cash to the end), and the top-20 cut proxy of backtest/scoring/competition.py (max(0, best of the six benchmarks'
14-day R_liq); about 150 teams, so top 20 is the top 13%). Rounds are grouped by BTC's move from the round start to
the hour the lock fires, which the bot knows at that hour.

    python -m research.baitoey.lock_scenarios
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

import backtest.scoring.score as scoring
from backtest.data import load_market
from backtest.engine import Costs, Simulator, compute_targets, decision_times
from backtest.scoring.evaluate import first_decisions
from backtest.scoring.metrics import clock_series
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models import get

NAME = "pol_switch_vt_tl_e20v45"
OUT = ROOT / "results" / "baitoey" / "20261004-lock-scenarios"
HOURS, LOCK_FROM, LOCK = 336, 240, 0.03


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log = logging.getLogger("lock_scenarios")
    cfg = load_config(); market = load_market(cfg); h = cfg["harness"]
    cost = h["fees"]["taker"] + market.notes["median_half_spread_bps"] / 1e4
    starts = scoring.scored_starts(market, cfg, None)
    field = scoring.field_runs(market, cfg, scoring.simulated_starts(market, cfg, starts), True, log)
    best = pd.concat({n: r.windows.R_liq.reindex(starts) for n, r in field.items()}, axis=1).max(axis=1)
    cut = best.clip(lower=0.0)
    model, params = get(NAME), cfg["models"][NAME]
    btc = market.close["BTCUSDT"]
    rows = []
    for i, t0 in enumerate(starts):
        idx = market.close.index
        times = decision_times(idx, model.spec.rebalance_hours, h["grid_hour_utc"], t0 - pd.Timedelta(days=3), t0 + pd.Timedelta(hours=HOURS))
        targets, shared = compute_targets(model, market, times, params, keep_raw=True)
        f = first_decisions(model, market, pd.DatetimeIndex([t0]), times, shared, params, HOURS)[t0]
        sim = Simulator(market, targets, model.spec.band, Costs(h["fees"]["taker"], h["fees"]["short"]), h["execution_lag_hours"],
                        h["grid_hour_utc"], h["activity_guard_offset_hours"], float(h.get("keep_alive_weight", 0.0)),
                        guard_utc_day=bool(h.get("guard_utc_day", False)), extra_cols=sorted({c for x in f.decisions for c in x.index}))
        i0 = sim.index.get_loc(t0)
        until = sim.index.get_loc(f.until) if f.until is not None else i0 + HOURS + 1
        res = sim.run(i0, HOURS, trace=True, first=(np.array([sim.index.get_loc(t) for t in f.times]), sim.rows(f.decisions), until))
        at = sim.index[i0: i0 + HOURS + 1]
        E = clock_series(res.equity, at, t0, HOURS); G = clock_series(res.trace["gross"], at, t0, HOURS)
        E = E / E[0]
        k = next((k for k in range(LOCK_FROM, len(E) - 1) if E[k] - 1 >= LOCK), None)
        locked = E[-1] - 1 if k is None else E[k + 1] * (1 - cost * G[k + 1]) - 1
        tk = t0 + pd.Timedelta(hours=k if k is not None else LOCK_FROM)
        rows.append(dict(start=t0, R=E[-1] - 1, R_lock=locked, fired=k is not None, hour=k, R_at=E[k] - 1 if k is not None else np.nan,
                         btc_at=btc.asof(tk) / btc.asof(t0) - 1, btc_end=btc.asof(t0 + pd.Timedelta(hours=HOURS)) / btc.asof(t0) - 1,
                         cut=float(cut.loc[t0])))
        if i % 200 == 0:
            log.info("%d / %d rounds", i, len(starts))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "rounds.csv", index=False)
    lines = ["Lock-in vs the top-20 cut proxy (max(0, best of 6 benchmarks)), pol_switch_vt_tl_e20v45, %d rounds" % len(df), ""]
    P = lambda x: "%+.1f%%" % (100 * x)
    fired = df[df.fired]
    lines.append("lock fires in %d rounds (%.0f%%); in the others nothing changes" % (len(fired), 100 * len(fired) / len(df)))
    lines.append("")
    lines.append("%-30s %6s %11s %12s %14s %14s %16s %16s" % ("BTC move when the lock fires", "n", "cut (avg)", "our R then", "top-20 if lock", "top-20 if not", "behind cut then", "of those, caught up"))
    for lab, a, b in (("BTC down", -9, 0), ("BTC 0 to +5%", 0, 0.05), ("BTC +5 to +10%", 0.05, 0.10), ("BTC +10% or more", 0.10, 9), ("all", -9, 9)):
        x = fired[(fired.btc_at > a) & (fired.btc_at <= b)] if lab != "all" else fired
        if x.empty:
            continue
        behind = x[x.R_at < x.cut]
        lines.append("%-30s %6d %11s %12s %13.0f%% %13.0f%% %15.0f%% %15.0f%%" % (lab, len(x), P(x.cut.mean()), P(x.R_at.mean()),
                     100 * (x.R_lock >= x.cut).mean(), 100 * (x.R >= x.cut).mean(), 100 * len(behind) / len(x),
                     100 * (behind.R >= behind.cut).mean() if len(behind) else float("nan")))
    lines += ["", "top-20 if lock / if not: share of rounds whose final R clears the cut with the lock-in on / off.",
              "behind cut then: share where our return when the lock fires is below the round's final cut (the lock then",
              "guarantees a miss); caught up: of those, the share where continuing would have ended above the cut."]
    (OUT / "report.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
