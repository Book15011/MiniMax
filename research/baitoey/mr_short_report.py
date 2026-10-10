"""Exploratory (2026-10-10): mean reversion plus a short-capable sleeve, as 50/50 blends of cached model paths
(hourly return mix, rebalancing costs ignored), and Pol's switch3 models. Same steady definition as steady.py."""
import numpy as np, pandas as pd
from backtest.data import load_market
from backtest.scoring.evaluate import simulate
from backtest.scoring.windows import pool_starts
from src.config import load_config
from src.models import get
cfg = load_config(); m = load_market(cfg); s = pool_starts(m, cfg); liq = float(cfg["scoring"]["liquidation_cost"])
runs = {n: simulate(get(n), m, cfg, s, use_cache=True) for n in
        ["pol_switch_vt_tl_e20v45", "baitoey_mr_4h", "pol_mr_cap", "pol_trend_ls", "baitoey_btc_short_c", "baitoey_mjt_24_96_d", "pol_switch3", "pol_switch3_cap"]}
def path(n): return runs[n].equity.astype(float), runs[n].gross.astype(float)
def blend(a, b, wa=0.5):
    Ea, Ga = path(a); Eb, Gb = path(b)
    ra = Ea[:, 1:] / Ea[:, :-1] - 1; rb = Eb[:, 1:] / Eb[:, :-1] - 1
    E = np.concatenate([np.ones((len(Ea), 1)), np.cumprod(1 + wa * ra + (1 - wa) * rb, axis=1)], axis=1)
    return E, wa * Ga + (1 - wa) * Gb
P = lambda v: f"{100*v:+.1f}%"
base_E, base_G = path("pol_switch_vt_tl_e20v45"); st = runs["pol_switch_vt_tl_e20v45"].windows.index
D6, H, L0 = 144, 336, -0.066
later = st + pd.Timedelta(hours=D6); ok = later.isin(st); j = st.get_indexer(later)
r6 = base_E[:, D6] / base_E[:, 0] - 1; btc = m.close.BTCUSDT; b6 = btc.reindex(later).to_numpy() / btc.reindex(st).to_numpy() - 1
B = ok & (np.abs(r6 - L0) <= 0.03) & (b6 >= -0.06) & (b6 <= 0)
def stats(E, G):
    R = E[:, -1] * (1 - liq * G[:, -1]) / E[:, 0] - 1
    mdd = 1 - (E / np.maximum.accumulate(E, axis=1)).min(axis=1)
    d = E[:, ::24]; up = ((d[:, 1:] / d[:, :-1] - 1) > 0).sum(axis=1)
    steady = (R > 0) & (mdd <= 0.03) & (up >= 8)
    jj = j[B]; rest = (1 - base_G[B, D6] * 0.0015) * (E[jj, H - D6] * (1 - liq * G[jj, H - D6]) / E[jj, 0]) - 1
    tot = (1 + L0) * (1 + rest) - 1
    return (f"steady + {100*steady.mean():3.0f}% | bounce + {100*((R>0)&~steady).mean():3.0f}% | negative {100*(R<=0).mean():3.0f}% | median {P(np.median(R))}, "
            f"p10 {P(np.percentile(R,10))}, p90 {P(np.percentile(R,90))}, typical MDD {100*np.median(mdd):.1f}% || from our -6.6% (day 6, {B.sum()} rounds): "
            f"finish >= 0% {100*(tot>=0).mean():.0f}%, >= +1% {100*(tot>=0.01).mean():.0f}%, median {P(np.median(tot))}, <= -10% {100*(tot<=-0.10).mean():.0f}%")
print("All 2,298 rounds (14 days)")
for lab, (E, G) in [("e20 (live)", path("pol_switch_vt_tl_e20v45")), ("mean reversion 4h alone", path("baitoey_mr_4h")), ("mean reversion + volume alone", path("pol_mr_cap")),
                    ("Pol switch3: calm MR / up momentum / down long-short", path("pol_switch3")), ("Pol switch3_cap (MR on capitulation volume)", path("pol_switch3_cap")),
                    ("50% MR 4h + 50% long-short trend", blend("baitoey_mr_4h", "pol_trend_ls")), ("50% MR + volume + 50% long-short trend", blend("pol_mr_cap", "pol_trend_ls")),
                    ("50% MR 4h + 50% BTC failed-rally short", blend("baitoey_mr_4h", "baitoey_btc_short_c")),
                    ("50% MR 4h + 50% large-coin trend (24/96)", blend("baitoey_mr_4h", "baitoey_mjt_24_96_d"))]:
    print(f"  {lab:52s} {stats(E, G)}")
