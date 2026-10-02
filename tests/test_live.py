"""Live runner: bars from each source, Book's universe rule, the guard and keep-alive, restarts. No network."""
from __future__ import annotations

import copy
import io
import json
import logging
import zipfile

import numpy as np
import pandas as pd
import pytest

from src.config import load_config
from src.execution.planner import Holdings, Quote
from src.live import feed
from src.live.runner import Runner, day_start, keep_alive_targets, live_universe
from src.live.broker import PaperAccount, ShortsUnreadable, parse_short, quotes_from_ticker
from src.validation.features import StateEngine
from tests.synth import make_market

CFG = load_config()
LOG = logging.getLogger("test_live")
T0 = pd.Timestamp("2024-03-01 00:00", tz="UTC")


def kl(open_ms: int, close: float, qv: float) -> list:
    return [open_ms, "1", "1", "1", str(close), "1", open_ms + 3_599_999, str(qv), 1, "0", "0", "0"]


# ---------------- feed ----------------

def test_klines_are_indexed_by_close_time_in_ms_and_us():
    ms = int(T0.timestamp() * 1000)
    f = feed.klines_frame([kl(ms, 100.0, 5.0), kl(ms * 1000 + 3_600_000_000, 101.0, 6.0)])   # second row in µs
    assert list(f.index) == [T0 + pd.Timedelta(hours=1), T0 + pd.Timedelta(hours=2)]
    assert f.close.tolist() == [100.0, 101.0] and f.qv.tolist() == [5.0, 6.0]


def small_store(hours: int = 48) -> feed.Store:
    idx = pd.date_range(T0 - pd.Timedelta(hours=hours - 1), T0, freq="h")
    c = pd.DataFrame({"BTCUSDT": 100.0, "XUSDT": 1.0}, index=idx)
    return feed.Store(c, c * 0 + 10.0, T0)


def test_rest_tops_up_every_series_and_completes():
    st = small_store()
    upto = T0 + pd.Timedelta(hours=3)

    def rest(sym, start, end):
        idx = pd.date_range(start + pd.Timedelta(hours=1), end, freq="h")
        return pd.DataFrame({"close": 200.0, "qv": 1.0}, index=idx)
    added = feed.top_up(st, upto, rest, None, None, LOG)
    assert added["rest"] == 6 and st.complete_through == upto and st.close.loc[upto].tolist() == [200.0, 200.0]


def test_blocked_rest_falls_back_to_archive_then_ticker_and_archive_later_replaces_the_ticker():
    st = small_store()

    def rest(*a):
        raise feed.SourceDown("blocked")
    published = {T0}                                        # only 2024-03-01 is in the archive

    def archive(sym, day):
        if day not in published:
            return None
        idx = pd.date_range(day + pd.Timedelta(hours=1), day + pd.Timedelta(days=1), freq="h")
        return pd.DataFrame({"close": 150.0, "qv": 2.0}, index=idx)
    upto = T0 + pd.Timedelta(hours=30)                      # 2024-03-02 06:00
    added = feed.top_up(st, upto, rest, archive, lambda: {"BTCUSDT": 175.0}, LOG)
    assert st.complete_through == T0 + pd.Timedelta(days=1)
    assert added["archive"] == 48 and added["ticker"] == 1 and upto in st.ticker_only
    assert st.close.loc[upto, "BTCUSDT"] == 175.0 and np.isnan(st.close.loc[upto, "XUSDT"])
    assert st.close.loc[T0 + pd.Timedelta(hours=27):upto - pd.Timedelta(hours=1)].isna().all().all()  # unseen hours stay NaN
    published.add(T0 + pd.Timedelta(days=1))
    feed.top_up(st, T0 + pd.Timedelta(days=2), rest, archive, None, LOG)
    assert st.close.loc[upto, "BTCUSDT"] == 150.0 and not st.ticker_only


