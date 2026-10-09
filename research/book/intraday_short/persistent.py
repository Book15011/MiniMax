"""Two post-diagnostic hypotheses; original entry masks are unchanged."""
from research.book.intraday_short.engine import features
def persistent_features(data,cfg):
 f=features(data,cfg);btc=f["close"].BTCUSDT
 ema=btc.ewm(span=cfg["ema_minutes"],adjust=False,min_periods=cfg["ema_minutes"]).mean()
 keep=(btc/btc.shift(cfg["warmup_minutes"])-1<0)&(btc<ema*(1+cfg["exit_rebound_buffer"]))
 f["weak"]=keep
 f["signals"]={"flow_persistent":f["signals"]["flow_breakout"],"volume_persistent":f["signals"]["volume_breakout"]}
 return f
