"""Tick-scalping sleeve (src/live/sleeve.py) on a paper exchange with scripted quotes, its failure handling, and the
hourly runner's sleeve split. No network."""
from __future__ import annotations

import copy
import json
import logging
from decimal import Decimal

import pandas as pd

from src.api.client import OrderStateUnknown, RoostooError
from src.api.rules import PairRule
from src.config import load_config
from src.execution.planner import Holdings
from src.live.runner import sleeve_split
from src.live.sleeve import (Coin, Fill, Params, PaperExchange, Sleeve, after_stop, after_win, buy_price, edge_breaker,
                             fill_from_detail, recorder_quotes)
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


def make_sleeve(tmp_path, bids, lot=1000.0, ex_cls=PaperExchange, mode="paper", **over):
    cfg = copy.deepcopy(CFG)
    sc = cfg["live"]["sleeve"]
    sc.update(lots_usd={PAIR: lot}, capital_usd=lot, **over)
    cfg["live"].update(start_at=None, end_at=None)
    s = Script(bids)
    ex = ex_cls(s.quotes, "mid", lot)
    sl = Sleeve(cfg, ex, RULES, tmp_path, mode, LOG, clock=s.clock, sleep=lambda x: None)
    return sl, s, ex


def run(sl, s, n):
    for _ in range(n):
        sl.tick()
        s.k += 1


def events(tmp_path):
    return [json.loads(x) for f in (tmp_path / "logs" / "sleeve").glob("*.jsonl") for x in f.read_text().splitlines()]


# ---------------- the strategy core

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


def test_edge_breaker_pauses_a_coin_that_stopped_earning():
    c, p = Coin(PAIR, 1000.0), Params(breaker_trips=20, breaker_win=0.75, breaker_pause_s=100.0)
    hit = [edge_breaker(c, r, 50.0, p) for r in [0.001] * 12 + [-0.006] * 8]    # 60% wins, net negative
    assert hit[-1] and not any(hit[:-1]) and c.blocked_until == 150.0 and c.recent == []
    c2 = Coin(PAIR, 1000.0)
    assert not any(edge_breaker(c2, r, 0.0, p) for r in [0.0015] * 17 + [-0.006] * 3)   # 85% wins: fine


def test_fills_are_booked_from_quantity_price_and_commission():
    b = fill_from_detail({"Pair": PAIR, "Status": "FILLED", "Side": "BUY", "FilledQuantity": 1000, "FilledAverPrice": 2.0,
                          "CommissionCoin": "BONK", "CommissionChargeValue": 0.5, "Role": "MAKER", "OrderID": 7})
    assert b.coin_change == 999.5 and b.usd_change == -2000.0 and b.order_id == "7"
    s = fill_from_detail({"Pair": PAIR, "Status": "FILLED", "Side": "SELL", "FilledQuantity": 999, "FilledAverPrice": 2.01,
                          "CommissionCoin": "USD", "CommissionChargeValue": 1.0})
    assert s.coin_change == -999 and abs(s.usd_change - (999 * 2.01 - 1.0)) < 1e-9
    m = fill_from_detail({"Pair": PAIR, "Status": "FILLED", "FilledQuantity": 10, "FilledAverPrice": 2.0, "Type": "MARKET"}, "SELL")
    assert abs(m.usd_change - 20.0 * (1 - 0.001)) < 1e-12                # no commission field: taker fee assumed
    assert fill_from_detail({"Status": "CANCELLED"}, "BUY").status == "CANCELED"


# ---------------- the loop on a paper exchange

def test_a_flickering_bid_is_harvested_with_buy_backs_one_step_lower(tmp_path):
    bids = [100.0, 100.0] + [101.0, 101.0, 100.0, 100.0] * 10          # the bid flickers 100 <-> 101
    sl, s, ex = make_sleeve(tmp_path, bids, min_check_s=0)
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
    assert not list((tmp_path / "logs").glob("*.jsonl"))               # the bot's own logs folder stays the bot's


def test_order_checks_are_rate_limited(tmp_path):
    bids = [100.0, 100.0] + [101.0, 101.0, 100.0, 100.0] * 10
    calls = {"n": 0}

    class Counting(PaperExchange):
        def pending_pairs(self):
            calls["n"] += 1
            return super().pending_pairs()
    sl, s, ex = make_sleeve(tmp_path, bids, ex_cls=Counting, min_check_s=12)
    run(sl, s, len(bids))
    assert calls["n"] <= len(bids) / 2 + 1 and sl.coins[PAIR].trips >= 3