def test_ticker_volume_makes_the_24h_sum_match_the_tickers_figure():
    st = small_store()                                      # 10.0 per hour through T0
    h1, h2 = T0 + pd.Timedelta(hours=1), T0 + pd.Timedelta(hours=2)
    added = feed.top_up(st, h1, None, None, lambda: {"BTCUSDT": 101.0}, LOG, lambda: {"BTCUSDT": 300.0, "XUSDT": 0.0})
    assert added["ticker_qv"] == 1 and st.qv.loc[h1, "BTCUSDT"] == pytest.approx(300.0 - 23 * 10.0)
    assert np.isnan(st.qv.loc[h1, "XUSDT"])                 # no figure: stays unknown
    feed.top_up(st, h2, None, None, lambda: {"BTCUSDT": 102.0}, LOG, lambda: {"BTCUSDT": 310.0})
    assert st.qv["BTCUSDT"].iloc[-24:].sum() == pytest.approx(310.0)
    st.qv.loc[T0, "BTCUSDT"] = np.nan                       # a hole in the 23 bars before: flat estimate
    h3 = T0 + pd.Timedelta(hours=3)
    feed.top_up(st, h3, None, None, lambda: {"BTCUSDT": 103.0}, LOG, lambda: {"BTCUSDT": 240.0})
    assert st.qv.loc[h3, "BTCUSDT"] == pytest.approx(10.0)
    st.qv.loc[T0, "BTCUSDT"] = 10.0
    feed.top_up(st, T0 + pd.Timedelta(hours=4), None, None, lambda: {"BTCUSDT": 1.0}, LOG, lambda: {"BTCUSDT": 1.0})
    assert st.qv.loc[T0 + pd.Timedelta(hours=4), "BTCUSDT"] == 0.0     # never negative


def test_archive_day_is_published_when_btc_is_and_a_missing_coin_is_no_data():
    st = small_store()

    def archive(sym, day):
        if sym == "XUSDT":
            return None                                     # delisted: never published
        idx = pd.date_range(day + pd.Timedelta(hours=1), day + pd.Timedelta(days=1), freq="h")
        return pd.DataFrame({"close": 150.0, "qv": 2.0}, index=idx)
    feed.top_up(st, T0 + pd.Timedelta(days=1), None, archive, None, LOG)
    assert st.complete_through == T0 + pd.Timedelta(days=1) and st.close.loc[T0 + pd.Timedelta(days=1), "BTCUSDT"] == 150.0


def test_seed_drops_series_without_data(tmp_path):
    idx = pd.date_range("2026-01-01", periods=24 * 10, freq="h", tz="UTC")
    c = pd.DataFrame({"BTCUSDT": 1.0, "DEADUSDT": np.nan, "OLDUSDT~until-2022-11-15": 1.0}, index=idx)
    c.to_parquet(tmp_path / "panel_close_1h.parquet")
    c.to_parquet(tmp_path / "panel_quote_volume_1h.parquet")
    assert list(feed.seed(tmp_path, 5).close.columns) == ["BTCUSDT"]


def test_store_round_trip(tmp_path):
    st = small_store()
    st.ticker_only.add(T0)
    st.save(tmp_path)
    back = feed.Store.load(tmp_path)
    pd.testing.assert_frame_equal(back.close, st.close, check_freq=False)
    assert back.complete_through == T0 and back.ticker_only == {T0}


# ---------------- universe: Book's rule, exactly ----------------

def test_live_universe_equals_the_validation_rule():
    md = make_market()
    eng = StateEngine(md, CFG["validation"])
    allowed = set(md.close.columns)
    grid = eng.close_d.index
    for t in grid[200::97]:
        assert live_universe(md.close, md.quote_volume, t, CFG["validation"], allowed) == tuple(sorted(eng.universe(t)))


# ---------------- helpers ----------------

