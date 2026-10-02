"""Leakage guard: selection code runs inside forbid_outcome_access(); reading outcomes there raises."""
from __future__ import annotations

import threading
from contextlib import contextmanager
from functools import wraps

import pandas as pd

OUTCOME_COLUMNS = ("Y1", "Y2", "Y3", "Y4", "Y5", "Y6", "Y7", "Y8")

_state = threading.local()


class LeakageError(RuntimeError):
    pass


def _depth() -> int:
    return getattr(_state, "depth", 0)


@contextmanager
def forbid_outcome_access():
    _state.depth = _depth() + 1
    try:
        yield
    finally:
        _state.depth -= 1


def check_outcome_access() -> None:
    if _depth() > 0:
        raise LeakageError("outcome table accessed inside selection code")


def assert_no_outcome_columns(*objs) -> None:
    for o in objs:
        labels = o.columns if isinstance(o, pd.DataFrame) else o.index if isinstance(o, pd.Series) else []
        bad = {str(x) for x in labels} & set(OUTCOME_COLUMNS)
        if bad:
            raise LeakageError(f"selection input contains outcome columns {sorted(bad)}")


def selection_only(fn):
    """Decorator: run fn with outcome access forbidden and reject inputs that carry outcome columns."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        assert_no_outcome_columns(*args, *kwargs.values())
        with forbid_outcome_access():
            return fn(*args, **kwargs)
    return wrapper
