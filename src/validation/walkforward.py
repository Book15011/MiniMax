"""Walk-forward test: does similarity of the starting state predict the next 14 days?"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.validation.crps import crps_fair, crps_standard
from src.validation.guard import OUTCOME_COLUMNS
from src.validation.selection import (
    MAIN_VARIANTS, PickRules, active_features, pool_index, random_pick, recent_nonoverlapping, select_lookalikes,
)

log = logging.getLogger(__name__)
BASELINES = {"all": "ALL of pool_D", "recent": "25 most recent non-overlapping", "random": "25 random (same spacing rules, mean of 50 draws)"}
crps = crps_standard  # the pre-registered v1 rule scores with the standard CRPS


def test_dates(start: str, holdout: pd.Timestamp, horizon_days: int, step_days: int, hour: int) -> pd.DatetimeIndex:
    first = pd.Timestamp(f"{start} {hour:02d}:00", tz="UTC")
    last = holdout - pd.Timedelta(days=horizon_days)
    return pd.date_range(first, last, freq=f"{step_days}D")


def run_walkforward(features: pd.DataFrame, outcomes: pd.DataFrame, variants: dict[str, list[str]],
                    rules: PickRules, dates: pd.DatetimeIndex, earliest: pd.Timestamp, draws: int,
                    seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (crps rows: variant, D, Y, lookalike, all, recent, random) and per-(variant, D) audit rows."""
    Y = list(OUTCOME_COLUMNS)
    O = outcomes[Y].to_numpy(dtype=float)
    opos = pd.Series(np.arange(len(outcomes)), index=outcomes.index)
    h = pd.Timedelta(days=rules.horizon_days)
    rand_cache: dict[tuple, np.ndarray] = {}
    rows, audit = [], []
    for name, groups in variants.items():
        feats = features[active_features(groups)]
        for D in dates:
            pool = pool_index(features, groups, D, rules.horizon_days, earliest)
            rec = {"variant": name, "D": D, "n_pool": len(pool),
                   "pool_max_end": (pool.max() + h) if len(pool) else pd.NaT}
            if D not in feats.index or feats.loc[D].isna().any() or D not in opos.index:
                audit.append({**rec, "status": "skipped: state or outcome at D unavailable"})
                continue
            if len(pool) < rules.k:
                audit.append({**rec, "status": f"skipped: pool has only {len(pool)} starts"})
                continue
            picks, dropped = select_lookalikes(feats.loc[pool], feats.loc[D], groups, rules)
            if len(picks) < rules.k:
                audit.append({**rec, "status": f"skipped: only {len(picks)} lookalikes"})
                continue
            recent = recent_nonoverlapping(pool, rules)
            key = (D, pool[0], len(pool))
            if key not in rand_cache:
                rng = np.random.default_rng([seed, int(D.value // 86_400_000_000_000)])
                draws_pos = [opos[random_pick(pool, rules, rng)].to_numpy() for _ in range(draws)]
                y_true = O[opos[D]]
                rand_cache[key] = np.array([[(crps(O[p, j], y_true[j]), crps_fair(O[p, j], y_true[j]))
                                             for j in range(len(Y))] for p in draws_pos]).mean(axis=0)
            y_true = O[opos[D]]
            lp = opos[picks["t0"]].to_numpy()
            ap, rp = opos[pool].to_numpy(), opos[recent].to_numpy()
            for j, y in enumerate(Y):
                yt = y_true[j]
                rows.append((name, D, y, crps(O[lp, j], yt), crps(O[ap, j], yt), crps(O[rp, j], yt),
                             float(rand_cache[key][j, 0]), crps_fair(O[lp, j], yt), crps_fair(O[ap, j], yt),
                             crps_fair(O[rp, j], yt), float(rand_cache[key][j, 1])))
            audit.append({**rec, "status": "ok", "pick_max_end": picks["t0"].max() + h,
                          "mean_distance": float(picks["distance"].mean()), "dropped": ",".join(dropped)})
        log.info("walk-forward %s done", name)
    cols = ["lookalike", "all", "recent", "random"]
    cr = pd.DataFrame(rows, columns=["variant", "D", "Y", *cols, *[f"{c}_fair" for c in cols]])
    return cr, pd.DataFrame(audit)


def skill(crps_rows: pd.DataFrame, variant: str, baseline: str, lo: pd.Timestamp, hi: pd.Timestamp,
          n_boot: int, block: int, seed: int, fair: bool = False) -> pd.DataFrame:
    """Skill = 1 - sum CRPS_lookalike / sum CRPS_baseline per Y, plus the mean over Y; block-bootstrap 90% CI.
    fair=True uses the fair-CRPS columns for both sides."""
    d = crps_rows[(crps_rows.variant == variant) & (crps_rows.D >= lo) & (crps_rows.D <= hi)]
    Y = list(OUTCOME_COLUMNS)
    if d.empty:
        return pd.DataFrame(index=Y + ["MEAN"], columns=["skill", "lo", "hi", "n_dates"], dtype=float)
    sfx = "_fair" if fair else ""
    L = d.pivot(index="D", columns="Y", values="lookalike" + sfx)[Y].to_numpy()
    B = d.pivot(index="D", columns="Y", values=baseline + sfx)[Y].to_numpy()
    return skill_arrays(L, B, Y, n_boot, block, seed)


def skill_arrays(L: np.ndarray, B: np.ndarray, labels: list[str], n_boot: int, block: int,
                 seed: int) -> pd.DataFrame:
    """L, B: CRPS per (test date, outcome), dates in time order. Moving-block bootstrap over dates."""
    Y = list(labels)
    n = len(L)
    point = 1 - L.sum(0) / B.sum(0)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, max(n - block + 1, 1), size=(n_boot, nb))
    idx = (starts[:, :, None] + np.arange(block)).reshape(n_boot, -1)[:, :n]
    idx = np.minimum(idx, n - 1)
    boot = 1 - L[idx].sum(1) / B[idx].sum(1)
    out = pd.DataFrame({"skill": point, "lo": np.percentile(boot, 5, axis=0), "hi": np.percentile(boot, 95, axis=0)},
                       index=Y, dtype=float)
    mb = boot.mean(axis=1)
    out.loc["MEAN"] = [point.mean(), np.percentile(mb, 5), np.percentile(mb, 95)]
    out["n_dates"] = n
    return out


def choose_variant(screen_mean: dict[str, float], confirm_mean: dict[str, float]) -> dict:
    """The pre-registered rule (see reports/validation_set_v1.md)."""
    cands = {v: s for v, s in screen_mean.items() if v in MAIN_VARIANTS and np.isfinite(s)}
    best = max(MAIN_VARIANTS, key=lambda v: cands.get(v, -np.inf))  # ties -> earlier in MAIN_VARIANTS
    core_c = confirm_mean.get("CORE", np.nan)
    best_c = confirm_mean.get(best, np.nan)
    if best == "CORE":
        chosen, why = "CORE", "CORE had the highest SCREEN skill vs (a)"
    elif np.isfinite(best_c) and best_c > 0 and best_c >= core_c:
        chosen, why = best, f"{best} led SCREEN and its CONFIRM skill ({best_c:.4f}) is > 0 and >= CORE's ({core_c:.4f})"
    else:
        chosen, why = "CORE", (f"{best} led SCREEN but its CONFIRM skill ({best_c:.4f}) is not both > 0 and "
                               f">= CORE's ({core_c:.4f}); fall back to CORE")
    return {"screen_leader": best, "chosen": chosen, "reason": why, "core_confirm_skill": core_c,
            "core_not_predictive": bool(not np.isfinite(core_c) or core_c <= 0)}