def test_day_start_and_keep_alive_targets():
    assert day_start(pd.Timestamp("2026-10-03 16:00", tz="UTC"), 16) == pd.Timestamp("2026-10-03 16:00", tz="UTC")
    assert day_start(pd.Timestamp("2026-10-04 13:00", tz="UTC"), 16) == pd.Timestamp("2026-10-03 16:00", tz="UTC")
    q = {"BTC/USD": Quote(100.0, 100.0), "ETH/USD": Quote(10.0, 10.0)}
    assert keep_alive_targets(Holdings(1000.0), q, 1000.0, 0.002, 0.99) == {"BTC/USD": 0.002}
    full = Holdings(10.0, {"ETH/USD": 99.0})                # 99% ETH: no room, trims ETH
    t = keep_alive_targets(full, q, 1000.0, 0.002, 0.99)
    assert t["ETH/USD"] == pytest.approx(0.99 - 0.002)


def test_short_positions_are_read_or_refused():
    doc = {"ID": 412, "Pair": "BTC/USD", "EntryPrice": 50000, "ShortQty": 0.2, "Collateral": 10000, "CurrentPrice": 48000,
           "UnrealizedPNL": 400, "UnrealizedPNLPct": 0.04, "PositionValue": 10400, "CreateTimestamp": 1757980800000,
           "PositionStatus": "OPEN"}                                    # the API docs' own example
    pair, pos = parse_short(doc)
    assert pair == "BTC/USD" and pos.qty == 0.2 and pos.collateral == 10000.0 and pos.entry == 50000.0
    assert parse_short({**doc, "PositionStatus": "PENDING"}) is None   # a pending LIMIT short holds nothing yet
    with pytest.raises(ShortsUnreadable):
        parse_short({"Pair": "BTC/USD", "Collateral": 1})


def test_order_status_follows_each_endpoints_documented_reply():
    from src.execution.planner import BUY, SHORT_CLOSE, SHORT_OPEN
    from src.live.broker import order_status
    assert order_status(BUY, {"Status": "FILLED"}) == "FILLED"
    assert order_status(BUY, {"OrderDetail": {"Status": "PENDING"}}) == "PENDING"
    assert order_status(SHORT_OPEN, {"Status": "OPEN", "ShortQty": 0.2}) == "FILLED"
    assert order_status(SHORT_OPEN, {"Status": "PENDING"}) == "PENDING"
    assert order_status(SHORT_CLOSE, {"ClosedQty": 0.1, "FullyClosed": False}) == "FILLED"
    assert order_status(SHORT_CLOSE, {}) == "UNCONFIRMED"


# ---------------- the runner, end to end on a fake exchange ----------------

class FakeClient:
    def __init__(self, prices: dict):
        self.prices = prices

    def ticker(self, pair=None):
        return {p: {"MaxBid": x, "MinAsk": x * 1.0002, "LastPrice": x} for p, x in self.prices.items()}

    def exchange_info(self):
        return {"TradePairs": {p: {"PricePrecision": 2, "AmountPrecision": 5, "MiniOrder": 1, "CanTrade": True}
                               for p in self.prices}}

    offset_ms = 0.0

    def sync_clock(self):
        return self.offset_ms


def make_runner(tmp_path, model: str, store: feed.Store, mode="paper", start_at=None, account=None) -> Runner:
    store.save(tmp_path)
    cfg = copy.deepcopy(CFG)
    cfg["live"].update(state_dir=str(tmp_path), start_at=start_at)
    client = FakeClient({"BTC/USD": 100.0, "ETH/USD": 10.0})
    st = tmp_path / "state.json"
    h = Holdings(100_000.0)
    if st.exists():
        from src.live.runner import holdings_from_json
        paper = json.loads(st.read_text())["paper"]                     # None in a live state
        h = holdings_from_json(paper) if paper else h
    broker = PaperAccount(h, {}, lambda: quotes_from_ticker(client.ticker()))
    r = Runner(cfg, model, mode, broker, client, tmp_path, LOG, account=account)
    broker.rules = r.rules
    return r


def flat_store(start: pd.Timestamp, days: int) -> feed.Store:
    idx = pd.date_range(start - pd.Timedelta(days=days), start, freq="h")
    c = pd.DataFrame({"BTCUSDT": 100.0, "ETHUSDT": 10.0}, index=idx)
    return feed.Store(c, c * 0 + 1e6, start)


