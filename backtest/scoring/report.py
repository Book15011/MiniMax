"""Outputs of a scoring run (docs/EVALUATION.md section 4).

- reports/<model>/<stamp>-score.md and its charts in reports/<model>/<stamp>-score/ (committed with the model);
  the run log is the harness's reports/<model>/<stamp>.log (never committed);
- results/<runner>/<YYYYMMDD>-scoring/<model>-<stamp>/score.json and trades.csv.gz (too large to commit; their
  sha256 is in the report and the registry);
- one registry line per full run, then the leaderboard is regenerated.
"""
from __future__ import annotations

import hashlib
import logging
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.scoring import registry, svg
from backtest.scoring.competition import REL, headline
from backtest.scoring.returnfirst import BARS
from backtest.scoring.score import dumps, score_model
from src.config import REPO_ROOT, resolve
from src.contracts import MEMBERS

VARIANT_NAMES = {"V1": "daily_raw", "V2": "daily_annual", "V3": "hourly_annual", "V4": "total_calmar",
                 REL: "field-relative (1.00 = field average, V1–V4 averaged)"}
FIELD_LABELS = {"team_btc_hold": "BTC_HOLD", "team_ew_daily": "EW_DAILY", "team_rot_ew": "ROT_EW",
                "team_rot_iv": "ROT_IV", "team_trend_2": "TREND_2", "team_mom_ss25": "MOM_SS25", "team_cash": "CASH"}


def runner() -> str:
    m = os.environ.get("MM_MEMBER")
    if m:
        return m
    head = REPO_ROOT.name.split("-", 1)[0]
    return head if REPO_ROOT.parent.name == ".worktrees" and head in MEMBERS else "team"


def pct(x, d=2) -> str:
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x * 100:+.{d}f}%"


def mag(x, d=2) -> str:
    """A non-negative share (drawdown, exposure) without a sign."""
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x * 100:.{d}f}%"


def num(x, d=3) -> str:
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:+.{d}f}"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def field_headlines(ctx: dict, cfg: dict) -> dict[str, dict]:
    """Every benchmark scored exactly like the model: same windows, same field median, same weights."""
    sc = cfg["scoring"]
    out = {}
    for n, r in ctx["field"].items():
        cs = ctx["field_cs"][n]
        w = r.windows.loc[ctx["starts"]]
        head = {c: {v: headline(cs[f"{c}.{v}.cs"], ctx["w_live"], ctx["w_rec"], sc["headline"])["headline"]
                    for v in sc["variants"]} for c in sc["conventions"]}
        for c, hv in head.items():
            hv[REL] = float(np.mean([hv[v] / ctx["field_scale"][c][v] for v in sc["variants"]]))
        out[n] = {"headline": head,
                  "median_R": float(w.R.median()), "worst10_R": float(w.R.quantile(0.1)), "worst_R": float(w.R.min()),
                  "median_MDD": float(w.MDD.median()), "min_active": int(w.active_days.min()),
                  "stress_worst": float(r.windows.R.reindex(ctx["sets"]["STRESS"]).min())}
    return out


