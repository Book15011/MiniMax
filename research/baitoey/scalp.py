"""A one-step scalper on large-step coins against e20v45 (research/baitoey/prereg/20261005-scalp.md). Research only.

    python -m research.baitoey.scalp
"""
from __future__ import annotations

import glob
import json

import numpy as np
import pandas as pd

from backtest.data import load_market
from backtest.scoring.evaluate import simulate
from backtest.scoring.windows import pool_starts
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models import get

MINUTES = ROOT / "data" / "binance_spot" / "parquet"
SNAP = ROOT / "data" / "roostoo_snapshots" / "exchangeInfo_20260928T174533Z.json"
OUT = ROOT / "results" / "baitoey" / "20261005-scalp"
TOOL = "3036a0d8bfdaa6a0"
TAKER, MAKER, MIN_STEP, INVEST, STALE = 0.001, 0.0005, 0.0015, 0.90, 5
COINS = ["BONK", "PEPE", "STO", "1000CHEEMS", "SHIB", "WLFI", "HEMI"]
RUNS = {"P0": dict(), "P0T": dict(fill="touch"), "V1": dict(offset=0), "V2": dict(stop=2), "V3": dict(target=2)}
START, END, MARGIN = "2025-09-02 12:00", "2026-09-15 12:00", 0.03


