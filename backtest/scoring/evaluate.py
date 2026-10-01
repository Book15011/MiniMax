"""Run one model through the harness engine on every scored window and keep what the score needs.

Reuses backtest.engine as is: decisions from compute_targets, fills from Simulator.run(trace=True), which returns
the same equity as a plain run plus the trades and the hourly exposure. A window is 14 days of clock time: every
value is read at t0 + k hours (the last one at or before), and a fill belongs to the 24 h day of its timestamp, so
a missing bar in the panel never stretches the window or shifts a day. Adds, per window (docs/EVALUATION.md 2.5):
active days and how many came only from the activity guard, fees and spread over E_0, turnover, average and max
gross exposure, average net exposure, orders, and the most orders in one decision (planner rules).
Results are cached under scoring.cache_dir, keyed by the tool version and the model's code, parameters and mode.
"""
from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.data import Market
from backtest.engine import Costs, Simulator, compute_targets, decision_times
from backtest.evaluate import git_state, model_modules
from backtest.scoring.metrics import clock_series, window_metrics
from src.config import REPO_ROOT, resolve
from src.contracts import MarketView, Model

# Files whose content defines the numbers. Presentation-only modules (report, charts, registry, CLI) are left out,
# so a report change keeps the cache and the leaderboard.
TOOL_FILES = ("backtest/engine.py", "backtest/data.py", "backtest/evaluate.py", "src/contracts.py",
              "backtest/scoring/metrics.py", "backtest/scoring/windows.py", "backtest/scoring/evaluate.py",
              "backtest/scoring/leakage.py", "backtest/scoring/competition.py", "backtest/scoring/score.py")
NOT_IN_VERSION = ("report", "registry", "leaderboard", "cache_dir", "compare")
HOUR = pd.Timedelta(hours=1)
TRADE_COLUMNS = ["window_start", "hour", "time_utc", "kind", "series", "w_before", "w_after",
                 "notional_usd", "fee_usd", "spread_usd"]


class LongOnly:
    """G4: the same model with every negative target forced to 0 (the live fallback if shorts are disabled)."""

    def __init__(self, inner: Model):
        self.inner = inner
        self.spec = dataclasses.replace(inner.spec, uses_shorts=False)

    def targets(self, view: MarketView) -> pd.Series:
        return self.inner.targets(view).clip(lower=0.0)


@dataclass
class Run:
    name: str
    spec: object
    params: dict
    long_only: bool
    key: str
    windows: pd.DataFrame          # index = window start; section 2 metrics and section 2.5 activity per window
    equity: np.ndarray             # (windows, hours + 1), in units of E_0
    gross: np.ndarray              # (windows, hours + 1) sum |w| after each hour's trades
    net: np.ndarray                # (windows, hours + 1) sum w
    days: np.ndarray               # (windows, days) 1 = strategy trade, 2 = guard trade only, 0 = no trade
    trades: pd.DataFrame           # one row per coin traded, TRADE_COLUMNS
    targets: pd.DataFrame          # every decision (rows = decision times), for the leakage checks
    meta: dict = field(default_factory=dict)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_FILE_SHA: dict[str, str] = {}      # read once per process, so editing a file mid-run cannot mix two versions


def field_fingerprint(cfg: dict) -> dict:
    """Code and parameters of every field member. They set the return gate and the REL unit of every score, so a
    change to any of them (e.g. pol_mom_ss's code behind team_mom_ss25) must start a new leaderboard."""
    from src.models import get                                # deferred: src.models imports every model module
    models = cfg.get("models") or {}
    return {n: {"src": _sha(model_sources(get(n)).encode()), "params": models.get(n) or {}}
            for n in cfg["scoring"]["field"]}


def tool_version(cfg: dict, market: Market) -> str:
    if not _FILE_SHA:
        _FILE_SHA.update({f: _sha((REPO_ROOT / f).read_bytes()) for f in TOOL_FILES})
    files = dict(_FILE_SHA)
    sc = {k: v for k, v in cfg["scoring"].items() if k not in NOT_IN_VERSION}
    blob = json.dumps({"files": files, "scoring": sc, "harness": cfg["harness"], "data": market.notes,
                       "field": field_fingerprint(cfg)}, sort_keys=True, default=str)
    return _sha(blob.encode())[:16]


