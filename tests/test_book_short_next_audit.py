"""Independent audit arithmetic tests written before implementation."""
from decimal import Decimal
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prefix_audit", ROOT / "research/book/short_next_audit/audit.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def event(action, q, p, fee):
    return {"action":action,"asset":"BTC","quantity":str(q),"price_usd":str(p),"fee":str(fee)}


def test_signed_cash_for_long_and_short_roundtrips():
    cash,longs,shorts = module.account_events([
        event("Buy Long",2,100,.2),event("Sell Long",1,110,.11),
        event("Open Short",3,90,.27),event("Cover Short",1,80,.08)],1000)
    assert cash == Decimal("1099.34")
    assert longs == {"BTC":Decimal("1")}
    assert shorts == {"BTC":Decimal("2")}


def test_duplicate_conflicts_quarantine_all_rows_and_exact_repeats_collapse():
    import pandas as pd
    q=pd.DataFrame({"ts_utc":["2026-10-05T00:00Z"]*5,
                    "pair":["BTC/USD"]*2+["ETH/USD"]*3,
                    "max_bid":[1,1,2,2,3],"min_ask":[1.1,1.1,2.1,2.1,3.1],
                    "last_price":[1,1,2,2,3]})
    kept,bad=module.canonical_quotes(q)
    assert kept.pair.tolist() == ["BTC/USD"]
    assert len(bad) == 3


def test_closed_missing_position_fails():
    import pytest
    with pytest.raises(AssertionError):
        module.account_events([event("Cover Short",1,100,.1)],1000)
