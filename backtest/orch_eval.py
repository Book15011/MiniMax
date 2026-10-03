"""The skill gate of book_orch's forecaster and its report-only diagnostics (reports/review/20261003-prereg-orch-v2.md,
section 2.6), from the stored out-of-sample forecasts of backtest/orch_train.py and the labels in rows.parquet.

    PYTHONPATH=. python -m backtest.orch_eval --out results/book/20261003-book-orch-v2/ml

Gate (all on forecast rows with a label, from the first retrain):
- G-a: per horizon, multi-class log loss of the forecast below that of the base-rate predictor (the same training
  windows' class shares), at all three horizons;
- G-b: IC_t = Spearman correlation across coins at hour t of q with r_8 (hours with >= 10 coins); mean over hours
  >= 0.02 and the yearly mean > 0 in at least 3 of 2023-2026;
- G-c: the `shuffled` forecasts' G-b statistic within +-0.005 (the `shuffled_hour` one is reported);
- G-d: mean r_8 of confident-RISE rows >= 2 x mean c; of confident-FALL rows <= -2 x mean c (short round trip = c).
Diagnostics: L and S alone, calibration (B2), q buckets (B1), return size by probability (B3), per coin (B4, IC,
precision). Nothing here is tuned on; it writes gate.json and diagnostics.json next to the forecasts.
"""
from __future__ import annotations

import argparse
import json
import logging

import numpy as np
import pandas as pd

from src.config import resolve

HORIZONS = (2, 4, 8)
CLASSES = ("fall", "flat", "rise")
SHORT = {"fall": "f", "flat": "n", "rise": "r"}
GATE_YEARS = (2023, 2024, 2025, 2026)
MIN_COINS = 10
EPS = 1e-15
log = logging.getLogger("orch_eval")


def load(out: str, kind: str = "real", detail: bool = True) -> pd.DataFrame:
    """Forecasts joined to their labels (r_h, y_h, c) by (t, coin)."""
    f = pd.read_parquet(resolve(out) / kind / ("forecasts_detail.parquet" if detail else "forecasts.parquet"))
    rows = pd.read_parquet(resolve(out) / "rows.parquet",
                           columns=["t", "coin", "c"] + [f"r{h}" for h in HORIZONS] + [f"y{h}" for h in HORIZONS])
    df = f.merge(rows, on=["t", "coin"], how="left", validate="one_to_one")
    for suf in ("", "_L", "_S"):
        if f"pr2{suf}" in df:
            pr = df[[f"pr{h}{suf}" for h in HORIZONS]].to_numpy()
            pf = df[[f"pf{h}{suf}" for h in HORIZONS]].to_numpy()
            df[f"q{suf}"] = (pr - pf).mean(axis=1)
            df[f"p_rise{suf}"], df[f"p_fall{suf}"] = pr.mean(axis=1), pf.mean(axis=1)
    df["year"] = df.t.dt.year
    df["day"] = df.t.dt.floor("D")
    return df


def base_rates(manifest: dict, which: str) -> pd.DataFrame:
    """Per retrain and horizon, the base-rate probabilities: which = pbar (L/S average), pbar_L or pbar_S."""
    rows = []
    for e in manifest["models"]:
        for h in HORIZONS:
            rows.append({"retrain": pd.Timestamp(e["retrain"]), "h": h, **dict(zip(CLASSES, e["horizons"][str(h)][which]))})
    return pd.DataFrame(rows)


def spearman(a: pd.Series, b: pd.Series) -> float:
    """Spearman correlation as the Pearson correlation of ranks (average ties); no scipy needed."""
    a, b = pd.Series(np.asarray(a, dtype=float)), pd.Series(np.asarray(b, dtype=float))
    ok = a.notna() & b.notna()
    return float(a[ok].rank().corr(b[ok].rank())) if ok.sum() > 2 else np.nan


def logloss(P: np.ndarray, y: np.ndarray) -> float:
    return float(-np.mean(np.log(np.clip(P[np.arange(len(y)), y], EPS, 1.0))))