def charts(score: dict, ctx: dict, cfg: dict, out: Path) -> list[tuple[str, str]]:
    """Writes the SVG charts; returns [(file name, caption)]."""
    sc, h = cfg["scoring"], cfg["harness"]
    out.mkdir(parents=True, exist_ok=True)
    run, field, starts = ctx["run"], ctx["field"], ctx["starts"]
    name = score["model"]["name"]
    wl = ctx["w_final"]
    pos = {t: k for k, t in enumerate(run.windows.index)}
    hours = h["window_days"] * 24
    step = 4
    xs = np.arange(0, hours + 1, step) / 24.0
    btc = field[sc["btc_hold"]]
    made = []

    top = wl.sort_values(ascending=False).index[: int(sc["report"]["curves"])]
    panels = []
    for t in top:
        k = pos[t]
        fmed = np.median(np.stack([r.equity[k] for r in field.values()]), axis=0)
        panels.append({"title": f"{t:%Y-%m-%d}  w={wl[t] * 1e3:.2f}‰", "x": xs,
                       "series": [(btc.equity[k][::step] - 1, 2), (fmed[::step] - 1, 3), (run.equity[k][::step] - 1, 1)]})
    (out / "curves.svg").write_text(svg.small_multiples(
        f"{name}: the 25 heaviest windows (final weights w')", "Return since the window start (each panel has its own scale), "
        "14 days from cash", panels, [(name, 1), ("BTC_HOLD", 2), ("field median (6 benchmarks)", 3)]))
    made.append(("curves.svg", "Top-25 windows by final weight: equity path vs BTC_HOLD and the field median"))

    R, M = run.windows.R.loc[starts], run.windows.MDD.loc[starts]
    wv = wl.reindex(starts).to_numpy()

    def wmed(x, w):
        o = np.argsort(x)
        c = np.cumsum(w[o]) / w.sum()
        return float(np.asarray(x)[o][np.searchsorted(c, 0.5)])

    lo, hi = np.floor(min(R.quantile(0.005), -0.05) * 50) / 50, np.ceil(max(R.quantile(0.995), 0.05) * 50) / 50
    edges = np.linspace(lo, hi, 41)
    (out / "hist_R.svg").write_text(svg.histogram(
        f"{name}: 14-day return R, weighted by the final weights w'", f"{len(starts)} windows; bar = weighted share; "
        "outliers are clipped into the end bins", R.to_numpy(), wv, edges, "R (mark-to-market)",
        lambda t: f"{t * 100:.0f}%", refs=[(f"{name} weighted median {wmed(R.to_numpy(), wv) * 100:+.2f}%", wmed(R.to_numpy(), wv)),
                                           (f"BTC_HOLD weighted median {wmed(btc.windows.R.loc[starts].to_numpy(), wv) * 100:+.2f}%",
                                            wmed(btc.windows.R.loc[starts].to_numpy(), wv))]))
    made.append(("hist_R.svg", "Weighted distribution of the 14-day return R"))
    edges = np.linspace(0, np.ceil(max(M.quantile(0.995), 0.02) * 50) / 50, 41)
    (out / "hist_MDD.svg").write_text(svg.histogram(
        f"{name}: max drawdown within the window, weighted by w'", f"{len(starts)} windows; bar = weighted share",
        M.to_numpy(), wv, edges, "MDD", lambda t: f"{t * 100:.0f}%",
        refs=[(f"weighted median {wmed(M.to_numpy(), wv) * 100:.2f}%", wmed(M.to_numpy(), wv))]))
    made.append(("hist_MDD.svg", "Weighted distribution of the max drawdown"))

    st = ctx["sets"]["STRESS"].intersection(run.windows.index)
    kinds = {}
    for k, s in enumerate(ctx["sets"]["STRESS"]):
        kinds[s] = "drop" if k < len(ctx["sets"]["STRESS"]) // 2 else "rebound"
    rows = [(f"{kinds[t]} {t:%Y-%m-%d}", float(run.windows.R[t]), float(btc.windows.R[t])) for t in st]
    (out / "stress.svg").write_text(svg.dumbbell(
        f"{name} vs BTC_HOLD on the 20 STRESS windows", "10 sharpest BTC drops and 10 sharpest rebounds (G6, report-only)",
        rows, (name, "BTC_HOLD")))
    made.append(("stress.svg", "STRESS windows: the model's R vs BTC_HOLD's"))

    grid = ctx["grid"]
    med = grid["median"].to_numpy().tolist()
    cnt = grid["count"].to_numpy().tolist()
    (out / "regimes.svg").write_text(svg.heatmap(
        f"{name}: median R by ex-post regime", "Terciles of BTC's 14-day return x its volatility (G3, report-only: no cell "
        f"below {sc['gates']['G3']['min_cell_median_return'] * 100:.0f}%)", med, cnt, ["down", "flat", "up"],
        ["low vol", "mid vol", "high vol"], 0.10, "BTC return", "BTC volatility"))
    made.append(("regimes.svg", "Median R in each cell of the 3x3 regime grid"))

    idx = [pos[t] for t in starts]
    wn = wv / wv.sum()
    gross, net = (wn[:, None] * run.gross[idx]).sum(0), (wn[:, None] * run.net[idx]).sum(0)
    (out / "exposure.svg").write_text(svg.lines(
        f"{name}: exposure through the window", "Weighted mean over windows (final weights w'), share of equity",
        xs, [("gross", gross[::step], 1), ("net", net[::step], 2)], "day of the window", lambda t: f"{t * 100:.0f}%",
        xticks=list(range(0, 15, 2))))
    made.append(("exposure.svg", "Gross and net exposure by hour of the window"))

    e0 = float(sc["e0"])
    fee = np.zeros((len(starts), hours + 1))
    spr = np.zeros((len(starts), hours + 1))
    row_of = {t: k for k, t in enumerate(starts)}
    tr = run.trades[run.trades.window_start.isin(starts)]
    if len(tr):
        at = (tr.window_start.map(row_of).to_numpy(dtype=int), tr.hour.to_numpy(dtype=int))
        np.add.at(fee, at, tr.fee_usd.to_numpy() / e0)
        np.add.at(spr, at, tr.spread_usd.to_numpy() / e0)
    cf, cs_ = (wn[:, None] * np.cumsum(fee, 1)).sum(0), (wn[:, None] * np.cumsum(spr, 1)).sum(0)
    (out / "fees.svg").write_text(svg.lines(
        f"{name}: cumulative trading costs", "Weighted mean over windows, share of the starting equity E_0",
        xs, [("exchange fees", cf[::step], 1), ("spread", cs_[::step], 2)], "day of the window",
        lambda t: f"{t * 100:.2f}%", xticks=list(range(0, 15, 2))))
    made.append(("fees.svg", "Cumulative fees and spread through the window"))

    d = run.days[idx]
    d = d[:, (d >= 0).all(axis=0)]                                  # buckets every window has
    strat = (wn[:, None] * (d == 1)).sum(0)
    guard = (wn[:, None] * (d == 2)).sum(0)
    none = 1.0 - strat - guard
    (out / "active.svg").write_text(svg.stacked_columns(
        f"{name}: active HKT days, strategy vs guard", "Weighted share of windows in which each HKT day (16:00 UTC "
        "boundaries; the first and last are partial) had a strategy trade, only the activity guard's trade, or no trade", [str(k + 1) for k in range(d.shape[1])],
        [("strategy trade", strat, 1), ("guard trade only", guard, 2), ("no trade", none, 0)], "HKT day of the window"))
    made.append(("active.svg", "Active days: strategy trades vs the engine's daily-trade guard"))
    return made