def model_sources(model: Model) -> str:
    """Source of every src.models module the model's code can reach (backtest.evaluate.model_modules: its class
    hierarchy and, transitively, what those modules refer to, e.g. a reused class or a combination's sleeves)."""
    base = model.inner if isinstance(model, LongOnly) else model
    return "\n".join(inspect.getsource(sys.modules[m]) for m in model_modules(base))


def run_key(model: Model, params: dict, long_only: bool, starts: pd.DatetimeIndex, cfg: dict, market: Market) -> str:
    blob = json.dumps({"tool": tool_version(cfg, market), "src": model_sources(model), "params": params,
                       "long_only": long_only, "starts": _sha("|".join(map(str, starts)).encode())},
                      sort_keys=True, default=str)
    return _sha(blob.encode())[:16]


def planner_orders(w0: np.ndarray, w1: np.ndarray, tol: float = 1e-12) -> int:
    """Orders src/execution/planner.py places to move w0 to w1: per coin, sell or buy spot and close or open a
    short (a long-to-short flip is two orders). Its minimum-order skipping is not modelled."""
    cl, cs, tl, ts = np.maximum(w0, 0), np.maximum(-w0, 0), np.maximum(w1, 0), np.maximum(-w1, 0)
    return int((tl < cl - tol).sum() + (ts < cs - tol).sum() + (tl > cl + tol).sum() + (ts > cs + tol).sum())


def _paths(cdir: Path, key: str) -> dict[str, Path]:
    return {k: cdir / f"{key}.{k}" for k in ("windows.parquet", "arrays.npz", "trades.parquet",
                                              "targets.parquet", "json")}


def _load(name, spec, params, long_only, key, p) -> Run:
    arr = np.load(p["arrays.npz"])
    return Run(name, spec, params, long_only, key, pd.read_parquet(p["windows.parquet"]), arr["equity"],
               arr["gross"], arr["net"], arr["days"], pd.read_parquet(p["trades.parquet"]),
               pd.read_parquet(p["targets.parquet"]), json.loads(p["json"].read_text()))


