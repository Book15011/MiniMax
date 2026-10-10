"""Independent complete-ledger short quantity, fee and cash reconciliation."""
from decimal import Decimal
def terminal_audit(events,seed,fee,terminal_equity,quantity_tolerance=1e-7,money_tolerance=1e-6):
 qty={};cash=float(seed);fee_sum=0.
 for e in events.itertuples():
  q=Decimal(str(e.quantity));kind=e.action
  if q<=0:raise ValueError("Nonpositive quantity")
  expected=float(q)*float(e.price_usd)*fee
  if abs(expected-float(e.fee))>money_tolerance:raise ValueError("Terminal fee mismatch")
  if kind=="Open Short":qty[e.asset]=qty.get(e.asset,Decimal(0))+q;cash+=float(q)*float(e.price_usd)-float(e.fee)
  elif kind=="Cover Short":qty[e.asset]=qty.get(e.asset,Decimal(0))-q;cash-=float(q)*float(e.price_usd)+float(e.fee)
  else:raise ValueError("Non-short action in short-only study")
  if qty[e.asset]<-Decimal(str(quantity_tolerance)):raise ValueError("negative short quantity")
  fee_sum+=float(e.fee)
 residual=max((abs(float(q)) for q in qty.values()),default=0.)
 if residual>quantity_tolerance:raise ValueError("residual terminal short quantity")
 if abs(cash-terminal_equity)>money_tolerance:raise ValueError("Terminal equity mismatch")
 return dict(status="PASS",maximum_residual_quantity=residual,cash_equity_error_usd=abs(cash-terminal_equity),total_fees_usd=fee_sum)
