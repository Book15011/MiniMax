"""e20v45 unchanged plus negative-momentum shorts (gross cap 25%) only while the cash-short regime is on (_e20guard.py)."""
from src.contracts import MarketView, ModelSpec
from src.models.book import _e20guard


class E20Guard:
    spec = ModelSpec(name="book_e20guard_confirm", method="selector", author="book", rebalance_hours=24, band=0.03,
                     uses_shorts=True, description="e20v45 plus negative-momentum shorts up to 25% in a weak BTC regime")

    def targets(self, view: MarketView):
        return _e20guard.targets(view, pullback=False)


MODEL = E20Guard()
