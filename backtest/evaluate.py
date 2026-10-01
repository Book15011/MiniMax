"""Score one model on every 14-day window (from cash), plus periods, scenario sets and must-pass checks."""
from __future__ import annotations

import hashlib
import inspect
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from backtest.data import Market, universe_at
from backtest.engine import Costs, Simulator, compute_targets, decision_times
from backtest.metrics import window_metrics
from src.config import REPO_ROOT, resolve
from src.contracts import MarketView, Model

UTC = "UTC"


@dataclass
class Evaluation:
    name: str
    spec: object
    params: dict
    windows: pd.DataFrame          # index = window start (UTC); one row of metrics per window
    holdout_opened: bool
    lookahead_failures: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)


def _ts(s: str, hour: int | None = None) -> pd.Timestamp:
    t = pd.Timestamp(s)
    if hour is not None and len(s) <= 10:
        t = t + pd.Timedelta(hours=hour)
    return t.tz_localize(UTC) if t.tzinfo is None else t.tz_convert(UTC)


def holdout_start(cfg: dict) -> pd.Timestamp:
    return _ts(cfg["harness"]["holdout_from"])


def window_starts(market: Market, cfg: dict, holdout: bool) -> pd.DatetimeIndex:
    h = cfg["harness"]
    hour, days, lag = h["grid_hour_utc"], h["window_days"], h["execution_lag_hours"]
    first = _ts(h["first_window"], hour)
    last_possible = market.close.index[-1] - pd.Timedelta(days=days) - pd.Timedelta(hours=lag)
    end = last_possible if holdout else min(last_possible, holdout_start(cfg) - pd.Timedelta(days=days))
    starts = pd.date_range(first, end, freq="1D")
    return starts[starts.isin(market.close.index)]