FORMULAS = r"""
Per window (14 days from cash, starting at {wh:02d}:00 UTC like the round; hourly equity E_0..E_336 from the harness engine, which makes the model's first decision at the window start; E_0 = {e0:,.0f} before the first trade):

- R = E_336 / E_0 - 1 (mark-to-market); **R_liq** = (E_336 - {liq} x gross notional at the end) / E_0 - 1, what is left after the system liquidates at the end
- HKT days: boundaries at the start, every 16:00 UTC inside the window and the end (15 daily returns for a 12:00 UTC start, the first 4 h and the last 20 h); UTC days the same with 00:00 UTC (12 h, 13 x 24 h, 12 h). A fill at time t belongs to the day containing t
- MDD = max over k of (1 - E_k / max_(j<=k) E_j), including E_0
- for a series x of length n: m = mean, s = sqrt(sum((x - m)^2) / (n - 1)), dd = sqrt(sum(min(x, 0)^2) / n); Sharpe = m / s, Sortino = m / dd (risk-free 0); a ratio is 0 when m = 0
- V1 daily_raw: Sharpe = m/s, Sortino = m/dd, Calmar = m / MDD (daily r) · V2 daily_annual: (m/s)·√365, (m/dd)·√365, (m·365) / MDD · V3 hourly_annual (hourly h): (m/s)·√8760, (m/dd)·√8760, (m·8760) / MDD · V4 total_calmar: Sharpe and Sortino as V1, Calmar = R / MDD
- Composite = {cw[sortino]} Sortino + {cw[sharpe]} Sharpe + {cw[calmar]} Calmar · FLOORED: s and dd floored at {fl[s_daily]} (daily) and {fl[s_hourly]:.6g} (hourly), MDD at {fl[mdd]} · POL: MDD floored at {pl[mdd]}, s and dd unfloored, a zero denominator gives 0

Across windows:

- weights: LL from `{ll}` (PART 0's method), REC = 0.5^(age / {hl} d), age = days from the start to the latest start; w = {a} LL / sum LL + {b} REC / sum REC; a window is UP if BTC's close at its end >= at its start; w' = w x pi_up / sum_UP w (UP) or w x (1 - pi_up) / sum_DOWN w (DOWN), pi_up = the unweighted share of UP windows
- bars on R_liq: LENIENT = {ld:+.7%} in DOWN windows (the previous edition's #20 cut), {lu:+.1%} in UP windows (ASSUMPTION) · MIDDLE = {mid:+.1%} · STRICT = max({sf:.0%}, median R_liq of the 6 gate benchmarks)
- HIT_b = sum of w' over windows with R_liq >= bar_b · **HEADLINE_RET = (HIT_LENIENT + HIT_MIDDLE + HIT_STRICT) / 3**
- CS_HIT = sum of w' x composite (V1 FLOORED, HKT days) over the windows clearing LENIENT / their sum of w' (0 if none)
- hard gates: G1 >= {g1} active HKT days in {g1s:.0%} of windows · G4 the long-only run completes cleanly · G5 {g5} decisions reproducible, unchanged under future noise, no I/O
- report-only gates: G2 worst R > BTC_HOLD's worst · G3 no regime cell median R < {g3:+.0%} · G6_median STRESS worst >= BTC_HOLD's and median >= BTC_HOLD's · G6_worst STRESS worst >= BTC_HOLD's
"""


