"""Return-first score (docs/EVALUATION.md section 3; pre-registered in reports/review/20261002-prereg-return-first.md).

The competition keeps the top 20 by return first and ranks by Sortino, Sharpe and Calmar only after that. So the
primary number is how often a model clears the return cut, with each window weighted by how much its market
resembles the coming one (w', scoring.windows.final_weights):
- bars per window, on R_liq (what is left after the system liquidates everything at the end):
    LENIENT  DOWN windows: the previous edition's measured #20 cut (-1.4965%); UP windows: 0% (an assumption)
    MIDDLE   0%
    STRICT   max(0, median R_liq of the 6 gate benchmarks that window)
- HIT_b = sum of w' over the windows with R_liq >= bar_b; HEADLINE_RET = mean of the three HITs (primary).
- CS_HIT = the w'-weighted mean of the primary composite (V1 FLOORED on HKT days) over the windows that clear
  LENIENT (0 if none): risk ranks second.
- Tie test: a paired bootstrap over calendar months of the window start, the same draws for every model.
- Pick order (candidates only): hard gates, HEADLINE_RET, CS_HIT inside the top model's tie group, then
  min(SCREEN, CONFIRM) when CS_HITs are within 0.05.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

BARS = ("LENIENT", "MIDDLE", "STRICT")
POL_BARS = {"q67": 2 / 3, "q83": 5 / 6, "best": None}      # Pol's bars (results/pol/20261001-final/bars2.py)


def bar_table(up: pd.Series, field_R: pd.DataFrame, cfg_bars: dict) -> pd.DataFrame:
    """The three bars of every window (rows = windows, as up's index; field_R: the gate benchmarks' returns)."""
    f = field_R.reindex(up.index)
    lb = cfg_bars["LENIENT"]
    return pd.DataFrame({"LENIENT": np.where(up.to_numpy(dtype=bool), float(lb["up"]), float(lb["down"])),
                         "MIDDLE": float(cfg_bars["MIDDLE"]),
                         "STRICT": np.maximum(float(cfg_bars["STRICT"]["floor"]), f.median(axis=1).to_numpy())},
                        index=up.index)


def pol_bar_table(field_R: pd.DataFrame, index: pd.DatetimeIndex) -> pd.DataFrame:
    """Pol's report-only bars: max(0, the benchmarks' 67th / 83rd percentile / best return), pandas linear quantiles."""
    f = field_R.reindex(index)
    out = {k: (f.max(axis=1) if q is None else f.quantile(q, axis=1)) for k, q in POL_BARS.items()}
    return pd.DataFrame({k: np.maximum(0.0, v.to_numpy()) for k, v in out.items()}, index=index)


def hits(R: pd.Series, bars: pd.DataFrame, w: pd.Series) -> dict[str, float]:
    """HIT per bar: the share of weight (w renormalized over R's windows) on windows with R >= the bar."""
    ww = w.reindex(R.index).to_numpy(dtype=float)
    ww = ww / ww.sum()
    b = bars.reindex(R.index)
    return {c: float((ww * (R.to_numpy() >= b[c].to_numpy())).sum()) for c in b.columns}


def headline_ret(hit: dict[str, float]) -> float:
    return float(np.mean([hit[b] for b in BARS]))


def cs_hit(composite: pd.Series, R: pd.Series, lenient: pd.Series, w: pd.Series) -> float:
    """w-weighted mean composite over the windows with R >= the LENIENT bar; 0 if there are none."""
    ok = (R >= lenient.reindex(R.index)).to_numpy()
    ww = w.reindex(R.index).to_numpy(dtype=float)
    if not ok.any():
        return 0.0
    return float((ww[ok] * composite.reindex(R.index).to_numpy()[ok]).sum() / ww[ok].sum())


def score_pool(win: pd.DataFrame, bars: pd.DataFrame, pbars: pd.DataFrame, bars_plain: pd.DataFrame,
               up: pd.Series, w: pd.Series, primary: str, utc_primary: str) -> dict:
    """Every return-first number of one model on one pool (win: its per-window table on that pool)."""
    idx = win.index
    R, Rp = win.R_liq, win.R
    hit = hits(R, bars, w)
    u = up.reindex(idx).to_numpy(dtype=bool)
    return {
        "n": int(len(idx)), "headline_ret": headline_ret(hit), "hit": hit,
        "hit_up": hits(R[u], bars, w) if u.any() else None,
        "hit_down": hits(R[~u], bars, w) if (~u).any() else None,
        "hit_pol_bars": hits(R, pbars, w),
        "headline_ret_plain_R": headline_ret(hits(Rp, bars_plain, w)),
        "cs_hit": cs_hit(win[primary], R, bars.LENIENT, w),
        "cs_hit_utc": cs_hit(win[utc_primary], R, bars.LENIENT, w),
        "share_up_weight": float(w.reindex(idx)[u].sum() / w.reindex(idx).sum()),
    }


# ---------------- tie test: paired bootstrap over calendar months ----------------

def month_codes(starts: pd.DatetimeIndex) -> np.ndarray:
    """Calendar month (UTC) of each window start, as year * 12 + month."""
    return np.asarray(starts.year * 12 + starts.month, dtype=int)


def month_multiplicity(starts: pd.DatetimeIndex, reps: int, seed: int) -> np.ndarray:
    """(reps, windows): how many times each window is drawn when M months are drawn with replacement from the M
    calendar months of the pool (every window of a drawn month comes with it). numpy default_rng(seed)."""
    codes = month_codes(starts)
    months, pos = np.unique(codes, return_inverse=True)
    rng = np.random.default_rng(seed)
    picks = rng.integers(0, len(months), size=(reps, len(months)))
    counts = np.zeros((reps, len(months)))
    np.add.at(counts, (np.repeat(np.arange(reps), len(months)), picks.ravel()), 1.0)
    return counts[:, pos]


def boot_headline(ind: np.ndarray, w: np.ndarray, mult: np.ndarray) -> np.ndarray:
    """HEADLINE_RET in every draw. ind: (windows, 3) cleared LENIENT / MIDDLE / STRICT; w: w' per window."""
    den = mult @ w
    return ((mult @ (w[:, None] * ind)) / den[:, None]).mean(axis=1)


def tie_test(inds: dict[str, np.ndarray], w: np.ndarray, top: str, mult: np.ndarray, level: float) -> dict:
    """For every model: HEADLINE_RET(model) - HEADLINE_RET(top) with its central `level` interval; tied if it
    contains 0 (the top model is tied with itself)."""
    base = boot_headline(inds[top], w, mult)
    a = (1.0 - level) / 2.0
    out = {}
    for n, ind in inds.items():
        d = boot_headline(ind, w, mult) - base
        point = float((w[:, None] * ind).sum(axis=0).mean() / w.sum() - (w[:, None] * inds[top]).sum(axis=0).mean() / w.sum())
        lo, hi = (float(x) for x in np.quantile(d, [a, 1.0 - a]))
        out[n] = {"diff": point, "lo": lo, "hi": hi, "tied": bool(lo <= 0.0 <= hi) or n == top}
    return out


def pick_order(rows: dict[str, dict], tie: dict[str, dict], cs_tol: float) -> list[str]:
    """Candidates in the pre-registered order. rows[name] needs: eligible, headline_ret, cs_hit, min_sc.
    1. eligible first; 2. highest HEADLINE_RET; 3. inside the tie group (the top model and every eligible candidate
    tied with it) the highest CS_HIT, and 4. among those within cs_tol of that CS_HIT, the highest min(SCREEN,
    CONFIRM). The tie group is ordered by applying 3-4 again to what is left; then the other eligible candidates by
    HEADLINE_RET, then the ineligible ones by HEADLINE_RET."""
    elig = [n for n, r in rows.items() if r["eligible"]]
    group = [n for n in elig if tie.get(n, {}).get("tied")]
    order = []
    while group:
        best_cs = max(rows[n]["cs_hit"] for n in group)
        near = [n for n in group if rows[n]["cs_hit"] >= best_cs - cs_tol]
        def key(n: str) -> tuple:
            sc_ = rows[n].get("min_sc")
            sc_ = sc_ if sc_ is not None and np.isfinite(sc_) else -np.inf
            return (sc_ if len(near) > 1 else 0.0, rows[n]["cs_hit"], rows[n]["headline_ret"], n)

        pick = max(near, key=key)
        order.append(pick)
        group.remove(pick)
    rest = sorted((n for n in elig if n not in order), key=lambda n: -rows[n]["headline_ret"])
    inel = sorted((n for n in rows if not rows[n]["eligible"]), key=lambda n: -rows[n]["headline_ret"])
    return order + rest + inel


# ---------------- Pol's period check (tie-break 4) ----------------

def pol_period_rel(model_win: pd.DataFrame, field_wins: dict[str, pd.DataFrame], w_live: pd.Series,
                   w_rec: pd.Series, mask: np.ndarray, sc: dict) -> float:
    """Pol's REL on the field-best bar over a set of windows (results/pol/20261001-final/bars2.py, rel()):
    gate = R >= max(0, the benchmarks' best R), CS = gate x composite(v), HEADLINE = 0.7 live-like + 0.3 recency
    weighted means over the masked windows, REL = mean over V1-V4 of HEADLINE(model) / mean HEADLINE(benchmarks)."""
    idx = model_win.index
    m = np.asarray(mask, dtype=bool)
    bar = np.maximum(0.0, pd.DataFrame({n: f.R.reindex(idx) for n, f in field_wins.items()}).max(axis=1).to_numpy())
    wl, wr = w_live.reindex(idx).to_numpy()[m], w_rec.reindex(idx).to_numpy()[m]
    split = sc["headline"]

    def head(t: pd.DataFrame, v: str) -> float:
        cs = ((t.R.reindex(idx).to_numpy() >= bar) * t[f"FLOORED.{v}.composite"].reindex(idx).to_numpy())[m]
        return split["live_like"] * (cs * wl).sum() / wl.sum() + split["recency"] * (cs * wr).sum() / wr.sum()

    out = []
    for v in sc["variants"]:
        f = float(np.mean([head(t, v) for t in field_wins.values()]))
        out.append(head(model_win, v) / f if f > 0 else np.nan)
    return float(np.mean(out))
