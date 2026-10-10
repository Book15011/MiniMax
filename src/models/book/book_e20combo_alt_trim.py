"""e20v45 + alts to cash when they lag BTC + negative-momentum shorts (trimming longs, cap 25%) in a weak BTC regime (_e20combo.py)."""
from src.contracts import MarketView, ModelSpec
from src.models.book import _e20combo


class E20Combo:
    spec = ModelSpec(name="book_e20combo_alt_trim", method="selector", author="book", rebalance_hours=24, band=0.03,
                     uses_shorts=True, description="e20v45 + alts to cash when they lag BTC + negative-momentum shorts (trimming longs) in a weak BTC regime")

    def targets(self, view: MarketView):
        return _e20combo.targets(view, base="alt", pullback=False, funding="trim")


MODEL = E20Combo()
