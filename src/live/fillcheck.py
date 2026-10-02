"""Fill checks on the TEST account: do bigger market orders fill worse, and do limit (maker) orders fill at all?

    python -m src.live.fillcheck [--pair BTC/USD] [--sizes 100,1000,10000] [--env-file PATH]
    python -m src.live.fillcheck --limit [--wait 300] [--sizes 100,1000]     maker test (see below)

For each size: read the ticker, market-BUY that many USD of the pair, read the fill from the order response and
query_order, then market-SELL the same quantity back. Reports each fill against the bid/ask seen just before it
(slippage in bps) and the fee charged. Refuses unless ROOSTOO_ENV=test. Writes reports/fillcheck/<stamp>.md
(commit it) and .log (never committed). Orders are never retried; an unknown outcome stops the run.

--limit: the maker question (0.05% instead of 0.1% per trade would save about a fifth of a percent per 14 days at
our turnover). For each size: a LIMIT BUY at the best bid, polled every --poll seconds for up to --wait seconds, then
cancelled if still open; whatever filled is sold back with a LIMIT SELL at the best ask the same way, and any
remainder with a market SELL, so the account ends flat. Reports the role, seconds to fill, fill vs the mid at
placement, and the fee rate actually charged.
"""
from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timezone

from src.api.client import OrderStateUnknown, RoostooClient, load_credentials
from decimal import ROUND_DOWN, ROUND_UP, Decimal

from src.api.rules import fmt, parse_exchange_info, quantity_for
from src.config import REPO_ROOT, load_config


def bps(fill: float, ref: float, side: str) -> float:
    """Cost of the fill against the quote it should have met: positive = worse than the quote."""
    return (fill / ref - 1) * 1e4 if side == "BUY" else (1 - fill / ref) * 1e4


def fill_of(resp: dict) -> tuple[float, float, float]:
    """(average price, quantity, fee) from an OrderDetail. Field names follow the API docs; missing means 0."""
    price = float(resp.get("FilledAverPrice") or resp.get("Price") or 0.0)
    qty = float(resp.get("FilledQuantity") or resp.get("Quantity") or 0.0)
    fee = float(resp.get("CommissionChargeValue") or 0.0)
    return price, qty, fee


def passive_price(x: float, places: int, side: str) -> Decimal:
    """Our side of the book at the pair's precision, never crossing it: bids round down, asks round up."""
    return Decimal(str(x)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_DOWN if side == "BUY" else ROUND_UP)


def wait_fill(c: RoostooClient, oid, wait_s: float, poll_s: float) -> tuple[dict, float | None]:
    """Poll one order until it is FILLED or CANCELED, or wait_s passes (then the seconds are None)."""
    t0, last = time.time(), {}
    while True:
        rows = c.query_order(order_id=oid)
        last = rows[0] if rows else last
        if str(last.get("Status", "")).upper() in ("FILLED", "CANCELED", "CANCELLED"):
            return last, time.time() - t0
        if time.time() - t0 >= wait_s:
            return last, None
        time.sleep(poll_s)


def limit_leg(c: RoostooClient, rule, pair: str, side: str, qty: Decimal, wait_s: float, poll_s: float,
              log: logging.Logger) -> dict:
    """One passive LIMIT order, waited for, cancelled if still open. Returns what happened."""
    q = c.ticker(pair)[pair]
    bid, ask = float(q["MaxBid"]), float(q["MinAsk"])
    px = passive_price(bid if side == "BUY" else ask, rule.price_precision, side)
    resp = c.place_order(pair, side, fmt(qty), "LIMIT", fmt(px))
    oid, role = resp.get("OrderID"), str(resp.get("Role", ""))
    if str(resp.get("Status", "")).upper() == "FILLED":
        detail, secs = resp, 0.0
    else:
        detail, secs = wait_fill(c, oid, wait_s, poll_s)
        if secs is None:
            c.cancel_order(order_id=oid)
            rows = c.query_order(order_id=oid)
            detail = rows[0] if rows else detail
    price, filled, fee = fill_of(detail) if float(detail.get("FilledQuantity") or 0) > 0 else (0.0, 0.0, 0.0)
    filled = float(detail.get("FilledQuantity") or 0.0)
    mid = (bid + ask) / 2
    row = {"side": side, "bid": bid, "ask": ask, "limit": float(px), "role": role or str(detail.get("Role", "")),
           "status": str(detail.get("Status", "")).upper(), "secs": secs, "price": price, "qty": filled, "fee": fee,
           "fee_rate": fee / (price * filled) if price and filled else None,
           "vs_mid_bps": bps(price, mid, side) if price else None}
    log.info("LIMIT %s %s %s @ %s: %s, role %s, %s s, filled %s at %s, fee %s", side, fmt(qty), pair, fmt(px),
             row["status"], row["role"], "-" if secs is None else f"{secs:.0f}", filled, price, fee)
    return row


