"""Frozen price-only research. See research/book/price_trend/PROTOCOL.md."""
from ._price_trend import PriceTrend
MODEL=PriceTrend("book_price_channel_signed","channel",False)
