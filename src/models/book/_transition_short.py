"""Four-hour defensive transition research; pure causal targets."""
from dataclasses import replace
import numpy as np
import pandas as pd
from src.contracts import MarketView
from src.models.book import _cashshort as shared
from src.models.baitoey.baitoey_ovl_brk_dual import MODEL as BASE

def weak_regime(view):
 p=view.params
 chosen,breadth=shared.liquid_breadth(view,p)
 if breadth is None or breadth>float(p["breadth_max_positive"]):return False,chosen
 btc=p["btc_symbol"]
 if btc not in view.close:return False,chosen
 need=max(int(p["btc_return_hours"]),int(p["btc_drawdown_hours"]))+1
 c=view.close[btc].reindex(shared._grid(view,need))
 if not shared._valid_prices(c):return False,chosen
 ret=float(c.iloc[-1]/c.loc[view.t-pd.Timedelta(hours=int(p["btc_return_hours"]))]-1)
 dd=1-float(c.iloc[-1]/c.max())
 return bool(ret<=float(p["btc_return_max"]) and dd>=float(p["btc_drawdown_min"])),chosen

def short_sleeve(view,longs,coins):
 p=view.params;empty=pd.Series(dtype=float)
 budget=min(float(p["short_gross_cap"]),max(0.,1-float(longs.sum())))
 coins=sorted(set(coins)-set(longs.index))
 if not coins or budget<=0:return empty
 hours=int(p["short_vol_days"])*24
 c=view.close.reindex(index=shared._grid(view,hours+1),columns=coins)
 ok=np.isfinite(c).all()&(c>0).all();c=c.loc[:,ok]
 if c.empty:return empty
 sigma=c.pct_change(fill_method=None).iloc[-hours:].std()*np.sqrt(24.)
 ret=c.iloc[-1]/c.loc[view.t-pd.Timedelta(hours=int(p["short_return_hours"]))]-1
 recent=c.iloc[-1]/c.loc[view.t-pd.Timedelta(hours=int(p["entry_confirmation_hours"]))]-1
 held=c.columns.isin(view.prev_targets[view.prev_targets<0].index)
 eligible=np.isfinite(sigma)&(sigma>0)&(ret<0)
 eligible &= pd.Series(np.where(held,recent<float(p["short_rebound_exit_return"]),recent<float(p["entry_return_max"])),index=c.columns)
 score=(ret/sigma)[eligible]
 if score.empty:return empty
 pick=score.sort_index().sort_values(kind="mergesort").head(int(p["short_k"])).index
 inv=1/sigma[pick];w=(inv/inv.sum()*budget).clip(upper=float(p["short_coin_cap"]))
 bound=float((w*sigma[pick]).sum())
 if bound>float(p["short_daily_vol"]):w*=float(p["short_daily_vol"])/bound
 return -w[w>0]

def targets(view:MarketView):
 view=shared._causal(view);p=view.params
 base_view=replace(view,params=p["long_base"],prev_targets=view.prev_targets[view.prev_targets>0])
 longs=BASE.targets(base_view).astype(float);longs=longs[longs>0]
 weak,coins=weak_regime(view)
 if not weak:return longs
 longs=longs*float(p["long_scale_weak"])
 return pd.concat([longs,short_sleeve(view,longs,coins)])