def gate_a(df: pd.DataFrame, manifest: dict, suf: str = "") -> dict:
    which = {"": "pbar", "_L": "pbar_L", "_S": "pbar_S"}[suf]
    br = base_rates(manifest, which)
    out = {}
    for h in HORIZONS:
        d = df[df[f"y{h}"] >= 0]
        y = d[f"y{h}"].to_numpy(dtype=int)
        P = d[[f"p{SHORT[c]}{h}{suf}" for c in CLASSES]].to_numpy(dtype=float)
        b = br[br.h == h].set_index("retrain")[list(CLASSES)].reindex(d.retrain.dt.tz_convert("UTC")).to_numpy(dtype=float)
        out[h] = {"rows": int(len(d)), "logloss": logloss(P, y), "logloss_base_rate": logloss(b, y)}
        out[h]["better"] = out[h]["logloss"] < out[h]["logloss_base_rate"]
    return out


def hourly_ic(df: pd.DataFrame, sig: str, ret: str) -> pd.Series:
    """Spearman correlation across coins at each hour (hours with >= MIN_COINS coins having both values)."""
    d = df[["t", sig, ret]].dropna()
    n = d.groupby("t")[sig].transform("size")
    d = d[n >= MIN_COINS]
    rx = d.groupby("t")[sig].rank()
    ry = d.groupby("t")[ret].rank()
    g = d.t
    mx, my = rx.groupby(g).transform("mean"), ry.groupby(g).transform("mean")
    dx, dy = rx - mx, ry - my
    num = (dx * dy).groupby(g).sum()
    den = np.sqrt((dx * dx).groupby(g).sum() * (dy * dy).groupby(g).sum())
    return (num / den.where(den > 0)).dropna()


def ic_summary(ic: pd.Series) -> dict:
    daily = ic.groupby(ic.index.floor("D")).mean()
    t = float(daily.mean() / daily.std(ddof=1) * np.sqrt(len(daily))) if len(daily) > 1 else np.nan
    by_year = ic.groupby(ic.index.year).mean()
    return {"mean": float(ic.mean()), "hours": int(len(ic)), "t_daily": t, "share_hours_positive": float((ic > 0).mean()),
            "by_year": {int(y): float(v) for y, v in by_year.items()}}


def gate_b(df: pd.DataFrame, suf: str = "") -> dict:
    out = {"q": ic_summary(hourly_ic(df.assign(_s=df[f"q{suf}"]), "_s", "r8"))}
    for h in HORIZONS:
        s = df[f"pr{h}{suf}"] - df[f"pf{h}{suf}"]
        out[f"h{h}"] = ic_summary(hourly_ic(df.assign(_s=s), "_s", f"r{h}"))
    q = out["q"]
    q["years_positive"] = int(sum(q["by_year"].get(y, -1.0) > 0 for y in GATE_YEARS))
    q["pass"] = q["mean"] >= 0.02 and q["years_positive"] >= 3
    return out


def confident(df: pd.DataFrame, margin: float, suf: str = "") -> dict:
    d = df[df.r8.notna()]
    out = {}
    for side, cls in (("rise", 2), ("fall", 0)):
        sel = d[d[f"p_{side}{suf}"] >= d[f"pbar_{side}"] + margin]
        out[side] = {"n": int(len(sel)), "hit_rate": float((sel.y8 == cls).mean()) if len(sel) else np.nan,
                     "mean_r8": float(sel.r8.mean()) if len(sel) else np.nan,
                     "two_round_trips": float(2.0 * sel.c.mean()) if len(sel) else np.nan}
    r, f = out["rise"], out["fall"]
    out["G_d_long"] = bool(r["n"] > 0 and r["mean_r8"] >= r["two_round_trips"])
    out["G_d_short"] = bool(f["n"] > 0 and f["mean_r8"] <= -f["two_round_trips"])
    return out


