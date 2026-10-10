"""e20v45 unchanged plus failed-bounce shorts (gross cap 40%) only while the cash-short regime is on (_e20guard.py)."""
from src.contracts import MarketView, ModelSpec
from src.models.book import _e20guard


class E20Guard:
    spec = ModelSpec(name="book_e20guard_pullback40", method="selector", author="book", rebalance_hours=24, band=0.03,
                     uses_shorts=True, description="e20v45 plus failed-bounce shorts up to 40% in a weak BTC regime")

    def targets(self, view: MarketView):
        return _e20guard.targets(view, pullback=True)


MODEL = E20Guard()
