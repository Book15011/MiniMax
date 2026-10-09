from decimal import Decimal
import pandas as pd
import pytest
from src.validation.observed_baseline import (ledger,match_events,truncate_quantity,signal_weights,simulate,closed_minutes)

def test_ledger_long_short_and_fees():
    e=pd.DataFrame([dict(asset="BTC",action="Buy Long",quantity=2,price_usd=10),
                    dict(asset="BTC",action="Sell Long",quantity=1,price_usd=12),
                    dict(asset="BTC",action="Open Short",quantity=1,price_usd=12),
                    dict(asset="BTC",action="Cover Short",quantity=.5,price_usd=8)])
    r=ledger(e,100,.001)
    assert r[-1]["gross_realized"]==pytest.approx(4)
    assert r[-1]["fees"]==pytest.approx(.048)
    assert r[-1]["equity_at_marks"]==pytest.approx(103.952)
    assert r[-1]["long"]["BTC"]==1
    assert r[-1]["short"]["BTC"]==.5

def test_ledger_refuses_to_invent_missing_positions():
    with pytest.raises(ValueError):
        ledger(pd.DataFrame([dict(asset="BTC",action="Sell Long",quantity=1,price_usd=10)]),100,.001)

def test_truncate_never_rounds_up():
    assert truncate_quantity(1.239,2)==Decimal("1.23")
    with pytest.raises(ValueError):truncate_quantity(-1,2)

def test_one_to_one_global_matching_and_missing_time():
    t=pd.Timestamp("2026-10-06T01:04Z")
    obs=pd.DataFrame([dict(asset="BTC",action="Buy Long",quantity=1,time_utc=t),
                      dict(asset="BTC",action="Buy Long",quantity=1,time_utc=t+pd.Timedelta(seconds=120)),
                      dict(asset="BTC",action="Buy Long",quantity=1,time_utc=pd.NaT)])
    pred=pd.DataFrame([dict(asset="BTC",action="Buy Long",quantity=1,time_utc=t+pd.Timedelta(seconds=119)),
                       dict(asset="BTC",action="Buy Long",quantity=1,time_utc=t)])
    m=match_events(obs,pred,60,.05)
    assert m["matched"]==2 and m["recall"]==pytest.approx(2/3) and m["precision"]==1

def test_match_penalizes_extra_and_quantity():
    t=pd.Timestamp("2026-10-06T01:04Z")
    obs=pd.DataFrame([dict(asset="BTC",action="Buy Long",quantity=1,time_utc=t)])
    pred=pd.DataFrame([dict(asset="BTC",action="Buy Long",quantity=1.1,time_utc=t)]*2)
    assert match_events(obs,pred,120,.05)["matched"]==0

def test_signals_causal_and_bounded():
    idx=pd.date_range("2026-10-01",periods=72,freq="h",tz="UTC")
    p=pd.DataFrame({"BTCUSDT":range(100,172),"ETHUSDT":range(172,100,-1)},index=idx)
    cfg=dict(family="momentum",lookback=24,scale="raw",clip=1,gross=.98)
    w=signal_weights(p,idx[-2],cfg)
    p.iloc[-1]=100000
    assert signal_weights(p,idx[-2],cfg).equals(w)
    assert w.iloc[0]>0 and w.iloc[1]<0 and w.abs().sum()<=.98+1e-10

def test_minute_closes_not_open_clock():
    q=pd.DataFrame({"ts_utc":pd.to_datetime(["2026-10-06T01:00:59Z","2026-10-06T01:01:01Z"]),
                    "pair":["BTC/USD"]*2,"last_price":[10,11]})
    d=closed_minutes(q)
    assert d.loc[pd.Timestamp("2026-10-06T01:01Z"),"BTCUSDT"]==10
    assert d.loc[pd.Timestamp("2026-10-06T01:02Z"),"BTCUSDT"]==11

def test_simulator_no_future_prices_no_leverage_or_negative_cash():
    idx=pd.date_range("2026-10-04T12:00Z",periods=1500,freq="min")
    p=pd.DataFrame({"BTCUSDT":100.0,"ETHUSDT":100.0},index=idx)
    cfg=dict(family="momentum",lookback=6,scale="sign",clip=1,gross=1,initial_equal=True,
             first_decision="2026-10-05T01:00Z",decision_hour=1,delay_minutes=3,band=0,fee=.001,
             seed=100000,precisions={"BTC":5,"ETH":4},min_order=1,proxy_half_spread=.0001)
    e,path=simulate(p,cfg)
    assert (path.cash>=-1e-8).all()
    assert (path.gross/path.equity<=1+1e-9).all()
    assert e.time_utc.min()>=pd.Timestamp(cfg["first_decision"])+pd.Timedelta(minutes=1)

