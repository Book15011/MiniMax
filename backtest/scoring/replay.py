"""Report-only: a model over the previous edition's real windows, its return ranked among the real teams' returns.

Pol's replay (results/pol/20261001-final/replay.py) in the scoring engine: each window (scoring.replay) runs from
cash at 12:00 UTC with the engine's first decision at the start, as every scoring window does; decisions before it
start 3 days earlier, and every decision sees only data up to its time. R is mark-to-market, as in Pol's table.
The leaderboard file holds final returns only (numbers, no names).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.data import Market
from backtest.engine import Costs, Simulator, compute_targets, decision_times
from backtest.scoring.evaluate import first_decisions
from backtest.scoring.metrics import clock_series
from src.config import resolve
from src.contracts import Model


def replay(model: Model, market: Market, cfg: dict, params: dict) -> dict | None:
    rp = cfg["scoring"].get("replay")
    if not rp or not resolve(rp["leaderboard_csv"]).exists():
        return None
    lb = pd.read_csv(resolve(rp["leaderboard_csv"]))
    h = cfg["harness"]
    spec = model.spec
    idx = market.close.index
    out = []
    for w in rp["windows"]:
        t0 = pd.Timestamp(w["start"], tz="UTC")
        hours = int(w["hours"])
        if t0 + pd.Timedelta(hours=hours + h["execution_lag_hours"]) > idx[-1]:
            continue
        times = decision_times(idx, spec.rebalance_hours, h["grid_hour_utc"], t0 - pd.Timedelta(days=3),
                               t0 + pd.Timedelta(hours=hours))
        targets, shared = compute_targets(model, market, times, params, keep_raw=True)
        f = first_decisions(model, market, pd.DatetimeIndex([t0]), times, shared, params, hours)[t0]
        sim = Simulator(market, targets, spec.band, Costs(h["fees"]["taker"], h["fees"]["short"]),
                        h["execution_lag_hours"], h["grid_hour_utc"], h["activity_guard_offset_hours"],
                        float(h.get("keep_alive_weight", 0.0)), guard_utc_day=bool(h.get("guard_utc_day", False)),
                        extra_cols=sorted({c for x in f.decisions for c in x.index}))
        i0 = sim.index.get_loc(t0)
        until = sim.index.get_loc(f.until) if f.until is not None else i0 + hours + 1
        res = sim.run(i0, hours, first=(np.array([sim.index.get_loc(t) for t in f.times]), sim.rows(f.decisions), until))
        E = clock_series(res.equity, sim.index[i0: i0 + hours + 1], t0, hours)
        R = float(E[-1] / E[0] - 1.0)
        ranks = [{"competition": int(c), "rank": int((lb[lb.cpt == c].ret > R).sum()) + 1,
                  "teams": int((lb.cpt == c).sum())} for c in w["competitions"]]
        out.append({"name": w["name"], "start": t0, "hours": hours, "R": R,
                    "MDD": float((1 - E / np.maximum.accumulate(E)).max()), "ranks": ranks})
    return {"source": rp["leaderboard_csv"], "windows": out}
