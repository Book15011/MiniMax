"""A mid-frequency volume-spike strategy against e20v45 (research/baitoey/prereg/20261005-mft.md).

    python -m research.baitoey.mft
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
OUT = ROOT / "results" / "baitoey" / "20261005-mft"
TOOL = "3036a0d8bfdaa6a0"
TAKER, MAKER, SLOTS = 0.001, 0.0005, 5
RUNS = {"M4": (3.0, 4, "market"), "M1": (3.0, 1, "market"), "M4K5": (5.0, 4, "market"), "M4L": (3.0, 4, "limit")}
START, END, MARGIN = "2025-09-02 12:00", "2026-09-15 12:00", 0.03


def load(market):
    have = {p.stem for p in MINUTES.glob("*.parquet")}
    days = market.universe_by_day.loc["2025-08-20":]
    coins = sorted({c for ids in days for c in ids} & have)
    close, qv, mlow, mclose = {}, {}, {}, {}
    for c in coins:
        d = pd.read_parquet(MINUTES / f"{c}.parquet", columns=["timestamp", "low", "close", "quote_volume"]).set_index("timestamp")
        r = d.resample("15min").agg({"close": "last", "quote_volume": "sum"})
        r.index = r.index + pd.Timedelta(minutes=15)                    # labelled by the bar end: the decision time
        close[c], qv[c], mlow[c], mclose[c] = r.close, r.quote_volume, d.low, d.close
    close, qv = pd.DataFrame(close), pd.DataFrame(qv)
    member = pd.DataFrame(False, index=days.index, columns=coins)
    for t, ids in days.items():
        member.loc[t, [c for c in ids if c in coins]] = True
    member = member.reindex(close.index, method="ffill").fillna(False).astype(bool)
    return coins, close, qv, member, mlow, mclose


def run(coins, close, qv, member, mlow, mclose, half, K, H, entry):
    idx = close.index; P = close.to_numpy(); r15 = close.pct_change(fill_method=None).to_numpy()
    sig = (qv / qv.rolling(96).mean()).to_numpy() >= K
    sig &= (r15 > 0) & member.to_numpy()
    hold = H * 4
    cash, pos = 1.0, {}
    eq, fee_cum, trade_cum = np.empty(len(idx)), np.empty(len(idx)), np.empty(len(idx))
    fees, trades = 0.0, 0
    for i in range(len(idx)):
        for j in [j for j, (u, ex) in pos.items() if i >= ex and np.isfinite(P[i, j])]:
            u, _ = pos.pop(j)
            gross = u * P[i, j] * (1 - half[j])
            cash += gross * (1 - TAKER); fees += gross * TAKER + u * P[i, j] * half[j]; trades += 1
        value = cash + sum(u * P[i, j] for j, (u, _) in pos.items() if np.isfinite(P[i, j]))
        free = SLOTS - len(pos)
        if free > 0:
            cand = [j for j in np.nonzero(sig[i])[0] if j not in pos and np.isfinite(P[i, j])]
            for j in sorted(cand, key=lambda j: -r15[i, j])[:free]:
                size = min(value / SLOTS, cash)
                if size <= 1e-9:
                    break
                px, h = P[i, j], half[j]
                price, rate = px * (1 + h), TAKER
                if entry == "limit":
                    t, c = idx[i], coins[j]
                    lows = mlow[c].reindex([t, t + pd.Timedelta(minutes=1)]).to_numpy()
                    if np.nanmin(lows) < px * (1 - h) if np.isfinite(lows).any() else False:
                        price, rate = px * (1 - h), MAKER
                    else:
                        later = mclose[c].reindex([t + pd.Timedelta(minutes=1)]).to_numpy()[0]
                        price = (later if np.isfinite(later) else px) * (1 + h)
                units = size * (1 - rate) / price
                cash -= size; fees += size * rate + max(units * (price - px), 0.0); trades += 1
                pos[j] = (units, i + hold)
        eq[i] = cash + sum(u * P[i, j] for j, (u, _) in pos.items() if np.isfinite(P[i, j]))
        fee_cum[i], trade_cum[i] = fees, trades
    return pd.Series(eq, idx), pd.Series(fee_cum, idx), pd.Series(trade_cum, idx)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_config(); sc = cfg["scoring"]; market = load_market(cfg)
    coins, close, qv, member, mlow, mclose = load(market)
    half = np.array([float(market.half_spread.get(c, 5e-4)) for c in coins])
    starts = pd.date_range(START, END, freq="D", tz="UTC")
    pool = pool_starts(market, cfg); liq = float(sc["liquidation_cost"])
    ref = [json.load(open(f)) for f in glob.glob(str(ROOT / "results/*/*/pol_switch_vt_tl_e20v45-*/score.json"))]
    ref = [s for s in ref if s.get("tool_version") == TOOL][-1]
    pw = pd.DataFrame(ref["per_window"]); pw.index = pd.to_datetime(pw.pop("start"), utc=True)
    pw = pw[pw.scored.astype(bool)]
    starts = starts[starts.isin(pw.index)]
    pw = pw.reindex(starts)
    w = pw.w_final.to_numpy(); w = w / w.sum(); up = pw.btc_up.astype(bool).to_numpy()
    bars = pw[["bar_LENIENT", "bar_MIDDLE", "bar_STRICT"]].to_numpy()
    fr = {}
    for n in sc["field"]:
        rr = simulate(get(n), market, cfg, pool, use_cache=True); k = rr.windows.index.get_indexer(starts)
        fr[n] = rr.equity[k, -1] * (1 - liq * rr.gross[k, -1]) - 1
    cut = np.where(up, np.maximum(0, pd.DataFrame(fr).max(axis=1).to_numpy()), 0.006)

    def stats(R, fees=None, trades=None):
        hit = float(np.mean([(w * (R >= bars[:, b])).sum() for b in range(3)]))
        out = {"hit": hit, "cut": float((w * (R >= cut)).sum()), "mean": float((w * R).sum()), "median": float(np.median(R)),
               "worst": float(R.min()), "pos": float((w * (R > 0)).sum())}
        if fees is not None:
            out["fees"], out["trades"] = float(np.mean(fees)), float(np.mean(trades))
        return out

    res = {"e20v45": stats(pw.R_liq.to_numpy())}
    for key, (K, H, entry) in RUNS.items():
        eq, fc, tc = run(coins, close, qv, member, mlow, mclose, half, K, H, entry)
        a, b = eq.asof(starts), eq.asof(starts + pd.Timedelta(days=14))
        R = b.to_numpy() / a.to_numpy() - 1
        fees = (fc.asof(starts + pd.Timedelta(days=14)).to_numpy() - fc.asof(starts).to_numpy()) / a.to_numpy()
        trades = tc.asof(starts + pd.Timedelta(days=14)).to_numpy() - tc.asof(starts).to_numpy()
        res[key] = stats(R, fees, trades)
        res[key]["year"] = float(eq.iloc[-1] / eq.loc[:pd.Timestamp(START, tz="UTC")].iloc[-1] - 1)
    P = lambda v: f"{100 * v:+.2f}%"
    lines = ["# A mid-frequency volume-spike strategy against e20v45", "",
             f"Pre-registration: `research/baitoey/prereg/20261005-mft.md`. {len(starts)} rounds ({START} to {END} starts), {len(coins)} coins.", "",
             "| Strategy | Clears the bars | Top-20 proxy | Mean R | Median R | Worst R | Rounds > 0 | Trades per round | Fees + spread per round | Whole year |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    labels = {"e20v45": "e20v45 (live, same rounds)", "M4": "M4: 3x spike, hold 4 h, market", "M1": "M1: 3x spike, hold 1 h, market",
              "M4K5": "M4K5: 5x spike, hold 4 h, market", "M4L": "M4L: 3x spike, hold 4 h, limit-first entry"}
    for key, s in res.items():
        tr = "—" if "trades" not in s else f"{s['trades']:.0f}"
        fe = "—" if "fees" not in s else P(s["fees"])
        yr = "—" if "year" not in s else P(s["year"])
        lines.append(f"| {labels[key]} | {100 * s['hit']:.0f}% | {s['cut']:.3f} | {P(s['mean'])} | {P(s['median'])} | {P(s['worst'])} | "
                     f"{100 * s['pos']:.0f}% | {tr} | {fe} | {yr} |")
    e = res["e20v45"]
    ok = (res["M4"]["hit"] >= e["hit"] + MARGIN and res["M4"]["cut"] >= e["cut"] and res["M1"]["mean"] > 0 and res["M4K5"]["mean"] > 0)
    lines += ["", f"- M4 vs e20v45 on the same rounds; neighbours M1 and M4K5 -> **{'CANDIDATE' if ok else 'NO CANDIDATE'}**."]
    (OUT / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
