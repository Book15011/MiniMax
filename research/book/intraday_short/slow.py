"""One slower-range hypothesis, retaining minute monitoring and delayed fills."""
from research.book.intraday_short.engine import features
import pandas as pd
def slow_features(data,cfg):
 f=features(data,cfg)
 low=pd.DataFrame({s:z.low for s,z in data.items()})
 range_low=low.shift(1).rolling(cfg["range_minutes"],min_periods=cfg["range_minutes"]).min()
 mask=f["signals"]["volume_breakout"]&(f["close"]<range_low*(1-cfg["break_buffer"]))
 btc=f["close"].BTCUSDT
 ema=btc.ewm(span=cfg["ema_minutes"],adjust=False,min_periods=cfg["ema_minutes"]).mean()
 f["weak"]=(btc/btc.shift(cfg["warmup_minutes"])-1<0)&(btc<ema*(1+cfg["exit_rebound_buffer"]))
 f["signals"]={"slow_breakdown":mask}
 return f
