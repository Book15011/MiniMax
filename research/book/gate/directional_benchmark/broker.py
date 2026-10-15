"""Exact cash/short-collateral ledger; no API, credential or order-sending code."""
from dataclasses import dataclass
from decimal import Decimal as D,ROUND_CEILING,ROUND_FLOOR
@dataclass(frozen=True)
class Order:
    coin:str
    side:int
    quantity:D
class Portfolio:
    def __init__(self,cash):
        self.cash=D(cash);self.positions={};self.fees=D(0);self.fills=[]
    def free_cash(self):
        return self.cash-sum((-q*e for q,e in self.positions.values() if q<0),D(0))
    def nav(self,quotes):
        result=self.cash
        for c,(q,e) in self.positions.items():
            bid,ask=map(D,quotes[c])
            if bid<=0 or ask<bid:raise ValueError("invalid mark")
            result+=q*bid if q>0 else -q*(e-ask)
        return result
    def gross(self,quotes):
        return sum((abs(q)*(D(quotes[c][0]) if q>0 else D(quotes[c][1])) for c,(q,_) in self.positions.items()),D(0))
    def fill(self,o,price,fee):
        price,fee=D(price),D(fee);qty=D(o.quantity)
        if o.side not in (-1,1) or price<=0 or qty<=0 or not 0<=fee<=1:raise ValueError("invalid fill")
        commission=(qty*price*fee).quantize(D(".00000001"),rounding=ROUND_CEILING)
        cash=self.cash-commission;positions=dict(self.positions)
        old,entry=positions.get(o.coin,(D(0),D(0)));left=qty
        if old and (old>0)!=(o.side>0):
            closed=min(abs(old),left)
            cash+=closed*price if old>0 else closed*(entry-price)
            old+=o.side*closed;left-=closed
        new=old
        if left:
            if o.side>0:cash-=left*price
            new=old+o.side*left
            entry=(abs(old)*entry+left*price)/abs(new)
        if new:positions[o.coin]=(new,entry)
        else:positions.pop(o.coin,None)
        locked=sum((-q*e for q,e in positions.values() if q<0),D(0))
        if left and cash-locked<0:raise ValueError("insufficient cash/collateral")
        self.cash=cash;self.positions=positions;self.fees+=commission
        self.fills.append({"coin":o.coin,"side":o.side,"quantity":str(qty),"price":str(price),"fee":str(commission)})
        return commission
def role(side,limit,bid,ask):
    if side not in (-1,1):raise ValueError("side")
    return "TAKER" if (limit>=ask if side>0 else limit<=bid) else "RESTING"
def sized(budget,price,precision,fee):
    if not 0<=precision<=8:raise ValueError("precision")
    step=D(10)**-precision
    q=(D(budget)/(D(price)*(1+D(fee)))).quantize(step,rounding=ROUND_FLOOR)
    while q>0 and q*D(price)+(q*D(price)*D(fee)).quantize(D(".00000001"),rounding=ROUND_CEILING)>D(budget):q-=step
    return q
