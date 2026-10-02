"""Exchange self-check: proves signing, clock, fills, fees and shorts with the TEST key before going live.

    python -m src.live.selfcheck            public checks, plus signed read-only checks if .env holds the TEST key
    python -m src.live.selfcheck --orders   also place tiny test orders (TEST key only)

Refuses every signed call when ROOSTOO_ENV=competition: the competition key is used only by the running bot.
Writes reports/selfcheck/<YYYYMMDD-HHMM>.md (commit it) and .log (never committed). Keys are never printed.
"""
from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timezone

from src.api.client import RoostooClient, RoostooError, load_credentials
from src.api.rules import fmt, parse_exchange_info, quantity_for, truncate
from src.config import REPO_ROOT, load_config, universe

ORDER_USD = 20.0   # size of each test order


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--orders", action="store_true", help="place tiny test orders (TEST key only)")
    ap.add_argument("--pair", default="BTC/USD")
    a = ap.parse_args(argv)
    cfg = load_config()
    ex = cfg["execution"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    out = REPO_ROOT / "reports" / "selfcheck"
    out.mkdir(parents=True, exist_ok=True)
    md, lg = out / f"{stamp}.md", out / f"{stamp}.log"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(lg), logging.StreamHandler()])
    log = logging.getLogger("selfcheck")
    rows: list[tuple[str, str, str]] = []

    def check(name: str, fn):
        try:
            detail = fn()
            rows.append((name, "PASS", detail))
            log.info("%s: PASS %s", name, detail)
        except Exception as e:  # noqa: BLE001 -- every failure is reported, none stops the other checks
            rows.append((name, "FAIL", f"{type(e).__name__}: {e}"))
            log.warning("%s: FAIL %s: %s", name, type(e).__name__, e)

    try:
        creds = load_credentials(REPO_ROOT / ex["env_file"])
    except RoostooError as e:
        creds = None
        log.info("no usable credentials (%s); running public checks only", e)
    if creds is not None and creds.env == "competition":
        rows.append(("credentials", "REFUSED", "ROOSTOO_ENV=competition: the competition key is used only by the bot"))
        creds = None
    client = RoostooClient(cfg["exchange"]["base_url"], creds, ex["calls_per_minute"], ex["timeout_s"], log=log)
    state: dict = {}

    def clock():
        off = client.sync_clock()
        if abs(off) > 30_000:
            raise RoostooError(f"local clock is {off / 1000:+.1f} s off the server (limit 60 s); offset will be applied")
        return f"offset {off / 1000:+.2f} s (applied to every signed request)"
    check("server time and clock offset", clock)

    def info():
        state["rules"] = parse_exchange_info(client.exchange_info())
        mine = set(universe(cfg))
        missing = sorted(mine - set(state["rules"]))
        return f"{len(state['rules'])} pairs listed; config universe missing on exchange: {missing or 'none'}"
    check("exchangeInfo vs config universe", info)

    def ticker():
        t = client.ticker()
        state["ticker"] = t
        quoted = [p for p in universe(cfg) if p in t and t[p].get("MaxBid")]
        return f"{len(t)} pairs quoted; {len(quoted)}/{len(universe(cfg))} of the config universe"
    check("ticker coverage", ticker)

    if creds is not None:
        check("signed balance", lambda: f"{len(client.balance())} wallet entries (values not logged)")
        check("pending orders", lambda: f"{client.pending_count().get('TotalPending', 0)} pending")
        check("order history query", lambda: f"{len(client.query_order(limit=5))} recent orders")
        check("short positions", lambda: f"{len(client.short_positions())} open shorts")

    if a.orders:
        if creds is None or creds.env != "test":
            rows.append(("test orders", "SKIPPED", "needs ROOSTOO_ENV=test and the test key in .env"))
        else:
            rule = state.get("rules", {}).get(a.pair)
            q = client.ticker(a.pair)[a.pair]
            qty = quantity_for(ORDER_USD, q["MinAsk"], rule)

            def buy_sell():
                b = client.place_order(a.pair, "BUY", fmt(qty))
                s = client.place_order(a.pair, "SELL", fmt(truncate(b.get("FilledQuantity", qty), rule.amount_precision)))
                return (f"BUY role={b.get('Role')} fee%={b.get('CommissionPercent', 0)} avg={b.get('FilledAverPrice')} "
                        f"(ask was {q['MinAsk']}); SELL role={s.get('Role')} fee%={s.get('CommissionPercent', 0)} "
                        f"avg={s.get('FilledAverPrice')} (bid was {q['MaxBid']})")
            check("market buy then sell", buy_sell)

            def limit_rest_cancel():
                price = truncate(q["MaxBid"] * 0.97, rule.price_precision)
                o = client.place_order(a.pair, "BUY", fmt(qty), "LIMIT", fmt(price))
                time.sleep(2)
                pend = client.query_order(order_id=o.get("OrderID"))
                cancelled = client.cancel_order(order_id=o.get("OrderID"))
                return (f"resting limit 3% below bid: status={o.get('Status')} role={o.get('Role')}; "
                        f"query shows {pend[0].get('Status') if pend else '?'}; cancelled {cancelled}")
            check("limit order rests and cancels", limit_rest_cancel)

            def shorts():
                o = client.short_open(a.pair, "10")
                pos = client.short_positions()
                c = client.short_close(a.pair)
                return (f"open: status={o.get('Status')} fee={o.get('OpenFee', 0)}; positions={len(pos)}; "
                        f"close: pnl={c.get('RealizedPNL', 0)} fee={c.get('CloseFee', 0)} fully={c.get('FullyClosed')}")
            check("short open and close ($10)", shorts)

    lines = ["# Exchange self-check", "",
             f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC · credentials: {creds.env if creds else 'none (public checks only)'} · "
             f"test orders: {'yes' if a.orders and creds and creds.env == 'test' else 'no'}", "",
             "| Check | Result | Detail |", "|---|---|---|"]
    lines += [f"| {n} | {r} | {d} |" for n, r, d in rows]
    md.write_text("\n".join(lines) + "\n")
    log.info("report: %s", md)
    return 0 if all(r in ("PASS", "SKIPPED") for _, r, _ in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
