"""EXPERIMENTAL / report-only: the short guard's three regime conditions at every hour of the round (paper-live bars),
as the daily decision would read them: BTC vs its 20-day (480 h) EMA, BTC's 168 h return, and the share of the 30
most liquid coins up over 48 h (must be <= 40%). The guard can short only at a 16:00 UTC decision where all three
hold."""
from __future__ import annotations

import sys

import pandas as pd

from backtest.data import universe_at
from src.config import REPO_ROOT, load_config
from src.contracts import MarketView
from src.models.book import _cashshort

MAIN = REPO_ROOT.parents[1] if REPO_ROOT.parent.name == ".worktrees" else REPO_ROOT
sys.path.insert(0, str(MAIN / "results/book/paper-live"))
import paper_live as pl  # noqa: E402

pl.STORE = MAIN / "results/book/shadow/h1"
HK = "Asia/Hong_Kong"
FILL = int(sys.argv[1]) if len(sys.argv) > 1 else 0          # volume gap fill (hours), as in the _r variants


def main() -> None:
    cfg = load_config()
    p = cfg["models"]["book_e20guard_pullback"]
    mk = pl.load_market(cfg)
    close, qv = mk.close, mk.quote_volume
    btc = close.BTCUSDT
    ema = btc.ewm(span=480, adjust=False).mean()
    rows = []
    for t in close.loc[pl.T0 - pd.Timedelta(days=2):].index:
        uni = universe_at(mk, t)
        v = MarketView(t=t, close=close.loc[:t], quote_volume=qv.loc[:t].ffill(limit=FILL) if FILL else qv.loc[:t],
                       universe=uni, params=p)
        _, breadth = _cashshort.liquid_breadth(v, p)
        ok, _ = _cashshort.regime_ok(v, p)
        r168 = btc.loc[t] / btc.loc[:t - pd.Timedelta(hours=168)].iloc[-1] - 1
        rows.append({"t": t, "btc_vs_ema_%": 100 * (btc.loc[t] / ema.loc[t] - 1), "btc_7d_%": 100 * r168,
                     "breadth_up_%": None if breadth is None else 100 * breadth, "all_three": ok})
    d = pd.DataFrame(rows).set_index("t")
    print("hours with all three conditions:", int(d.all_three.sum()), "of", len(d))
    on = d[d.all_three]
    if len(on):
        print("first/last such hour (HKT):", on.index[0].tz_convert(HK), on.index[-1].tz_convert(HK))
    daily = d[d.index.hour == 16].copy()
    daily.index = daily.index.tz_convert(HK).strftime("%m-%d %H:%M")
    print("\nat the daily decisions (16:00 UTC = 00:00 HKT):")
    print(daily.round(2).to_string())
    last = d.iloc[-1]
    print("\nnow:", d.index[-1].tz_convert(HK), {k: (round(v, 2) if isinstance(v, float) else v) for k, v in last.items()})


if __name__ == "__main__":
    main()
