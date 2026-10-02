"""Stress tests of the harness verdict for one model: python -m research.baitoey.validity [model] [--null-seeds N]

1. Null: the same model on randomly relabelled coins (BTC kept), so its picks carry no information.
2. Timing: fills 2 and 3 hours after the decision instead of 1.
3. Costs: fees x1.5, half-spreads x2.
4. Survivorship: every liquid coin (harness.universe = broad) instead of coins Roostoo lists today.
5. Luck: paired differences on non-overlapping fortnights.
6. Attribution: gross P&L of the long book vs the short sleeve, and average exposure (no band, no fees).
Writes results/baitoey/<YYYYMMDD>-validity-<model>/report.md.
"""
from __future__ import annotations

import argparse
import copy
import logging
from dataclasses import replace
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from backtest.data import load_market
from backtest.engine import compute_targets, decision_times
from backtest.evaluate import evaluate, period_masks, window_starts
from src.config import REPO_ROOT, load_config
from src.contracts import MarketView, ModelSpec
from src.models import get

BTC = "BTCUSDT"
PERIODS = ("SCREEN", "CONFIRM")


class Relabelled:
    """Wraps a model: each decision's non-BTC weights land on randomly shuffled coins, so picks are random."""

    def __init__(self, inner, seed: int):
        self.inner, self.seed = inner, seed
        self.spec = ModelSpec(name="baitoey_null", method="momentum", author="baitoey",
                              rebalance_hours=inner.spec.rebalance_hours, band=inner.spec.band, uses_shorts=True)

    def targets(self, view: MarketView) -> pd.Series:
        rng = np.random.default_rng([self.seed, int(view.t.timestamp()) // 3600])
        coins = [c for c in view.universe if c != BTC]
        perm = dict(zip(coins, rng.permutation(coins)))
        close = view.close.iloc[-1000:].rename(columns=perm)
        qv = view.quote_volume.iloc[-1000:].rename(columns=perm)
        # not mapped back: the weight computed from coin X's data lands on a different coin
        return self.inner.targets(replace(view, close=close, quote_volume=qv))


def stats(ev, cfg) -> dict:
    out = {}
    for per, m in period_masks(ev.windows, cfg, False).items():
        if per in PERIODS:
            w = ev.windows[m.to_numpy()]
            out[per] = (w.ret.median(), w.ret.quantile(0.1), (w.ret > 0).mean(), w.comp_a.median())
    return out


def row(name: str, s: dict) -> str:
    cells = [f"{s[p][0]:+.2%} / {s[p][1]:+.2%} / {s[p][2]:.0%} / {s[p][3]:+.2f}" for p in PERIODS]
    return f"| {name} | " + " | ".join(cells) + " |"


def paired(a, b, cfg) -> list[str]:
    lines = []
    for per in PERIODS:
        m = period_masks(a.windows, cfg, False)[per].to_numpy()
        d = (a.windows.ret - b.windows.ret)[m]
        means = [d.iloc[o::14].mean() for o in range(14)]
        x = d.iloc[0::14]
        se = x.std(ddof=1) / np.sqrt(len(x))
        lines.append(f"| {per} | {len(x)} | {np.mean(means):+.2%} | ±{1.645 * se:.2%} | {(d > 0).mean():.0%} |")
    return lines


def attribution(model, market, cfg, params) -> list[str]:
    h = cfg["harness"]
    starts = window_starts(market, cfg, False)
    times = decision_times(market.close.index, model.spec.rebalance_hours, h["grid_hour_utc"], starts[0],
                           starts[-1] + pd.Timedelta(days=h["window_days"]))
    tg = compute_targets(model, market, times, params)
    w = tg.reindex(market.close.index).ffill().fillna(0.0).shift(h["execution_lag_hours"] + 1).fillna(0.0)
    r = market.close.pct_change(fill_method=None).fillna(0.0)[w.columns]
    lines = []
    for per, (a, b) in h["periods"].items():
        sel = (w.index >= pd.Timestamp(a, tz="UTC")) & (w.index < pd.Timestamp(b, tz="UTC") + pd.Timedelta(days=14))
        ws, rs = w[sel], r[sel]
        lp = (ws.clip(lower=0) * rs).sum(axis=1)
        sp = (ws.clip(upper=0) * rs).sum(axis=1)
        f = 14 * 24
        lines.append(f"| {per} | {ws.clip(lower=0).sum(axis=1).mean():.0%} | {-ws.clip(upper=0).sum(axis=1).mean():.0%} | "
                     f"{lp.mean() * f:+.2%} | {sp.mean() * f:+.2%} | {(lp + sp).mean() * f:+.2%} |")
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("model", nargs="?", default="baitoey_tg_mom")
    ap.add_argument("--null-seeds", type=int, default=5)
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    log = logging.getLogger("validity")
    cfg = load_config()
    model, ref = get(a.model), get("pol_mom_ss")
    params = cfg["models"][a.model]
    market = load_market(cfg)
    base = evaluate(model, market, cfg, log=log)
    refev = evaluate(ref, market, cfg, log=log)
    out = [f"# Validity checks: {a.model}", "",
           "Cells: median / worst 10% / share > 0 / median comp. A, per 14-day window.", "",
           "| Scenario | SCREEN | CONFIRM |", "|---|---|---|", row("base", stats(base, cfg)),
           row("ref: pol_mom_ss", stats(refev, cfg))]

    nulls = []
    for s in range(a.null_seeds):
        c = copy.deepcopy(cfg)
        c["models"]["baitoey_null"] = {**params, "_null_seed": s, "_inner": a.model}
        ev = evaluate(Relabelled(model, s), market, c, log=log)
        nulls.append(ev)
        out.append(row(f"null: random picks, seed {s}", stats(ev, c)))
        log.info("null seed %d done", s)

    for lag in (2, 3):
        c = copy.deepcopy(cfg); c["harness"]["execution_lag_hours"] = lag
        out.append(row(f"fills {lag}h after decision", stats(evaluate(model, market, c, log=log), c)))
    c = copy.deepcopy(cfg); c["harness"]["fees"] = {k: v * 1.5 for k, v in cfg["harness"]["fees"].items()}
    out.append(row("fees x1.5", stats(evaluate(model, market, c, log=log), c)))
    m2 = copy.copy(market); m2.half_spread = market.half_spread * 2
    m2.notes = {**market.notes, "spread_mult": 2}
    out.append(row("half-spreads x2", stats(evaluate(model, m2, cfg, log=log), cfg)))

    c = copy.deepcopy(cfg); c["harness"]["universe"] = "broad"
    mb = load_market(c)
    out.append(row("broad universe (incl. coins Roostoo doesn't list)", stats(evaluate(model, mb, c, log=log), c)))
    out.append(row("broad universe: pol_mom_ss", stats(evaluate(ref, mb, c, log=log), c)))

    out += ["", f"## Paired difference on non-overlapping fortnights: {a.model} minus pol_mom_ss", "",
            "| Period | Independent fortnights | Mean difference | 90% interval (±) | Windows where model wins |",
            "|---|---|---|---|---|"] + paired(base, refev, cfg)
    out += ["", f"## Paired difference: {a.model} minus null seed 0 (does coin picking add value?)", "",
            "| Period | Independent fortnights | Mean difference | 90% interval (±) | Windows where model wins |",
            "|---|---|---|---|---|"] + paired(base, nulls[0], cfg)
    out += ["", "## Attribution (gross, no band or fees, per 14 days)", "",
            "| Period | Avg long exposure | Avg short exposure | Long P&L | Short P&L | Total |", "|---|---|---|---|---|---|"]
    out += attribution(model, market, cfg, params)

    text = "\n".join(out)
    print(text)
    root = REPO_ROOT.parent.parent if REPO_ROOT.parent.name == ".worktrees" else REPO_ROOT
    dest = root / "results" / "baitoey" / f"{datetime.now(timezone.utc):%Y%m%d}-validity-{a.model}"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "report.md").write_text(text)
    log.info("saved %s", dest / "report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