def test_stops_then_a_pause_after_three(tmp_path):
    bids = [100.0, 100.0, 99.0, 98.0, 98.0, 97.0, 96.0, 95.0, 95.0, 94.0, 93.0, 92.0, 92.0, 91.0, 90.0, 89.0, 89.0, 89.0]
    sl, s, ex = make_sleeve(tmp_path, bids, daily_loss_limit=0.5, total_loss_limit=0.9, min_check_s=0)
    run(sl, s, len(bids))
    c = sl.coins[PAIR]
    assert c.stops == 3 and c.phase == "PAUSED" and c.wins == 0


def test_no_new_orders_in_the_hourly_bots_minutes(tmp_path):
    sl, s, ex = make_sleeve(tmp_path, [100.0] * 5)
    s.t0 = pd.Timestamp("2026-10-08 10:00:30", tz="UTC").timestamp()    # minute 0: the hourly bot's window
    run(sl, s, 5)
    assert not [e for e in events(tmp_path) if e["event"] == "order"]


def test_kill_file_flattens_and_stops(tmp_path):
    sl, s, ex = make_sleeve(tmp_path, [100.0, 100.0, 100.0, 100.0], min_check_s=0)
    run(sl, s, 3)
    assert sl.coins[PAIR].phase == "HOLDING"
    (tmp_path / "sleeve.KILL").write_text("stop")
    run(sl, s, 1)
    assert sl.stopped == "kill" and sl.coins[PAIR].qty * 100 < 1 and ex.pending_pairs() == {}
    assert json.loads((tmp_path / "sleeve-paper.json").read_text())["flat"]


def test_daily_loss_limit_cancels_the_resting_buy_and_stops_buying(tmp_path):
    bids = [100.0, 100.0, 100.0, 95.0, 95.0, 95.0, 95.0, 95.0]
    sl, s, ex = make_sleeve(tmp_path, bids, min_check_s=0)
    run(sl, s, len(bids))
    c = sl.coins[PAIR]
    assert c.stops == 1 and c.order_id is None and ex.pending_pairs() == {}
    assert sl.value(s.quotes([PAIR])) < 1000.0 * 0.97


def test_flatten_before_the_rounds_end(tmp_path):
    sl, s, ex = make_sleeve(tmp_path, [100.0] * 10, min_check_s=0)
    sl.end_at = T_START + 6 * 4 + 600 - 1                               # the flatten window opens at tick 4
    run(sl, s, 6)
    assert sl.stopped == "round_end" and sl.coins[PAIR].qty * 100 < 1


def test_no_buys_while_one_step_is_too_small_a_share_of_the_price(tmp_path):
    sl, s, ex = make_sleeve(tmp_path, [1000.0] * 5)                     # step 1 at 1000: 0.1% < 0.15%
    run(sl, s, 5)
    ev = events(tmp_path)
    assert not [e for e in ev if e["event"] == "order"] and any(e["event"] == "step_too_small" for e in ev)


# ---------------- failures: never fatal, books stay right

class Refusing(PaperExchange):
    def place_limit(self, pair, side, qty, price):
        raise RoostooError("/v3/place_order: insufficient balance")


def test_a_refused_buy_backs_off_and_is_not_an_error(tmp_path):
    sl, s, ex = make_sleeve(tmp_path, [100.0] * 30, ex_cls=Refusing)
    run(sl, s, 30)                                                       # 3 minutes
    rej = [e for e in events(tmp_path) if e["event"] == "rejected"]
    assert 1 <= len(rej) <= 3 and sl.coins[PAIR].rejects == len(rej) and not sl.stopped
    assert sl.cash == 1000.0


class Unknown(PaperExchange):
    """The first buy times out but reaches the exchange (it rests there); the books must find it."""
    first = True

    def place_limit(self, pair, side, qty, price):
        f = super().place_limit(pair, side, qty, price)
        if side == "BUY" and Unknown.first:
            Unknown.first = False
            raise OrderStateUnknown("place_order: transport error")
        return f


def test_an_order_whose_outcome_is_unknown_is_reconciled_not_fatal(tmp_path):
    sl, s, ex = make_sleeve(tmp_path, [100.0] * 6, ex_cls=Unknown, min_check_s=0)
    run(sl, s, 6)
    ev = events(tmp_path)
    assert any(e["event"] == "reconcile" and "unknown" in e["why"] for e in ev)
    assert len(ex.open_orders(PAIR)) <= 1 and not sl.stopped                # the stray order was cancelled
    assert abs(sl.value(s.quotes([PAIR])) - 1000.0) < 20.0                  # books still add up


