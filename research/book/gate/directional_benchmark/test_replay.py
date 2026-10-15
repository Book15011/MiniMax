from research.book.gate.directional_benchmark.replay import simulate
def cfg():
 return {"paper_starting_equity":2000,"maximum_quote_age_seconds":12,"max_process_calls_per_minute":20,
 "sampled_public_calls_per_minute":10,"reserve_exit_calls":3,"entry_ttl_seconds":12,"minimum_order_usd":1,
 "maker_fee":.0005,"taker_fee":.001,"cooldown_seconds":60,"hold_seconds":600}
def test_signal_must_wait_for_next_observed_quote():
 r=simulate([0,6,12],[[99],[100],[101]],[[100],[101],[102]],["BTC"],{0:{"BTC":.5}},{"BTC/USD":{"AmountPrecision":4}},cfg())
 assert r["fills"][0]["time"]==6 and r["fills"][0]["price"]=="101.0" and r["actual_orders"]==0
def test_passive_entry_waits_for_ask_and_charges_role():
 r=simulate([0,6,12,18],[[99],[99],[98],[100]],[[100],[100],[99],[101]],["BTC"],{0:{"BTC":.5}},{"BTC/USD":{"AmountPrecision":4}},cfg(),maker=True)
 assert r["fills"][0]["time"]==12 and r["fills"][0]["role"]=="RESTING" and r["maker_fills"]==1
def test_crossing_limit_on_arrival_is_taker():
 r=simulate([0,6,12],[[99],[98],[100]],[[100],[99],[101]],["BTC"],{0:{"BTC":.5}},{"BTC/USD":{"AmountPrecision":4}},cfg(),maker=True)
 assert r["fills"][0]["role"]=="TAKER" and r["maker_fills"]==0
def test_missing_target_is_not_silently_profitable():
 r=simulate([0,6],[[99],[99]],[[100],[100]],["BTC"],{0:{"ETH":.5}},{"BTC/USD":{"AmountPrecision":4}},cfg())
 assert not r["complete"] and "missing_target_quote:ETH" in r["errors"]
def test_unfilled_limit_has_no_fake_profit():
 r=simulate([0,6,12,18,24],[[99]]*5,[[100]]*5,["BTC"],{0:{"BTC":.5}},{"BTC/USD":{"AmountPrecision":4}},cfg(),maker=True)
 assert not r["fills"] and r["return"]==0 and r["expired"]==1
