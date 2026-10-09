"""Render the weak-market selection report without changing metric definitions."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd


def _cell(value):
    if value is None:
        return "\u2014"
    if isinstance(value, (dict, list, tuple)):
        value = json.dumps(value, default=str, sort_keys=True)
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _number(value, percent=False, signed=False, digits=2):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "\u2014"
    if not math.isfinite(value):
        return "\u2014"
    if percent:
        return format(value, f"{'+' if signed else ''}.{digits}%")
    return format(value, f"{'+' if signed else ''}.{digits}f")


def _count(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "\u2014"
    return str(int(value)) if math.isfinite(value) else "\u2014"


def _yes(value):
    if value is None:
        return False
    if isinstance(value, str):
        return value.lower() == "true"
    try:
        return bool(value) and not bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return out


def _precision(row, h):
    good, n = row.get(f"correct_{h}h"), row.get(f"valid_{h}h")
    try:
        ratio = float(good) / float(n) if float(n) > 0 else None
    except (TypeError, ValueError, ZeroDivisionError):
        ratio = None
    return f"{_count(good)}/{_count(n)} ({_number(ratio, percent=True, digits=1)})"


def render(cp, frame, short, evidence):
    """Produce Markdown from already computed, versioned evidence.

    This presentation function never selects windows, assigns ranks, infers a winner
    from mean returns, or upgrades hourly short proxies into executable account PnL.
    """
    c, base = cp["c"], cp["base"]
    incumbent = base.get("incumbent") or base.get("book_regime_eval", {}).get("incumbent")
    if not incumbent:
        incumbent = cp.get("incumbent_score", {}).get("model", {}).get("name", "fixed e20")
    root = str(cp["root"])
    config_root = str(Path(root).parent.parent.parent) if root.startswith("/") else "/home/ubuntu/test/MiniMax"
    if "/results/book/" in root:
        config_root = root.split("/results/book/")[0]
    worktree = "/home/ubuntu/test/MiniMax/.worktrees/book-book-bear-eval"
    primary = int(c["primary_hours"])
    profiles = ["archive_full", "fresh_btc"]
    if len(short) and "profile" in short:
        profiles = list(dict.fromkeys(map(str, short["profile"])))
    ordered = frame.sort_values("rank", kind="stable", na_position="last") if "rank" in frame else frame
    eligible = ordered[ordered["candidate"].map(_yes) & ordered["original_eligible"].map(_yes)]
    strengthened = eligible[eligible["strengthened_evidence"].map(_yes)]
    minclusters = int(c["min_clusters"])
    horizon_text = "/".join(str(int(h)) for h in c["horizons_hours"])
    lines = ["# Leaderboard 2: weak-market model selection", ""]
    if len(eligible):
        best = eligible.iloc[0]
        lines += [f"**Highest ranked originally eligible candidate: {_cell(best['model'])}.** "
                  f"Its conservative selection score is {_number(best.get('selection_score'), True, True)}; "
                  f"its archive-profile mean {primary}-hour return is "
                  f"{_number(best.get('return_mean'), True, True)}.", ""]
    else:
        lines += ["**No originally eligible candidate is available in this protocol.**", ""]
    if len(strengthened):
        names = ", ".join(_cell(x) for x in strengthened["model"])
        lines += [f"**Stronger historical replacement evidence: {names}.** "
                  "These candidates clear the simultaneous return comparisons and sample-support checks below. "
                  "Actual switching from the live account still requires a separate transition evaluation.", ""]
    else:
        lines += ["**No candidate currently clears the stronger replacement-evidence checks.** "
                  "The numeric ranks remain useful for choosing the next experiment. A rank alone does not "
                  "establish that switching improves the live account.", ""]
    lines += [
        "## Read this first",
        "",
        f"The question answered here is: **which tested model performs most defensibly across historical "
        f"weak-market checkpoints resembling this competition state, over the remaining {primary} hours?** "
        "The main table now has explicit experimental ranks and comparisons against cash and the fixed e20 revision.",
        "",
        f"Market checkpoint: **{_cell(c['asof'])}**. Competition endpoint: "
        f"**{_cell(c['competition_end'])}**. Main horizon: **{primary} h = {primary / 24:.2f} days**; "
        f"robustness horizons: **{horizon_text} h**. Historical tests start from cash at each selected checkpoint. "
        "They do not recreate the live account's holdings, pending orders, accrued activity or earlier loss.",
        "",
        "1. Start with **Rank** and **Selection score**. Higher is better. The score is the smallest simultaneous "
        "lower return bound across both data profiles, all three horizons, and both cash/e20 comparisons "
        "(12 contrasts per model). It is a conservative evidence statistic; it is not expected profit.",
        "2. Check **Original gates**. A model can have a high experimental rank while failing the team's original "
        "engineering/activity/compatibility gates. References and failed-gate models are visible for comparison.",
        f"3. Read **Mean {primary}h**, **Median**, **P10**, **Tail 10%**, **Worst**, **Cash wins** and "
        "**vs e20** together. A large average with severe bad tails is weaker evidence. Fresh BTC mean is a "
        "separate current-data sensitivity, not a substituted breadth observation.",
        "4. Read the risk table. **CS** keeps the existing daily competition composite formula. "
        "**CS UTC** changes the day clock; **CS on positive windows** conditions on a positive after-cost return. "
        "That positive-window definition differs from the original leaderboard's return-bar CS_HIT.",
        "5. Use the separate short table to inspect how many short onsets fired correctly at 1/3/6 hours, "
        "how often direction/costs defeated them, and how often a sampled profit was surrendered to a rebound. "
        "Its labels do not enter the main selection score.",
        "6. A new model tested with **--score2** is automatically appended to this protocol's separate registry "
        "and the Markdown/CSV boards are regenerated. The market checkpoint and selection rules remain frozen.",
        "",
        "A value of 0.02 in a CSV means +2%; the Markdown displays percentages. CS is a ratio composite, "
        "not a percentage. Missing/censored short labels appear explicitly and are excluded from valid-label "
        "precision, so inspect their counts alongside any accuracy percentage.",
        "",
        "## Windows and data coverage",
        "",
        f"Weak historical eligibility is fixed before model comparisons: BTC's trailing 48-hour return lies "
        f"between {_number(c['weak']['ret48_min'], True)} and {_number(c['weak']['ret48_max'], True)}, "
        f"its 24-hour log return is at most {_number(c['weak']['ret24_max'], True)}, and historical positive "
        f"48-hour breadth is at most {_number(c['weak']['breadth_max'], True)}. Matching uses only "
        "information available at the historical checkpoint, never the following return.",
        "",
        f"The primary cohort requests {int(c['lookalikes']['k'])} similar checkpoints, with at least "
        f"{int(c['lookalikes']['min_separation_days'])} days between selected starts and at most "
        f"{int(c['lookalikes']['max_per_span'])} starts in any "
        f"{int(c['lookalikes']['span_days'])}-day span. Only matured historical paths with the "
        f"{int(c['embargo_hours'])}-hour embargo qualify. The saved cohort contains the actual admitted windows.",
        "",
        f"**Archive-full profile** uses a confirmed full-feature query at {_cell(c['reference_asof'])}, "
        "24 hours before the current checkpoint. **Fresh-BTC profile** uses complete BTC features from ticker-assisted observations at the "
        "current checkpoint and deliberately declares its narrower feature set. It does not claim fresh full "
        "market breadth. The exact fresh broad-universe query remains **29/30 endpoints** because BCH is "
        "absent from competition ticker data; that failed coverage is preserved.",
        "",
        "The previous October 8 adaptive forecast method did not pass all its evidence gates. Its failed "
        "activation record remains unchanged. This report ranks a separately declared conditional experiment; "
        "it does not silently enable that failed forecasting method or establish a validated downward forecast.",
        "",
        "## Main ranked table",
        "",
        f"Mean/risk distribution columns use the archive-full cohort at {primary} hours. The selection score "
        "uses the joint evidence across both profiles and all three horizons.",
        "",
    ]
    rows = []
    for _, r in ordered.iterrows():
        gates = "PASS" if _yes(r.get("original_eligible")) else "FAIL"
        rows.append([_count(r.get("rank")), r.get("model"), gates,
                     _number(r.get("selection_score"), True, True),
                     _number(r.get("return_mean"), True, True), _number(r.get("fresh_mean"), True, True),
                     _number(r.get("return_median"), True, True), _number(r.get("return_p10"), True, True),
                     _number(r.get("tail10_mean"), True, True), _number(r.get("return_worst"), True, True),
                     _number(r.get("return_positive"), True, digits=1),
                     _number(r.get("delta_vs_incumbent"), True, True), _number(r.get("CS"))])
    lines += _table(["Rank", "Model", "Original gates", "Selection score", f"Mean {primary}h",
                     "Fresh BTC mean", "Median", "P10", "Tail 10% mean", "Worst", "Cash wins",
                     "Mean vs e20", "CS"], rows)
    lines += ["", f"Fixed incumbent: **{_cell(incumbent)}**. Cash is the zero-return comparator. "
              "The incumbent's cached revision stays fixed even if a new run reuses its model name. "
              "All model returns include the existing cached trading fees, spread assumptions and execution "
              "lag; an endpoint liquidation fee is applied once. Results begin from cash and measure an "
              "experimental replacement strategy, not a transaction from incumbent holdings.", "",
              "## Risk and original-gate detail", ""]
    rows = []
    for _, r in ordered.iterrows():
        rows.append([r.get("model"), "candidate" if _yes(r.get("candidate")) else "reference",
                     _number(r.get("mdd_mean"), True), _number(r.get("mdd_worst"), True),
                     _number(r.get("CS")), _number(r.get("CS_UTC")),
                     _number(r.get("CS_HIT_positive")),
                     "YES" if _yes(r.get("strengthened_evidence")) else "NO",
                     r.get("failed_hard_gates") or "\u2014"])
    lines += _table(["Model", "Role", "Mean MDD", "Worst MDD", "CS", "CS UTC",
                     "CS on positive windows", "Stronger evidence", "Failed original hard gates"], rows)
    lines += ["", "MDD is a positive loss fraction from a prior equity peak and includes terminal liquidation. "
              "CS = 0.4 Sortino + 0.3 Sharpe + 0.3 Calmar using the configured FLOORED.V1 daily-raw formulas, "
              "with the same handling of partial first/last days as the original scorer. "
              "A favourable CS cannot replace the return and downside checks.", "",
              "## Separate stress/control tables", "",
              "The following-down and following-rebound subsets are **ex-post scenarios**. They classify the "
              "following 240-hour BTC outcome using the frozen down/rebound thresholds, then report the model's "
              f"{primary}-hour return. Their different horizons are intentional and must not be read as exact "
              "same-horizon market attribution. Their future labels are never used to admit the main lookalikes.",
              "",
              f"Down stress: BTC's following 240-hour return <= {_number(c['stress']['future_down'], True)}. "
              f"Rebound stress: >= {_number(c['stress']['future_rebound'], True)}. Positive control checkpoints "
              "are selected from the separately predeclared positive pre-window state, so they test the cost of "
              "a short/defensive model when market conditions improve.", ""]
    rows = []
    for _, r in ordered.iterrows():
        rows.append([r.get("model"), _count(r.get("future_down_stress_n")),
                     _number(r.get("future_down_stress_mean"), True, True),
                     _count(r.get("future_rebound_stress_n")),
                     _number(r.get("future_rebound_stress_mean"), True, True),
                     _count(r.get("positive_control_n")),
                     _number(r.get("positive_control_mean"), True, True)])
    lines += _table(["Model", "Down N", "Down mean", "Rebound N", "Rebound mean",
                     "Positive-control N", "Positive-control mean"], rows)
    lines += ["", "Small scenario counts have weak precision. Scenario means remain diagnostic and do not "
              "override the main conservative ranking.", "",
              "## Separate short-trigger table", "",
              "**Hourly directional proxies only.** An onset is a cached entry/decision fill crossing from "
              "zero/long to a negative asset weight. Adds and partial covers do not create extra triggers; "
              "activity-guard onsets remain separately recorded. The cache already includes the engine's "
              "one-hour execution lag.",
              "",
              f"For a unit short, the entry proxy is hourly close x (1 - "
              f"{_number(c['short']['half_spread'], True, digits=3)}); the cover proxy is hourly close x "
              f"(1 + {_number(c['short']['half_spread'], True, digits=3)}). Both entry and cover pay "
              f"{_number(c['short']['fee_rate'], True, digits=3)} of their respective notionals. "
              "The spread is a declared constant stress assumption, not measured historical bid/ask. "
              "Correct means a positive after-cost unit-short proxy at the stated fixed horizon.",
              "",
              "Fixed-horizon labels continue probing market direction even if the model already covered. "
              "Episode-cover behaviour is exported separately and is not quantity-weighted through adds or "
              "partial covers. **Actual account short PnL, minute/second timing, and intrahour TP/SL order "
              "are unverified.** Every hourly sampled barrier keeps that ambiguity; sampled take-profit counts "
              "must not be presented as executable before-rebound accuracy.",
              "",
              "Each precision cell is **correct/valid (percentage)**. Six-hour intervals cluster by historical "
              "windows; 30 triggers in one window do not provide 30 independent market episodes.", ""]
    srows = []
    if len(short):
        for _, r in short.iterrows():
            ci = f"[{_number(r.get('precision_6h_lower90'), True, digits=1)}, " + \
                 f"{_number(r.get('precision_6h_upper90'), True, digits=1)}]"
            srows.append([r.get("model"), r.get("profile"), _count(r.get("onsets")),
                          f"{_count(r.get('windows_with_onsets'))}/{_count(r.get('total_windows'))}",
                          _precision(r, 1), _precision(r, 3), _precision(r, 6), ci,
                          _count(r.get("terminal_censored"))])
    lines += _table(["Model", "Profile", "Onsets", "Windows firing/total", "Correct 1h",
                     "Correct 3h", "Correct 6h", "6h precision 90% interval", "Open at endpoint"], srows)
    lines += ["", "Wrong direction means the underlying price did not fall. Cost-only loss means it fell but "
              "the move did not cover the declared spread and both fees. A rebound loss means sampled "
              "profit existed within the horizon but the final proxy was nonpositive.", ""]
    srows = []
    if len(short):
        for _, r in short.iterrows():
            counts = lambda name: "/".join(_count(r.get(f"{name}_{h}h")) for h in (1, 3, 6))
            srows.append([r.get("model"), r.get("profile"), counts("wrong_direction"),
                          counts("cost_only_loss"), counts("unresolved"), counts("rebound_losses")])
    lines += _table(["Model", "Profile", "Wrong direction 1/3/6h", "Cost-only loss 1/3/6h",
                     "Unresolved 1/3/6h", "Rebound losses 1/3/6h"], srows)
    lines += ["", "## Evidence strength and limits", "",
              f"Stronger historical replacement evidence requires the original hard gates, a positive "
              f"joint conservative selection score, and at least **{minclusters} merged overlap clusters "
              f"and {minclusters} calendar quarters in every comparison context**. "
              "This requirement is not relaxed to manufacture a winner.",
              "",
              f"Uncertainty uses {_count(evidence.get('bootstrap_reps', c['bootstrap']['reps']))} paired "
              f"bootstrap draws across {_count(evidence.get('family_models'))} model revisions. "
              "The standardized centred maximum statistic controls the simultaneous family of cash/e20 "
              "comparisons over two profiles and three horizons. It uses shared resampling so correlated "
              "models and comparisons remain paired.",
              "",
              "Nonoverlapping selected windows can still share market regimes; nearby context windows are "
              "merged for dependence and the quarter check guards narrow calendar coverage. Bootstrap "
              "bounds remain finite-sample estimates. They do not erase prior strategy-development search, "
              "prove future profitability or provide a 90% probability of winning the remaining competition.",
              "",
              f"Evidence method: {_cell(evidence.get('method'))}. "
              f"Joint family quantile: {_number(evidence.get('family_quantile'), digits=4)}.", ""]
    for name in ("clusters", "contexts"):
        value = evidence.get(name)
        if value is not None:
            lines += [f"Saved {name} summary:", "",
                      "~~~json", json.dumps(value, default=str, indent=2, sort_keys=True), "~~~", ""]
    lines += ["## Test a new model and update this board", "",
              "Run on the server in the feature worktree containing this implementation. Register the pure "
              "model through the project's existing model interface and place its tunable parameters in "
              "config.yaml. Check scripts/status before a heavy job and use an owned mm-book-* tmux session "
              "for a long run.", "",
              "~~~bash",
              "ssh metallurgy-server",
              f"cd {worktree}",
              "scripts/status",
              "scripts/lock harness-book-weak-score -- nice -n 10 .venv/bin/python -B -m backtest.run --model book_NAME --score2",
              "~~~", "",
              "After a successful run, this secondary leaderboard updates automatically. It contains the "
              "latest compatible run for each model under the frozen protocol; the separate registry retains "
              "previous attempts and immutable artifacts. Repeating the same run is idempotent.", "",
              "To update both the team's original scoring board and this board from one scoring run:", "",
              "~~~bash",
              "scripts/lock harness-book-weak-score -- nice -n 10 .venv/bin/python -B -m backtest.run --model book_NAME --score --score2",
              "~~~", "",
              "To rebuild this board from already published results, or import the frozen registered models:", "",
              "~~~bash",
              "scripts/lock harness-book-weak-score -- nice -n 10 .venv/bin/python -B -m backtest.scoring leaderboard2",
              "scripts/lock harness-book-weak-score -- nice -n 10 .venv/bin/python -B -m backtest.scoring import-score2",
              "~~~", "",
              "--score keeps the original scoring rules. --score2 alone publishes this separate evaluation; "
              "it does not update the original leaderboard. Neither command deploys a model, changes the "
              "live bot, merges main or opens the holdout. A new market checkpoint requires a new frozen "
              "protocol; ordinary model scoring cannot alter the selected windows or thresholds.", "",
              "## Files and provenance", ""]
    files = [
        ("/home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md", "This guide, ranked table and separate short diagnostics"),
        ("/home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.csv", "Full numeric model-selection rows"),
        ("/home/ubuntu/test/MiniMax/results/scoring/registry_2.jsonl", "Append-only publication history"),
        (root + "/", "Frozen protocol, selected windows, data/coverage manifests, detailed diagnostics and reliability evidence"),
        ("/home/ubuntu/test/MiniMax/results/book/20261008-regime-eval/", "Preserved earlier failed adaptive activation and original evidence"),
        ("/home/ubuntu/test/MiniMax/results/scoring/leaderboard.md", "Original team full-round leaderboard"),
        (worktree + "/backtest/scoring/", "Book feature implementation: weak evaluation, risk, short diagnostics and publisher"),
    ]
    lines += _table(["Remote path", "Purpose"], files)
    lines += ["", f"Protocol identity: {_cell(cp['protocol'])}. Original incumbent source identity is pinned. "
              "Input manifests, cached-path compatibility and hashes are checked before publication; outputs "
              "from different checkpoints or metric definitions cannot silently share a ranking.", "",
              "This is historical selection evidence for the next experiment. The actual live-account "
              "transition and future realised competition result remain unverified.", ""]
    return "\n".join(lines)
