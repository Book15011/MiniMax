"""Does a market order fill at the shown MinAsk/MaxBid or at LastPrice? (Book, 2026-10-15; live account, $20 orders)
BUY test: wait until LastPrice == MaxBid and MinAsk == MaxBid + 1 step, then market-buy. SELL test: wait until
LastPrice == MinAsk and MaxBid == MinAsk - 1 step, then market-sell what the test bought. Up to 3 of each over STO,
PEPE, BONK; at most 8 API calls a minute; only minutes :06-:54, never 03:30-04:30 / 15:30-16:30 UTC. It sells back
everything it bought, and also the 5494.5 STO left by yesterday's experiment if still there. No keys printed."""
import json
import time
from decimal import Decimal

from src.api.client import RoostooClient, load_credentials
from src.api.rules import fmt, parse_exchange_info, truncate
from src.config import load_config

PAIRS, USD, LEFTOVER_STO = ["STO/USD", "PEPE/USD", "BONK/USD"], Decimal("20"), Decimal("5494.5")
cfg = load_config()
c = RoostooClient(cfg["exchange"]["base_url"], load_credentials(".env"), 8, cfg["execution"]["timeout_s"])
c.sync_clock()
rules = parse_exchange_info(c.exchange_info())
step = {p: Decimal(1).scaleb(-rules[p].price_precision) for p in PAIRS}
bought = {p: Decimal(0) for p in PAIRS}


def out(ev, **d):
    print(json.dumps({"ts": time.strftime("%H:%M:%S", time.gmtime()), "ev": ev, **d}, default=str), flush=True)


def quotes():
    t = c.ticker()
    return {p: (Decimal(str(t[p]["MaxBid"])), Decimal(str(t[p]["MinAsk"])), Decimal(str(t[p]["LastPrice"])))
            for p in PAIRS if p in t}


def coin(p):
    w = c.balance().get(p.split("/")[0]) or {}
    return Decimal(str(w.get("Free") or 0)) + Decimal(str(w.get("Lock") or 0))


def safe():
    g = time.gmtime()
    hm = g.tm_hour * 100 + g.tm_min
    return 6 <= g.tm_min <= 54 and not (330 <= hm <= 430) and not (1530 <= hm <= 1630)


def market(p, side, qty, q0):
    r = c.place_order(p, side, fmt(qty), "MARKET")
    q1 = quotes().get(p)
    px = Decimal(str(r.get("FilledAverPrice") or 0))
    b, a, l = q0
    out("market", pair=p, side=side, qty=fmt(qty), before=[str(x) for x in q0], after=[str(x) for x in q1 or ()],
        fill=str(px), at_bid=px == b, at_ask=px == a, at_last=px == l, role=r.get("Role"), status=r.get("Status"),
        fee=r.get("CommissionChargeValue"), fee_coin=r.get("CommissionCoin"))
    return r


start = {p: coin(p) for p in PAIRS}
out("start", coins={p: str(v) for p, v in start.items()})
n_buy = n_sell = 0
t_end = time.time() + 40 * 60
try:
    while time.time() < t_end and (n_buy < 3 or n_sell < 3):
        if not safe():
            time.sleep(20)
            continue
        qs = quotes()
        for p, (b, a, l) in qs.items():
            one_tick = a - b == step[p]
            if n_buy < 3 and one_tick and l == b and bought[p] == 0:
                market(p, "BUY", truncate(USD / a, rules[p].amount_precision), (b, a, l))
                bought[p] = coin(p) - start[p]
                n_buy += 1
                break
            if n_sell < 3 and one_tick and l == a and bought[p] > 0:
                qty = truncate(bought[p], rules[p].amount_precision)
                market(p, "SELL", qty, (b, a, l))
                bought[p] = coin(p) - start[p]
                n_sell += 1
                break
        time.sleep(9)
finally:
    for p in PAIRS:
        try:
            left = truncate(coin(p) - start[p], rules[p].amount_precision)
            if left > 0:
                market(p, "SELL", left, quotes().get(p))
        except Exception as e:                                     # noqa: BLE001 - keep going: flat matters more
            out("error", pair=p, error=str(e)[:200])
    try:
        sto = coin("STO/USD")
        if sto >= LEFTOVER_STO:                                    # yesterday's experiment left this
            market("STO/USD", "SELL", LEFTOVER_STO, quotes().get("STO/USD"))
    except Exception as e:                                         # noqa: BLE001
        out("error", pair="STO/USD leftover", error=str(e)[:200])
    out("end", coins={p: str(coin(p)) for p in PAIRS})