def simulate(model: Model, market: Market, cfg: dict, starts: pd.DatetimeIndex, long_only: bool = False,
             use_cache: bool = True, log: logging.Logger | None = None) -> Run:
    log = log or logging.getLogger(__name__)
    h, sc = cfg["harness"], cfg["scoring"]
    name = model.spec.name
    m = LongOnly(model) if long_only else model
    spec = m.spec
    params = (cfg.get("models") or {}).get(name, {}) or {}
    key = run_key(model, params, long_only, starts, cfg, market)
    cdir = resolve(sc["cache_dir"]) / name
    p = _paths(cdir, key)
    if use_cache and p["json"].exists():
        log.info("%s%s: cached scoring run %s", name, " (long-only)" if long_only else "", key)
        return _load(name, spec, params, long_only, key, p)

    t_start = time.time()
    days, hour, lag = h["window_days"], h["grid_hour_utc"], h["execution_lag_hours"]
    hours = days * 24
    idx = market.close.index
    times = decision_times(idx, spec.rebalance_hours, hour, starts[0], starts[-1] + pd.Timedelta(days=days))
    targets = compute_targets(m, market, times, params)
    t_targets = time.time() - t_start
    costs = Costs(h["fees"]["taker"], h["fees"]["short"])
    sim = Simulator(market, targets, spec.band, costs, lag, hour, h["activity_guard_offset_hours"],
                    float(h.get("keep_alive_weight", 0.0)), guard_utc_day=bool(h.get("guard_utc_day", False)))
    cols = np.array(sim.cols)
    e0 = float(sc["e0"])
    W = len(starts)
    E = np.empty((W, hours + 1))
    G = np.empty((W, hours + 1))
    N = np.empty((W, hours + 1))
    DAYS = np.zeros((W, days), dtype=np.int8)
    rows, trades = [], []
    sidx = sim.index
    for k, t0 in enumerate(starts):
        # The window is 14 days of clock time, t0 .. t0 + 336 h. The engine steps through sim.index; every value is
        # read at the clock hour t0 + k h as the last one at or before it (clock_series), so a missing bar never
        # stretches the window or shifts a day, whichever engine produced the steps.
        i0 = sidx.get_loc(t0)
        res = sim.run(i0, hours, trace=True)
        tr = res.trace
        at = sidx[i0: i0 + hours + 1]
        E[k] = clock_series(res.equity, at, t0, hours)
        G[k] = clock_series(tr["gross"], at, t0, hours)
        N[k] = clock_series(tr["net"], at, t0, hours)
        cost_e0 = fee_e0 = turnover = 0.0
        n_orders = max_calls = events = 0
        strat_day = np.zeros(days, dtype=bool)
        guard_day = np.zeros(days, dtype=bool)
        utc_days = set()                                       # UTC dates with a fill (report only; G1 counts 24 h days)
        for hh, kind, w0, w1, eqb, cost in tr["trades"]:
            when = at[hh]
            ck = int((when - t0) / HOUR)                        # clock hour of the fill, 1 .. 336 inside the window
            if ck > hours:
                continue                                       # after t0 + 14 days: outside the window
            day = (ck - 1) // 24                               # the 24 h day (16:00 UTC boundaries) that contains it
            (guard_day if kind == "guard" else strat_day)[day] = True
            utc_days.add(when.floor("D"))
            d = w1 - w0
            fee = (np.abs(np.maximum(w1, 0) - np.maximum(w0, 0)) * costs.taker
                   + np.abs(np.minimum(w1, 0) - np.minimum(w0, 0)) * costs.short)
            spread = np.abs(d) * sim.half
            orders = planner_orders(w0, w1)
            cost_e0 += cost * eqb
            fee_e0 += float(fee.sum()) * eqb
            turnover += float(np.abs(d).sum())
            n_orders += orders
            max_calls = max(max_calls, orders)
            events += 1
            for i in np.flatnonzero(np.abs(d) > 1e-12):
                trades.append((t0, ck, when, kind, cols[i], w0[i], w1[i], abs(d[i]) * eqb * e0,
                               fee[i] * eqb * e0, spread[i] * eqb * e0))
        DAYS[k] = np.where(strat_day, 1, np.where(guard_day, 2, 0))
        strat = int(strat_day.sum())
        guard_only = int((guard_day & ~strat_day).sum())
        rows.append({"active_days": strat + guard_only, "strategy_days": strat, "guard_days": guard_only,
                     "active_days_utc": len(utc_days),
                     "costs_e0": cost_e0, "fees_e0": fee_e0, "spread_e0": cost_e0 - fee_e0,
                     "turnover": turnover, "gross_avg": float(G[k, 1:].mean()), "gross_max": float(G[k, 1:].max()),
                     "net_avg": float(N[k, 1:].mean()), "gross_end": float(G[k, -1]), "orders": n_orders,
                     "max_calls_decision": max_calls, "trade_events": events})
    act = pd.DataFrame(rows, index=starts)
    met = window_metrics(E, act["gross_end"].to_numpy(), sc)
    met.index = starts
    windows = pd.concat([met, act], axis=1)
    windows.index.name = "t0"
    tdf = pd.DataFrame(trades, columns=TRADE_COLUMNS)
    held = targets.ne(0).sum(axis=1)
    meta = {"key": key, "tool_version": tool_version(cfg, market), "model": name, "long_only": long_only,
            "n_windows": W, "n_decisions": len(times), "coins_held_median": float(held.median()),
            "git": git_state(), "runtime_s": {"targets": round(t_targets, 1), "total": round(time.time() - t_start, 1)}}
    log.info("%s%s: %d decisions, %d windows in %.0f s (targets %.0f s)", name, " (long-only)" if long_only else "",
             len(times), W, meta["runtime_s"]["total"], t_targets)
    cdir.mkdir(parents=True, exist_ok=True)
    windows.to_parquet(p["windows.parquet"])
    np.savez_compressed(p["arrays.npz"], equity=E, gross=G, net=N, days=DAYS)
    tdf.to_parquet(p["trades.parquet"])
    targets.to_parquet(p["targets.parquet"])
    p["json"].write_text(json.dumps(meta, default=str))       # written last: marks the entry complete
    return Run(name, spec, params, long_only, key, windows, E, G, N, DAYS, tdf, targets, meta)