def test_causal_replay_future_mutation_does_not_change_earlier_fills():
    idx=pd.date_range("2026-09-28T00:00Z", "2026-10-07T01:15Z",freq="min")
    p=pd.DataFrame({"BTCUSDT":100+pd.Series(range(len(idx))).to_numpy()*.0001},index=idx)
    cfg=dict(family="momentum",lookback=6,scale="sign",clip=1,gross=.98,initial_equal=True,
             first_decision="2026-10-05T01:00Z",start="2026-10-04T12:00Z",end="2026-10-07T01:15Z",
             decision_hour=1,delay_minutes=3,band=0,fee=.001,seed=100000,
             precisions={"BTC":5},min_order=1,proxy_half_spread=.0001)
    e1,_=simulate(p,cfg)
    future=p.index>pd.Timestamp("2026-10-06T01:04Z")
    p.loc[future]=1000000
    e2,_=simulate(p,cfg)
    pd.testing.assert_frame_equal(e1[e1.time_utc<=pd.Timestamp("2026-10-06T01:04Z")].reset_index(drop=True),
                                  e2[e2.time_utc<=pd.Timestamp("2026-10-06T01:04Z")].reset_index(drop=True))

def test_flip_closes_long_before_short_and_respects_capital():
    idx=pd.date_range("2026-10-04T12:00Z","2026-10-06T01:15Z",freq="min")
    p=pd.DataFrame({"BTCUSDT":100.},index=idx)
    cfg=dict(family="momentum",lookback=6,scale="sign",clip=1,gross=1,initial_equal=True,
             first_decision="2026-10-05T01:00Z",decision_hour=1,delay_minutes=3,band=0,fee=.001,
             seed=100000,precisions={"BTC":5},min_order=1,proxy_half_spread=.0001,end="2026-10-06T01:15Z")
    weights={pd.Timestamp("2026-10-06T01:00Z"):pd.Series({"BTCUSDT":-1.})}
    ev,path=simulate(p,cfg,weights=weights)
    assert ev.action.tolist()==["Buy Long","Sell Long","Open Short"]
    assert (path.gross<=path.equity+1e-8).all()
    assert path.iloc[-1].BTC<0

def test_recorded_quote_used_only_at_or_before_execution():
    idx=pd.date_range("2026-10-04T12:00Z","2026-10-05T01:10Z",freq="min")
    p=pd.DataFrame({"BTCUSDT":100.},index=idx)
    cfg=dict(family="momentum",lookback=6,scale="sign",clip=1,gross=.9,initial_equal=True,
             first_decision="2026-10-05T01:00Z",decision_hour=1,delay_minutes=3,band=0,fee=.001,
             seed=100000,precisions={"BTC":5},min_order=1,proxy_half_spread=.0001)
    q=pd.DataFrame(dict(ts_utc=pd.to_datetime(["2026-10-05T01:02:59Z","2026-10-05T01:03:01Z"]),
                        pair=["BTC/USD"]*2,max_bid=[99.99,999],min_ask=[100.01,1000]))
    ev,_=simulate(p,cfg,q)
    assert ev.iloc[0].price_usd==100.01 and ev.iloc[0].source=="recorded_roostoo"

def test_bounded_signal_retains_cash_for_weak_conviction():
    idx=pd.date_range("2026-10-01",periods=72,freq="h",tz="UTC")
    p=pd.DataFrame({"BTCUSDT":100*(1.00001**pd.Series(range(72)).to_numpy())},index=idx)
    cfg=dict(family="momentum",lookback=6,scale="raw",clip=.01,gross=1,allocation="bounded")
    assert 0<signal_weights(p,idx[-1],cfg).abs().sum()<.01

def test_shared_broker_locks_collateral_instead_of_crediting_short_sale():
    from src.validation.observed_baseline import broker_replay
    idx=pd.date_range("2026-10-04T12:00Z","2026-10-05T01:15Z",freq="min")
    p=pd.DataFrame({"BTCUSDT":100.},index=idx)
    cfg=dict(assets=["BTC"],start="2026-10-04T12:00Z",end="2026-10-05T01:15Z",
             first_decision="2026-10-05T01:00Z",decision_hour=1,delay_minutes=3,band=0,fee=.001,
             seed=100000,precisions={"BTC":5},min_order=1,proxy_half_spread=.0001,
             minute_max_age=120,quote_max_age=30,initial_equal=False,cash_buffer=.001,order_spacing_seconds=10)
    wt={pd.Timestamp(cfg["first_decision"]):pd.Series({"BTCUSDT":-.9})}
    q=pd.DataFrame(columns=["ts_utc","pair","max_bid","min_ask"])
    ev,path,_=broker_replay(p,cfg,q,wt)
    assert ev.action.tolist()==["Open Short"]
    assert 9900<path.iloc[-1].cash<10000
    assert path.iloc[-1].locked_collateral==pytest.approx(90000)
    assert path.iloc[-1].equity<100000 and path.iloc[-1].gross<path.iloc[-1].equity
