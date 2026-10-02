"""Why a model wins or loses: its results by market type, with a plain-language reason (report layer only; not a
tool-version file, so nothing is rescored).

Market types of a 14-day window, from BTC's closes (the research panel) and the window's ex-post regime label:
- strong fall (BTC 14-day return <= -5%), mild fall (-5% to 0), mild rise (0 to +5%), strong rise (>= +5%);
- turning point: BTC's first week and second week move at least 2% each, in opposite directions;
- calm / volatile: the low / high tercile of BTC's realized volatility (the regime label).
For each type: the hit rate (mean of the three bar hits), the mean 14-day R_liq and the average net and gross
exposure, all weighted with w'. The reason sentence states where the model is clearly better or worse than its own
average (10 points or more) and what it held there (net long, net short, mostly cash), which is measured, not guessed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TYPES = ("strong fall", "mild fall", "mild rise", "strong rise", "turning point", "calm", "volatile")
FALLS, RISES = ("strong fall", "mild fall"), ("mild rise", "strong rise")


def market_types(starts: pd.DatetimeIndex, btc: pd.Series, regime: pd.Series, hours: int = 336) -> pd.DataFrame:
    """Boolean column per market type (rows = window starts). btc: hourly closes (close-time index)."""
    px = btc.dropna()
    at = lambda t: px.asof(t)                                           # last close at or before t
    r = np.array([at(t + pd.Timedelta(hours=hours)) / at(t) - 1 for t in starts])
    h1 = np.array([at(t + pd.Timedelta(hours=hours // 2)) / at(t) - 1 for t in starts])
    h2 = (1 + r) / (1 + h1) - 1
    vol = regime.reindex(starts).astype(str).str.split("/").str[-1].to_numpy()
    return pd.DataFrame({"strong fall": r <= -0.05, "mild fall": (r > -0.05) & (r < 0), "mild rise": (r >= 0) & (r < 0.05),
                         "strong rise": r >= 0.05,
                         "turning point": (np.abs(h1) >= 0.02) & (np.abs(h2) >= 0.02) & (np.sign(h1) != np.sign(h2)),
                         "calm": vol == "lowvol", "volatile": vol == "highvol"}, index=starts)


def profile(t: pd.DataFrame, types: pd.DataFrame) -> dict[str, dict]:
    """Per type (and 'all'): weight share, hit rate, mean R_liq, net and gross exposure, w'-weighted."""
    w = t.w_final.to_numpy(dtype=float)
    hit = t[["hit_LENIENT", "hit_MIDDLE", "hit_STRICT"]].to_numpy(dtype=float).mean(axis=1)
    cols = {"hit": hit, "R": t.R_liq.to_numpy(dtype=float),
            "net": t["net_avg"].to_numpy(dtype=float) if "net_avg" in t else np.full(len(t), np.nan),
            "gross": t["gross_avg"].to_numpy(dtype=float) if "gross_avg" in t else np.full(len(t), np.nan)}
    out = {}
    for name, m in [("all", np.ones(len(t), bool))] + [(k, types.reindex(t.index)[k].to_numpy(dtype=bool)) for k in TYPES]:
        if not m.any() or w[m].sum() <= 0:
            continue
        ww = w[m] / w[m].sum()
        out[name] = {"share": float(w[m].sum() / w.sum()), **{k: float((ww * v[m]).sum()) for k, v in cols.items()}}
    return out


def _held(p: dict) -> str:
    net, gross = p["net"], p["gross"]
    if not np.isfinite(net):
        return ""
    if gross < 0.25:
        return f"mostly in cash ({gross:.0%} invested)"
    if net <= -0.05:
        return f"net short ({net:+.0%})"
    if net < 0.3:
        return f"close to flat ({net:+.0%} net)"
    return f"{net:.0%} net long"


def reason(p: dict[str, dict], gap: float = 0.10) -> str:
    """One plain sentence: the best and worst market types against the model's own average, and what it held."""
    base = p["all"]["hit"]
    cand = {k: v for k, v in p.items() if k != "all" and v["share"] >= 0.03}
    if not cand:
        return "—"
    best = max(cand, key=lambda k: cand[k]["hit"] - base)
    worst = min(cand, key=lambda k: cand[k]["hit"] - base)
    parts = []
    if cand[best]["hit"] - base >= gap:
        parts.append(f"strong in {best} windows ({cand[best]['hit']:.0%} vs {base:.0%} overall; {_held(cand[best])})")
    if base - cand[worst]["hit"] >= gap:
        why = _held(cand[worst])
        if worst in FALLS and cand[worst]["net"] >= 0.3:
            why = f"it stays {cand[worst]['net']:.0%} net long while prices drop"
        elif worst in RISES and cand[worst]["net"] < 0.4:
            why = f"it is under-invested ({cand[worst]['net']:+.0%} net) while prices rise"
        elif worst == "turning point":
            why = f"its trend signals lag when the trend reverses ({why})"
        parts.append(f"weak in {worst} windows ({cand[worst]['hit']:.0%}; {why})")
    return "; ".join(parts).capitalize() + "." if parts else "About the same in every market type."


def section(names: list[str], tables: dict[str, pd.DataFrame], types: pd.DataFrame) -> list[str]:
    """Markdown: one row per model, hit rate (net exposure) per market type, and the reason."""
    if not names:
        return []
    ref = tables[names[0]]
    share = profile(ref, types)
    head = "| Model | All | " + " | ".join(TYPES) + " | Why (measured) |"
    L = ["", "## Why: results by market type (report-only)", "",
         "Hit rate (mean of the three bars) per type of 14-day window, with the model's average net exposure in "
         "brackets; weights w'. Types from BTC: strong fall <= -5%, mild fall, mild rise, strong rise >= +5% over 14 "
         "days; turning point = first and second week move >= 2% in opposite directions; calm / volatile = low / high "
         "volatility tercile. The sentence names the types at least 10 points above or below the model's own average "
         "and what it held there (backtest/scoring/explain.py).", "",
         head, "|" + "---|" * (len(TYPES) + 3),
         "| *share of weight* | 100% | " + " | ".join(f"{share[k]['share']:.0%}" if k in share else "—" for k in TYPES) + " | |"]
    for n in names:
        p = profile(tables[n], types)
        cells = [f"{p[k]['hit']:.0%} ({p[k]['net']:+.0%})" if k in p and np.isfinite(p[k]['net']) else (f"{p[k]['hit']:.0%}" if k in p else "—")
                 for k in TYPES]
        L.append(f"| {n} | {p['all']['hit']:.0%} | " + " | ".join(cells) + f" | {reason(p)} |")
    return L
