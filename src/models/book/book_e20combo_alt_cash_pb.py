"""e20v45 + alts to cash when they lag BTC + failed-bounce shorts (its unused cash, cap 25%) in a weak BTC regime (_e20combo.py)."""
from src.contracts import MarketView, ModelSpec
from src.models.book import _e20combo


class E20Combo:
    spec = ModelSpec(name="book_e20combo_alt_cash_pb", method="selector", author="book", rebalance_hours=24, band=0.03,
                     uses_shorts=True, description="e20v45 + alts to cash when they lag BTC + failed-bounce shorts (its unused cash) in a weak BTC regime")

    def targets(self, view: MarketView):
        return _e20combo.targets(view, base="alt", pullback=True, funding="cash")


MODEL = E20Combo()