class PartialCancel(PaperExchange):
    """A resting buy partly fills; then the trail cancels it: the coins bought must be booked."""

    def cancel(self, pair, order_id):
        o = self.open.get(order_id)
        ok = super().cancel(pair, order_id)
        if ok and o and o["side"] == "BUY":
            half = o["qty"] / 2
            base = pair.split("/")[0]
            self.held[base] = self.held.get(base, 0.0) + half * (1 - 0.0005)
            self.usd -= half * o["price"]
            self.done[order_id] = Fill("CANCELED", o["price"], half, half * (1 - 0.0005), -half * o["price"], order_id,
                                       "MAKER", "BUY")
        return ok


def test_a_partial_fill_before_a_cancel_is_booked(tmp_path):
    sl, s, ex = make_sleeve(tmp_path, [102.0, 102.0, 102.0, 104.0, 104.0], ex_cls=PartialCancel, min_check_s=0)
    sl.coins[PAIR].next_px = 101.0                                       # rests below the bid of 102
    run(sl, s, 4)                                                        # the bid moves to 104: trail, cancel
    c = sl.coins[PAIR]
    assert c.qty > 4.0 and c.phase == "HOLDING" and abs(c.cost - c.qty / (1 - 0.0005) * 101.0) < 1e-6
    assert abs(sl.cash - (1000.0 - c.cost)) < 1e-9                       # the unfilled half came back to the cash
    run(sl, s, 1)                                                        # then sold at the bid (2 steps up) as a taker
    assert c.trips == 1 and c.pnl > 0 and c.qty * 104 < 1


