"""Rebuild the tables behind the README charts (docs/assets/data/) from results/, data/ and the git history.

Run on a machine that has results/ and data/ (kept in the team's private archive, see docs/DATA.md).
Drawing the charts needs only the tables: scripts/report/make_charts.py.

    .venv/bin/python scripts/report/build_data.py
"""
from __future__ import annotations

import collections
import csv
import glob
import json
import os
import subprocess

import numpy as np
import pandas as pd

OUT = "docs/assets/data"
TOOL = "3036a0d8bfdaa6a0"                          # scoring v2 tool version: every run compared here used it
ROUND_START = pd.Timestamp("2026-10-04 12:00", tz="UTC")
BRK_CASH_RUN = "results/scoring/cache/book_e20combo_brk_cash/8c149ee12abb99c2.windows.parquet"

LABELS = {
    "book_e20combo_brk_cash": "Final live model (brk_cash)",
    "pol_switch_vt_tl_e20v45": "Launch model (e20v45)",
    "baitoey_vt_mom": "Volume-timed momentum",
    "book_orch": "Orchestrator (research)",
    "team_btc_hold": "BTC hold",
    "team_rot_ew": "Rotation, equal weight",
    "team_rot_iv": "Rotation, inverse vol",
    "team_ew_daily": "Equal weight, daily",
    "team_mom_ss25": "Momentum + 25% shorts",
    "team_trend_2": "BTC/ETH trend",
}
PAPER_BOTS = {
    "data/live_e20v45": "Launch model (e20v45)",
    "data/live_vtmom": "Volume-timed momentum",
    "data/live_shock": "Momentum + shock rule",
    "data/live_mr4h": "Mean reversion, 4h",
    "data/live_mrcap": "Mean reversion, capped",
    "data/live_swtl": "Rotation/trend switch",
    "data/live_swvt": "Volume/trend switch",
    "data/live": "Rotation, equal weight",
}


def write(name: str, rows: list[dict]) -> None:
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{name}: {len(rows)} rows")


def registry() -> dict[str, dict]:
    """The last full run of each model under the scoring v2 tool version."""
    last = {}
    for line in open("results/scoring/registry.jsonl"):
        r = json.loads(line)
        if r.get("full") and r.get("tool_version") == TOOL:
            last[r["model"]] = r
    return last


def window_returns(model: str, reg: dict[str, dict]) -> pd.DataFrame:
    if model == "book_e20combo_brk_cash":
        return pd.read_parquet(BRK_CASH_RUN)[["R_liq", "MDD"]]
    w = json.load(open(reg[model]["score_json"]))["per_window"]
    return pd.DataFrame({"R_liq": w["R_liq"], "MDD": w["MDD"]}, index=pd.to_datetime(w["start"], utc=True))


def distribution(windows: dict[str, pd.DataFrame]) -> None:
    rows = []
    for model, w in windows.items():
        r = w["R_liq"].to_numpy(float)
        rows.append({
            "model": model, "label": LABELS[model], "windows": len(r),
            "mean": round(r.mean(), 5), "median": round(np.median(r), 5),
            "p10": round(np.percentile(r, 10), 5), "p90": round(np.percentile(r, 90), 5),
            "worst": round(r.min(), 5), "best": round(r.max(), 5), "share_positive": round((r > 0).mean(), 4),
            "median_mdd": round(w["MDD"].median(), 5), "worst_mdd": round(w["MDD"].max(), 5),
        })
    write("backtest_distribution.csv", rows)


def by_year(windows: dict[str, pd.DataFrame]) -> None:
    rows = []
    for model in ("book_e20combo_brk_cash", "pol_switch_vt_tl_e20v45", "team_btc_hold"):
        w = windows[model]
        for year, g in w.groupby(w.index.year):
            r = g["R_liq"]
            rows.append({"year": year, "model": model, "windows": len(r), "median": round(r.median(), 5),
                         "p10": round(r.quantile(0.1), 5), "worst": round(r.min(), 5),
                         "share_positive": round((r > 0).mean(), 4)})
    write("backtest_by_year.csv", rows)


def leaderboard(reg: dict[str, dict]) -> None:
    rows = []
    for model, r in reg.items():
        h = r.get("headline_ret")
        if not isinstance(h, dict):
            continue
        rows.append({
            "model": model, "author": r.get("author"), "candidate": bool(r.get("candidate")),
            "headline_ret": round(h["full"], 4), "headline_ret_in_sample": round(h["in_sample"], 4),
            "hit_up": round(float(np.mean(list(r["hit_up"]["full"].values()))), 4),
            "hit_down": round(float(np.mean(list(r["hit_down"]["full"].values()))), 4),
            "cs_hit": round(r["cs_hit"]["full"], 4),
            "median_return": round(r["median_R"], 5), "worst10_return": round(r["worst10_R"], 5),
            "worst_return": round(r["worst_R"], 5), "eligible": r.get("eligible"),
        })
    # The final live model was registered later (registry_2), on the same scoring tool version.
    w = pd.read_parquet(BRK_CASH_RUN)["R_liq"]
    for line in open("results/scoring/registry_2.jsonl"):
        r = json.loads(line)
        if r["model"] == "book_e20combo_brk_cash":
            final = r["row"]
    rows.append({"model": "book_e20combo_brk_cash", "author": "book", "candidate": True,
                 "headline_ret": round(final["original_headline_ret"], 4), "headline_ret_in_sample": "", "hit_up": "", "hit_down": "",
                 "cs_hit": round(final["original_cs_hit"], 4), "median_return": round(w.median(), 5),
                 "worst10_return": round(w.quantile(0.1), 5), "worst_return": round(w.min(), 5), "eligible": final["original_eligible"]})
    rows.sort(key=lambda x: -x["headline_ret"])
    write("leaderboard.csv", rows)


