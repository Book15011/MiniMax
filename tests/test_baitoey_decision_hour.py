import pandas as pd

from src.contracts import MarketView
from src.models.baitoey._decision_hour import DecisionHour

IDX = pd.date_range("2026-01-01 00:00", periods=48, freq="h", tz="UTC")


class Inner:
    calls = 0

    def targets(self, view):
        Inner.calls += 1
        return pd.Series({"AUSDT": 0.5})


def view(end: int, prev: dict, hour: int = 8) -> MarketView:
    close = pd.DataFrame({"AUSDT": 100.0, "BUSDT": 100.0}, index=IDX).iloc[: end + 1]
    return MarketView(t=close.index[-1], close=close, quote_volume=close * 0 + 1e6, universe=("AUSDT", "BUSDT"),
                      params={"vt": {}, "decision_hour": hour}, prev_targets=pd.Series(prev, dtype=float))


def model():
    m = DecisionHour()
    m.INNER = Inner()
    return m


def test_it_decides_at_the_chosen_hour_and_holds_the_book_otherwise():
    m, Inner.calls = model(), 0
    assert m.targets(view(8, {"BUSDT": 0.3})).to_dict() == {"AUSDT": 0.5}          # 08:00: a new decision
    assert m.targets(view(9, {"BUSDT": 0.3})).to_dict() == {"BUSDT": 0.3}          # 09:00: the book is held
    assert m.targets(view(16, {"BUSDT": 0.3})).to_dict() == {"BUSDT": 0.3}         # 16:00 is not special any more
    assert Inner.calls == 1


def test_an_empty_book_decides_at_once():
    m, Inner.calls = model(), 0
    assert m.targets(view(13, {})).to_dict() == {"AUSDT": 0.5}
    assert Inner.calls == 1
