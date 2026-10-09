from decimal import Decimal
import pandas as pd
import pytest
from src.execution.planner import Holdings, Quote
from src.validation.short_competition import QuoteBook, replay_targets, observed_path, hourly_archives

def prices(start="2026-10-04T12:00Z", end="2026-10-04T15:00Z", price=100.):
    idx=pd.date_range(start,end,freq="min")
    return pd.DataFrame({"BTCUSDT":price},index=idx)

def settings():
    return dict(assets=["BTC"],seed=100.,fee=.001,band=0.,min_order=1.,cash_buffer=0.,
                precisions={"BTC":6},price_precisions={"BTC":2},minute_max_age=120,
                quote_max_age=30,proxy_half_spread=0.,order_spacing_seconds=0,
                start="2026-10-04T12:00Z",end="2026-10-04T15:00Z")

def empty_quotes():
    return pd.DataFrame(columns=["ts_utc","pair","max_bid","min_ask","last_price"])

def test_quote_lookup_never_uses_future_and_rejects_stale_archive():
    p=prices(end="2026-10-04T12:02Z")
    q=pd.DataFrame(dict(ts_utc=pd.to_datetime(["2026-10-04T12:00:59Z","2026-10-04T12:01:01Z"]),
                        pair=["BTC/USD"]*2,max_bid=[99.,999.],min_ask=[101.,1001.],last_price=[100.,1000.]))
    book=QuoteBook(p,q,settings())
    quotes,meta=book.at(pd.Timestamp("2026-10-04T12:01Z"))
    assert quotes["BTC/USD"]==Quote(99.,101.)
    assert meta["BTC/USD"]["quote_time"]=="2026-10-04 12:00:59+00:00"
    assert book.at(pd.Timestamp("2026-10-04T12:05Z"))[0] is None

def test_hourly_source_requires_sixty_completed_minutes():
    ts=pd.date_range("2026-10-04T12:01Z",periods=60,freq="min")
    a=pd.DataFrame(dict(timestamp=ts,symbol="BTCUSDT",close=range(100,160),quote_volume=2.))
    h,v=hourly_archives(a)
    assert h.loc[pd.Timestamp("2026-10-04T13:00Z"),"BTCUSDT"]==159
    assert v.iloc[0,0]==120
    h,v=hourly_archives(a.iloc[:-1])
    assert pd.isna(h.iloc[0,0]) and pd.isna(v.iloc[0,0])

def test_replay_uses_one_hour_lag_and_does_not_force_first_long():
    c=settings();book=QuoteBook(prices(),empty_quotes(),c)
    t=pd.Timestamp("2026-10-04T13:00Z")
    e,p,d,f,cycles,end=replay_targets({t:pd.Series({"BTCUSDT":-.5})},book,c,60)
    normal=e[e.phase=="strategy"]
    assert normal.iloc[0].action=="Open Short"
    assert normal.iloc[0].time_utc==t+pd.Timedelta(hours=1)
    assert normal.iloc[0].fee==pytest.approx(.05)
    assert p.iloc[0].equity==100.
    assert end["marked_equity"]==pytest.approx(99.95)
    assert end["liquidated_equity"]==pytest.approx(99.9)
    assert len(f)==0
    assert len(cycles)==1 and cycles[0]["status"]=="censored"

def test_terminal_fee_charged_once_and_real_bidask_used():
    c=settings()
    q=pd.DataFrame(dict(ts_utc=pd.to_datetime(["2026-10-04T14:00Z","2026-10-04T15:00Z"]),
                        pair=["BTC/USD"]*2,max_bid=[99.,99.],min_ask=[101.,101.],last_price=[100.,100.]))
    book=QuoteBook(prices(),q,c)
    e,p,d,f,cycles,end=replay_targets({pd.Timestamp("2026-10-04T13:00Z"):pd.Series({"BTCUSDT":.5})},book,c,60)
    strategy=e[e.phase=="strategy"].iloc[0]
    assert strategy.price_usd==101.
    qty=strategy.quantity
    assert end["marked_equity"]==pytest.approx(100-qty*101*1.001+qty*99)
    assert end["liquidated_equity"]==pytest.approx(100-qty*101*1.001+qty*99*.999)
    assert len(e[e.phase=="terminal"])==1

def test_literal_observed_ledger_retains_negative_cash_and_fee_override():
    c=settings()
    ev=pd.DataFrame([dict(trade_id="T001",time_utc=pd.Timestamp("2026-10-04T13:00Z"),asset="BTC",action="Buy Long",price_usd=100.,quantity=1.)])
    e,p,m,cycles=observed_path(ev,QuoteBook(prices(),empty_quotes(),c),c,{"T001":.11})
    assert m["minimum_signed_cash"]==pytest.approx(-.11)
    assert m["fees"]==pytest.approx(.11)
    assert m["marked_equity"]==pytest.approx(99.89)
    assert m["liquidated_equity"]==pytest.approx(99.79)

def test_completed_short_cycle_counts_net_entry_exit_fees_not_forced_terminal():
    c=settings();book=QuoteBook(prices(),empty_quotes(),c)
    w={pd.Timestamp("2026-10-04T12:00Z"):pd.Series({"BTCUSDT":-.5}),
       pd.Timestamp("2026-10-04T13:00Z"):pd.Series(dtype=float)}
    e,p,d,f,cycles,end=replay_targets(w,book,c,60)
    done=[x for x in cycles if x["status"]=="completed"]
    assert len(done)==1 and done[0]["net_pnl"]==pytest.approx(-.1)
    assert not done[0]["profitable"]
