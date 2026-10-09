import pandas as pd,numpy as np
from prefix_audit import short_basis_steps
def test_short_add_partial_cover_and_full_exit_basis():
 e=pd.DataFrame({"asset":["A"]*5,"action":["Open Short","Open Short","Cover Short","Buy Long","Cover Short"],"quantity":[2.,1.,1.,3.,2.],"price_usd":[10.,13.,9.,5.,20.]})
 basis,bound=short_basis_steps(e,{"A":2})
 np.testing.assert_allclose(basis,[20.,33.,22.,22.,0.])
 np.testing.assert_allclose(bound,[.10,.23,.23*2/3,.23*2/3,0.])