def test_api_errors_back_off_and_only_a_long_outage_stops_it(tmp_path):
    sl, s, ex = make_sleeve(tmp_path, [100.0] * 3, error_kill_minutes=10)
    naps = []
    sl.sleep = lambda x: (naps.append(x), setattr(s, "k", s.k + int(x // 6) + 1))

    def boom():
        raise RoostooError("/v3/ticker: try again later")
    sl.tick = boom
    sl.run()
    assert sl.stopped == "errors" and naps[:4] == [30.0, 60.0, 120.0, 240.0] and max(naps) == 300.0
    assert s.clock() - T_START >= 600


def test_a_config_change_of_capital_and_lots_is_picked_up_at_restart(tmp_path):
    sl, s, ex = make_sleeve(tmp_path, [100.0] * 3, min_check_s=0)
    run(sl, s, 3)
    sl.save(s.quotes([PAIR]))
    cash0 = sl.cash
    sl2, *_ = make_sleeve(tmp_path, [100.0] * 3, lot=2000.0)
    assert sl2.capital == 2000.0 and abs(sl2.cash - (cash0 + 1000.0)) < 1e-9 and sl2.coins[PAIR].lot_usd == 2000.0
    assert sl2._changes == {"capital_change": 1000.0}


def test_recorder_quotes_ignore_a_stopped_recorder(tmp_path):
    f = tmp_path / "20261008.csv"
    f.write_text("ts_utc,pair,max_bid,min_ask,last_price\n2026-10-08T10:00:00+00:00,BONK/USD,1,2,1\n")
    t = pd.Timestamp("2026-10-08 10:00:30", tz="UTC").timestamp()
    assert recorder_quotes(str(tmp_path / "2026*.csv"), 60, lambda: t)([PAIR]) == {PAIR: (1.0, 2.0, 1.0)}
    assert recorder_quotes(str(tmp_path / "2026*.csv"), 60, lambda: t + 120)([PAIR]) == {}


# ---------------- the hourly runner's side

def test_runner_split_keeps_the_sleeves_cash_and_coins_out_of_the_model():
    h = Holdings(5_000.0, {"BTC/USD": 1.0, "BONK/USD": 1e6}, {})
    m = sleeve_split(h, {"BONK/USD"}, 20_000.0)
    assert m.usd_free == -15_000.0 and "BONK/USD" not in m.spot and m.spot["BTC/USD"] == 1.0


def test_runner_sizes_the_model_on_its_share_and_resizes_when_the_sleeve_changes(tmp_path):
    start = pd.Timestamp("2026-10-03 16:00", tz="UTC")
    r = make_runner(tmp_path, "team_btc_hold", flat_store(start, 120))
    r.lv["sleeve"] = {**r.lv["sleeve"], "enabled": True, "mode": "live", "capital_usd": 30_000.0, "lots_usd": {PAIR: 30_000.0}}
    (tmp_path / "sleeve.json").write_text(json.dumps({"cash_free": 30_000.0}))
    r.process(start)
    btc = r.broker.h.spot["BTC/USD"] * 100.0
    assert 68_000 < btc < 70_001 and r.broker.h.usd_free > 29_900      # the model invested its 70k, not the sleeve's 30k
    r.lv["sleeve"]["enabled"] = False                                     # the sleeve is switched off at 17:00: no new
    r.process(start + pd.Timedelta(hours=1))                              # decision, the 16:00 weights on the whole account
    assert r.state["last_decision"] == str(start)
    assert r.broker.h.spot["BTC/USD"] * 100.0 > 97_000


def test_a_sleeve_change_off_schedule_never_calls_the_model(tmp_path):
    # e20v45 reads BTC's trend on 6-hour points counted from the hour it is called: off its 16:00 schedule it can flip
    # (Oct 10, 18:00 UTC). A change of the sleeve's capital must resize the last decision, not call the model again.
    start = pd.Timestamp("2026-10-03 16:00", tz="UTC")
    r = make_runner(tmp_path, "team_btc_hold", flat_store(start, 120))
    calls = []
    inner = r.model.targets
    r.model = type("Spy", (), {"spec": r.model.spec, "targets": lambda self, v: (calls.append(v.t), inner(v))[1]})()
    r.process(start)                                                      # 16:00: the normal decision, no sleeve
    assert calls == [start] and r.broker.h.spot["BTC/USD"] * 100.0 > 97_000
    r.lv["sleeve"] = {**r.lv["sleeve"], "enabled": True, "mode": "live", "capital_usd": 30_000.0, "lots_usd": {PAIR: 30_000.0}}
    (tmp_path / "sleeve.json").write_text(json.dumps({"cash_free": 30_000.0}))
    r.process(start + pd.Timedelta(hours=2))                              # the sleeve starts at 18:00
    assert calls == [start] and r.state["last_decision"] == str(start)  # not called off schedule
    assert 68_000 < r.broker.h.spot["BTC/USD"] * 100.0 < 70_001 and r.broker.h.usd_free > 29_900   # resized: cash freed
    logs = [json.loads(x) for f in (tmp_path / "logs").glob("2*.jsonl") for x in f.read_text().splitlines()]
    assert any(e["event"] == "sleeve_resize" for e in logs) and not any(e["event"] == "decision" and e["bar"].startswith("2026-10-03 18") for e in logs)
    r.process(start + pd.Timedelta(hours=24))                             # the next 16:00: a normal decision again
    assert calls == [start, start + pd.Timedelta(hours=24)]


def test_a_sleeve_stopped_for_good_and_flat_gives_its_cash_back(tmp_path):
    start = pd.Timestamp("2026-10-03 16:00", tz="UTC")
    r = make_runner(tmp_path, "team_btc_hold", flat_store(start, 120))
    r.lv["sleeve"] = {**r.lv["sleeve"], "enabled": True, "mode": "live", "capital_usd": 30_000.0, "lots_usd": {PAIR: 30_000.0}}
    (tmp_path / "sleeve.json").write_text(json.dumps({"cash_free": 30_000.0}))
    r.process(start)
    (tmp_path / "sleeve.json").write_text(json.dumps({"cash_free": 29_000.0, "stopped": "total_loss", "flat": True}))
    r.process(start + pd.Timedelta(hours=1))
    assert r.broker.h.spot["BTC/USD"] * 100.0 > 97_000 and r.state["sleeve_capital"] == 0.0


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
    r.process(start)
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


# ---------------- the live probe (Book, 2026-10-08)

def probe_cfg(**over):
    return {"probe": {"enabled": True, "pair": PAIR, "lot_usd": 500.0, "buys": 5, "max_failed": 2, "wait_s": 20}, **over}


def test_probe_passes_when_buys_at_the_bid_fill_then_full_lots(tmp_path):
    bids = [100.0, 100.0] + [101.0, 101.0, 100.0, 100.0] * 12
    sl, s, ex = make_sleeve(tmp_path, bids, mode="live", min_check_s=0, **probe_cfg())
    first = []
    orig = ex.place_limit
    ex.place_limit = lambda pair, side, qty, price: (first.append(float(qty) * float(price)) if side == "BUY" else None) or orig(pair, side, qty, price)
    run(sl, s, len(bids))
    assert sl.probe["status"] == "passed" and all(r["pass"] for r in sl.probe["results"])
    assert max(first[:5]) <= 500.0 and max(first) > 900.0              # small lots while probing, full lots after
    assert not sl.stopped


class Queued(PaperExchange):
    """A real order book: a resting buy fills only when the bid goes BELOW it."""

    def _match(self):
        for oid, o in list(self.open.items()):
            q = self.last.get(o["pair"])
            if q and o["side"] == "BUY" and q[0] < o["price"] - 1e-12:
                super()._match()
                return


def test_probe_fails_and_stops_for_good_when_buys_at_the_bid_do_not_fill(tmp_path):
    sl, s, ex = make_sleeve(tmp_path, [100.0] * 40, ex_cls=Queued, mode="live", min_check_s=0, **probe_cfg())
    run(sl, s, 40)                                                       # 4 minutes, the bid never moves
    assert sl.probe["status"] == "failed" and sl.stopped == "fill_rule"
    assert sum(1 for r in sl.probe["results"] if not r["pass"]) == 3 and ex.pending_pairs() == {}
    assert sl.value(s.quotes([PAIR])) > 999.0                           # it never bought: nothing lost


def test_no_probe_in_paper_mode(tmp_path):
    sl, s, ex = make_sleeve(tmp_path, [100.0] * 3, **probe_cfg())
    assert sl.probe["status"] == "off"


# ---------------- Oct 13: the first live probe buy was cancelled unfilled, but its order detail reported a full fill

class PhantomCancel(PaperExchange):
    """The cancel goes through (nothing filled, the lock comes back), but the order detail reports the whole quantity."""

    def cancel(self, pair, order_id):
        o = self.open.get(order_id)
        ok = super().cancel(pair, order_id)
        if ok and o:
            self.done[order_id] = Fill("CANCELED", o["price"], o["qty"], o["qty"] * (1 - 0.0005), -o["qty"] * o["price"],
                                       order_id, "MAKER", o["side"])
        return ok


def test_a_cancelled_buy_reported_as_filled_books_only_what_the_wallet_received(tmp_path):
    sl, s, ex = make_sleeve(tmp_path, [102.0, 102.0, 102.0, 104.0, 104.0], ex_cls=PhantomCancel, min_check_s=0)
    sl.coins[PAIR].next_px = 101.0                                       # rests below the bid of 102: never fills
    run(sl, s, 4)                                                        # the bid moves to 104: trail, cancel
    c = sl.coins[PAIR]
    ev = events(tmp_path)
    assert any(e["event"] == "fill_unconfirmed" for e in ev)
    assert c.qty == 0.0 and abs(sl.value(s.quotes([PAIR])) - 1000.0) < 1e-6 and not sl.stopped   # no phantom loss


def test_coins_the_books_paid_for_but_the_wallet_lacks_are_refunded(tmp_path):
    sl, s, ex = make_sleeve(tmp_path, [100.0] * 3, min_check_s=0)
    c = sl.coins[PAIR]
    c.phase, c.qty, c.entry, c.cost = "HOLDING", 9.995, 100.0, 1000.0    # books: a lot bought; wallet: nothing
    sl.cash -= 1000.0
    sl._reconcile_pair(c, "test")
    assert c.qty == 0.0 and c.phase == "BUYING" and abs(sl.cash - 1000.0) < 1e-9
    assert any(e["event"] == "reconcile_refund" and abs(e["usd"] - 1000.0) < 1e-9 for e in events(tmp_path))


def test_a_new_run_id_starts_fresh_and_keeps_the_old_state(tmp_path):
    sl, s, ex = make_sleeve(tmp_path, [100.0] * 3, mode="live", run_id="a")
    sl.stopped, sl.cash = "total_loss", 900.0
    sl.save(s.quotes([PAIR]))
    again, *_ = make_sleeve(tmp_path, [100.0] * 3, mode="live", run_id="a")
    assert again.stopped == "total_loss"                                 # same run: the stop holds
    fresh, *_ = make_sleeve(tmp_path, [100.0] * 3, mode="live", run_id="b", lot=2000.0)
    assert fresh.stopped is None and fresh.cash == 2000.0 and fresh.capital == 2000.0
    assert (tmp_path / "sleeve-before-b.json").exists() and fresh._changes["fresh_run"] == "b"