def write_report(score: dict, ctx: dict, cfg: dict, md: Path, runtime_s: float, ranks: dict, outputs: dict,
                 log: logging.Logger) -> None:
    sc = cfg["scoring"]
    chart_dir = md.parent / f"{md.stem}"
    made = charts(score, ctx, cfg, chart_dir)
    m, prim, rf = score["model"], score["primary"], score["return_first"]
    win, act, gates, tail = score["windows"], score["activity"], score["gates"], score["tail"]
    full, ins = rf["full"], rf.get("in_sample")
    hard_fail = [g for g, v in gates.items() if v["hard"] and not v["pass"]]
    soft_fail = [g for g, v in gates.items() if not v["hard"] and not v["pass"]]
    L = [f"# {m['name']}: competition-style score (return first)", "", m["description"], "",
         "| | |", "|---|---|",
         f"| Method · author | {m['method']} · {m['author']} · {'candidate' if m['candidate'] else 'reference row (benchmark)'} |",
         f"| Code | commit `{score['code'].get('commit')}`{' (uncommitted changes!)' if score['code'].get('dirty') else ''} · "
         f"run key `{m['run_key']}` · tool version `{score['tool_version']}` (scoring v{score['scoring_version']}) |",
         f"| Windows | {win['scored']} scored, starts {win['first_start'][:16]} → {win['last_start'][:16]} UTC, every day at "
         f"{win['start_hour_utc']:02d}:00 UTC; {win['post_holdout']} end after the spent holdout date "
         f"{win['holdout_from'][:16]} UTC (included: {win['include_spent_holdout']}) |",
         f"| Weights | LL `{sc['live_like']}` (effective n {full['weights']['live_like']['effective_n']:.0f}) · recency half-life "
         f"{full['weights']['recency']['half_life_days']:.0f} d from {full['weights']['recency']['age_from'][:16]} · "
         f"split {sc['headline']['live_like']:.0%} / {sc['headline']['recency']:.0%} · pi_up {full['pi_up']:.3f} · "
         f"effective n of w' {full['weights']['effective_n_final']:.0f} |",
         f"| Data | panel to {score['data']['panel_last'][:16]} UTC · universe `{score['data']['universe_mode']}` · spreads {score['data']['spreads_source']} |",
         f"| Outputs | `{outputs['score_json']}` (sha256 `{outputs['score_sha256'][:16]}…`) · `{outputs['trades_csv']}` |",
         f"| Runtime | {runtime_s:.0f} s (cached parts are reused) |", "",
         "## Summary", "",
         f"**HEADLINE_RET {full['headline_ret']:.3f}** (primary; rank {ranks['primary'][0]} of {ranks['primary'][1]} "
         f"registered runs of this tool version) · without the post-holdout windows "
         f"**{ins['headline_ret']:.3f}** · **{'eligible' if score['eligible'] else 'NOT eligible'}** "
         f"({'hard gates pass' if score['eligible'] else 'fails ' + ', '.join(hard_fail)}"
         f"{'; report-only gates failed: ' + ', '.join(soft_fail) if soft_fail else ''})." if ins else
         f"**HEADLINE_RET {full['headline_ret']:.3f}** · **{'eligible' if score['eligible'] else 'NOT eligible'}**.", "",
         f"CS_HIT (risk second: mean V1 FLOORED composite on HKT days over the windows clearing LENIENT) "
         f"**{full['cs_hit']:.3f}**, on UTC days {full['cs_hit_utc']:.3f}. Pol's period check (REL on the field-best "
         f"bar): SCREEN {num(score['period_check'].get('SCREEN'))}, CONFIRM {num(score['period_check'].get('CONFIRM'))}.", "",
         "| Pool | HEADLINE_RET | HIT LENIENT | HIT MIDDLE | HIT STRICT | UP windows (L / M / S) | DOWN windows (L / M / S) | "
         "Pol's bars q67 / q83 / best | HEADLINE_RET on plain R | CS_HIT | pi_up |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, b in (("full", full), ("without post-holdout", ins)):
        if not b:
            continue
        hu, hd, hp = b["hit_up"] or {}, b["hit_down"] or {}, b["hit_pol_bars"]
        up_txt = " / ".join("—" if hu.get(k) is None else f"{hu[k]:.2f}" for k in BARS)
        down_txt = " / ".join("—" if hd.get(k) is None else f"{hd[k]:.2f}" for k in BARS)
        L.append(f"| {name} ({b['n']}) | **{b['headline_ret']:.3f}** | {b['hit']['LENIENT']:.3f} | {b['hit']['MIDDLE']:.3f} | "
                 f"{b['hit']['STRICT']:.3f} | {up_txt} | {down_txt} | {hp['q67']:.2f} / {hp['q83']:.2f} / {hp['best']:.2f} | "
                 f"{b['headline_ret_plain_R']:.3f} | {b['cs_hit']:.3f} | {b['pi_up']:.3f} |")
    fr = score.get("field_return_first") or {}
    if fr:
        L += ["", "Benchmarks on the same windows, bars and weights (HEADLINE_RET full / without post-holdout): "
              + " · ".join(f"{FIELD_LABELS.get(n, n)} {v['full']['headline_ret']:.3f} / "
                           f"{v.get('in_sample', {}).get('headline_ret', float('nan')):.3f}" for n, v in fr.items()) + "."]
    L += ["", "### Gates", "", "| Gate | Kind | Result | Detail |", "|---|---|---|---|"]
    names = {"G1": "activity", "G2": "worst fortnight", "G3": "regimes", "G4": "shorts disabled", "G5": "leakage",
             "G6_median": "STRESS, median-of-20", "G6_worst": "STRESS, worst-of-20"}
    for g, v in gates.items():
        extra = ""
        if g == "G1":
            extra = (f" · guard-only days {v['guard_share_of_active_days']:.1%} of active days"
                     + (" · **flag: relies on the guard**" if v.get("relies_on_guard") else ""))
        L.append(f"| {g} {names.get(g, '')} | {'hard' if v['hard'] else 'report-only'} | "
                 f"{'PASS' if v['pass'] else '**FAIL**'} | {v['detail']}{extra} |")
    t = tail["full"]
    L += ["", "### Tail (plain R, report-only)", "",
          "| Pool | Worst R | 5th percentile R | Median MDD | p90 MDD | STRESS crashes, median R | STRESS rebounds, median R |",
          "|---|---|---|---|---|---|---|"]
    for name, t in tail.items():
        L.append(f"| {name} | {pct(t['worst_R'])} | {pct(t['p5_R'])} | {mag(t['median_MDD'])} | {mag(t['p90_MDD'])} | "
                 f"{pct(t['stress_drops_median_R'])} | {pct(t['stress_rebounds_median_R'])} |")
    rp = score.get("replay")
    if rp and rp.get("windows"):
        L += ["", "### Previous edition's real windows (report-only, numbers only)", "",
              "| Window | R | Max drawdown | Rank among the real teams |", "|---|---|---|---|"]
        for w in rp["windows"]:
            L.append(f"| {w['name']} | {pct(w['R'])} | {mag(w['MDD'])} | "
                     + ", ".join(f"#{r['rank']} of {r['teams']} (competition {r['competition']})" for r in w["ranks"]) + " |")
    rel = score["rel"]
    L += ["", "### Report-only: the previous primary on these windows", "",
          f"REL (field-best bar, {sc['rel']['convention']}): "
          f"{num(rel['headline'][sc['rel']['convention']]['REL']['headline'])} · robustness min layer "
          f"{num(rel['robustness']['min'])} ({'robust' if rel['robustness']['pass'] else 'not robust'}). "
          "Not comparable with the REL of earlier tool versions (other windows and weights).", "",
          f"Median 14-day R {pct(score['summary']['median_R'])} · worst 10% {pct(score['summary']['worst10_R'])} · "
          f"worst fortnight {pct(score['summary']['worst_R'])} · median R_liq {pct(score['returns_liquidated']['median_R'])}.", "",
          "## Activity, exposure, costs", "",
          "| Min / median active HKT days | Min active UTC days | Guard-only share (HKT / UTC) | Fees / E_0 | Spread / E_0 | "
          "Turnover | Mean gross | Max gross | Mean net | Orders / window | Most orders in one decision |",
          "|---|---|---|---|---|---|---|---|---|---|---|",
          f"| {act['min_active_days']} / {act['median_active_days']:.0f} of {act['day_buckets']} | "
          f"{act['min_active_days_utc']} of {act['day_buckets_utc']} | {act['guard_share_of_active_days']:.1%} / "
          f"{act['guard_share_of_active_days_utc']:.1%} | {act['mean_fees_e0'] * 100:.2f}% | {act['mean_spread_e0'] * 100:.2f}% | "
          f"{act['mean_turnover']:.2f} | {act['mean_gross']:.0%} | {act['max_gross']:.0%} | {act['mean_net']:+.0%} | "
          f"{act['mean_orders']:.0f} | {act['max_calls_one_decision']} |", "",
          f"First decisions at the window start: {win.get('first_decision_calls')} model calls in all; "
          f"{win.get('first_decisions_not_converged')} windows where they never rejoined the shared decisions.", "",
          "## Floor hits (windows where a floor set the denominator)", "",
          "| Convention | s daily | dd daily | s hourly | dd hourly | MDD | of windows |", "|---|---|---|---|---|---|---|"]
    for c, d in score["floor_hits"].items():
        L.append(f"| {c} | {d['s_daily']} | {d['dd_daily']} | {d['s_hourly']} | {d['dd_hourly']} | {d['mdd']} | {win['scored']} |")
    L += ["", "## Charts", ""]
    for f, cap in made:
        L += [f"**{cap}**", "", f"![{cap}]({chart_dir.name}/{f})", ""]
    fl, pl = sc["conventions"]["FLOORED"], sc["conventions"].get("POL", {"mdd": "—"})
    g, bars = sc["gates"], sc["bars"]
    L += ["## Formulas", "", FORMULAS.format(
        wh=int(sc["window_hour_utc"]), e0=float(sc["e0"]), liq=sc["liquidation_cost"], cw=sc["composite"], fl=fl, pl=pl,
        ll=sc["live_like"], hl=sc["recency_half_life_days"], a=sc["headline"]["live_like"], b=sc["headline"]["recency"],
        ld=float(bars["LENIENT"]["down"]), lu=float(bars["LENIENT"]["up"]), mid=float(bars["MIDDLE"]),
        sf=float(bars["STRICT"]["floor"]), g1=g["G1"]["min_active_days"], g1s=g["G1"]["share_of_windows"],
        g3=g["G3"]["min_cell_median_return"], g5=g["G5"]["decisions"]).strip(), "",
        "Every setting is pending team review: docs/EVALUATION.md, TEAM SIGN-OFF CHECKLIST."]
    md.write_text("\n".join(L) + "\n")
    log.info("score report: %s", md)


def publish(score: dict, ctx: dict, cfg: dict, md: Path, runtime_s: float, log: logging.Logger,
            register: bool = True) -> dict:
    """Write score.json and the trades, register a full run, regenerate the leaderboard, then write the report."""
    sc = cfg["scoring"]
    who = runner()
    stamp = md.stem.replace("-score", "")
    out = resolve("results") / who / f"{stamp[:8]}-scoring" / f"{score['model']['name']}-{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    sj = out / "score.json"
    sj.write_text(dumps(score))
    tr = ctx["run"].trades
    tcsv = out / "trades.csv.gz"
    tr.assign(window_start=tr.window_start.map(lambda t: t.isoformat()),
              time_utc=tr.time_utc.map(lambda t: t.isoformat())).to_csv(tcsv, index=False, float_format="%.10g")
    outputs = {"score_json": str(sj.relative_to(REPO_ROOT)), "score_sha256": _sha(sj),
               "trades_csv": str(tcsv.relative_to(REPO_ROOT)), "report": str(md.relative_to(REPO_ROOT))}
    full = bool(score["windows"]["full_run"])
    if register and full:
        registry.append(sc["registry"], registry.entry_from(score, who, outputs))
        registry.write_leaderboard(cfg, score["tool_version"])
        log.info("registered in %s; leaderboard %s", sc["registry"], sc["leaderboard"])
    elif not full:
        log.info("not registered: not a full run (stride %s)", score["windows"]["stride_days"])
    entries, _ = registry.read(sc["registry"])
    cur = registry.current(entries, score["tool_version"])
    if not any(e["run_key"] == score["model"]["run_key"] for e in cur):
        cur = cur + [registry.entry_from(score, who, outputs)]
    ranks = {"primary": registry.rank(cur, score["primary"]["headline"])}
    write_report(score, ctx, cfg, md, runtime_s, ranks, outputs, log)
    log.info("score.json: %s (sha256 %s)", sj, outputs["score_sha256"])
    return outputs


def score_and_publish(model, market, cfg: dict, md: Path, log: logging.Logger, use_cache: bool = True,
                      stride: int | None = None, register: bool = True) -> dict:
    """Score one model, write every output, register it (full runs only) and log the headline and the gates."""
    t0 = time.time()
    score, ctx = score_model(model, market, cfg, use_cache=use_cache, stride=stride, log=log)
    publish(score, ctx, cfg, md, time.time() - t0, log, register)
    rf = score["return_first"]
    log.info("HEADLINE_RET = %.4f (without post-holdout %s), CS_HIT %.4f; eligible: %s", rf["full"]["headline_ret"],
             f"{rf['in_sample']['headline_ret']:.4f}" if "in_sample" in rf else "-", rf["full"]["cs_hit"], score["eligible"])
    for g, v in score["gates"].items():
        log.info("gate %s (%s) %s  %s", g, "hard" if v["hard"] else "report-only", "PASS" if v["pass"] else "FAIL", v["detail"])
    log.info("scoring runtime %.0f s", time.time() - t0)
    return score
