import pandas as pd,pytest
from research.book.short_forecast.audit import terminal_audit
def sample(cover="1"):
 return pd.DataFrame([dict(asset="BTC",action="Open Short",quantity="1",price_usd=100.,fee=.1),dict(asset="BTC",action="Cover Short",quantity=cover,price_usd=90.,fee=float(cover)*.09)])
def test_terminal_reconciles_quantity_fees_and_money():
 e=sample();z=terminal_audit(e,100000.,.001,100009.81)
 assert z["status"]=="PASS"
def test_small_unclosed_position_fails():
 with pytest.raises(ValueError,match="residual"):terminal_audit(sample(".99999"),100000.,.001,100009.81)
def test_cover_over_open_fails():
 with pytest.raises(ValueError,match="negative"):terminal_audit(sample("1.001"),100000.,.001,100009.81)
def test_terminal_fee_or_equity_error_fails():
 e=sample();e.loc[1,"fee"]=0
 with pytest.raises(ValueError,match="fee"):terminal_audit(e,100000.,.001,100009.81)
 with pytest.raises(ValueError,match="equity"):terminal_audit(sample(),100000.,.001,100010.)