def limit_check(c: RoostooClient, rule, pair: str, sizes: list[float], wait_s: float, poll_s: float,
                log: logging.Logger) -> list[str]:
    rows = []
    for usd in sizes:
        q = c.ticker(pair)[pair]
        qty = quantity_for(usd, float(q["MaxBid"]), rule)
        try:
            buy = limit_leg(c, rule, pair, "BUY", qty, wait_s, poll_s, log)
            rows.append((usd, buy))
            held = truncate_qty(buy["qty"], rule.amount_precision)
            if held > 0:
                sell = limit_leg(c, rule, pair, "SELL", held, wait_s, poll_s, log)
                rows.append((usd, sell))
                rest = held - truncate_qty(sell["qty"], rule.amount_precision)
                if rest > 0:
                    resp = c.place_order(pair, "SELL", fmt(rest))
                    log.info("market SELL of the unfilled %s: %s", fmt(rest), resp.get("Status"))
        except OrderStateUnknown as e:
            log.error("order outcome unknown, stopping: %s", e)
            break
        time.sleep(3)
    lines = [f"| Size (USD) | Side | Bid / ask at placement | Limit | Role | Status | Seconds to fill | Fill | Fee rate | vs mid (bps) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for usd, r in rows:
        secs = "—" if r["secs"] is None else f"{r['secs']:.0f}"
        rate = "—" if r["fee_rate"] is None else f"{r['fee_rate']:.4%}"
        vs = "—" if r["vs_mid_bps"] is None else f"{r['vs_mid_bps']:+.2f}"
        lines.append(f"| {usd:,.0f} | {r['side']} | {r['bid']:.6g} / {r['ask']:.6g} | {r['limit']:.6g} | {r['role'] or '—'} | "
                     f"{r['status']} | {secs} | {r['price'] or '—'} | {rate} | {vs} |")
    n_fill = sum(1 for _, r in rows if r["status"] == "FILLED")
    lines += ["", f"{n_fill} of {len(rows)} limit orders filled within {wait_s:.0f} s. Negative 'vs mid' = better than the mid "
              "(a maker earns about half the spread). Fee rate is the commission over the filled notional."]
    return lines


def truncate_qty(x: float, places: int) -> Decimal:
    return Decimal(str(x)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_DOWN)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pair", default="BTC/USD")
    ap.add_argument("--sizes", default="100,1000,10000", help="USD per test order, comma-separated")
    ap.add_argument("--env-file", default=None, help="key file (default: execution.env_file)")
    ap.add_argument("--limit", action="store_true", help="maker test: passive LIMIT orders instead of market orders")
    ap.add_argument("--wait", type=float, default=300.0, help="--limit: seconds to wait for a fill before cancelling")
    ap.add_argument("--poll", type=float, default=15.0, help="--limit: seconds between order queries")
    a = ap.parse_args(argv)
    cfg = load_config()
    ex = cfg["execution"]
    creds = load_credentials(a.env_file or (REPO_ROOT / ex["env_file"]))
    if creds.env != "test":
        raise SystemExit("fillcheck runs only with ROOSTOO_ENV=test (the competition key is used only by the bot)")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    out = REPO_ROOT / "reports" / "fillcheck"
    out.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(out / f"{stamp}.log"), logging.StreamHandler()])
    log = logging.getLogger("fillcheck")
    c = RoostooClient(cfg["exchange"]["base_url"], creds, ex["calls_per_minute"], ex["timeout_s"], log=log)
    log.info("clock offset %+.0f ms", c.sync_clock())
    rule = parse_exchange_info(c.exchange_info())[a.pair]
    if a.limit:
        lines = [f"# Limit (maker) fill check, {a.pair}, TEST account ({stamp} UTC)", ""]
        lines += limit_check(c, rule, a.pair, [float(x) for x in a.sizes.split(",")], a.wait, a.poll, log)
        (out / f"{stamp}-limit.md").write_text("\n".join(lines) + "\n")
        log.info("report: %s", out / f"{stamp}-limit.md")
        return 0
    rows = []
    for usd in [float(x) for x in a.sizes.split(",")]:
        for side in ("BUY", "SELL"):
            q = c.ticker(a.pair)[a.pair]
            bid, ask = float(q["MaxBid"]), float(q["MinAsk"])
            ref = ask if side == "BUY" else bid
            if side == "BUY":
                qty = quantity_for(usd, ask, rule)
            t0 = time.time()
            try:
                resp = c.place_order(a.pair, side, fmt(qty))
            except OrderStateUnknown as e:
                log.error("order outcome unknown, stopping: %s", e)
                rows.append((usd, side, ref, None, None, None, None, "UNKNOWN"))
                break
            price, filled, fee = fill_of(resp)
            status = str(resp.get("Status", "")).upper()
            rows.append((usd, side, ref, price, filled, fee, bps(price, ref, side) if price else None, status))
            log.info("%s $%.0f %s: status %s, fill %.6g vs quote %.6g, qty %s, fee %.4f, %.2f s", side, usd, a.pair, status,
                     price, ref, filled, fee, time.time() - t0)
            time.sleep(3)
    lines = [f"# Fill-size check, {a.pair}, TEST account ({stamp} UTC)", "",
             "| Size (USD) | Side | Quote before | Fill | Quantity | Fee | Cost vs quote (bps) | Status |", "|---|---|---|---|---|---|---|---|"]
    for usd, side, ref, price, filled, fee, cost, status in rows:
        lines.append(f"| {usd:,.0f} | {side} | {ref:.6g} | {price if price else '—'} | {filled if filled else '—'} | "
                     f"{fee if fee is not None else '—'} | {f'{cost:+.2f}' if cost is not None else '—'} | {status} |")
    lines += ["", "Positive cost = filled worse than the quote seen just before sending. Each BUY is sold back at once."]
    (out / f"{stamp}.md").write_text("\n".join(lines) + "\n")
    log.info("report: %s", out / f"{stamp}.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