def scalp_coin(o, h, l, c, step, offset=1, target=1, stop=3, fill="through"):
    """Minute-by-minute sub-account starting at 1. Returns mid equity, liquidation value, cumulative fees, trips, wins,
    calls per minute."""
    n = len(c)
    cash, units, entry, entry_bar, sell_px, buy_px, buy_t, buy_size = 1.0, 0.0, 0.0, -1, 0.0, None, -1, 0.0
    eq, liq, fee_c, trip_c, win_c, calls = (np.empty(n), np.empty(n), np.empty(n), np.empty(n), np.empty(n), np.zeros(n))
    fees, trips, wins = 0.0, 0, 0
    lvl = lambda x: np.floor(x / step + 1e-6) * step
    through = fill == "through"
    last = 1.0
    for i in range(n):
        if not np.isfinite(c[i]):
            eq[i] = liq[i] = last; fee_c[i], trip_c[i], win_c[i] = fees, trips, wins
            continue
        if units > 0 and entry_bar < i:
            stop_px = entry - stop * step
            if l[i] <= stop_px:
                px = (o[i] - step) if o[i] <= stop_px else (stop_px - step)
                px = max(px, step)
                cash += units * px * (1 - TAKER); fees += units * px * TAKER; trips += 1; units = 0.0
            elif (h[i] > sell_px) if through else (h[i] >= sell_px):
                cash += units * sell_px * (1 - MAKER); fees += units * sell_px * MAKER; trips += 1; wins += 1; units = 0.0
        elif buy_px is not None and buy_t < i and ((l[i] < buy_px) if through else (l[i] <= buy_px)):
            units = buy_size / buy_px * (1 - MAKER); fees += buy_size * MAKER; cash -= buy_size
            entry, entry_bar, sell_px, buy_px = buy_px, i, buy_px + target * step, None
            calls[i] += 1                                               # the sell order
        if units == 0 and buy_px is None:
            b = lvl(c[i]) - offset * step
            if b > 0:
                buy_px, buy_t, buy_size = b, i, INVEST * cash; calls[i] += 1
        elif buy_px is not None and i - buy_t >= STALE and lvl(c[i]) - offset * step > buy_px:
            buy_px, buy_t, buy_size = lvl(c[i]) - offset * step, i, INVEST * cash; calls[i] += 2
        last = cash + units * c[i]
        eq[i] = last; liq[i] = cash + units * max(c[i] - step, 0.0) * (1 - TAKER)
        fee_c[i], trip_c[i], win_c[i] = fees, trips, wins
    return eq, liq, fee_c, trip_c, win_c, calls


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_config(); sc = cfg["scoring"]; market = load_market(cfg)
    info = json.load(open(SNAP)); pairs = info.get("TradePairs") or info.get("Data") or info
    steps = {c: 10 ** (-int(pairs[f"{c}/USD"]["PricePrecision"])) for c in COINS}
    idx = pd.read_parquet(MINUTES / "BTCUSDT.parquet", columns=["timestamp"]).timestamp
    idx = pd.DatetimeIndex(idx)
    data = {}
    for c in COINS:
        d = pd.read_parquet(MINUTES / f"{c}USDT.parquet", columns=["timestamp", "open", "high", "low", "close"]).set_index("timestamp").reindex(idx)
        data[c] = d
    starts = pd.date_range(START, END, freq="D", tz="UTC")
    pool = pool_starts(market, cfg); liq_cost = float(sc["liquidation_cost"])
    ref = [json.load(open(f)) for f in glob.glob(str(ROOT / "results/*/*/pol_switch_vt_tl_e20v45-*/score.json"))]
    ref = [s for s in ref if s.get("tool_version") == TOOL][-1]
    pw = pd.DataFrame(ref["per_window"]); pw.index = pd.to_datetime(pw.pop("start"), utc=True); pw = pw[pw.scored.astype(bool)]
    starts = starts[starts.isin(pw.index)]; pw = pw.reindex(starts)
    w = pw.w_final.to_numpy(); w = w / w.sum(); up = pw.btc_up.astype(bool).to_numpy()
    bars = pw[["bar_LENIENT", "bar_MIDDLE", "bar_STRICT"]].to_numpy()
    fr = {}
    for n in sc["field"]:
        rr = simulate(get(n), market, cfg, pool, use_cache=True); k = rr.windows.index.get_indexer(starts)
        fr[n] = rr.equity[k, -1] * (1 - liq_cost * rr.gross[k, -1]) - 1
    cut = np.where(up, np.maximum(0, pd.DataFrame(fr).max(axis=1).to_numpy()), 0.006)
    s_pos = idx.get_indexer(starts); e_pos = idx.get_indexer(starts + pd.Timedelta(days=14))

    def stats(R, extra=None):
        out = {"hit": float(np.mean([(w * (R >= bars[:, b])).sum() for b in range(3)])), "cut": float((w * (R >= cut)).sum()),
               "mean": float((w * R).sum()), "median": float(np.median(R)), "worst": float(R.min()), "pos": float((w * (R > 0)).sum())}
        out.update(extra or {})
        return out

    res = {"e20v45": stats(pw.R_liq.to_numpy())}
    for key, kw in RUNS.items():
        per = {}
        calls_all = np.zeros(len(idx))
        for c in COINS:
            d = data[c]
            eq, lq, fc, tc, wc, calls = scalp_coin(d.open.to_numpy(), d.high.to_numpy(), d.low.to_numpy(), d.close.to_numpy(), steps[c], **kw)
            per[c] = (eq, lq, fc, tc, wc); calls_all += calls
        R, fees, trips, wins, n_elig = [], [], [], [], []
        for a, b in zip(s_pos, e_pos):
            el = [c for c in COINS if np.isfinite(data[c].close.iloc[a]) and steps[c] / data[c].close.iloc[a] >= MIN_STEP]
            n_elig.append(len(el))
            if not el:
                R.append(0.0); fees.append(0.0); trips.append(0); wins.append(0); continue
            R.append(float(np.mean([per[c][1][b] / per[c][0][a] - 1 for c in el])))
            fees.append(float(np.mean([(per[c][2][b] - per[c][2][a]) / per[c][0][a] for c in el])))
            trips.append(float(sum(per[c][3][b] - per[c][3][a] for c in el))); wins.append(float(sum(per[c][4][b] - per[c][4][a] for c in el)))
        R = np.array(R)
        per_min = pd.Series(calls_all, idx).resample("1min").sum()
        res[key] = stats(R, {"trips": float(np.mean(trips)), "win": float(np.sum(wins) / max(np.sum(trips), 1)), "fees": float(np.mean(fees)),
                             "coins": float(np.mean(n_elig)), "calls_peak": float(per_min.max()), "calls_mean": float(per_min.mean())})
    P = lambda v: f"{100 * v:+.2f}%"
    labels = {"e20v45": "e20v45 (live, same rounds)", "P0": "P0: buy 1 step below, +1 / -3 steps, THROUGH",
              "P0T": "P0T: P0 with TOUCH fills", "V1": "V1: buy at the last-price level", "V2": "V2: stop -2 steps", "V3": "V3: target +2 steps"}
    lines = ["# A one-step scalper on large-step coins against e20v45 (research only)", "",
             f"Pre-registration: `research/baitoey/prereg/20261005-scalp.md`. {len(starts)} rounds ({START} to {END} starts); coins {', '.join(COINS)}.", "",
             "| Strategy | Clears the bars | Top-20 proxy | Mean R | Median R | Worst R | Rounds > 0 | Eligible coins | Round trips per round | Win rate | Fees per round | Calls/min peak / mean |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, s in res.items():
        x = lambda k, f: f(s[k]) if k in s else "—"
        lines.append(f"| {labels[key]} | {100 * s['hit']:.0f}% | {s['cut']:.3f} | {P(s['mean'])} | {P(s['median'])} | {P(s['worst'])} | {100 * s['pos']:.0f}% | "
                     f"{x('coins', lambda v: f'{v:.1f}')} | {x('trips', lambda v: f'{v:.0f}')} | {x('win', lambda v: f'{100 * v:.0f}%')} | "
                     f"{x('fees', P)} | {x('calls_peak', lambda v: f'{v:.0f}')} / {x('calls_mean', lambda v: f'{v:.1f}')} |")
    e, p0, p0t = res["e20v45"], res["P0"], res["P0T"]
    ok = p0["hit"] >= e["hit"] + MARGIN and p0["cut"] >= e["cut"] and p0["mean"] > 0 and p0["worst"] > -0.10 and p0t["mean"] > 0
    lines += ["", f"- P0 against e20v45 on the same rounds (and P0T positive) -> **{'CANDIDATE FOR TEAM DISCUSSION' if ok else 'NO CANDIDATE'}**.",
              "- Steps (Roostoo snapshot 2026-09-28): " + ", ".join(f"{c} {steps[c]:g}" for c in COINS) + "."]
    (OUT / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
