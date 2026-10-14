"""Roostoo fill-rule experiment on the live account (Book, 2026-10-14). STO/USD, about $200 an order, at most 8 API
calls a minute (the bot keeps 20), only in minutes :06-:54 and never 03:30-04:30 or 15:30-16:30 UTC, and flat in STO
(back to its starting balance) at the end. One JSON line per event, raw order replies included; no keys printed.
  E1 market buy | E2 limit sell at the ask | E3 market sell (rest) | E4 limit buy at bid-1 | E5 limit sell at entry+1
  E6 limit buy at the bid, 8 min | flatten"""
import json
import time
from decimal import Decimal

from src.api.client import RoostooClient, load_credentials
from src.api.rules import fmt, parse_exchange_info, truncate
from src.config import load_config

PAIR, USD, WAIT = "STO/USD", Decimal("200"), 480
cfg = load_config()
c = RoostooClient(cfg["exchange"]["base_url"], load_credentials(".env"), 8, cfg["execution"]["timeout_s"])
c.sync_clock()
rule = parse_exchange_info(c.exchange_info())[PAIR]
STEP, PREC, BASE = Decimal(1).scaleb(-rule.price_precision), rule.amount_precision, PAIR.split("/")[0]


def out(ev, **d):
    print(json.dumps({"ts": time.strftime("%H:%M:%S", time.gmtime()), "ev": ev, **d}, default=str), flush=True)


def q():
    t = c.ticker(PAIR)
    t = t.get(PAIR, t)
    return {"bid": t.get("MaxBid"), "ask": t.get("MinAsk"), "last": t.get("LastPrice")}


def held():
    w = c.balance().get(BASE) or {}
    return Decimal(str(w.get("Free") or 0)) + Decimal(str(w.get("Lock") or 0))


def safe():
    g = time.gmtime()
    hm = g.tm_hour * 100 + g.tm_min
    return 6 <= g.tm_min <= 54 and not (330 <= hm <= 430) and not (1530 <= hm <= 1630)


def wait_safe():
    while not safe():
        time.sleep(20)


def detail(oid):
    rows = c.query_order(order_id=oid)
    return rows[0] if rows else {}


def rest(side, px, qty):
    wait_safe()
    r = c.place_order(PAIR, side, fmt(qty), "LIMIT", fmt(px))
    oid = r.get("OrderID")
    out("placed", side=side, px=fmt(px), qty=fmt(qty), quote=q(), reply=r)
    t0 = time.time()
    while time.time() - t0 < WAIT and safe():
        time.sleep(20)
        d = detail(oid)
        if str(d.get("Status", "")).upper() in ("FILLED", "CANCELED", "CANCELLED"):
            out("final", side=side, s=int(time.time() - t0), quote=q(), detail=d)
            return d
        out("waiting", side=side, s=int(time.time() - t0), quote=q(), status=d.get("Status"))
    c.cancel_order(order_id=oid)
    time.sleep(3)
    d = detail(oid)
    out("cancelled", side=side, s=int(time.time() - t0), quote=q(), detail=d, wallet_coin=fmt(held()))
    return d


def market(side, qty):
    wait_safe()
    before = q()
    r = c.place_order(PAIR, side, fmt(qty), "MARKET")
    out("market", side=side, qty=fmt(qty), quote_before=before, quote_after=q(), reply=r)


start = held()
out("start", coin_start=fmt(start), rule=str(rule), quote=q())
try:
    a = Decimal(str(q()["ask"]))
    market("BUY", truncate(USD / a, PREC))                                          # E1
    got = truncate(held() - start, PREC)
    if got > 0:
        rest("SELL", Decimal(str(q()["ask"])), got)                                 # E2
    left = truncate(held() - start, PREC)
    if left * a >= 1:
        market("SELL", left)                                                         # E3
    p = Decimal(str(q()["bid"])) - STEP
    rest("BUY", p, truncate(USD / p, PREC))                                          # E4
    got = truncate(held() - start, PREC)
    if got * p >= 1:
        rest("SELL", p + STEP, got)                                                  # E5
    left = truncate(held() - start, PREC)
    if left * p >= 1:
        market("SELL", left)
    p = Decimal(str(q()["bid"]))
    rest("BUY", p, truncate(USD / p, PREC))                                          # E6
finally:
    c.cancel_order(pair=PAIR)                          # any experiment order still resting (only STO; the bot has none)
    time.sleep(3)
    left = truncate(held() - start, PREC)
    if left * Decimal(str(q()["bid"])) >= 1:
        market("SELL", left)
    out("end", coin_now=fmt(held()), coin_start=fmt(start))
