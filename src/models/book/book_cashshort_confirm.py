"""Confirmed negative-momentum shorts in the pinned long book's unused cash."""
from src.contracts import MarketView, ModelSpec
from src.models.book import _cashshort


class CashShortConfirm:
    spec = ModelSpec(name="book_cashshort_confirm", method="momentum", author="book",
                     rebalance_hours=24, band=0.05, uses_shorts=True,
                     description="Pinned dual-momentum longs plus cash-only confirm shorts")

    def targets(self, view: MarketView):
        return _cashshort.targets(view, pullback=False)


MODEL = CashShortConfirm()