def paper_round() -> None:
    series, summary = {}, []
    for path, label in PAPER_BOTS.items():
        rec = []
        for f in sorted(glob.glob(path + "/logs/*.jsonl")):
            for line in open(f):
                try:
                    x = json.loads(line)
                except ValueError:
                    continue
                if x.get("event") == "snapshot" and "equity" in x:
                    rec.append((pd.Timestamp(x["bar"]), x["equity"], x.get("model")))
        s = pd.DataFrame(rec, columns=["bar", "equity", "model"]).drop_duplicates("bar", keep="last").set_index("bar").sort_index()
        s = s[s.index >= ROUND_START]
        eq = s["equity"] / s["equity"].iloc[0] * 100
        series[label] = eq
        summary.append({"label": label, "model": "/".join(s["model"].unique()), "hours": len(s),
                        "first_bar": s.index[0], "last_bar": s.index[-1], "return": round(eq.iloc[-1] / 100 - 1, 5),
                        "max_drawdown": round((1 - eq / eq.cummax()).max(), 5),
                        "largest_gap_hours": s.index.to_series().diff().max() / pd.Timedelta(hours=1)})
    btc = pd.read_parquet("data/live_e20v45/close_1h.parquet")["BTCUSDT"].dropna()
    btc = btc[btc.index >= ROUND_START]
    series["BTC hold"] = btc / btc.iloc[0] * 100
    summary.append({"label": "BTC hold", "model": "BTCUSDT", "hours": len(btc), "first_bar": btc.index[0], "last_bar": btc.index[-1],
                    "return": round(btc.iloc[-1] / btc.iloc[0] - 1, 5), "max_drawdown": round((1 - btc / btc.cummax()).max(), 5),
                    "largest_gap_hours": btc.index.to_series().diff().max() / pd.Timedelta(hours=1)})
    wide = pd.DataFrame(series).sort_index().round(3)
    wide.index.name = "bar"
    wide.to_csv(os.path.join(OUT, "paper_round.csv"))
    print("paper_round.csv:", wide.shape)
    write("paper_round_summary.csv", summary)


def commits() -> None:
    names = {"Book15011": "Book", "Pol": "Pol", "P": "Pol", "Baitoey": "Baitoey"}
    out = subprocess.run(["git", "log", "--branches=feature/*", "--no-merges", "--until=2026-10-31", "--format=%cs %an"],
                         capture_output=True, text=True, check=True).stdout
    days = collections.defaultdict(collections.Counter)
    for line in out.splitlines():
        day, who = line.split(" ", 1)
        days[day][names.get(who, who)] += 1
    write("commits_by_day.csv", [{"date": d, "Book": days[d]["Book"], "Pol": days[d]["Pol"], "Baitoey": days[d]["Baitoey"]} for d in sorted(days)])


def histogram(windows: dict[str, pd.DataFrame]) -> None:
    r = windows["pol_switch_vt_tl_e20v45"]["R_liq"].to_numpy(float) * 100
    edges = np.arange(-30, 62.5, 2.5)
    counts, _ = np.histogram(np.clip(r, edges[0], edges[-1] - 1e-9), bins=edges)
    write("backtest_histogram.csv", [{"bin_low": edges[i], "bin_high": edges[i + 1], "windows": int(counts[i])} for i in range(len(counts))])
    paper = {x["label"]: x for x in csv.DictReader(open(os.path.join(OUT, "paper_round_summary.csv")))}
    round_ret = float(paper["Launch model (e20v45)"]["return"]) * 100
    write("backtest_histogram_meta.csv", [{"round_return_pct": round_ret, "windows": len(r), "windows_worse_than_round": int((r < round_ret).sum())}])


def scalp() -> None:
    """Hand-copied from deploy/SLEEVE.md (+15.6% over 46 h, converted to a day) and research/book/roostoo_fills/README.md."""
    replay = (1.156 ** (24 / 46) - 1) * 100
    rows = [("Assumed: a resting buy fills when the bid touches it", "Replay at default lots", replay),
            ("Measured fill rules", "Resting buy, sell +1 step, stop 2 steps", -1.6),
            ("Measured fill rules", "Resting buy, sell +1 step, stop 4 steps", -0.5),
            ("Measured fill rules", "Resting buy, sell +1 step, stop 8 steps", -1.3),
            ("Measured fill rules", "Resting buy, no stop (closed trips only)", 0.2),
            ("Measured fill rules", "Buy fills only when the ask falls to it", -10.6),
            ("Measured fill rules", "Market buy at the ask, stop 2 steps", -29.0)]
    write("scalp_fill_rules.csv", [{"group": g, "label": l, "per_day_pct": round(v, 2)} for g, l, v in rows])


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    reg = registry()
    windows = {m: window_returns(m, reg) for m in LABELS}
    distribution(windows)
    by_year(windows)
    leaderboard(reg)
    paper_round()
    histogram(windows)
    scalp()
    commits()


if __name__ == "__main__":
    main()
