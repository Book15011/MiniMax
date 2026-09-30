"""Shared contracts between models, the backtest harness and the live engine.

Changing anything in this file needs both other members as reviewers (AGENTS.md section 5).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import numpy as np
import pandas as pd

METHODS = ("momentum", "trend", "selector")
REFERENCE = "reference"  # team baselines: reported for context, never compete
MEMBERS = ("pol", "book", "baitoey")
REBALANCE_HOURS = (1, 2, 3, 4, 6, 8, 12, 24)  # divisors of 24, so a decision always lands on 16:00 UTC


@dataclass(frozen=True)
class ModelSpec:
    name: str                 # unique; starts with the author ("pol_mom_ss"); equals the module file name
    method: str               # one of METHODS, or REFERENCE for team baselines
    author: str               # one of MEMBERS, or "team" for baselines
    rebalance_hours: int = 24  # a decision every N hours, anchored at 16:00 UTC (00:00 HKT)
    band: float = 0.02        # at a decision, trade a coin only if its weight is off target by more than this
    uses_shorts: bool = False  # True if targets can be negative
    description: str = ""

    def validate(self) -> None:
        if self.method not in METHODS + (REFERENCE,):
            raise ValueError(f"{self.name}: method must be one of {METHODS} (or '{REFERENCE}' for baselines)")
        if self.author not in MEMBERS + ("team",):
            raise ValueError(f"{self.name}: author must be one of {MEMBERS} or 'team'")
        if (self.method == REFERENCE) != (self.author == "team"):
            raise ValueError(f"{self.name}: only team baselines use method '{REFERENCE}'")
        if self.author != "team" and not self.name.startswith(self.author + "_"):
            raise ValueError(f"{self.name}: model names start with the author, e.g. '{self.author}_...'")
        if self.rebalance_hours not in REBALANCE_HOURS:
            raise ValueError(f"{self.name}: rebalance_hours must be one of {REBALANCE_HOURS}")
        if not 0.0 <= self.band < 0.5:
            raise ValueError(f"{self.name}: band must be in [0, 0.5)")


@dataclass(frozen=True)
class MarketView:
    """Everything a model may see at decision time t: bars that closed at or before t, nothing later."""
    t: pd.Timestamp
    close: pd.DataFrame          # hourly closes; index = bar close time (UTC) <= t; columns = series ids ("BTCUSDT")
    quote_volume: pd.DataFrame   # same shape; quote volume in USDT
    universe: tuple[str, ...]    # series ids the model may hold at t (point-in-time, liquid, tradable)
    params: dict = field(default_factory=dict)                     # this model's block under `models:` in config.yaml
    prev_targets: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))  # this model's previous decision

    def tail(self, hours: int) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Last `hours` bars of close and quote volume, restricted to the universe (cheap; use this first)."""
        cols = list(self.universe)
        return self.close.iloc[-hours:][cols], self.quote_volume.iloc[-hours:][cols]


@runtime_checkable
class Model(Protocol):
    spec: ModelSpec

    def targets(self, view: MarketView) -> pd.Series:
        """Signed target weights by series id: long > 0, short < 0, sum of |w| <= 1.

        Only ids in view.universe may be non-zero. Pure: no I/O, no clock, no randomness.
        """
        ...


def check_targets(w: pd.Series, view: MarketView, spec: ModelSpec, tol: float = 1e-9) -> pd.Series:
    """Validate a model's output against the contract and return the non-zero weights."""
    if not isinstance(w, pd.Series):
        raise TypeError(f"{spec.name} at {view.t}: targets() must return a pandas Series")
    w = w.astype(float)
    if not np.isfinite(w.to_numpy()).all():
        raise ValueError(f"{spec.name} at {view.t}: weights contain NaN or inf")
    w = w[w != 0.0]
    outside = sorted(set(w.index) - set(view.universe))
    if outside:
        raise ValueError(f"{spec.name} at {view.t}: weights outside the universe: {outside[:5]}")
    if (w < 0).any() and not spec.uses_shorts:
        raise ValueError(f"{spec.name} at {view.t}: negative weights but spec.uses_shorts is False")
    gross = float(w.abs().sum())
    if gross > 1.0 + tol:
        raise ValueError(f"{spec.name} at {view.t}: gross exposure {gross:.6f} > 1 (no leverage)")
    return w