def test_cash_model_stays_active_through_guard_and_keep_alive(tmp_path):
    start = pd.Timestamp("2026-10-03 16:00", tz="UTC")
    r = make_runner(tmp_path, "team_cash", flat_store(start, 120))
    for k in range(48):
        r.process(start + pd.Timedelta(hours=k))
    days = r.state["active_days"]
    assert days == [str(start), str(start + pd.Timedelta(days=1))]   # both HKT days active
    logs = [json.loads(x) for f in (tmp_path / "logs").glob("*.jsonl") for x in f.read_text().splitlines()]
    kinds = [e["event"] for e in logs]
    assert kinds.count("keep_alive") >= 1 and "decision" in kinds
    assert all("API" not in json.dumps(e) for e in logs)                # nothing key-like is logged
    ka = [e for e in logs if e["event"] == "keep_alive"][0]
    assert ka["bar"].startswith("2026-10-04 04:00")                     # hour 12 of the HKT day (12:00 HKT), as the engine


def test_a_gap_in_the_bars_does_not_empty_the_model(tmp_path):
    start = pd.Timestamp("2026-10-03 16:00", tz="UTC")
    st = flat_store(start, 120)
    rng = np.random.default_rng(3)
    st.close = st.close * np.exp(np.cumsum(rng.normal(0, 0.003, st.close.shape), axis=0))
    st.close.iloc[-30:-1] = np.nan                                      # 29 hours no source filled
    r = make_runner(tmp_path, "team_rot_ew", st)
    r.process(start)
    assert r.state["standing"], "the rotation must still pick coins over a gap shorter than max_fill_hours"


def test_btc_hold_buys_once_and_restart_resumes(tmp_path):
    start = pd.Timestamp("2026-10-03 16:00", tz="UTC")
    r = make_runner(tmp_path, "team_btc_hold", flat_store(start, 120))
    r.process(start)
    assert r.broker.h.spot.get("BTC/USD", 0) > 0 and r.state["active_days"] == [str(start)]
    btc = r.broker.h.spot["BTC/USD"]
    r2 = make_runner(tmp_path, "team_btc_hold", feed.Store.load(tmp_path))
    assert r2.state["last_bar"] == str(start) and r2.broker.h.spot["BTC/USD"] == btc
    assert not r2.due_decision(start + pd.Timedelta(hours=1))
    with pytest.raises(SystemExit, match="state.json is for paper"):
        make_runner(tmp_path, "team_btc_hold", feed.Store.load(tmp_path), mode="live")
    r3 = make_runner(tmp_path, "team_cash", feed.Store.load(tmp_path))      # the committed exit to cash
    assert r3.switched_from == "team_btc_hold" and r3.state["active_days"] == [str(start)]
    r3.process(start + pd.Timedelta(hours=1))
    assert not r3.broker.h.spot.get("BTC/USD") and r3.state["last_decision"] == str(start + pd.Timedelta(hours=1))


def test_nothing_trades_before_start_at(tmp_path):
    start = pd.Timestamp("2026-10-03 16:00", tz="UTC")
    r = make_runner(tmp_path, "team_btc_hold", flat_store(start, 120), mode="live", start_at="2026-10-03 17:00")
    r.process(start)
    assert not r.broker.h.spot and r.state["last_decision"] is None
    r.process(start + pd.Timedelta(hours=1))
    assert r.broker.h.spot.get("BTC/USD", 0) > 0


def test_competition_key_is_refused_off_ec2(monkeypatch, tmp_path):
    from argparse import Namespace

    from src.api.client import Credentials
    from src.live import runner as rmod
    monkeypatch.setattr(rmod, "load_credentials", lambda *a, **k: Credentials("k", "s", "competition"))
    monkeypatch.delenv("MM_HOST", raising=False)
    with pytest.raises(SystemExit, match="refused"):
        rmod.build(CFG, Namespace(mode="live", model=None, long_only=False), LOG)


