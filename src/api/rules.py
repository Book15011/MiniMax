"""Per-pair trading rules from /v3/exchangeInfo, and exact decimal rounding for order fields.

Quantities and prices are truncated (never rounded up) to the pair's precision with Decimal, and sent as plain
decimal strings: str(float) can produce '1e-05', which the exchange rejects.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal


@dataclass(frozen=True)
class PairRule:
    pair: str                 # e.g. "BTC/USD"
    price_precision: int
    amount_precision: int
    min_order: Decimal        # minimum price * quantity (MiniOrder)
    can_trade: bool = True


def parse_exchange_info(info: dict) -> dict[str, PairRule]:
    out = {}
    for pair, r in (info.get("TradePairs") or {}).items():
        out[pair] = PairRule(pair, int(r.get("PricePrecision", 2)), int(r.get("AmountPrecision", 0)),
                             Decimal(str(r.get("MiniOrder", 1))), bool(r.get("CanTrade", True)))
    return out


def truncate(x, places: int) -> Decimal:
    """Truncate toward zero to `places` decimals (0.29 stays 0.29; floats go through str to avoid binary noise)."""
    step = Decimal(1).scaleb(-places)
    return Decimal(str(x)).quantize(step, rounding=ROUND_DOWN)


def fmt(d: Decimal) -> str:
    """Plain decimal string, never scientific notation."""
    s = format(d, "f")
    return s


def quantity_for(value_usd: float, price: float, rule: PairRule) -> Decimal:
    """Largest quantity (at the pair's precision) whose value does not exceed value_usd."""
    if price <= 0:
        return Decimal(0)
    return truncate(Decimal(str(value_usd)) / Decimal(str(price)), rule.amount_precision)


def meets_minimum(qty: Decimal, price: float, rule: PairRule, min_usd: float = 0.0) -> bool:
    notional = qty * Decimal(str(price))
    return qty > 0 and notional >= rule.min_order and notional >= Decimal(str(min_usd))
