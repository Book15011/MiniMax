"""Pure money math; no API, clock, file or order imports."""
from decimal import Decimal,ROUND_DOWN
import math
def break_even(entry,fee_entry,fee_exit):
    return entry*(1+fee_entry)/(1-fee_exit)
def quantity(budget,price,precision,fee):
    if not all(math.isfinite(float(x)) for x in [budget,price,fee]) or budget<=0 or price<=0:return 0.
    q=Decimal(str(budget))/(Decimal(str(price))*(1+Decimal(str(fee))))
    return float(q.quantize(Decimal(1).scaleb(-int(precision)),rounding=ROUND_DOWN))
def trade_pnl(qty,entry,exit,fee_entry,fee_exit,side=1):
    return qty*(exit-entry)*side-qty*(entry*fee_entry+exit*fee_exit)
def resting_hit(side,limit,bid,ask,last,rule,consecutive,needed):
    hit=(ask<=limit if rule=="ask" else last<=limit and bid<=limit) if side=="BUY" else bid>=limit
    return bool(hit and consecutive>=needed)
def penalty_gain(current,cutoff,treatment):
    target=1+cutoff
    if treatment=="subtract_20pp":target+=.2
    elif treatment=="equity_haircut20":target/=.8
    elif treatment=="round_profit_haircut20":target=1+cutoff/.8
    elif treatment=="incremental_profit_haircut20":return ((1+cutoff)/(1+current)-1)/.8
    elif treatment!="none":raise ValueError(treatment)
    return target/(1+current)-1
