"""Template for a new model. Copy to src/models/<member>/<member>_<name>.py and edit.

Rules (docs/STRATEGY_GUIDE.md):
- The file name equals spec.name, and spec.name starts with your member name.
- targets() is pure: it may only use `view`. No files, no network, no clock, no randomness.
- Every tunable number goes in config.yaml under `models: <name>:`, read through view.params.
- Return signed weights by series id (e.g. "BTCUSDT"); sum of |w| <= 1; only ids in view.universe.
- Use view.tail(hours) first; slicing the full history on every call is slow.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.contracts import MarketView, ModelSpec


class Example:
    spec = ModelSpec(name="member_example", method="momentum", author="member", rebalance_hours=24, band=0.02,
                     uses_shorts=False, description="One line: what it holds and why")

    def targets(self, view: MarketView) -> pd.Series:
        p = view.params                                  # e.g. {"lookback_days": 7, "k": 5}
        close, _qv = view.tail((p["lookback_days"] + 1) * 24)
        ret = close.iloc[-1] / close.iloc[0] - 1
        top = ret.dropna().sort_values(ascending=False).head(p["k"])
        top = top[top > 0]
        if top.empty:
            return pd.Series(dtype=float)
        return pd.Series(np.full(len(top), 1.0 / len(top)), index=top.index)


# MODEL = Example()   # uncomment in your copy; the registry only picks up modules that define MODEL