def calibration(df: pd.DataFrame, suf: str) -> dict:
    out = {}
    for h in HORIZONS:
        d = df[df[f"y{h}"] >= 0]
        y = d[f"y{h}"].to_numpy(dtype=int)
        P = d[[f"p{SHORT[c]}{h}{suf}" for c in CLASSES]].to_numpy(dtype=float)
        Y = np.eye(3)[y]
        res = {"brier": float(((P - Y) ** 2).sum(axis=1).mean())}
        for j, c in enumerate(CLASSES):
            b = np.minimum((P[:, j] * 10).astype(int), 9)
            tab = pd.DataFrame({"bin": b, "p": P[:, j], "y": Y[:, j]}).groupby("bin").agg(n=("p", "size"), mean_p=("p", "mean"),
                                                                                         freq=("y", "mean"))
            res[c] = {"ece": float((tab.n / tab.n.sum() * (tab.mean_p - tab.freq).abs()).sum()),
                      "bins": {int(k): {"n": int(v.n), "mean_p": float(v.mean_p), "freq": float(v.freq)} for k, v in tab.iterrows()}}
        out[h] = res
    return out


def buckets(df: pd.DataFrame, sig: str = "q", by_coin: bool = False) -> dict:
    """B1: every hour with >= MIN_COINS coins, 5 equal-count buckets by the signal; mean r_8 per bucket."""
    d = df[["t", "coin", "year", sig, "r8"]].dropna()
    d = d[d.groupby("t")[sig].transform("size") >= MIN_COINS].copy()
    rk = d.groupby("t")[sig].rank(method="first")
    n = d.groupby("t")[sig].transform("size")
    d["bucket"] = np.minimum(((rk - 1) * 5 // n).astype(int), 4) + 1
    if by_coin:
        return {c: {int(b): float(v) for b, v in g.groupby("bucket").r8.mean().items()} for c, g in d.groupby("coin")}
    hb = d.groupby(["t", "bucket"]).r8.mean().unstack()
    pooled = hb.mean()
    spread = (hb[5] - hb[1]).dropna()
    daily = spread.groupby(spread.index.floor("D")).mean()
    yearly = hb.groupby(hb.index.year).mean()
    mono = spearman(pooled.index.to_numpy(), pooled.to_numpy())
    return {"pooled": {int(k): float(v) for k, v in pooled.items()},
            "by_year": {int(y): {int(k): float(v) for k, v in r.items()} for y, r in yearly.iterrows()},
            "top_minus_bottom": float(spread.mean()), "t_daily": float(daily.mean() / daily.std(ddof=1) * np.sqrt(len(daily))),
            "monotonic_spearman": mono}


def size_by_probability(df: pd.DataFrame) -> dict:
    """B3: mean r_8 by 0.1 bin of P(rise) and P(fall) (horizon means), and the +0.15 / +0.25 confident groups."""
    d = df[df.r8.notna()]
    out = {}
    for side, cls in (("rise", 2), ("fall", 0)):
        p = d[f"p_{side}"]
        b = np.minimum((p * 10).astype(int), 9)
        tab = d.groupby(b).agg(n=("r8", "size"), mean_r8=("r8", "mean"))
        groups = {}
        for m in (0.15, 0.25):
            sel = d[p >= d[f"pbar_{side}"] + m]
            groups[f"+{m}"] = {"n": int(len(sel)), "hit_rate": float((sel.y8 == cls).mean()) if len(sel) else np.nan,
                               "mean_r8": float(sel.r8.mean()) if len(sel) else np.nan}
        out[side] = {"bins": {int(k): {"n": int(v.n), "mean_r8": float(v.mean_r8)} for k, v in tab.iterrows()},
                     "confident": groups}
    return out


def per_coin(df: pd.DataFrame) -> dict:
    """Per coin: IC of q with r_8 over its rows, the IC of daily means with its t, and confident-call precision."""
    out = {}
    d = df[df.r8.notna()]
    for c, g in d.groupby("coin"):
        daily = g.groupby("day")[["q", "r8"]].mean()
        rho = spearman(daily.q, daily.r8)
        n = len(daily)
        t = float(rho * np.sqrt(max(n - 2, 1)) / np.sqrt(max(1e-12, 1 - rho * rho))) if np.isfinite(rho) else np.nan
        cr = g[g.p_rise >= g.pbar_rise + 0.15]
        cf = g[g.p_fall >= g.pbar_fall + 0.15]
        res = {"rows": int(len(g)), "ic_rows": spearman(g.q, g.r8), "ic_daily": rho, "t_daily": t,
               "days": int(n), "conf_rise_n": int(len(cr)), "conf_rise_precision": float((cr.y8 == 2).mean()) if len(cr) else np.nan,
               "conf_rise_mean_r8": float(cr.r8.mean()) if len(cr) else np.nan, "conf_fall_n": int(len(cf)),
               "conf_fall_precision": float((cf.y8 == 0).mean()) if len(cf) else np.nan,
               "conf_fall_mean_r8": float(cf.r8.mean()) if len(cf) else np.nan}
        for m in (0.15, 0.25):
            for side, cls in (("rise", 2), ("fall", 0)):
                sel = g[g[f"p_{side}"] >= g[f"pbar_{side}"] + m]
                res[f"B3_{side}_+{m}"] = {"n": int(len(sel)), "hit_rate": float((sel.y8 == cls).mean()) if len(sel) else np.nan,
                                         "mean_r8": float(sel.r8.mean()) if len(sel) else np.nan}
        res["predictable"] = bool(np.isfinite(rho) and rho > 0 and t >= 2.0)
        out[c] = res
    return out


def run(out: str) -> dict:
    man = json.loads((resolve("validation/book_orch_v2_forecasts.json")).read_text())
    df = load(out, "real")
    gate = {"rows": int(len(df)), "first": str(df.t.min()), "last": str(df.t.max())}
    gate["G_a"] = gate_a(df, man)
    gate["G_a"]["pass"] = all(gate["G_a"][h]["better"] for h in HORIZONS)
    gate["G_b"] = gate_b(df)
    controls = {}
    for kind in ("shuffled", "shuffled_hour"):
        s = load(out, kind, detail=False)              # its q against the real labels (rows.parquet is never shuffled)
        controls[kind] = ic_summary(hourly_ic(s, "q", "r8"))
    gate["G_c"] = {"shuffled": controls["shuffled"], "shuffled_hour": controls["shuffled_hour"],
                   "pass": abs(controls["shuffled"]["mean"]) < 0.005}
    gate["G_d"] = confident(df, 0.15)
    common = gate["G_a"]["pass"] and gate["G_b"]["q"]["pass"] and gate["G_c"]["pass"]
    gate["long_gate"] = bool(common and gate["G_d"]["G_d_long"])
    gate["short_gate"] = bool(common and gate["G_d"]["G_d_short"])
    diag = {"L": {"G_a": gate_a(df, man, "_L"), "G_b": gate_b(df, "_L"), "G_d": confident(df, 0.15, "_L")},
            "S": {"G_a": gate_a(df, man, "_S"), "G_b": gate_b(df, "_S"), "G_d": confident(df, 0.15, "_S")},
            "B1": buckets(df), "B2": {name: calibration(df, suf) for name, suf in (("combined", ""), ("L", "_L"), ("S", "_S"))},
            "B3": size_by_probability(df), "B4_B1": buckets(df, by_coin=True), "per_coin": per_coin(df)}
    o = resolve(out)
    (o / "gate.json").write_text(json.dumps(gate, indent=1, default=float))
    (o / "diagnostics.json").write_text(json.dumps(diag, indent=1, default=float))
    return {"gate": gate, "diag": diag}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    r = run(a.out)
    g = r["gate"]
    print(json.dumps({k: g[k] for k in ("long_gate", "short_gate")}, indent=1))
    print("G-a", {h: (round(g["G_a"][h]["logloss"], 5), round(g["G_a"][h]["logloss_base_rate"], 5)) for h in HORIZONS})
    print("G-b q", {k: g["G_b"]["q"][k] for k in ("mean", "t_daily", "by_year", "years_positive", "pass")})
    print("G-c", {k: round(g["G_c"][k]["mean"], 5) for k in ("shuffled", "shuffled_hour")}, g["G_c"]["pass"])
    print("G-d", json.dumps(g["G_d"], default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
