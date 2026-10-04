"""Shadow mode (src/orchestrator/shadow.py): the bots' layer switches, the wrapped model deciding exactly as
book_orch, one hour's records, and the daily summary's per-coin paper P&L by hand."""
from __future__ import annotations

import copy
import json

import pandas as pd

from src.config import load_config
from src.models.book.book_orch import MODEL
from src.orchestrator import shadow
from tests.test_book_orch import H, T0, market, view  # noqa: F401 - the synthetic market fixture

LAYERS = ("size", "stage", "forecast_longs", "forecast_shorts", "trailing_stop", "btc_hedge")


def test_bot_switches_are_pinned_whatever_the_config_defaults():
    cfg = load_config()
    other = copy.deepcopy(cfg)
    other["models"]["book_orch"]["stage"].update(enabled=True, gate="breadth")   # e.g. a hybrid as the default
    for c in (cfg, other):
        a, e5 = shadow.bot_params(c, "a"), shadow.bot_params(c, "e5")
        assert not any(a[k]["enabled"] for k in LAYERS)
        assert e5["stage"]["enabled"] and e5["stage"]["gate"] == "none"
        assert not any(e5[k]["enabled"] for k in LAYERS if k != "stage")
        h1 = shadow.bot_params(c, "h1")
        assert h1["stage"]["enabled"] and h1["stage"]["gate"] == "breadth" and h1["stage"]["gate_breadth_max"] == 0.60
        assert not any(h1[k]["enabled"] for k in LAYERS if k != "stage")
    assert MODEL.spec.band == 0.05


def test_the_wrapped_model_decides_exactly_as_book_orch_and_logs_the_hour(market):
    p = shadow.bot_params(load_config(), "e5")
    proxy = shadow.ExplainProxy(MODEL)
    prev = pd.Series(dtype=float)
    for k in range(8):                                                      # a window's first hour, then hourly
        v = view(market, T0 - 4 * H + k * H, p, prev)
        w = proxy.targets(v)
        assert w.equals(MODEL.targets(v)) and proxy.last[0] is v and proxy.last[1] is w
        prev = w
    held = sorted(w.index)
    pair = held[0].replace("USDT", "/USD")
    events = [("feed", {}), ("decision", {"universe": list(v.universe), "targets": {}}),
              ("rebalance", {"orders": [{"kind": "BUY", "pair": pair, "quantity": "1", "collateral": None,
                                         "est_value": 1234.5, "reason": "target"}],
                             "fills": [{"order": {"kind": "BUY", "pair": pair}, "status": "FILLED", "price": 1.0,
                                        "qty": 1234.5, "fee": 1.2345}]}),
              ("keep_alive", {"orders": [{"kind": "BUY", "pair": "PAXG/USD", "est_value": 10.0, "reason": "keep-alive"}],
                              "fills": []}),
              ("snapshot", {"equity": 100_000.0, "gross": 0.6, "usd_free": 40_000.0, "weights": {pair: 0.1}})]
    lines = shadow.hour_records("e5", v.t, proxy.last, events, "abc123")
    json.dumps(lines)                                                       # one JSON line each
    hour = lines[-1]
    assert hour["type"] == "hour" and hour["equity"] == 100_000.0 and hour["n_orders"] == 2 and hour["fees"] == 1.2345
    assert hour["targets"] == {k: float(x) for k, x in w.items()} and hour["commit"] == "abc123"
    coins = {x["coin"]: x for x in lines if x["type"] == "coin"}
    assert set(held) <= set(coins)
    assert coins[held[0]]["orders"][0]["usd"] == 1234.5 and coins[held[0]]["weight_after"] == 0.1
    assert coins[held[0]]["decision"] == "hold" and coins[held[0]]["size"] == float(w[held[0]])
    assert coins["PAXGUSDT"]["decision"] == "none" and coins["PAXGUSDT"]["orders"][0]["step"] == "keep_alive"


def test_day_summary_paper_pnl_by_hand():
    h0, h1 = pd.Timestamp("2026-10-04 05:00", tz="UTC"), pd.Timestamp("2026-10-04 06:00", tz="UTC")
    lines = [{"type": "hour", "bar": str(h0), "equity": 100_000.0, "weights": {"AAAUSDT": 0.5}, "commit": "c"},
             {"type": "coin", "bar": str(h0), "coin": "AAAUSDT", "close": 100.0, "weight_after": 0.5,
              "decision": "enter", "reason": "base decision", "orders": [{"kind": "BUY", "usd": 50_000.0}],
              "fills": [{"status": "FILLED", "fee": 50.0}]},
             {"type": "hour", "bar": str(h1), "equity": 100_950.0, "weights": {"AAAUSDT": 0.5}, "commit": "c"},
             {"type": "coin", "bar": str(h1), "coin": "AAAUSDT", "close": 102.0, "weight_after": 0.5,
              "decision": "hold", "reason": "between decisions", "orders": [], "fills": []}]
    pnl, fees = shadow.coin_pnl(lines, h0.floor("D"))
    assert fees == {"AAAUSDT": 50.0} and abs(pnl["AAAUSDT"] - (100_000 * 0.5 * 0.02 - 50.0)) < 1e-9
    md = shadow.day_summary("a", h0.floor("D"), lines)
    assert "| Hours logged | 2 of 24 |" in md and "+950.00" in md and "| AAAUSDT | 2 | enter 1 |" in md
    assert "key" not in md.lower().replace("no keys", "")                   # paper amounts only
