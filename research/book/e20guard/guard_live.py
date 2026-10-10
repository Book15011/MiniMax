"""EXPERIMENTAL / report-only: the e20v45 short-guard variants on the round's live window (feature/e20-shortguard).

The paper-live engine, imported unchanged (same bars, fees, 1 h fill lag, from cash at Oct 4 12:00 UTC). Per model:
round return, max drawdown, the book now, every decision with a short leg, and "Oct 7 again" (the latest book marked
with each coin's actual move, Oct 7 01:00 -> Oct 8 06:00 UTC).

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m src.experimental.e20guard_live   (or as a script)
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from backtest.engine import decide, decision_times
from src.config import REPO_ROOT, load_config
from src.models import get

MAIN = REPO_ROOT.parents[1] if REPO_ROOT.parent.name == ".worktrees" else REPO_ROOT
sys.path.insert(0, str(MAIN / "results/book/paper-live"))
import paper_live as pl  # noqa: E402

pl.STORE = MAIN / "results/book/shadow/h1"
NAMES = ["pol_switch_vt_tl_e20v45", "book_e20guard_pullback", "book_e20guard_confirm", "book_e20guard_pullback40",
         "book_e20guard_confirm40", "book_e20guard_pullback_r", "book_e20guard_confirm_r"]
S0, S1 = pd.Timestamp("2026-10-07 01:00", tz="UTC"), pd.Timestamp("2026-10-08 06:00", tz="UTC")
HK = "Asia/Hong_Kong"


def path(name, mk, cfg):
    model = get(name)
    params = (cfg.get("models") or {}).get(name, {}) or {}
    h = cfg["harness"]
    grid = decision_times(mk.close.index, model.spec.rebalance_hours, h["grid_hour_utc"], pl.T0, mk.close.index[-1])
    times = [pl.T0] + [t for t in grid if t > pl.T0]
    prev, out = pd.Series(dtype=float), []
    for t in times:
        w = decide(model, mk, t, params, prev)
        out.append((t, w))
        prev = w
    return out


def main() -> None:
    cfg = load_config()
    mk = pl.load_market(cfg)
    close = mk.close
    shock = close.loc[:S1].iloc[-1] / close.loc[:S0].iloc[-1] - 1
    print("window", pl.T0, "->", close.index[-1], "| BTC", f"{100 * (close.BTCUSDT.iloc[-1] / close.BTCUSDT.loc[:pl.T0].iloc[-1] - 1):+.2f}%")
    rows = []
    for n in NAMES:
        r = pl.run_model(n, mk, cfg)
        E = np.asarray(r["E"])
        tgt = pd.Series({c: float(x) for c, x in r["target"].items() if abs(float(x)) > 1e-9}, dtype=float)
        shorts_on = [(t.tz_convert(HK).strftime("%m-%d %H:%M"), {c.replace("USDT", ""): round(100 * v, 1) for c, v in w[w < 0].items()})
                     for t, w in path(n, mk, cfg) if (w < 0).any()]
        rows.append({"model": n, "round_%": round(100 * (E[-1] - 1), 2),
                     "maxdd_%": round(100 * float((E / np.maximum.accumulate(E) - 1).min()), 2),
                     "net_now_%": round(100 * tgt.sum(), 0), "gross_now_%": round(100 * tgt.abs().sum(), 0),
                     "oct7_again_%": round(100 * float((tgt * shock.reindex(tgt.index).fillna(0)).sum()), 2),
                     "decisions_with_shorts": len(shorts_on), "short_legs": shorts_on})
    d = pd.DataFrame(rows)
    pd.set_option("display.width", 300)
    pd.set_option("display.max_colwidth", 200)
    print(d.to_string(index=False))


if __name__ == "__main__":
    main()