def test_competition_key_needs_start_at(monkeypatch, tmp_path):
    from argparse import Namespace

    from src.api.client import Credentials
    from src.live import runner as rmod
    monkeypatch.setattr(rmod, "load_credentials", lambda *a, **k: Credentials("k", "s", "competition"))
    monkeypatch.setenv("MM_HOST", "ec2")
    cfg = copy.deepcopy(CFG)
    cfg["live"].update(state_dir=str(tmp_path), start_at=None)
    with pytest.raises(SystemExit, match="needs live.start_at"):
        rmod.build(cfg, Namespace(mode="live", model=None, long_only=False), LOG)


def test_a_test_runs_state_never_carries_into_the_round(tmp_path):
    start = pd.Timestamp("2026-10-03 16:00", tz="UTC")
    r = make_runner(tmp_path, "team_btc_hold", flat_store(start, 120), mode="live", account="test")
    r.process(start)                                                    # a test run that started trading at once
    assert r.state["account"] == "test" and r.state["round_start"] == str(start)
    with pytest.raises(SystemExit, match="for the test account"):
        make_runner(tmp_path, "team_btc_hold", feed.Store.load(tmp_path), mode="live", account="competition",
                    start_at="2026-10-04 12:00")
    st = json.loads((tmp_path / "state.json").read_text())
    del st["account"]                                                   # a state saved before the account stamp
    (tmp_path / "state.json").write_text(json.dumps(st))
    with pytest.raises(SystemExit, match="before live.start_at"):
        make_runner(tmp_path, "team_btc_hold", feed.Store.load(tmp_path), mode="live", account="competition",
                    start_at="2026-10-04 12:00")
    r2 = make_runner(tmp_path, "team_btc_hold", feed.Store.load(tmp_path), mode="live", account="test")
    assert r2.state["account"] == "test"                                # the test run itself resumes


def test_a_restart_inside_the_round_resumes(tmp_path):
    start = pd.Timestamp("2026-10-04 12:00", tz="UTC")
    r = make_runner(tmp_path, "team_btc_hold", flat_store(start, 120), mode="live", account="competition",
                    start_at="2026-10-04 12:00")
    r.process(start)
    r2 = make_runner(tmp_path, "team_btc_hold", feed.Store.load(tmp_path), mode="live", account="competition",
                     start_at="2026-10-04 12:00")
    assert r2.state["round_start"] == str(start) and r2.state["active_days"] == r.state["active_days"] != []


def test_late_funding_at_the_rounds_first_hour(tmp_path):
    """The competition wallet still empty at the round's first hour: no baseline from $0 (the lock-in would divide by
    it), and the next hour's guard buys the decided targets once the money is there."""
    start = pd.Timestamp("2026-10-04 12:00", tz="UTC")
    r = make_runner(tmp_path, "team_btc_hold", flat_store(start, 120), mode="live", account="competition",
                    start_at="2026-10-04 12:00")
    r.lv["endgame"] = {"enabled": True, "from_day": 10, "lock_return": 0.03}
    r.broker.h.usd_free = 0.0
    r.process(start)
    assert r.state.get("round_start") is None and not r.broker.h.spot and r.state["last_decision"] == str(start)
    r.broker.h.usd_free = 100_000.0                                     # the organizers fund the account
    r.process(start + pd.Timedelta(hours=1))
    assert r.state["round_start"] == str(start + pd.Timedelta(hours=1)) and r.state["round_start_equity"] > 0
    assert r.broker.h.spot.get("BTC/USD", 0) > 0                        # the guard caught up the same evening
    r.process(start + pd.Timedelta(days=11))                           # past day 10: the lock check runs, no error
    assert not r.state.get("locked_at")                                 # flat prices: +0%, below the +3% lock


