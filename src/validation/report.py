"""Markdown rendering for reports/validation_set_v1.md."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _fmt(v, nd: int = 4) -> str:
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "—"
    if isinstance(v, (float, np.floating)):
        return f"{v:.{nd}f}"
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d %H:%M")
    return str(v)


def table(df: pd.DataFrame, nd: int = 4, index: bool = True) -> str:
    cols = ([df.index.name or ""] if index else []) + [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for idx, row in df.iterrows():
        cells = ([_fmt(idx, nd)] if index else []) + [_fmt(x, nd) for x in row.tolist()]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def _skill_cell(s: pd.Series) -> str:
    if not np.isfinite(s["skill"]):
        return "—"
    return f"{s['skill']:+.3f} [{s['lo']:+.3f}, {s['hi']:+.3f}]"


def _coverage(notes: dict, artifact: dict, groups_ok: dict, universe: pd.DataFrame) -> str:
    p = notes.get("panel", {})
    lines = [f"- Hourly panel: {p.get('n_series')} series, {p.get('first')} → {p.get('last')} (bar close times, UTC).",
             "- Sources per symbol: the 65 Roostoo crypto symbols use the 1h archive before "
             f"{artifact['parameters']['validation']['hourly_from_1m']} and resampled 1m bars after; "
             "every other symbol uses the 1h archive."]
    oc = p.get("overlap_check")
    if oc:
        lines.append(f"- 1m→1h overlap check ({oc['month']}, BTCUSDT): {oc['hours_1m']} of {oc['hours_expected']} hours, "
                     f"closes identical in every hour (max |diff| = {oc['max_abs_diff']}).")
    for r in p.get("renames", []):
        detail = ", ".join(f"{k}={_fmt(v)}" for k, v in r.items() if k not in ("old", "new", "clean", "stitched"))
        lines.append(f"- Rename {r['old']} → {r['new']}: {'STITCHED' if r.get('stitched') else 'NOT stitched'} "
                     f"({detail}).")
    for sym, segs in p.get("segments", {}).items():
        lines.append(f"- {sym} split into separate listings at a gap > "
                     f"{artifact['parameters']['validation']['segment_gap_days']} days: "
                     + "; ".join(f"`{k}` {a[:10]} → {b[:10]}" for k, (a, b) in segs.items()))
    dl = notes.get("downloads")
    if dl:
        lines.append("- This run's downloads: " + "; ".join(f"{k}: {v}" for k, v in dl.items()))
    lines.append(f"- Inputs (verified files whose period starts at or before the as-of): {artifact['inputs_files']}. "
                 f"Hash of the inputs the chosen variant uses ({', '.join(artifact['inputs_active_sources'])}): "
                 f"`{artifact['inputs_sha256_active'][:16]}…`; all inputs: `{artifact['inputs_sha256_all'][:16]}…`.")
    fs = artifact["fred_snapshot"]
    lines.append(f"- FRED snapshot {'pinned for this as-of' if fs['pinned'] else 'newly pinned for this as-of'} "
                 "(`validation/fred_pins.json`; `--refresh-macro` fetches a new one): "
                 + ", ".join(f"{k} `{f}`" for k, f in sorted(fs["files"].items())) + ".")
    ld = artifact["data_last"]
    lines.append(f"- Latest data: BTC hourly close {ld['btc_last_hourly_close']}; funding print {ld['funding_last']}; "
                 f"OI snapshot {ld['oi_last']}; FRED last observations {ld['fred_last']}.")
    for k in ("funding_error", "oi_error"):
        if notes.get(k):
            lines.append(f"- **{k.split('_')[0].upper()} could not be loaded: {notes[k]} → POSITIONING disabled.**")
    if notes.get("oi_boundary_conflicts_resolved"):
        lines.append(f"- Open interest: {notes['oi_boundary_conflicts_resolved']} midnight snapshots appeared in two "
                     "adjacent daily files with slightly different values; the row from the file of that date was kept.")
    if notes.get("fred_missing"):
        lines.append(f"- **FRED series missing: {notes['fred_missing']} → MACRO group disabled.**")
    lines.append("- Groups with data: " + ", ".join(f"{g}={'yes' if ok else 'NO'}" for g, ok in groups_ok.items()))
    if len(universe):
        sizes = universe.groupby("t").size()
        lines.append(f"- Universe U(t): {sizes.min()}–{sizes.max()} series per day "
                     f"({universe.series.nunique()} distinct series ever included).")
    return "\n".join(lines)


def render(**c) -> str:
    a, v = c["artifact"], c["artifact"]["parameters"]["validation"]
    hz = c["horizon"]
    ys = c["outcome_cols"]
    out = [
        "# Lookalike validation set v1",
        "",
        f"As-of requested: **{a['asof_requested']}** · state time used: **{a['state_time']}** · "
        f"T* = {a['live_start_T_star']} · holdout H = T* − {v['holdout_days']}d = {a['holdout_H']} · "
        f"gap T* − last bar used: **{a['gap_hours_T_star_minus_state_time']:.0f} h**",
        "",
        f"Code commit `{a['git_commit'][:12]}` · pre-registration commit `{(a['prereg_commit'] or '?')[:12]}` · "
        f"inputs `{a['inputs_sha256_active'][:12]}`. Generated by "
        "`python -m src.validation.build`; do not edit by hand (the pre-registration block is preserved verbatim).",
        "",
        c["prereg"],
        "",
        "## Data coverage",
        "",
        _coverage(c["notes"], a, c["groups_ok"], c["universe"]),
        "",
    ]

    ch = c["choice"]
    out += ["## Result of the pre-registered rule", ""]
    out.append(f"- SCREEN leader vs baseline (a): **{ch['screen_leader']}**. Chosen: **{ch['chosen']}** — {ch['reason']}.")
    if ch["unavailable_variants"]:
        out.append(f"- Not candidates (no data for a group): {ch['unavailable_variants']}.")
    if ch["core_not_predictive"]:
        out.append(f"- **CORE's CONFIRM skill vs (a) is {ch['core_confirm_skill']:+.4f} ≤ 0: on this test, CORE "
                   "lookalikes are NOT predictive of the next 14 days relative to simply using the whole pool.**")
    else:
        out.append(f"- CORE's CONFIRM skill vs (a) is {ch['core_confirm_skill']:+.4f} > 0.")
    skills, periods = c["skills"], c["periods"]
    chosen = ch["chosen"]
    for p in periods:
        m = skills[(chosen, "all", p)].loc["MEAN"]
        if np.isfinite(m["skill"]):
            verdict = ("includes 0: not distinguishable from no skill" if m["lo"] <= 0 <= m["hi"]
                       else "excludes 0")
            out.append(f"- {chosen} {p} skill vs (a): {_skill_cell(m)} — the 90% interval {verdict}.")
    mb = skills[(chosen, "recent", "CONFIRM")].loc["MEAN"]
    if np.isfinite(mb["skill"]):
        rel = ("interval includes 0: no distinguishable difference" if mb["lo"] <= 0 <= mb["hi"]
               else ("worse" if mb["hi"] < 0 else "better"))
        out.append(f"- vs (b) 25 most recent non-overlapping windows, CONFIRM: {_skill_cell(mb)} — {rel}.")
    per = skills[(chosen, "all", "CONFIRM")].drop(index="MEAN")
    pos = [y for y, r in per.iterrows() if r["lo"] > 0]
    neg = [y for y, r in per.iterrows() if r["hi"] < 0]
    out.append(f"- Per outcome in CONFIRM vs (a): interval above 0 for {pos or 'none'}; below 0 for {neg or 'none'}.")
    out.append("")

    sf = c["skills_fair"]
    fa = {p: sf[(chosen, "all", p)].loc["MEAN"] for p in periods}
    fb = {p: sf[(chosen, "recent", p)].loc["MEAN"] for p in periods}
    beats = all(fa[p]["lo"] > 0 for p in periods)
    ties = all(fb[p]["lo"] <= 0 <= fb[p]["hi"] for p in periods)
    out += ["### Corrected reading: fair CRPS", "",
            "The standard sample CRPS used by the pre-registered rule divides its spread term by n², which penalises "
            "small ensembles: a 25-window set is judged against the ~2,000-window pool (baseline a) with a handicap. "
            "The fair CRPS divides by n(n − 1) (Ferro 2014). Baselines (b) and (c) are also 25-window sets, so the "
            "bias largely cancels there. The recorded choice does not change; this corrects the wording.", ""]
    out.append(f"- Under fair CRPS, {chosen} vs (a) whole pool: SCREEN {_skill_cell(fa['SCREEN'])}, CONFIRM "
               f"{_skill_cell(fa['CONFIRM'])} — " + ("**lookalikes beat the whole pool**" if beats else
                                                     "not above 0 in both periods") + ".")
    out.append(f"- Under fair CRPS, {chosen} vs (b) 25 recent windows: SCREEN {_skill_cell(fb['SCREEN'])}, CONFIRM "
               f"{_skill_cell(fb['CONFIRM'])} — " + ("**a tie with recent windows** (both intervals include 0)"
                                                     if ties else "not a tie in both periods") + ".")
    out.append("")
    rows = {var: {f"{p} vs ({'abc'[i]})": _skill_cell(sf[(var, b, p)].loc["MEAN"])
                  for p in periods for i, b in enumerate(c["baselines"])} for var in c["main_variants"]
            if (var, "all", "SCREEN") in sf}
    df = pd.DataFrame(rows).T
    df.index.name = "variant (fair CRPS)"
    out += [table(df), ""]

    cd = c.get("common_diag")
    if cd:
        out += ["Diagnostic, not part of the rule: the candidates were skipped on different early dates (the "
                "spacing rules cannot fit 25 picks into a short pool), so their SCREEN date sets differ. Mean skill "
                f"vs (a) on the {cd['n']['SCREEN']} SCREEN / {cd['n']['CONFIRM']} CONFIRM dates common to all "
                "candidates:", ""]
        df = pd.DataFrame({p: {v: _skill_cell(s) for v, s in cd["skill"][p].items()} for p in periods})
        df.index.name = "variant"
        out += [table(df), ""]

    for p in periods:
        out += [f"## Skill — {p} ({_fmt(periods[p][0])} → {_fmt(periods[p][1])})", "",
                "Mean skill over Y1..Y8 [90% block-bootstrap interval]; > 0 means lookalikes beat the baseline.", ""]
        rows = {var: {b: _skill_cell(skills[(var, b, p)].loc["MEAN"]) for b in c["baselines"]}
                for var in c["variants"]}
        df = pd.DataFrame(rows).T
        df.columns = [f"vs ({'abc'[i]}) {c['baselines'][b]}" for i, b in enumerate(c["baselines"])]
        df.insert(0, "dates", [int(skills[(var, "all", p)]["n_dates"].iloc[0]) if skills[(var, "all", p)]["n_dates"].notna().any() else 0
                               for var in c["variants"]])
        df.index.name = "variant"
        out += [table(df), ""]
        out += [f"Per-Y skill vs (a), {p}:", ""]
        per = pd.DataFrame({var: {y: _skill_cell(skills[(var, "all", p)].loc[y]) for y in ys}
                            for var in c["variants"]}).T
        per.index.name = "variant"
        out += [table(per), ""]

    aud = c["audit"]
    skipped = aud[aud.status != "ok"]
    out += [f"Walk-forward audit: {len(aud)} (variant, D) cases, {len(skipped)} skipped"
            + (f" ({skipped.status.value_counts().to_dict()})" if len(skipped) else "")
            + "; every pool_D ended at or before its D (asserted).", ""]

    st = c["state"].copy()
    st.index.name = "feature"
    out += [f"## State at {a['state_time']} (variant {ch['chosen']})", "",
            f"Percentiles are within the reference pool ({a['pool']['n']} starts, {a['pool']['first_start'][:10]} → "
            f"{a['pool']['last_start'][:10]}).", ""]
    if a["query_features_dropped_nan"]:
        out += [f"**Active features unavailable at the state time (dropped from the distance): "
                f"{a['query_features_dropped_nan']}.**", ""]
    out += [table(st), ""]

    ms = c["main_set"].sort_values("distance").reset_index(drop=True)
    feats, outc = c["feats"], c["outcomes"]
    kf = c["key_features"]
    look = pd.DataFrame({"start": ms.t0, "end": ms.t0 + hz, "distance": ms.distance})
    for f in kf:
        look[f] = feats.loc[ms.t0, f].to_numpy()
    look.index = np.arange(1, len(look) + 1)
    look.index.name = "#"
    out += [f"## The {len(ms)} lookalikes (selected on features only)", "", table(look), ""]

    yo = outc.loc[ms.t0, ys + ["regime"]].copy()
    yo.index = [t.strftime("%Y-%m-%d") for t in yo.index]
    yo.index.name = "start"
    out += ["## What happened in them (outcomes; never used for selection)", "",
            "Y1 BTC 14d log return · Y2 BTC hourly realised vol (ann.) · Y3 BTC max drawdown · Y4 BTC efficiency "
            "ratio · Y5 cross-sectional std of 14d log returns · Y6 mean pairwise hourly correlation · Y7 median alt "
            "minus BTC 14d log return · Y8 BTC max rebound. `regime` = ex-post Y1 tercile / Y2 tercile (for a later task).",
            "", table(yo), ""]
    pool_o = outc.loc[c["pool"], ys]
    summ = pd.DataFrame({
        "lookalike median": yo[ys].median(), "lookalike p10": yo[ys].quantile(0.1), "lookalike p90": yo[ys].quantile(0.9),
        "pool median": pool_o.median(), "pool p10": pool_o.quantile(0.1), "pool p90": pool_o.quantile(0.9)})
    summ.index.name = "Y"
    out += [table(summ), "", "Regime counts in the lookalikes: "
            + ", ".join(f"{k}: {n}" for k, n in yo.regime.value_counts().sort_index().items()), ""]

    sens = pd.DataFrame(a["sensitivity"]).T
    sens.index.name = "variation"
    out += ["## Sensitivity (overlap with the main set)", "", table(sens, nd=3), "",
            "K = 15 and K = 40 are nested in the main pick by construction (same greedy order), so their overlap "
            "is simply 15/25 and 25/40 when the pick is not cut short; the group-drop rows are the informative ones.",
            ""]
    if a.get("windows_identical_to_previous_same_asof") is not None:
        out += [f"Rerun check: the 25 lookalike windows are "
                f"{'IDENTICAL' if a['windows_identical_to_previous_same_asof'] else 'DIFFERENT'} to the previous "
                "artifact built for the same as-of.", ""]

    rec = pd.DataFrame(a["recent"])
    rec["start"] = pd.to_datetime(rec["start"])
    rec[["Y1", "Y2", "Y5", "Y8"]] = outc.loc[rec["start"], ["Y1", "Y2", "Y5", "Y8"]].to_numpy()
    rec["start"] = rec["start"].dt.strftime("%Y-%m-%d")
    rec["end"] = pd.to_datetime(rec["end"]).dt.strftime("%Y-%m-%d")
    rec.index = np.arange(1, len(rec) + 1)
    rec.index.name = "#"
    out += ["## RECENT set: the 25 most recent non-overlapping pool windows", "",
            "Fixed by rule (walking back from the last pool window before H). Evaluation set, not selected on "
            "features or outcomes.", "", table(rec), ""]

    st_ = a["stress"]
    out += ["## STRESS set (uses outcomes by design: evaluation set, not selection)", "",
            "Greedy with starts ≥ 14 days apart within each list. DROPS = the 10 lowest BTC 14-day returns. "
            f"REBOUNDS = the 10 highest BTC 14-day returns among the {st_['rebound_candidates']} pool windows whose "
            "start has BTC ≥ 20% below its 90-day high.", ""]
    for name in ("drops", "rebounds"):
        df = pd.DataFrame(st_[name])
        df["start"] = pd.to_datetime(df["start"]).dt.strftime("%Y-%m-%d")
        df.index = np.arange(1, len(df) + 1)
        df.index.name = name.upper()
        out += [table(df), ""]

    t = c["tests"]
    trows = pd.DataFrame({"result": t["tests"]}).sort_index()
    trows.index.name = "test"
    out += ["## Tests (pytest, run by the build)", "", f"`{t['summary']}`", "",
            table(trows) if len(trows) else "(no per-test results parsed)", ""]

    out += ["## Limitations", "",
            "- **Survivorship is only approximated.** The market-wide measures (U(t), M1–M4, Y5–Y7) use today's Roostoo "
            "list plus 28 historically large coins (incl. delisted LUNA, FTT, XMR, MKR). Other coins that were large "
            "in the past and have since vanished are missing, and `data.binance.vision` only covers Binance.",
            "- **CPI release dates are approximate — known limitation.** MACRO assumes month m is released on the 16th "
            "of month m + 1, 00:00 UTC. Most real releases fall on the 10th–15th, so this is usually conservative. "
            "During the late-2025 US government shutdown, releases were delayed past the 16th and the October 2025 "
            "CPI was never published (blank in FRED); for those months X1/X2 may use a value before its real "
            "release. E1 approximates CPI day as the 12th. MACRO is inactive in the chosen variant.",
            "- **FRED values are the current vintage, not point-in-time vintages.** DTWEXBGS (H.10) is published "
            f"weekly; X5 therefore uses values at least {v.get('macro_lag_days', {}).get('DTWEXBGS', 0)} days old "
            "(lag added in revision 1.1).",
            "- **Archive lag near T*.** data.binance.vision publishes daily files about a day late and funding only "
            "as monthly files; live Binance REST is blocked on this server. The last bar used is "
            f"{a['gap_hours_T_star_minus_state_time']:.0f} h before T*; funding-based P1 is unavailable once its last "
            "monthly file is more than a few days old.",
            "- Outcome windows of consecutive weekly test dates overlap (14-day horizon, 7-day step); the block "
            "bootstrap (blocks of 4) is meant to absorb that dependence, but the intervals are still approximate.",
            "- Each variant's pool starts when all of its features exist (POSITIONING needs open interest from "
            "2020-09 plus 30 days), so pools differ slightly in their earliest dates.",
            "",
            "## Run history",
            "",
            "- 2026-09-30, first dry run: open interest failed to load (4 duplicated midnight snapshots with "
            "conflicting values), so POSITIONING and the three variants using it were wrongly excluded; that run "
            "chose CORE (CORE CONFIRM skill vs (a) +0.0250). The loader was fixed (keep the row from the file of "
            "that date) and the build rerun. No rule, parameter, feature or threshold was changed between runs.",
            "- Erratum in the pre-registration text: it says \"last D = 2026-07-25\". The rule it states (every 7 days "
            "from 2022-07-01 up to H − 14 days) actually ends on 2026-07-24, which is what was run; the block is "
            "left unedited.",
            "- The \"diagnostic\" lines (common-date skill, interval verdicts) were added to the report after the "
            "first results were seen. They only describe the numbers and do not feed the choice rule.",
            "- Revision 1.1 (2026-09-30/10-01, PART 0 follow-ups): FRED snapshot pinned per as-of; artifact hash "
            "limited to the inputs the chosen variant uses; DTWEXBGS lagged 7 days; RECENT and STRESS sets added; "
            "fair-CRPS diagnostics added and the wording corrected (the earlier \"lookalikes add nothing over the "
            "whole pool\" reading was an artefact of the standard CRPS). The pre-registered rule and its standard-"
            "CRPS scoring are unchanged.",
            ""]
    return "\n".join(out)
