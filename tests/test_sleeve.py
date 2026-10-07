"""Tick-scalping sleeve (src/live/sleeve.py) on a paper exchange with scripted quotes, and the hourly runner's
sleeve split. No network."""
from __future__ import annotations

import copy
import json
import logging
from decimal import Decimal

import pandas as pd

from src.api.rules import PairRule
from src.config import load_config
from src.execution.planner import Holdings
from src.live.runner import sleeve_split
from src.live.sleeve import Coin, Params, PaperExchange, Sleeve, after_stop, after_win, buy_price
from tests.test_live import flat_store, make_runner

CFG = load_config()
LOG = logging.getLogger("test_sleeve")
PAIR = "BONK/USD"
RULES = {PAIR: PairRule(PAIR, 0, 2, Decimal(1))}            # price step 1 (prices around 100: one step = 1%)
T_START = pd.Timestamp("2026-10-08 10:10", tz="UTC").timestamp()   # outside the hourly bot's minutes 0-6


class Script:
    """Quotes from a list, one per tick; the clock moves 6 s per tick."""

    def __init__(self, bids: list[float], t0: float = T_START):
        self.bids, self.k, self.t0 = bids, 0, t0

    def quotes(self, pairs):
        b = self.bids[min(self.k, len(self.bids) - 1)]
        return {PAIR: (b, b + 1.0, b)}

    def clock(self):
        return self.t0 + 6.0 * self.k


def make_sleeve(tmp_path, bids, lot=1000.0, **over):
    cfg = copy.deepcopy(CFG)
    sc = cfg["live"]["sleeve"]
    sc.update(lots_usd={PAIR: lot}, capital_usd=lot, **over)
    cfg["live"].update(start_at=None, end_at=None)
    s = Script(bids)
    ex = PaperExchange(s.quotes, "mid", lot)
    sl = Sleeve(cfg, ex, RULES, tmp_path, "paper", LOG, clock=s.clock)
    return sl, s, ex


def run(sl, s, n):
    for _ in range(n):
        sl.tick()
        s.k += 1


def events(tmp_path):
    return [json.loads(x) for f in (tmp_path / "logs").glob("sleeve-*.jsonl") for x in f.read_text().splitlines()]


def test_core_rules():
    c = Coin(PAIR, 1000.0, phase="HOLDING", entry=100.0)
    after_win(c, 101.0, 1.0)
    assert c.phase == "BUYING" and c.next_px == 100.0             # buy back one step below the sell
    assert buy_price(c, 101.0, 102.0, 1.0) == 100.0
    p = Params(pause_after_stops=3, pause_s=3600.0)
    for k in range(3):
        c.phase = "HOLDING"
        after_stop(c, 97.0, 1.0, 1000.0 + k, p)
    assert c.phase == "PAUSED" and c.paused_until == 1002.0 + 3600.0 and c.next_px is None


def test_a_flickering_bid_is_harvested_with_buy_backs_one_step_lower(tmp_path):
    bids = [100.0, 100.0] + [101.0, 101.0, 100.0, 100.0] * 10          # the bid flickers 100 <-> 101
    sl, s, ex = make_sleeve(tmp_path, bids)
    run(sl, s, len(bids))
    c = sl.coins[PAIR]
    ev = events(tmp_path)
    buys = [e["px"] for e in ev if e["event"] == "order" and e["side"] == "BUY"]
    sells = [e["px"] for e in ev if e["event"] == "order" and e["side"] == "SELL"]
    assert c.trips >= 5 and c.wins == c.trips and c.stops == 0
    assert set(buys) == {100.0} and set(sells) == {101.0}
    assert c.pnl > 0 and sl.value(s.quotes([PAIR])) > 1000.0
    st = json.loads((tmp_path / "sleeve-paper.json").read_text())       # a paper sleeve never writes the live file
    assert st["mode"] == "paper" and abs(st["cash_free"] - sl.cash) < 1e-9 and not (tmp_path / "sleeve.json").exists()


def test_stops_then_a_pause_after_three(tmp_path):
    # buy at 100, the bid falls to 98 (2 steps): stop; buy again at 97 (bid - 1) ... three times, then pause
    bids = [100.0, 100.0, 99.0, 98.0, 98.0, 97.0, 96.0, 95.0, 95.0, 94.0, 93.0, 92.0, 92.0, 91.0, 90.0, 89.0, 89.0, 89.0]
    sl, s, ex = make_sleeve(tmp_path, bids, daily_loss_limit=0.5, total_loss_limit=0.9)   # the loss limits would stop it first
    run(sl, s, len(bids))
    c = sl.coins[PAIR]
    assert c.stops == 3 and c.phase == "PAUSED" and c.wins == 0
    ev = events(tmp_path)
    assert all(e["side"] == "SELL" for e in ev if e["event"] == "fill" and e.get("kind") == "stop")


def test_no_new_orders_in_the_hourly_bots_minutes(tmp_path):
    t0 = pd.Timestamp("2026-10-08 10:00:30", tz="UTC").timestamp()       # minute 0: the hourly bot's window
    cfg_bids = [100.0] * 5
    sl, s, ex = make_sleeve(tmp_path, cfg_bids)
    s.t0 = t0
    run(sl, s, 5)
    assert not [e for e in events(tmp_path) if e["event"] == "order"]


