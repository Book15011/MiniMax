"""Lookalike selection. Operates on FEATURES only; never imports or reads the outcome table."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.validation.features import CORE_GROUPS, GROUPS
from src.validation.guard import selection_only

VARIANTS: dict[str, list[str]] = {
    "CORE": CORE_GROUPS,
    "CORE+POSITIONING": CORE_GROUPS + ["POSITIONING"],
    "CORE+MACRO": CORE_GROUPS + ["MACRO"],
    "CORE+CALENDAR": CORE_GROUPS + ["CALENDAR"],
    "CORE+POSITIONING+MACRO": CORE_GROUPS + ["POSITIONING", "MACRO"],
    "ALL": CORE_GROUPS + ["POSITIONING", "MACRO", "CALENDAR"],
}
MAIN_VARIANTS = list(VARIANTS)
DIAGNOSTIC_VARIANTS = {f"CORE-minus-{g}": [x for x in CORE_GROUPS if x != g] for g in CORE_GROUPS}


@dataclass(frozen=True)
class PickRules:
    k: int = 25
    min_separation_days: int = 14
    span_days: int = 90
    max_per_span: int = 3
    horizon_days: int = 14


def active_features(groups: list[str]) -> list[str]:
    return [f for g in groups for f in GROUPS[g]]


@selection_only
def pool_index(features: pd.DataFrame, groups: list[str], end_limit: pd.Timestamp, horizon_days: int,
               earliest: pd.Timestamp) -> pd.DatetimeIndex:
    """Starts t0 with t0 + horizon <= end_limit, t0 >= first date all active features exist, no NaN."""
    f = features[active_features(groups)]
    complete = f.notna().all(axis=1)
    if not complete.any():
        return pd.DatetimeIndex([], tz="UTC")
    first = max(complete.idxmax(), earliest)
    ok = complete & (f.index >= first) & (f.index + pd.Timedelta(days=horizon_days) <= end_limit)
    return f.index[ok.to_numpy()]


def mid_rank_pct(ref: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Percentile of each x within ref, per column: (#less + 0.5 * #equal) / n."""
    out = np.empty(x.shape, dtype=float)
    n = ref.shape[0]
    for j in range(ref.shape[1]):
        s = np.sort(ref[:, j])
        lo = np.searchsorted(s, x[:, j], side="left")
        hi = np.searchsorted(s, x[:, j], side="right")
        out[:, j] = (lo + 0.5 * (hi - lo)) / n
    return out


@selection_only
def distances(pool_feats: pd.DataFrame, query: pd.Series, groups: list[str]) -> tuple[pd.Series, list[str]]:
    """Distance of every pool start to the query state. Query features that are NaN are dropped
    (returned as the second value) so the caller can report them."""
    used = [g for g in groups if any(np.isfinite(query[f]) for f in GROUPS[g])]
    dropped = [f for g in groups for f in GROUPS[g] if not np.isfinite(query[f])]
    feats = [f for g in used for f in GROUPS[g] if np.isfinite(query[f])]
    ref = pool_feats[feats].to_numpy(dtype=float)
    p_pool = mid_rank_pct(ref, ref)
    p_q = mid_rank_pct(ref, query[feats].to_numpy(dtype=float)[None, :])[0]
    sq = (p_pool - p_q) ** 2
    col = {f: i for i, f in enumerate(feats)}
    total = np.zeros(len(pool_feats))
    for g in used:
        idx = [col[f] for f in GROUPS[g] if f in col]
        total += sq[:, idx].mean(axis=1) / len(used)
    return pd.Series(np.sqrt(total), index=pool_feats.index, name="distance"), dropped


def greedy_pick(ordered: pd.DatetimeIndex, rules: PickRules) -> list[pd.Timestamp]:
    """Walk candidates in the given order; accept one only if it is >= min_separation from every
    accepted start and no span of `span_days` would then hold more than max_per_span starts."""
    day = 86_400 * 10**9
    sep, span = rules.min_separation_days * day, rules.span_days * day
    acc: list[int] = []
    for t in ordered.asi8:
        if any(abs(t - a) < sep for a in acc):
            continue
        near = sorted([a for a in acc if abs(t - a) < span] + [t])
        m = rules.max_per_span
        if any(near[i + m] - near[i] < span for i in range(len(near) - m)):
            continue
        acc.append(t)
        if len(acc) == rules.k:
            break
    return list(pd.to_datetime(sorted(acc), utc=True))


@selection_only
def select_lookalikes(pool_feats: pd.DataFrame, query: pd.Series, groups: list[str],
                      rules: PickRules) -> tuple[pd.DataFrame, list[str]]:
    d, dropped = distances(pool_feats, query, groups)
    order = d.sort_values(kind="stable").index
    picked = greedy_pick(order, rules)
    return pd.DataFrame({"t0": picked, "distance": d.loc[picked].to_numpy()}), dropped


@selection_only
def recent_nonoverlapping(pool: pd.DatetimeIndex, rules: PickRules) -> list[pd.Timestamp]:
    """The k most recent pool starts, walking back so that windows never overlap."""
    out, limit = [], None
    for t in sorted(pool, reverse=True):
        if limit is None or t <= limit:
            out.append(t)
            limit = t - pd.Timedelta(days=rules.horizon_days)
            if len(out) == rules.k:
                break
    return sorted(out)


@selection_only
def random_pick(pool: pd.DatetimeIndex, rules: PickRules, rng: np.random.Generator) -> list[pd.Timestamp]:
    """Same spacing rules as the lookalike pick, but candidates in random order."""
    return greedy_pick(pool[rng.permutation(len(pool))], rules)


def jaccard(a, b) -> float:
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 1.0
