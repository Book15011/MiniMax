"""Tests for baitoey_two_sleeve (variants A-D), written before the model."""
import copy

import numpy as np
import pandas as pd

from src.config import load_config
from src.contracts import MarketView, check_targets
from src.models import get

P = load_config()["models"]["baitoey_two_sleeve"]
N = 1000
IDX = pd.date_range("2024-01-01 01:00", periods=N, freq="h", tz="UTC")


def market(n_coins: int = 30, seed: int = 0):
    """Coin i drifts from -0.0006 (i = 0) to +0.0006 per hour, with noise; volume falls with i (coin 0 most liquid)."""
    rng = np.random.default_rng(seed)
    k = np.arange(N)
    close, qv = {}, {}
    for i in range(n_coins):
        drift = -0.0006 + 0.0012 * i / (n_coins - 1)
        close[f"C{i:02d}USDT"] = 100 * np.exp(drift * k + 0.004 * rng.standard_normal(N).cumsum() / 4)
        qv[f"C{i:02d}USDT"] = np.full(N, 1e6 * (n_coins - i))
    return pd.DataFrame(close, index=IDX), pd.DataFrame(qv, index=IDX)


def view(close, qv, params=P, end=None):
    c, q = close.iloc[:end], qv.iloc[:end]
    return MarketView(t=c.index[-1], close=c, quote_volume=q, universe=tuple(c.columns), params=params,
                      prev_targets=pd.Series(dtype=float))


def variant(name: str) -> dict:
    p = copy.deepcopy(P)
    for k, v in P["variants"][name].items():
        p[k] = {**p[k], **v} if isinstance(v, dict) else v
    return p


def test_registered_with_its_config_block_and_a_2pct_band():
    m = get("baitoey_two_sleeve")
    assert m.spec.band == 0.02 and m.spec.rebalance_hours == 24 and not m.spec.uses_shorts
    assert P["trend"]["lookback_days"] == [7, 14, 30] and P["max_gross"] == 0.95 and P["cap"] == 0.25


def test_universe_needs_800_hours_and_ranks_by_7_day_volume():
    from src.models.baitoey.baitoey_two_sleeve import liquid
    close, qv = market()
    close["NEWUSDT"] = close["C29USDT"]; close.loc[close.index[:500], "NEWUSDT"] = np.nan   # only 500 h of history
    qv["NEWUSDT"] = 1e9                                                                    # the most liquid coin
    top = liquid(view(close, qv), P, 15)
    assert "NEWUSDT" not in top and top == [f"C{i:02d}USDT" for i in range(15)]


def test_trend_sleeve_holds_only_positive_scores_and_meets_its_volatility_target():
    from src.models.baitoey.baitoey_two_sleeve import annual_vol, trend_scores, trend_sleeve
    close, qv = market()
    v = view(close, qv)
    s = trend_scores(v, P, list(close.columns))
    assert s.abs().max() <= P["trend"]["clip"] + 1e-12
    w = trend_sleeve(v, P)
    assert (w > 0).all() and set(w.index) <= set(s[s > 0].index)
    assert abs(annual_vol(w, close, P["trend"]["vol_days"]) - P["trend"]["target_vol_annual"]) < 1e-6


def test_momentum_sleeve_longs_the_top_5_by_relative_return_with_inverse_vol_weights():
    from src.models.baitoey.baitoey_two_sleeve import momentum_sleeve
    close, qv = market()
    w = momentum_sleeve(view(close, qv), P)
    top = list(close.columns[:25])
    r = close[top].iloc[-1] / close[top].iloc[-1 - 14 * 24] - 1
    expect = list((r - r.mean()).sort_values(ascending=False).index[:5])
    assert sorted(w.index) == sorted(expect) and (w > 0).all()
    assert abs(w.sum() - P["momentum"]["long_gross"]) < 1e-9
    vol = np.log(close[expect]).diff().iloc[-P["momentum"]["vol_days"] * 24:].std()
    ratio = (w[expect] * vol[expect]).to_numpy()
    assert np.allclose(ratio, ratio[0])                                # weight x vol equal for each: inverse vol


def test_variant_b_shorts_the_bottom_5_and_a_is_trend_only():
    from src.models.baitoey._two_sleeve_variants import TwoSleeveLS
    from src.models.baitoey.baitoey_two_sleeve import combine, trend_sleeve
    close, qv = market()
    wb = TwoSleeveLS().targets(view(close, qv, variant("B")))
    assert (wb < 0).sum() >= 1 and abs(wb[wb < 0].sum()) <= variant("B")["momentum"]["short_gross"] + 1e-9
    va = view(close, qv, variant("A"))
    wa = get("baitoey_two_sleeve").targets(va)
    assert np.allclose(wa.sort_index(), combine(trend_sleeve(va, variant("A")), pd.Series(dtype=float), P).sort_index())


def test_caps_per_coin_and_gross():
    from src.models.baitoey.baitoey_two_sleeve import combine
    w = combine(pd.Series({"AUSDT": 0.6, "BUSDT": 0.3, "CUSDT": 0.3}), pd.Series({"AUSDT": 0.2, "DUSDT": 0.3}), P)
    assert w.abs().max() <= P["cap"] + 1e-12 and w.abs().sum() <= P["max_gross"] + 1e-12
    close, qv = market()
    v = view(close, qv)
    m = get("baitoey_two_sleeve")
    check_targets(m.targets(v), v, m.spec)


def test_no_look_ahead():
    close, qv = market()
    m = get("baitoey_two_sleeve")
    a = m.targets(view(close, qv, end=900))
    future = close.copy()
    future.iloc[900:] *= 3.0                                           # change only the future
    b = m.targets(view(future, qv, end=900))
    assert np.allclose(a.sort_index(), b.sort_index())


def test_variant_d_is_the_mean_of_three_tranches_rebalanced_at_00_08_16():
    from src.models.baitoey._two_sleeve_variants import TwoSleeveStaggered
    close, qv = market()
    t16 = [i for i, t in enumerate(IDX) if t.hour == 16][-1]
    p = variant("D")
    d = TwoSleeveStaggered().targets(view(close, qv, p, end=t16 + 1))
    c = get("baitoey_two_sleeve")
    parts = [c.targets(view(close, qv, p, end=t16 + 1 - 8 * k)) for k in range(3)]   # 16:00, 08:00, 00:00
    mean = pd.concat(parts, axis=1).fillna(0).mean(axis=1)
    mean = mean[mean != 0]
    assert TwoSleeveStaggered.spec.rebalance_hours == 8
    assert np.allclose(d.sort_index(), mean.sort_index())
