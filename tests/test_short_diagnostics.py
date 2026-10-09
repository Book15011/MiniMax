import numpy as np
import pandas as pd
import pytest
from research.book.short_diagnostics.run import attribute_path

def trade(before,after,fee=50.):
    return pd.DataFrame([dict(hour=1,series="BTCUSDT",w_before=before,w_after=after,
                              fee_usd=fee,spread_usd=0.,kind="entry")])

def test_short_attribution_cannot_capture_move_before_entry():
    price=np.array([[100.],[90.],[90.]])
    eq=np.array([1.,.9995,.9995])
    gross=np.array([0.,.5,.5]);net=-gross
    out=attribute_path(price,["BTCUSDT"],trade(0,-.5),eq,gross,net,100000,.001)
    assert out["short_pnl"] == 0
    assert out["long_pnl"] == 0
    assert out["return"] == pytest.approx(-.00099975)

def test_short_pnl_fees_and_liquidation_reconcile_exactly():
    price=np.array([[100.],[100.],[90.]])
    eq=np.array([1.,.9995,1.049475])
    gross=np.array([0.,.5,.5*.9/1.05]);net=-gross
    out=attribute_path(price,["BTCUSDT"],trade(0,-.5),eq,gross,net,100000,.001)
    assert out["short_pnl"] == pytest.approx(.049975)
    assert out["fees"] == .0005
    assert out["return"] == pytest.approx(eq[-1]*(1-.001*gross[-1])-1)
    assert out["identity_error"] < 1e-12

def test_bad_cached_money_or_before_weight_fails_closed():
    price=np.array([[100.],[100.],[90.]])
    eq=np.array([1.,.9995,1.049475])
    gross=np.array([0.,.5,.5*.9/1.05]);net=-gross
    with pytest.raises(ValueError,match="equity"):
        attribute_path(price,["BTCUSDT"],trade(0,-.5),eq+.01,gross,net,100000,.001)
    with pytest.raises(ValueError,match="before"):
        attribute_path(price,["BTCUSDT"],trade(.1,-.5),eq,gross,net,100000,.001)
