"""Market-type view (backtest/scoring/explain.py): window types from BTC, weighted profiles, measured reasons."""
import numpy as np
import pandas as pd

from backtest.scoring import explain


def btc_path(start, days, legs):
    """Hourly closes: piecewise-constant hourly growth per (hours, total return) leg."""
    px, out = 100.0, []
    for hours, total in legs:
        g = (1 + total) ** (1 / hours)
        for _ in range(hours):
            px *= g
            out.append(px)
    idx = pd.date_range(start, periods=len(out), freq="h", tz="UTC")
    return pd.Series([100.0] + out[:-1], index=idx)


def test_market_types_from_btc():
    s = btc_path("2025-01-01", 0, [(168, 0.06), (168, -0.08), (400, 0.0)])
    t0 = s.index[0]
    types = explain.market_types(pd.DatetimeIndex([t0]), s, pd.Series(["up/highvol"], index=[t0]))
    row = types.iloc[0]
    assert row["turning point"] and row["mild fall"] and row["volatile"] and not row["calm"]   # +6% then -8%


def test_profile_and_reason_name_the_weak_type_and_what_was_held():
    idx = pd.date_range("2025-01-01", periods=4, freq="D", tz="UTC")
    t = pd.DataFrame({"w_final": 0.25, "R_liq": [0.05, 0.06, -0.08, -0.07],
                      "hit_LENIENT": [1, 1, 0, 0], "hit_MIDDLE": [1, 1, 0, 0], "hit_STRICT": [1, 1, 0, 0],
                      "net_avg": [0.9, 0.9, 0.8, 0.8], "gross_avg": [0.9, 0.9, 0.8, 0.8]}, index=idx)
    types = pd.DataFrame({k: False for k in explain.TYPES}, index=idx)
    types.loc[idx[:2], "strong rise"] = True
    types.loc[idx[2:], "strong fall"] = True
    p = explain.profile(t, types)
    assert p["all"]["hit"] == 0.5 and p["strong rise"]["hit"] == 1.0 and p["strong fall"]["net"] == 0.8
    msg = explain.reason(p)
    assert "Strong in strong rise windows" in msg and "stays 80% net long while prices drop" in msg
    flat = explain.profile(t.assign(**{c: 1 for c in ("hit_LENIENT", "hit_MIDDLE", "hit_STRICT")}), types)
    assert explain.reason(flat) == "About the same in every market type."
