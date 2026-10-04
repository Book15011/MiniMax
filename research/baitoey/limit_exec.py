"""Limit orders with a 2-5 minute wait, then market; shorts at market (research/baitoey/prereg/20261005-limit-exec.md).

    python -m research.baitoey.limit_exec
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from backtest.data import load_market
from research.baitoey.vt_study import ROOT
from src.config import load_config

TRADES = ROOT / "results/pol/20261002-scoring/pol_switch_vt_tl_e20v45-20261002-0620/trades.csv.gz"
MINUTES = ROOT / "data/binance_spot/parquet"
OUT = ROOT / "results" / "baitoey" / "20261005-limit-exec"
TAKER, MAKER = 0.001, 0.0005
WAITS, START, END = (2, 5), "2025-09-01", "2026-09-15"
MIN_SAVING, MIN_QUARTERS = 0.0002, 3


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_config(); market = load_market(cfg)
    t = pd.read_csv(TRADES)
    t["start"] = pd.to_datetime(t.window_start, utc=True); t["T"] = pd.to_datetime(t.time_utc, utc=True)
    t = t[(t.start >= pd.Timestamp(START, tz="UTC")) & (t.start <= pd.Timestamp(END, tz="UTC"))]
    have = {p.stem for p in MINUTES.glob("*.parquet")}
    spot = (t.w_before >= -1e-12) & (t.w_after >= -1e-12)
    print("trades in the period: %d, of which touching a short (stay at market, left out): %d, coins without minute data: %d" % (
        len(t), int((~spot).sum()), int((~t.series.isin(have)).sum())))
    t = t[spot & t.series.isin(have)].copy()
    t["buy"] = t.w_after > t.w_before
    rows = []
    for coin, g in t.groupby("series"):
        d = pd.read_parquet(MINUTES / f"{coin}.parquet", columns=["timestamp", "low", "high", "close"]).set_index("timestamp")
        h = float(market.half_spread.get(coin, cfg["harness"]["default_half_spread_bps"] / 1e4))
        T = pd.DatetimeIndex(g["T"])
        mid0 = d.close.reindex(T - pd.Timedelta(minutes=1)).to_numpy()
        out = {"coin": coin, "h": h}
        for W in WAITS:
            lows = np.column_stack([d.low.reindex(T + pd.Timedelta(minutes=k)).to_numpy() for k in range(W)])
            highs = np.column_stack([d.high.reindex(T + pd.Timedelta(minutes=k)).to_numpy() for k in range(W)])
            midW = d.close.reindex(T + pd.Timedelta(minutes=W - 1)).to_numpy()
            lo, hi = np.nanmin(lows, axis=1), np.nanmax(highs, axis=1)
            drift = midW / mid0 - 1
            for price, off in (("passive", h), ("mid", 0.0)):
                buy = g["buy"].to_numpy()
                filled = np.where(buy, lo < mid0 * (1 - off), hi > mid0 * (1 + off))
                fill_cost = -off + MAKER
                miss_cost = np.where(buy, drift, -drift) + h + TAKER
                g[f"cost_{W}_{price}"] = np.where(filled, fill_cost, miss_cost)
                g[f"fill_{W}_{price}"] = filled
        g["cost_base"] = h + TAKER
        g["ok"] = np.isfinite(mid0) & np.isfinite(g[[c for c in g.columns if c.startswith("cost_")]].to_numpy()).all(axis=1)
        rows.append(g[g.ok])
    t = pd.concat(rows)
    n = t.notional_usd
    wavg = lambda c, m=None: float((t[c] * n)[m].sum() / n[m].sum()) if m is not None else float((t[c] * n).sum() / n.sum())
    P = lambda x: "%+.3f%%" % (100 * x)
    lines = ["# Limit orders with a 2-5 minute wait, then market; shorts at market", "",
             "Pre-registration: `research/baitoey/prereg/20261005-limit-exec.md`. Costs are notional-weighted, in % of the notional,",
             "relative to the mid at the trade hour; a lower cost is better. %d spot trades of e20v45's backtest, windows %s to %s." % (len(t), START, END), "",
             "| Policy | Fill rate | Cost (all) | Saving vs market now | Buys / sells saving | decision / entry / guard saving | Quarters saving | Saving per 14-day round |",
             "|---|---|---|---|---|---|---|---|",
             "| Market now (base) | — | %s | — | — | — | — | — |" % P(wavg("cost_base"))]
    t["q"] = t["T"].dt.tz_convert(None).dt.to_period("Q")
    verdict = {}
    for W in WAITS:
        for price in ("passive", "mid"):
            c = f"cost_{W}_{price}"
            t["sav"] = t["cost_base"] - t[c]
            fr = float((t[f"fill_{W}_{price}"] * n).sum() / n.sum())
            by = {k: wavg("sav", t.kind == k) for k in ("decision", "entry", "guard")}
            qs = t.groupby("q").apply(lambda x: float((x.sav * x.notional_usd).sum() / x.notional_usd.sum()))
            per_round = float((t.sav * n).groupby(t.window_start).sum().mean() / 100000)
            lines.append("| Limit at the %s, wait %d min | %.0f%% | %s | **%s** | %s / %s | %s / %s / %s | %d of %d | %s |" % (
                "bid/ask" if price == "passive" else "mid", W, 100 * fr, P(wavg(c)), P(wavg("sav")), P(wavg("sav", t.buy)), P(wavg("sav", ~t.buy)),
                P(by["decision"]), P(by["entry"]), P(by["guard"]), int((qs > 0).sum()), len(qs), P(per_round)))
            if price == "passive":
                verdict[W] = wavg("sav") >= MIN_SAVING and int((qs > 0).sum()) >= MIN_QUARTERS
    ok = all(verdict.values())
    lines += ["", "- Passive limit: " + ", ".join(f"W={W} {'passes' if v else 'fails'}" for W, v in verdict.items())
              + f" -> **{'WORTH PROPOSING TO THE TEAM' if ok else 'KEEP MARKET ORDERS'}**.",
              "- Median half-spread of the coins traded: %s." % P(float(t.drop_duplicates('coin').h.median()))]
    (OUT / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