def test_nothing_trades_after_end_at(tmp_path):
    start = pd.Timestamp("2026-10-04 12:00", tz="UTC")
    r = make_runner(tmp_path, "team_btc_hold", flat_store(start, 120), mode="live", account="competition",
                    start_at="2026-10-04 12:00")
    r.lv["end_at"] = "2026-10-04 13:00"
    r.end_at = pd.Timestamp("2026-10-04 13:00", tz="UTC")
    r.process(start)
    btc = r.broker.h.spot.get("BTC/USD", 0)
    assert btc > 0
    r.broker.h.spot.clear()                                             # the exchange liquidates at the end
    r.broker.h.usd_free = 100_000.0
    r.process(start + pd.Timedelta(hours=1))
    r.process(start + pd.Timedelta(hours=16))                           # past a decision hour and a guard hour
    assert not r.broker.h.spot                                          # nothing bought back
    logs = [json.loads(x) for f in (tmp_path / "logs").glob("*.jsonl") for x in f.read_text().splitlines()]
    assert [e for e in logs if e["event"] == "snapshot"][-1].get("round_over")


class StubbornPaper(PaperAccount):
    """Answers every order as filled but moves nothing for the first `misses` batches (a fill that never happened)."""

    def __init__(self, *a, misses: int = 2, **k):
        super().__init__(*a, **k)
        self.misses = misses

    def execute(self, orders, quotes, h):
        if self.misses > 0:
            self.misses -= 1
            return [{"order": o, "status": "FILLED"} for o in orders]
        return super().execute(orders, quotes, h)


def test_guard_fires_at_04_utc_confirms_the_fill_and_retries_the_same_day(tmp_path):
    start = pd.Timestamp("2026-10-03 16:00", tz="UTC")
    r = make_runner(tmp_path, "team_cash", flat_store(start, 120))
    r.broker = StubbornPaper(r.broker.h, r.rules, r.broker.quotes_fn, misses=2)
    for k in range(24):
        r.process(start + pd.Timedelta(hours=k))
    logs = [json.loads(x) for f in (tmp_path / "logs").glob("*.jsonl") for x in f.read_text().splitlines()]
    ka = [(e["bar"][:16], [f["status"] for f in e["fills"]]) for e in logs if e["event"] == "keep_alive"]
    assert ka == [("2026-10-04 04:00", ["UNCONFIRMED"]), ("2026-10-04 05:00", ["UNCONFIRMED"]),
                  ("2026-10-04 06:00", ["FILLED"])]                     # first at 12:00 HKT, retried until it fills
    assert r.state["active_days"] == [str(start)]                       # the day counts only after the real fill
    assert r.broker.h.spot.get("BTC/USD", 0.0) > 0


def test_guard_also_runs_for_a_model_that_decides_every_hour(tmp_path):
    """An hourly model's decision hour is every hour; a decision that trades nothing must not switch the guard off
    (the backtest engine fires the guard on decision hours too)."""
    import dataclasses
    start = pd.Timestamp("2026-10-03 16:00", tz="UTC")
    r = make_runner(tmp_path, "team_cash", flat_store(start, 120))
    r.model = copy.copy(r.model)
    r.model.spec = dataclasses.replace(r.model.spec, rebalance_hours=1)
    for k in range(24):
        r.process(start + pd.Timedelta(hours=k))
    logs = [json.loads(x) for f in (tmp_path / "logs").glob("*.jsonl") for x in f.read_text().splitlines()]
    assert sum(e["event"] == "decision" for e in logs) == 24            # it decided every hour ...
    ka = [e["bar"][:16] for e in logs if e["event"] == "keep_alive"]
    assert ka == ["2026-10-04 04:00"]                                   # ... and the guard still fired at 04:00 UTC, once
    assert r.state["active_days"] == [str(start)]


def rising_store(start: pd.Timestamp, days: int, hours_after: int, daily: float) -> feed.Store:
    idx = pd.date_range(start - pd.Timedelta(days=days), start + pd.Timedelta(hours=hours_after), freq="h")
    k = np.clip(np.arange(len(idx)) - days * 24, 0, None)
    c = pd.DataFrame({"BTCUSDT": 100.0 * (1 + daily) ** (k / 24), "ETHUSDT": 10.0}, index=idx)
    st = feed.Store(c, c * 0 + 1e6, idx[-1])
    return st


