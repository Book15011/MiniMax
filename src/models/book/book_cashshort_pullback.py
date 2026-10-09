"""Failed-rebound negative-momentum shorts in the pinned long book's unused cash."""
from src.contracts import MarketView, ModelSpec
from src.models.book import _cashshort


class CashShortPullback:
    spec = ModelSpec(name="book_cashshort_pullback", method="momentum", author="book",
                     rebalance_hours=24, band=0.05, uses_shorts=True,
                     description="Pinned dual-momentum longs plus cash-only pullback shorts")

    def targets(self, view: MarketView):
        return _cashshort.targets(view, pullback=True)


MODEL = CashShortPullback()