def test_kill_file_flattens_and_stops(tmp_path):
    sl, s, ex = make_sleeve(tmp_path, [100.0, 100.0, 100.0, 100.0])
    run(sl, s, 3)
    assert sl.coins[PAIR].phase == "HOLDING"                         # bought at 100
    (tmp_path / "sleeve.KILL").write_text("stop")
    run(sl, s, 1)
    assert sl.stopped == "kill" and sl.coins[PAIR].qty * 100 < 1 and ex.pending_pairs() == {}   # only dust left
    assert any(e["event"] == "flatten" for e in events(tmp_path))


def test_daily_loss_limit_cancels_the_resting_buy_and_stops_buying(tmp_path):
    # a lot bought at 100 then stopped at 95 (a 5-step gap: one 5% hit), so the sleeve is > 3% down on the day
    bids = [100.0, 100.0, 100.0, 95.0, 95.0, 95.0, 95.0, 95.0]
    sl, s, ex = make_sleeve(tmp_path, bids)
    run(sl, s, len(bids))
    c = sl.coins[PAIR]
    assert c.stops == 1 and c.order_id is None and ex.pending_pairs() == {}
    assert sl.value(s.quotes([PAIR])) < 1000.0 * 0.97


def test_flatten_before_the_rounds_end(tmp_path):
    end = pd.Timestamp(T_START + 6 * 4 + 600 - 1, unit="s", tz="UTC")     # flatten window opens at tick 4
    sl, s, ex = make_sleeve(tmp_path, [100.0] * 10)
    sl.end_at = end.timestamp()
    run(sl, s, 6)
    assert sl.stopped == "round_end" and sl.coins[PAIR].qty * 100 < 1


def test_runner_split_keeps_the_sleeves_cash_and_coins_out_of_the_model():
    h = Holdings(5_000.0, {"BTC/USD": 1.0, "BONK/USD": 1e6}, {})
    m = sleeve_split(h, {"BONK/USD"}, 20_000.0)
    assert m.usd_free == -15_000.0 and "BONK/USD" not in m.spot and m.spot["BTC/USD"] == 1.0


def test_runner_sizes_the_model_on_its_share_and_redecides_when_the_sleeve_changes(tmp_path):
    start = pd.Timestamp("2026-10-03 16:00", tz="UTC")
    r = make_runner(tmp_path, "team_btc_hold", flat_store(start, 120))
    r.lv["sleeve"] = {**r.lv["sleeve"], "enabled": True, "mode": "live", "capital_usd": 30_000.0, "lots_usd": {PAIR: 30_000.0}}
    (tmp_path / "sleeve.json").write_text(json.dumps({"cash_free": 30_000.0}))
    r.process(start)
    btc = r.broker.h.spot["BTC/USD"] * 100.0
    assert 68_000 < btc < 70_001 and r.broker.h.usd_free > 29_900      # the model invested its 70k, not the sleeve's 30k
    r.lv["sleeve"]["enabled"] = False                                     # the sleeve is switched off: decide again now
    r.process(start + pd.Timedelta(hours=1))
    assert r.state["last_decision"] == str(start + pd.Timedelta(hours=1))
    assert r.broker.h.spot["BTC/USD"] * 100.0 > 97_000


def test_a_paper_sleeve_takes_nothing_from_the_model(tmp_path):
    start = pd.Timestamp("2026-10-03 16:00", tz="UTC")
    r = make_runner(tmp_path, "team_btc_hold", flat_store(start, 120))
    r.lv["sleeve"] = {**r.lv["sleeve"], "enabled": True, "mode": "paper", "capital_usd": 30_000.0}
    r.process(start)
    assert r.broker.h.spot["BTC/USD"] * 100.0 > 97_000


class Boom:
    mode, capital, stopped = "paper", 1.0, None

    def run(self):
        raise RuntimeError("sleeve bug")


def test_a_failing_sleeve_thread_never_stops_the_hourly_model(tmp_path):
    start = pd.Timestamp("2026-10-03 16:00", tz="UTC")
    r = make_runner(tmp_path, "team_btc_hold", flat_store(start, 120))
    r.sleeve = Boom()
    r.start_sleeve()
    r.sleeve_thread.join(5)
    r.process(start)                                                     # the model still decides and trades
    assert r.broker.h.spot.get("BTC/USD", 0) > 0
    logs = [json.loads(x) for f in (tmp_path / "logs").glob("2*.jsonl") for x in f.read_text().splitlines()]
    assert any(e["event"] == "sleeve_thread" and e["status"] == "failed" for e in logs)


def test_in_process_sleeve_shares_the_bots_rate_limiter_and_a_paper_bot_never_runs_it_live(tmp_path, monkeypatch):
    import src.live.sleeve as sv
    from src.api.client import RoostooClient
    monkeypatch.setattr(sv.RoostooClient, "exchange_info",
                        lambda self: {"TradePairs": {PAIR: {"PricePrecision": 8, "AmountPrecision": 0, "MiniOrder": 1}}})
    cfg = copy.deepcopy(CFG)
    cfg["live"]["sleeve"].update(enabled=True, mode="live", lots_usd={PAIR: 1000.0}, capital_usd=1000.0)
    bot = RoostooClient(cfg["exchange"]["base_url"], None, 20, 5)
    sl = sv.build_in_process(cfg, bot, "paper", tmp_path, LOG)
    assert sl.mode == "paper" and isinstance(sl.ex, sv.PaperExchange)
    assert sl.ex.quote_fn.__self__.c.limiter is bot.limiter
    sl2 = sv.build_in_process(cfg, bot, "live", tmp_path, LOG)
    assert sl2.mode == "live" and isinstance(sl2.ex, sv.RoostooExchange) and sl2.ex.c.limiter is bot.limiter
