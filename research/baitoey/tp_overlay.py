"""A take-profit overlay on baitoey_vt_mom (research/baitoey/prereg/20261006-tp-overlay.md).

    python -m research.baitoey.tp_overlay SCREEN      the SCREEN windows (run first, report committed)
    python -m research.baitoey.tp_overlay CONFIRM     the CONFIRM windows (run once, after SCREEN)
"""
from __future__ import annotations

import bisect
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.data import load_market
from backtest.scoring.evaluate import simulate
from backtest.scoring.metrics import window_metrics
from backtest.scoring.returnfirst import pol_period_rel
from backtest.scoring.windows import pool_starts
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models import get

NAME = "baitoey_vt_mom"
SCORE = ROOT / "results/book/20261001-scoring/baitoey_vt_mom-20261001-1825"
KLINES = ROOT / "data/binance_spot/klines_1h"
OUT = ROOT / "results" / "baitoey" / "20261006-tp-overlay"
H, MAKER, TAKER = 336, 0.0005, 0.001
RUNS = {"A": (None, None), "B": (0.08, 1.0), "C": (0.12, 1.0), "D": (0.08, 0.5)}
REL_GAIN = 0.05


def overlay_window(E, G, close, high, trades, decisions, tp, frac, half):
    """One window. E, G: engine equity and gross at hours 0..H. close, high: {coin: array over hours}. trades: (hour,
    coin, weight after), in time order. decisions: decision bars; each fills at the next bar. half: {coin: half-spread}.
    tp None: no overlay. Returns (equity path, gross at the end, stats); the stats' extra_cost is in equity units."""
    E = np.asarray(E, dtype=float); last_h = len(E) - 1
    out = E.copy()
    st = {"orders": 0, "fills": 0, "higher": 0, "lower": 0, "dropped": 0, "extra_cost": 0.0}
    if tp is None:
        return out, float(G[-1]), st
    steps: dict[str, tuple[list, list]] = {}
    for h, c, w in trades:
        hs, us = steps.setdefault(c, ([], []))
        hs.append(h); us.append(w * E[h] / close[c][h] if close[c][h] > 0 else 0.0)

    def units(c, k):
        hs, us = steps[c]
        i = bisect.bisect_right(hs, k) - 1
        return us[i] if i >= 0 else 0.0

    M, g_end = 1.0, float(G[-1])
    for j, d in enumerate(decisions):
        f = d + 1
        if f > last_h:
            break
        nd = decisions[j + 1] if j + 1 < len(decisions) else None
        last = min(nd, last_h) if nd is not None else last_h
        settle = nd + 1 if nd is not None and nd + 1 <= last_h else None
        end = settle if settle is not None else last_h + 1
        delta = np.zeros(last_h + 2)                                   # overlay minus engine, this cycle, by hour
        held_diff = 0.0                                                # overlay minus engine holdings value at the end
        for c in steps:
            if units(c, f) <= 0:
                continue
            st["orders"] += 1
            T = close[c][d] * (1 + tp)
            k = next((k for k in range(f + 1, last + 1)
                      if (high[c][k] if np.isfinite(high[c][k]) else close[c][k]) >= T), None)
            if k is None:
                continue
            rate = TAKER + half.get(c, 0.0)
            u = units(c, k - 1); keep = (1 - frac) * u
            dcash = frac * u * T * (1 - MAKER)                         # the overlay's cash minus the engine's
            st["fills"] += 1; st["extra_cost"] += M * frac * u * T * MAKER
            prev = u
            for t in range(k, end):
                now = units(c, t)
                if now != prev:                                        # an engine trade the overlay skips
                    dcash += (now - prev) * close[c][t] + abs(now - prev) * close[c][t] * rate
                    st["extra_cost"] -= M * abs(now - prev) * close[c][t] * rate
                    prev = now
                delta[t] += dcash + (keep - prev) * close[c][t]
            if settle is None:
                held_diff += (keep - prev) * close[c][last_h]
                continue
            P, a, b = close[c][settle], prev, units(c, settle)
            cost_o, cost_e = abs(b - keep) * P * rate, abs(b - a) * P * rate
            delta[settle] += dcash + (keep - a) * P - cost_o + cost_e
            st["extra_cost"] += M * (cost_o - cost_e)
            if b > 0:
                st["higher" if P > T else "lower"] += 1
            else:
                st["dropped"] += 1
        for t in range(f, end):
            out[t] = M * (E[t] + delta[t])
        if settle is not None:
            M *= (E[settle] + delta[settle]) / E[settle]
            out[settle] = M * E[settle]
        else:
            g_end = max((G[-1] * E[-1] + held_diff) / (E[-1] + delta[last_h]), 0.0)
    return out, g_end, st