def run_round(tmp_path, enabled: bool, daily: float, hours: int = 24 * 12) -> tuple[Runner, list]:
    start = pd.Timestamp("2026-10-03 16:00", tz="UTC")
    st = rising_store(start, 120, hours, daily)
    r = make_runner(tmp_path, "team_btc_hold", st)
    r.lv["endgame"] = {"enabled": enabled, "from_day": 10, "lock_return": 0.03}
    for k in range(hours):
        H = start + pd.Timedelta(hours=k)
        px = float(st.close.loc[H, "BTCUSDT"])
        r.client.prices["BTC/USD"] = px
        r.process(H)
    logs = [json.loads(x) for f in (tmp_path / "logs").glob("*.jsonl") for x in f.read_text().splitlines()]
    return r, logs


def test_endgame_lock_sells_once_ahead_after_day_10_and_holds_cash(tmp_path):
    r, logs = run_round(tmp_path, True, daily=0.004)                    # +0.4% a day: +4% by day 10
    locks = [e for e in logs if e["event"] == "endgame_lock"]
    assert len(locks) == 1 and locks[0]["bar"].startswith("2026-10-13 16:00")   # the first hour of day 10
    assert locks[0]["round_return"] >= 0.03
    assert r.state["locked_at"] and r.state["standing"] == {}
    btc = r.broker.h.spot.get("BTC/USD", 0.0) * r.client.prices["BTC/USD"]
    assert btc <= 2 * 0.002 * 100_000 * 1.1                             # at most the keep-alive left in BTC
    days = {e["bar"][:10] for e in logs if any(f["status"] == "FILLED" for f in e.get("fills", []))}
    assert "2026-10-14" in days                                         # the guard keeps the days after active


def test_endgame_is_off_by_default_and_waits_for_the_gain(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    r, logs = run_round(tmp_path / "a", False, daily=0.004)
    assert not any(e["event"] == "endgame_lock" for e in logs) and r.broker.h.spot.get("BTC/USD", 0) > 0
    r, logs = run_round(tmp_path / "b", True, daily=0.001)              # +1% by day 10: below the 3% lock
    assert not any(e["event"] == "endgame_lock" for e in logs) and r.broker.h.spot.get("BTC/USD", 0) > 0


def test_utc_day_guard_trades_on_every_utc_day(tmp_path):
    start = pd.Timestamp("2026-10-03 16:00", tz="UTC")

    def fill_days(utc: bool, d) -> set:
        r = make_runner(d, "team_btc_hold", flat_store(start, 120))
        r.h["guard_utc_day"] = utc
        for k in range(24 * 4):
            r.process(start + pd.Timedelta(hours=k))
        logs = [json.loads(x) for f in (d / "logs").glob("*.jsonl") for x in f.read_text().splitlines()]
        return {e["bar"][:10] for e in logs if any(f["status"] == "FILLED" for f in e.get("fills", []))}

    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    full = {"2026-10-03", "2026-10-04", "2026-10-05", "2026-10-06", "2026-10-07"}
    assert fill_days(True, tmp_path / "a") == full                      # a confirmed trade on every UTC date
    assert fill_days(False, tmp_path / "b") != full                     # HKT days only: some UTC date has none


def test_the_bot_runs_on_roostoo_time_and_flags_a_drifting_clock(tmp_path):
    start = pd.Timestamp("2026-10-03 16:00", tz="UTC")
    r = make_runner(tmp_path, "team_cash", flat_store(start, 120))
    r.client.offset_ms = 3_600_000.0                                   # machine one hour behind Roostoo
    assert abs((r.now() - pd.Timestamp.now(tz="UTC")).total_seconds() - 3600) < 5
    assert r.check_clock() == 3_600_000.0
    r.client.offset_ms = 1_500.0
    r.check_clock()
    logs = [json.loads(x) for f in (tmp_path / "logs").glob("*.jsonl") for x in f.read_text().splitlines()]
    levels = [e["level"] for e in logs if e["event"] == "clock"]
    assert levels == ["error", "ok"]                                    # 3,600 s > clock_error_s; 1.5 s < clock_warn_s