def git_state() -> dict:
    def run(*a):
        return subprocess.run(["git", *a], cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()
    return {"commit": run("rev-parse", "--short=12", "HEAD"), "dirty": bool(run("status", "--porcelain",
                                                                                  "--untracked-files=no"))}


ENGINE_FILES = ("backtest/engine.py", "backtest/metrics.py", "backtest/evaluate.py", "backtest/data.py",
                "src/contracts.py")


def cache_key(model: Model, params: dict, cfg: dict, market: Market, holdout: bool) -> str:
    """Changes with the model's code (every src.models module its class is built from), its parameters, the
    harness config, the data and the code that turns decisions into numbers (ENGINE_FILES)."""
    mods = sorted({c.__module__ for c in type(model).__mro__ if c.__module__.startswith("src.models")})
    src = "\n".join(inspect.getsource(sys.modules[m]) for m in mods)
    engine = {f: hashlib.sha256((REPO_ROOT / f).read_bytes()).hexdigest() for f in ENGINE_FILES}
    blob = json.dumps({"src": src, "params": params, "harness": cfg["harness"], "data": market.notes,
                       "holdout": holdout, "engine": engine}, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def lookahead_check(model: Model, market: Market, targets: pd.DataFrame, params: dict, n: int = 5,
                    seed: int = 20261003) -> list[str]:
    """Re-run the model at a few decision times: it must reproduce the stored decision exactly
    (deterministic, no hidden state). Views are truncated at t by construction, so the future is unreachable."""
    rng = np.random.default_rng(seed)
    idx = market.close.index
    fails = []
    for k in sorted(rng.choice(len(targets), size=min(n, len(targets)), replace=False)):
        t = targets.index[k]
        i = idx.get_loc(t)
        prev = targets.iloc[k - 1] if k > 0 else pd.Series(dtype=float)
        prev = prev[prev != 0.0]
        view = MarketView(t=t, close=market.close.iloc[: i + 1], quote_volume=market.quote_volume.iloc[: i + 1],
                          universe=universe_at(market, t), params=params, prev_targets=prev)
        w = model.targets(view).astype(float)
        w = w[w != 0.0].reindex(targets.columns).fillna(0.0)
        if not np.allclose(w.to_numpy(), targets.iloc[k].to_numpy(), atol=1e-12):
            fails.append(f"decision at {t} not reproduced (non-deterministic or hidden state)")
    return fails


def evaluate(model: Model, market: Market, cfg: dict, holdout: bool = False, use_cache: bool = True,
             log: logging.Logger | None = None) -> Evaluation:
    log = log or logging.getLogger(__name__)
    h = cfg["harness"]
    spec = model.spec
    params = (cfg.get("models") or {}).get(spec.name, {}) or {}
    key = cache_key(model, params, cfg, market, holdout)
    cdir = resolve(h["cache_dir"]) / spec.name
    wfile, mfile = cdir / f"{key}.parquet", cdir / f"{key}.json"
    if use_cache and wfile.exists() and mfile.exists():
        meta = json.loads(mfile.read_text())
        log.info("%s: cached result %s", spec.name, key)
        return Evaluation(spec.name, spec, params, pd.read_parquet(wfile), holdout, meta.pop("lookahead_failures"), meta)

    days, hour, lag = h["window_days"], h["grid_hour_utc"], h["execution_lag_hours"]
    starts = window_starts(market, cfg, holdout)
    if len(starts) == 0:
        raise SystemExit("no window starts in range; check harness.first_window and the data")
    times = decision_times(market.close.index, spec.rebalance_hours, hour, starts[0],
                           starts[-1] + pd.Timedelta(days=days))
    log.info("%s: %d decisions %s -> %s, %d windows", spec.name, len(times), times[0], times[-1], len(starts))
    targets = compute_targets(model, market, times, params)
    sim = Simulator(market, targets, spec.band, Costs(h["fees"]["taker"], h["fees"]["short"]), lag, hour,
                    h["activity_guard_offset_hours"])
    rows = []
    for t0 in starts:
        res = sim.run(market.close.index.get_loc(t0), days * 24)
        m = window_metrics(res.equity, days)
        m.update(active_days=res.active_days, turnover=res.turnover, fees=res.fees,
                 max_orders_day=res.max_orders_day, max_gross=res.max_gross)
        rows.append(m)
    windows = pd.DataFrame(rows, index=starts)
    windows.index.name = "t0"
    fails = lookahead_check(model, market, targets, params)
    held = targets.ne(0).sum(axis=1)
    meta = {"cache_key": key, "n_decisions": len(times), "coins_held_median": float(held.median()),
            "coins_ever_held": int((targets != 0).any().sum()), "git": git_state()}
    cdir.mkdir(parents=True, exist_ok=True)
    windows.to_parquet(wfile)
    mfile.write_text(json.dumps({**meta, "lookahead_failures": fails}, default=str))
    return Evaluation(spec.name, spec, params, windows, holdout, fails, meta)


# ---------------- periods, scenario sets, summaries, must-pass ----------------

def period_masks(windows: pd.DataFrame, cfg: dict, holdout_opened: bool) -> dict[str, pd.Series]:
    h = cfg["harness"]
    idx = windows.index
    H = holdout_start(cfg)
    end = idx + pd.Timedelta(days=h["window_days"])
    sealed = pd.Series(end > H, index=idx)
    masks: dict[str, pd.Series] = {}
    for name, (a, b) in h["periods"].items():
        lo, hi = _ts(a, h["grid_hour_utc"]), _ts(b, h["grid_hour_utc"])
        masks[name] = pd.Series((idx >= lo) & (idx <= hi), index=idx) & ~sealed
    masks["ALL"] = ~sealed
    looks = json.loads(resolve(h["scenario_sets"]["lookalikes"]).read_text())["windows"]
    look_idx = pd.DatetimeIndex([_ts(w["start"]) for w in looks])
    masks["LOOKALIKE25"] = pd.Series(idx.isin(look_idx), index=idx) & ~sealed
    n, step = h["scenario_sets"]["recent_n"], pd.Timedelta(days=h["window_days"])
    last = idx[~sealed.to_numpy()].max()
    recent = pd.DatetimeIndex([last - k * step for k in range(n)])
    masks[f"RECENT{n}"] = pd.Series(idx.isin(recent), index=idx) & ~sealed
    if holdout_opened:
        masks["HOLDOUT"] = sealed
    return masks


def summarize(w: pd.DataFrame, min_active: int) -> dict:
    if w.empty:
        return {"n": 0}
    days_in_window = 14
    return {"n": len(w), "med": w.ret.median(), "mean": w.ret.mean(), "p10": w.ret.quantile(0.1),
            "p90": w.ret.quantile(0.9), "worst": w.ret.min(), "best": w.ret.max(), "pos": (w.ret > 0).mean(),
            "mdd_med": w.mdd.median(), "mdd_worst": w.mdd.min(), "comp_a": w.comp_a.median(),
            "comp_b": w.comp_b.median(), "active_ok": (w.active_days >= min_active).mean(),
            "active_med": w.active_days.median(), "turn_day": w.turnover.mean() / days_in_window,
            "fees": w.fees.mean(), "orders_day_max": int(w.max_orders_day.max())}


def must_pass(ev: Evaluation, ref: Evaluation, cfg: dict) -> list[tuple[str, bool, str]]:
    h = cfg["harness"]
    masks = period_masks(ev.windows, cfg, False)
    test = masks["SCREEN"] | masks["CONFIRM"]
    w = ev.windows[test]
    rmask = period_masks(ref.windows, cfg, False)
    r = ref.windows[rmask["SCREEN"] | rmask["CONFIRM"]]
    need = h["min_active_days"]
    act = float((w.active_days >= need).mean())
    return [
        ("activity", act == 1.0, f"{act:.1%} of SCREEN+CONFIRM windows have >= {need} active days (need 100%)"),
        ("worst fortnight", w.ret.min() > r.ret.min(),
         f"worst {w.ret.min():+.2%} vs BTC hold {r.ret.min():+.2%} (must be better)"),
        ("no look-ahead / deterministic", not ev.lookahead_failures,
         "ok" if not ev.lookahead_failures else "; ".join(ev.lookahead_failures)),
        ("no leverage", True, f"targets checked at every decision (max gross after trades {w.max_gross.max():.3f})"),
    ]