def load_highs(coins, index: pd.DatetimeIndex) -> pd.DataFrame:
    """Hourly highs labelled by the bar's close time (the panel's convention), from the monthly 1-hour kline zips."""
    months = pd.period_range(index[0].tz_convert(None).to_period("M") - 1, index[-1].tz_convert(None).to_period("M"), freq="M")
    out = {}
    for c in coins:
        parts = []
        for mth in months:
            f = KLINES / c / f"{c}-1h-{mth.strftime('%Y-%m')}.zip"
            if not f.exists():
                continue
            with zipfile.ZipFile(f) as z:
                d = pd.read_csv(z.open(z.namelist()[0]), header=None, usecols=[0, 2])
            t = d[0].astype("int64")
            t = np.where(t > 10 ** 14, t // 1000, t)                          # microseconds from 2025 on
            parts.append(pd.Series(d[2].to_numpy(), index=pd.to_datetime(t, unit="ms", utc=True) + pd.Timedelta(hours=1)))
        if parts:
            s = pd.concat(parts); out[c] = s[~s.index.duplicated()].reindex(index)
    return pd.DataFrame(out, index=index)


def main(period: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_config(); sc = cfg["scoring"]; market = load_market(cfg)
    a, b = cfg["harness"]["periods"][period]
    score = json.load(open(SCORE / "score.json"))
    pw = pd.DataFrame(score["per_window"]); pw.index = pd.to_datetime(pw.pop("start"), utc=True)
    w_live, w_rec = pw.w_live.astype(float), pw.w_rec.astype(float)
    d = pw.index.normalize()
    starts = pw.index[(d >= pd.Timestamp(a, tz="UTC")) & (d <= pd.Timestamp(b, tz="UTC"))]
    pool = pool_starts(market, cfg)
    run = simulate(get(NAME), market, cfg, pool, use_cache=True); k = run.windows.index.get_indexer(starts)
    assert (k >= 0).all(), "a scored start is missing from the cached run"
    E_all, G_all = run.equity[k].astype(float), run.gross[k].astype(float)
    tr = pd.read_csv(SCORE / "trades.csv.gz"); tr["start"] = pd.to_datetime(tr.window_start, utc=True)
    tr = tr[tr.start.isin(starts)]
    coins = sorted(tr.series.unique())
    hours = pd.date_range(starts[0], starts[-1] + pd.Timedelta(hours=H), freq="h")
    close = market.close.reindex(hours)[coins].ffill()
    high = load_highs(coins, hours)
    missing = [c for c in coins if c not in high.columns]
    for c in missing:
        high[c] = np.nan
    half = {c: float(market.half_spread.get(c, cfg["harness"]["default_half_spread_bps"] / 1e4)) for c in coins}
    by_start = {s: g for s, g in tr.groupby("start")}
    close_np, high_np = {c: close[c].to_numpy() for c in coins}, {c: high[c].to_numpy() for c in coins}
    field = {n: simulate(get(n), market, cfg, pool, use_cache=True).windows for n in sc["field"]}
    points = np.array([0] + list(range(4, H, 24)) + [H])
    decisions = [0] + list(range(4, H, 24))
    res = {}
    for key, (tp, frac) in RUNS.items():
        Es, gends, stats = [], [], []
        for i, s0 in enumerate(starts):
            g = by_start.get(s0)
            pos = hours.get_indexer(s0 + pd.to_timedelta(np.arange(H + 1), unit="h"))
            if g is None:
                Es.append(E_all[i]); gends.append(G_all[i, -1]); stats.append({"orders": 0, "fills": 0, "higher": 0, "lower": 0, "dropped": 0, "extra_cost": 0.0, "fees": 0.0}); continue
            cs = sorted(g.series.unique())
            cl = {c: close_np[c][pos] for c in cs}
            hi = {c: high_np[c][pos] for c in cs}
            trades = [(int(r.hour), r.series, float(r.w_after)) for r in g.sort_values("hour").itertuples()]
            e, ge, st = overlay_window(E_all[i], G_all[i], cl, hi, trades, decisions, tp, frac, half)
            st["fees"] = float((g.fee_usd + g.spread_usd).sum()) / 100000 + st["extra_cost"] / E_all[i, 0]
            Es.append(e); gends.append(ge); stats.append(st)
        Em = np.vstack(Es)
        win = window_metrics(Em, np.array(gends), sc, points=points); win.index = starts
        if tp is None:
            gap = float((win.R_liq - run.windows.R_liq.reindex(starts)).abs().max())
        rel = pol_period_rel(win, field, w_live, w_rec, np.ones(len(starts), dtype=bool), sc)
        S = pd.DataFrame(stats)
        res[key] = {"rel": rel, "median": float(win.R_liq.median()), "p75": float(win.R_liq.quantile(0.75)), "p90": float(win.R_liq.quantile(0.90)),
                    "fill_rate": float(S.fills.sum() / max(S.orders.sum(), 1)), "fills_per_round": float(S.fills.mean()),
                    "higher": int(S.higher.sum()), "lower": int(S.lower.sum()), "dropped": int(S.dropped.sum()), "fees": float(S.fees.mean())}
    P = lambda v: f"{100 * v:+.2f}%"
    pc = score["period_check"][period]
    lines = [f"# Take-profit overlay on baitoey_vt_mom: {period}", "",
             f"Pre-registration: `research/baitoey/prereg/20261006-tp-overlay.md`. {len(starts)} windows starting {a} to {b}; "
             f"{len(coins)} coins traded, {len(missing)} without hourly highs (close used): {', '.join(missing) or 'none'}.",
             f"Check: A's REL {res['A']['rel']:.4f} against the registered period_check {pc:.4f}; A's fortnight returns "
             f"differ from the engine's by at most {gap:.2e}. Hourly highs: Binance 1-hour klines (every window ends by "
             f"2026-08-08, so the 1-minute data is not needed). Between a fill and the next decision the overlay skips that "
             f"coin's guard trades (addendum, written before the run).", "",
             "| Variant | tp_pct / fraction | Median fortnight R | 75th pct | 90th pct | TP fill rate (per coin-decision) | Fills per round | Bought back higher / lower | Fees per round | REL | REL vs A |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, (tp, frac) in RUNS.items():
        r = res[key]
        if tp is None:
            lab, fill, per_round, back = "none", "—", "—", "—"
        else:
            lab, fill, per_round = f"{100 * tp:.0f}% / {frac:g}", f"{100 * r['fill_rate']:.1f}%", f"{r['fills_per_round']:.2f}"
            back = f"{r['higher']} / {r['lower']} ({r['dropped']} dropped)"
        lines.append(f"| {key} | {lab} | {P(r['median'])} | {P(r['p75'])} | {P(r['p90'])} | {fill} | {per_round} | {back} | "
                     f"{P(r['fees'])} | {r['rel']:.3f} | {r['rel'] - res['A']['rel']:+.3f} |")
    better = [k for k in ("B", "C", "D") if res[k]["rel"] >= res["A"]["rel"] + REL_GAIN and res[k]["median"] >= res["A"]["median"]]
    lines += ["", f"- Better than A in {period} (REL at least +{REL_GAIN}, median not lower): {', '.join(better) or 'none'}."]
    (OUT / f"report-{period}.md").write_text("\n".join(lines) + "\n")
    (OUT / f"rows-{period}.json").write_text(json.dumps(res, indent=1))
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1])
