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
from backtest.scoring.competition import REL, all_variants, headline
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
    wl = ctx["w_live"]
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
        f"{name}: the 25 most live-like windows", "Return since the window start (each panel has its own scale), "
        "14 days from cash", panels, [(name, 1), ("BTC_HOLD", 2), ("field median (6 benchmarks)", 3)]))
    made.append(("curves.svg", "Top-25 live-like windows: equity path vs BTC_HOLD and the field median, by weight"))

    R, M = run.windows.R.loc[starts], run.windows.MDD.loc[starts]
    wv = wl.reindex(starts).to_numpy()

    def wmed(x, w):
        o = np.argsort(x)
        c = np.cumsum(w[o]) / w.sum()
        return float(np.asarray(x)[o][np.searchsorted(c, 0.5)])

    lo, hi = np.floor(min(R.quantile(0.005), -0.05) * 50) / 50, np.ceil(max(R.quantile(0.995), 0.05) * 50) / 50
    edges = np.linspace(lo, hi, 41)
    (out / "hist_R.svg").write_text(svg.histogram(
        f"{name}: 14-day return R, weighted by live-likeness", f"{len(starts)} windows; bar = weighted share; "
        "outliers are clipped into the end bins", R.to_numpy(), wv, edges, "R (mark-to-market)",
        lambda t: f"{t * 100:.0f}%", refs=[(f"{name} weighted median {wmed(R.to_numpy(), wv) * 100:+.2f}%", wmed(R.to_numpy(), wv)),
                                           (f"BTC_HOLD weighted median {wmed(btc.windows.R.loc[starts].to_numpy(), wv) * 100:+.2f}%",
                                            wmed(btc.windows.R.loc[starts].to_numpy(), wv))]))
    made.append(("hist_R.svg", "Weighted distribution of the 14-day return R"))
    edges = np.linspace(0, np.ceil(max(M.quantile(0.995), 0.02) * 50) / 50, 41)
    (out / "hist_MDD.svg").write_text(svg.histogram(
        f"{name}: max drawdown within the window, weighted by live-likeness", f"{len(starts)} windows; bar = weighted share",
        M.to_numpy(), wv, edges, "MDD", lambda t: f"{t * 100:.0f}%",
        refs=[(f"weighted median {wmed(M.to_numpy(), wv) * 100:.2f}%", wmed(M.to_numpy(), wv))]))
    made.append(("hist_MDD.svg", "Weighted distribution of the max drawdown"))

    st = ctx["sets"]["STRESS"].intersection(run.windows.index)
    kinds = {}
    for k, s in enumerate(ctx["sets"]["STRESS"]):
        kinds[s] = "drop" if k < len(ctx["sets"]["STRESS"]) // 2 else "rebound"
    rows = [(f"{kinds[t]} {t:%Y-%m-%d}", float(run.windows.R[t]), float(btc.windows.R[t])) for t in st]
    (out / "stress.svg").write_text(svg.dumbbell(
        f"{name} vs BTC_HOLD on the 20 STRESS windows", "10 sharpest BTC drops and 10 sharpest rebounds (gate G6)",
        rows, (name, "BTC_HOLD")))
    made.append(("stress.svg", "STRESS windows: the model's R vs BTC_HOLD's"))

    grid = ctx["grid"]
    med = grid["median"].to_numpy().tolist()
    cnt = grid["count"].to_numpy().tolist()
    (out / "regimes.svg").write_text(svg.heatmap(
        f"{name}: median R by ex-post regime", "Terciles of BTC's 14-day return x its volatility (gate G3: no cell "
        f"below {sc['gates']['G3']['min_cell_median_return'] * 100:.0f}%)", med, cnt, ["down", "flat", "up"],
        ["low vol", "mid vol", "high vol"], 0.10, "BTC return", "BTC volatility"))
    made.append(("regimes.svg", "Median R in each cell of the 3x3 regime grid"))

    idx = [pos[t] for t in starts]
    wn = wv / wv.sum()
    gross, net = (wn[:, None] * run.gross[idx]).sum(0), (wn[:, None] * run.net[idx]).sum(0)
    (out / "exposure.svg").write_text(svg.lines(
        f"{name}: exposure through the window", "Weighted mean over windows (live-like weights), share of equity",
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
    strat = (wn[:, None] * (d == 1)).sum(0)
    guard = (wn[:, None] * (d == 2)).sum(0)
    none = 1.0 - strat - guard
    (out / "active.svg").write_text(svg.stacked_columns(
        f"{name}: active days, strategy vs guard", "Weighted share of windows in which each day had a strategy "
        "trade, only the activity guard's trade, or no trade", [str(k + 1) for k in range(d.shape[1])],
        [("strategy trade", strat, 1), ("guard trade only", guard, 2), ("no trade", none, 0)], "day of the window"))
    made.append(("active.svg", "Active days: strategy trades vs the engine's daily-trade guard"))
    return made


FORMULAS = r"""
Per window (14 days from cash, hourly equity E_0..E_336 from the harness engine; E_0 = {e0:,.0f} before the first trade):

- daily equity D_d = E_(24d), d = 0..14; daily returns r_d = D_d / D_(d-1) - 1 (14 values); hourly returns h_k = E_k / E_(k-1) - 1 (336 values)
- R = E_336 / E_0 - 1 (mark-to-market, primary); R_liq = (E_336 - {liq} x gross notional at the end) / E_0 - 1
- MDD = max over k of (1 - E_k / max_(j<=k) E_j), including E_0
- for a series x of length n: m = mean, s = sqrt(sum((x - m)^2) / (n - 1)), dd = sqrt(sum(min(x, 0)^2) / n); Sharpe = m / s, Sortino = m / dd (risk-free 0); a ratio is 0 when m = 0
- V1 daily_raw: Sharpe = m/s, Sortino = m/dd, Calmar = m / MDD (daily r) · V2 daily_annual: (m/s)·√365, (m/dd)·√365, (m·365) / MDD · V3 hourly_annual (hourly h): (m/s)·√8760, (m/dd)·√8760, (m·8760) / MDD · V4 total_calmar: Sharpe and Sortino as V1, Calmar = R / MDD
- Composite = {cw[sortino]} Sortino + {cw[sharpe]} Sharpe + {cw[calmar]} Calmar
- FLOORED: s and dd floored at {fl[s_daily]} (daily) and {fl[s_hourly]:.6g} = 0.001/√24 (hourly), MDD floored at {fl[mdd]} in Calmar · POL: MDD floored at {pl[mdd]}, s and dd unfloored, a zero denominator gives 0 (backtest/metrics.py)

Across windows:

- return gate: gate_w = 1 if R_w >= max({gf}, median of the 6 benchmarks' R_w), else 0 · CS_w = gate_w x Composite_w
- LIVE-LIKE weights from `{ll}` (PART 0), renormalized over the scored windows · RECENCY weight = 0.5^(age / {hl}), age = days from the window's end to T* = {ts}
- HEADLINE = {a} x (sum w_live CS / sum w_live) + {b} x (sum w_rec CS / sum w_rec)
- REL: CS_w(REL) = mean over V1–V4 of CS_w(v) / F(v), F(v) = the 6 benchmarks' mean HEADLINE(v); so HEADLINE(REL) = mean over v of HEADLINE(v) / F(v), and 1.00 is the field average
- Gates: G1 >= {g1} active days in {g1s:.0%} of windows (guard days count; flagged above {g1g:.0%} of active days) · G2 worst R > BTC_HOLD's worst · G3 no regime cell median R < {g3:+.0%} · G4 long-only run (negative targets set to 0) completes and passes G1 and G2 · G5 {g5} decisions: reproducible, unchanged when all data after t is random-walk noise, no I/O · G6 STRESS worst R >= BTC_HOLD's worst and median R >= BTC_HOLD's median
"""


def write_report(score: dict, ctx: dict, cfg: dict, md: Path, runtime_s: float, ranks: dict, outputs: dict,
                 log: logging.Logger) -> None:
    sc = cfg["scoring"]
    chart_dir = md.parent / f"{md.stem}"
    made = charts(score, ctx, cfg, chart_dir)
    fh = field_headlines(ctx, cfg)
    m, prim = score["model"], score["primary"]
    pc, pv = prim["convention"], prim["variant"]
    win = score["windows"]
    wts = score["weights"]
    act = score["activity"]
    gates = score["gates"]
    L = [f"# {m['name']}: competition-style score", "", m["description"], "",
         "| | |", "|---|---|",
         f"| Method · author | {m['method']} · {m['author']} |",
         f"| Code | commit `{score['code'].get('commit')}`{' (uncommitted changes!)' if score['code'].get('dirty') else ''} · "
         f"run key `{m['run_key']}` · tool version `{score['tool_version']}` (scoring v{score['scoring_version']}) |",
         f"| Windows | {win['scored']} scored (stride {win['stride_days']} day{'s' if win['stride_days'] != 1 else ''}), "
         f"starts {win['first_start'][:10]} → {win['last_start'][:10]}; holdout sealed from {win['holdout_sealed_from'][:16]} UTC |",
         f"| Weights | live-like: `{wts['live_like']['source']}` (effective n {wts['live_like']['effective_n']:.0f}) · "
         f"recency: half-life {wts['recency']['half_life_days']:.0f} d to T* {wts['recency']['t_star'][:16]} "
         f"(effective n {wts['recency']['effective_n']:.0f}) · split {sc['headline']['live_like']:.0%} / {sc['headline']['recency']:.0%} |",
         f"| Data | panel to {score['data']['panel_last'][:16]} UTC · universe `{score['data']['universe_mode']}` · spreads {score['data']['spreads_source']} |",
         f"| Outputs | `{outputs['score_json']}` (sha256 `{outputs['score_sha256'][:16]}…`) · `{outputs['trades_csv']}` |",
         f"| Runtime | {runtime_s:.0f} s (cached parts are reused) |", "",
         "## Summary", "",
         f"**HEADLINE {pv} {pc} (primary): {num(prim['headline'])}**"
         f"{' (1.00 = the field average under all four readings)' if pv == REL else ''}, rank {ranks[pc][pv][0]} of {ranks[pc][pv][1]} "
         f"scored runs · **{'eligible' if score['eligible'] else 'NOT eligible'}** "
         f"({'all gates pass' if score['eligible'] else 'fails ' + ', '.join(g for g, v in gates.items() if not v['pass'])}).", "",
         f"Median 14-day R {pct(score['summary']['median_R'])} · worst 10% {pct(score['summary']['worst10_R'])} · "
         f"worst fortnight {pct(score['summary']['worst_R'])} · median MDD {mag(score['summary']['median_MDD'])} "
         f"(liquidated median R {pct(score['returns_liquidated']['median_R'])}).", "",
         "| Variant | " + " | ".join(f"{c} | rank" for c in sc["conventions"]) + " | Live-like layer | Recency layer |",
         "|---|" + "---|---|" * len(sc["conventions"]) + "---|---|"]
    for v in all_variants(sc):
        cells = " | ".join(f"{num(score['headline'][c][v]['headline'])} | {ranks[c][v][0]}/{ranks[c][v][1]}"
                           for c in sc["conventions"])
        tag = " (primary)" if v == pv else ""
        L.append(f"| {v} {VARIANT_NAMES.get(v, '')}{tag} | {cells} | {num(score['headline'][pc][v]['live_like'])} | "
                 f"{num(score['headline'][pc][v]['recency'])} |")
    L += ["", f"Layers use the {pc} convention. Ranks are among the full runs in the registry with this tool version "
          "(identical results counted once).", "", "### Gates", "", "| Gate | Result | Detail |", "|---|---|---|"]
    names = {"G1": "activity", "G2": "worst fortnight", "G3": "regimes", "G4": "shorts disabled", "G5": "leakage",
             "G6": "STRESS survival"}
    for g, v in gates.items():
        extra = ""
        if g == "G1" and v.get("relies_on_guard"):
            extra = f" · **flag: {v['guard_share_of_active_days']:.0%} of active days come only from the guard**"
        elif g == "G1":
            extra = f" · guard-only days {v['guard_share_of_active_days']:.1%} of active days"
        if g == "G4" and v.get("headline_primary_long_only") is not None:
            extra = f" · long-only HEADLINE {num(v['headline_primary_long_only'])}"
        L.append(f"| {g} {names.get(g, '')} | {'PASS' if v['pass'] else '**FAIL**'} | {v['detail']}{extra} |")
    lay = score["layers"]
    L += ["", f"### Layer scores ({pv} {pc})", "",
          "| Layer | Role | n | CS | Median R | Worst 10% | Worst | Gate passed |", "|---|---|---|---|---|---|---|---|",
          f"| LIVE-LIKE | {sc['headline']['live_like']:.0%} of HEADLINE, weighted | {win['scored']} "
          f"(effective {wts['live_like']['effective_n']:.0f}) | {num(prim['live_like'])} | {pct(lay['weighted']['live_like']['median_R'])} | "
          f"{pct(lay['weighted']['live_like']['worst10_R'])} | {pct(score['summary']['worst_R'])} | {lay['weighted']['live_like']['gate_pass_share']:.0%} |",
          f"| RECENCY | {sc['headline']['recency']:.0%} of HEADLINE, weighted | {win['scored']} "
          f"(effective {wts['recency']['effective_n']:.0f}) | {num(prim['recency'])} | {pct(lay['weighted']['recency']['median_R'])} | "
          f"{pct(lay['weighted']['recency']['worst10_R'])} | {pct(score['summary']['worst_R'])} | {lay['weighted']['recency']['gate_pass_share']:.0%} |"]
    for k, role in (("ALL_flat", "report only, flat mean"), ("RECENT25", "report only"), ("LOOKALIKE25", "report only"),
                    ("STRESS", "gate G6 only")):
        b = lay[k]
        if not b.get("n"):
            continue
        L.append(f"| {k} | {role} | {b['n']} | {num(b['mean_cs_primary'])} | {pct(b['median_R'])} | {pct(b['worst10_R'])} | "
                 f"{pct(b['worst_R'])} | {b['gate_pass_share']:.0%} |")
    L += ["", "### Comparison with the benchmarks (same windows, same field median and weights)", "",
          f"| Model | HEADLINE {pv} {pc} | {pv} POL | Median R | Worst 10% | Worst | Median MDD | STRESS worst | Min active days |",
          "|---|---|---|---|---|---|---|---|---|",
          f"| **{m['name']}** | **{num(prim['headline'])}** | {num(score['headline'].get('POL', {}).get(pv, {}).get('headline'))} | "
          f"{pct(score['summary']['median_R'])} | {pct(score['summary']['worst10_R'])} | {pct(score['summary']['worst_R'])} | "
          f"{mag(score['summary']['median_MDD'])} | {pct(gates['G6'].get('worst'))} | {act['min_active_days']} |"]
    for n, f in fh.items():
        L.append(f"| {FIELD_LABELS.get(n, n)} | {num(f['headline'][pc][pv])} | {num(f['headline'].get('POL', {}).get(pv))} | "
                 f"{pct(f['median_R'])} | {pct(f['worst10_R'])} | {pct(f['worst_R'])} | {mag(f['median_MDD'])} | "
                 f"{pct(f['stress_worst'])} | {f['min_active']} |")
    hits = score["floor_hits"]
    L += ["", "## Activity, exposure, costs", "",
          "| Min / median active days | Guard-only share of active days | Fees / E_0 | Spread / E_0 | Turnover | "
          "Mean gross | Max gross | Mean net | Orders / window | Most orders in one decision |",
          "|---|---|---|---|---|---|---|---|---|---|",
          f"| {act['min_active_days']} / {act['median_active_days']:.0f} | {act['guard_share_of_active_days']:.1%} | "
          f"{act['mean_fees_e0'] * 100:.2f}% | {act['mean_spread_e0'] * 100:.2f}% | {act['mean_turnover']:.2f} | "
          f"{act['mean_gross']:.0%} | {act['max_gross']:.0%} | {act['mean_net']:+.0%} | {act['mean_orders']:.0f} | "
          f"{act['max_calls_one_decision']} |", "",
          "Means over the scored windows. Orders follow the shared planner's rules (a long-to-short flip is two orders); "
          "each decision also needs the bot's balance and price queries, which are not counted here.", "",
          "## Floor hits (windows where a floor set the denominator)", "",
          "| Convention | s daily | dd daily | s hourly | dd hourly | MDD | of windows |", "|---|---|---|---|---|---|---|"]
    for c, d in hits.items():
        L.append(f"| {c} | {d['s_daily']} | {d['dd_daily']} | {d['s_hourly']} | {d['dd_hourly']} | {d['mdd']} | {win['scored']} |")
    L += ["", "POL has no s or dd floor: its column counts zero denominators, where the ratio is set to 0.", "", "## Charts", ""]
    for f, cap in made:
        L += [f"**{cap}**", "", f"![{cap}]({chart_dir.name}/{f})", ""]
    fl, pl = sc["conventions"]["FLOORED"], sc["conventions"].get("POL", {"mdd": "—"})
    g = sc["gates"]
    L += ["## Formulas", "", FORMULAS.format(
        e0=float(sc["e0"]), liq=sc["liquidation_cost"], cw=sc["composite"], fl=fl, pl=pl, gf=sc["return_gate_floor"],
        ll=sc["live_like"], hl=sc["recency_half_life_days"], ts=sc["t_star"], a=sc["headline"]["live_like"],
        b=sc["headline"]["recency"], g1=g["G1"]["min_active_days"], g1s=g["G1"]["share_of_windows"],
        g1g=g["G1"]["guard_flag_share"], g3=g["G3"]["min_cell_median_return"], g5=g["G5"]["decisions"]).strip(), "",
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
    ranks = {c: {v: registry.rank(cur, score["headline"][c][v]["headline"], c, v) for v in all_variants(sc)}
             for c in sc["conventions"]}
    write_report(score, ctx, cfg, md, runtime_s, ranks, outputs, log)
    log.info("score.json: %s (sha256 %s)", sj, outputs["score_sha256"])
    return outputs


def score_and_publish(model, market, cfg: dict, md: Path, log: logging.Logger, use_cache: bool = True,
                      stride: int | None = None, register: bool = True) -> dict:
    """Score one model, write every output, register it (full runs only) and log the headline and the gates."""
    t0 = time.time()
    score, ctx = score_model(model, market, cfg, use_cache=use_cache, stride=stride, log=log)
    publish(score, ctx, cfg, md, time.time() - t0, log, register)
    p = score["primary"]
    log.info("HEADLINE %s %s = %+.4f (live-like %+.4f, recency %+.4f); eligible: %s", p["variant"], p["convention"],
             p["headline"], p["live_like"], p["recency"], score["eligible"])
    for g, v in score["gates"].items():
        log.info("gate %s %s  %s", g, "PASS" if v["pass"] else "FAIL", v["detail"])
    log.info("scoring runtime %.0f s", time.time() - t0)
    return score
