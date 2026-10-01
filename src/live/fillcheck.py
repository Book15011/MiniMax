"""Fill-size check on the TEST account: do bigger market orders fill worse on Roostoo?

    python -m src.live.fillcheck [--pair BTC/USD] [--sizes 100,1000,10000] [--env-file PATH]

For each size: read the ticker, market-BUY that many USD of the pair, read the fill from the order response and
query_order, then market-SELL the same quantity back. Reports each fill against the bid/ask seen just before it
(slippage in bps) and the fee charged. Refuses unless ROOSTOO_ENV=test. Writes reports/fillcheck/<stamp>.md
(commit it) and .log (never committed). Orders are never retried; an unknown outcome stops the run.
"""
from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timezone

from src.api.client import OrderStateUnknown, RoostooClient, load_credentials
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pair", default="BTC/USD")
    ap.add_argument("--sizes", default="100,1000,10000", help="USD per test order, comma-separated")
    ap.add_argument("--env-file", default=None, help="key file (default: execution.env_file)")
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
