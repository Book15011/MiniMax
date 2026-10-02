"""Append-only registry of scoring runs and the leaderboard regenerated from it (docs/EVALUATION.md section 4).

- registry: scoring.registry (JSONL, one line per run, never rewritten). Appends take the same lock file as
  `scripts/lock scoring-registry -- ...` (run/locks/scoring-registry.lock, flock), but wait for it instead of
  failing, so concurrent runs queue up.
- leaderboard: full runs of the current tool version, the latest run of each model. Candidates (team models) are
  ordered by the pre-registered pick order (backtest.scoring.returnfirst.pick_order): hard gates, HEADLINE_RET, CS_HIT
  inside the top model's tie group (a month bootstrap over the per-window results in each run's score.json), then
  min(SCREEN, CONFIRM). Benchmarks, CASH included, are reference rows. Every number is shown on the full pool and
  without the post-holdout windows. Rows from older tool versions stay below, marked as a previous version. Each
  person's run count sits next to their best score, so the number of attempts behind a score stays visible.
"""
from __future__ import annotations

import fcntl
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.scoring import selection
from backtest.scoring.returnfirst import BARS, month_multiplicity, pick_order, tie_test
from src.config import REPO_ROOT, resolve

LOCK_NAME = "scoring-registry"
POOLS = ("full", "in_sample")
LABELS = {"team_btc_hold": "BTC_HOLD", "team_ew_daily": "EW_DAILY", "team_rot_ew": "ROT_EW", "team_rot_iv": "ROT_IV",
          "team_trend_2": "TREND_2", "team_mom_ss25": "MOM_SS25", "team_cash": "CASH"}


def locks_dir() -> Path:
    common = REPO_ROOT / ".git"
    if common.is_file():                       # inside a worktree: .git is a file pointing at the common dir
        gitdir = Path(common.read_text().split(":", 1)[1].strip())
        root = gitdir.parent.parent.parent     # <root>/.git/worktrees/<name> -> <root>
    else:
        root = REPO_ROOT
    return root / "run" / "locks"


@contextmanager
def locked(name: str = LOCK_NAME, lock_dir: str | Path | None = None):
    d = Path(lock_dir) if lock_dir else locks_dir()
    d.mkdir(parents=True, exist_ok=True)
    with open(d / f"{name}.lock", "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            (d / f"{name}.info").write_text(f"pid={os.getpid()} user={os.environ.get('MM_MEMBER', '?')} "
                                            f"since={datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ} cmd=registry append\n")
            yield
        finally:
            (d / f"{name}.info").unlink(missing_ok=True)
            fcntl.flock(fh, fcntl.LOCK_UN)


def append(path: str | Path, entry: dict, lock_dir: str | Path | None = None) -> None:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n"
    with locked(lock_dir=lock_dir):
        with open(p, "a") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())


def read(path: str | Path) -> tuple[list[dict], int]:
    """Entries, and the number of unreadable lines (should be 0)."""
    p = resolve(path)
    if not p.exists():
        return [], 0
    out, bad = [], 0
    for line in p.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            bad += 1
    return out, bad


def entry_from(score: dict, runner: str, outputs: dict) -> dict:
    rf, g, act = score["return_first"], score["gates"], score["activity"]
    pools = [p for p in POOLS if p in rf]
    return {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "runner": runner,
            "model": score["model"]["name"], "author": score["model"]["author"], "method": score["model"]["method"],
            "candidate": score["model"]["candidate"],
            "run_key": score["model"]["run_key"], "tool_version": score["tool_version"],
            "scoring_version": score["scoring_version"], "full": bool(score["windows"]["full_run"]),
            "primary": score["primary"]["headline"], "primary_variant": score["primary"]["variant"],
            "headline_ret": {p: rf[p]["headline_ret"] for p in pools},
            "hit": {p: rf[p]["hit"] for p in pools}, "hit_up": {p: rf[p]["hit_up"] for p in pools},
            "hit_down": {p: rf[p]["hit_down"] for p in pools}, "hit_pol_bars": {p: rf[p]["hit_pol_bars"] for p in pools},
            "headline_ret_plain_R": {p: rf[p]["headline_ret_plain_R"] for p in pools},
            "cs_hit": {p: rf[p]["cs_hit"] for p in pools}, "cs_hit_utc": {p: rf[p]["cs_hit_utc"] for p in pools},
            "pi_up": {p: rf[p]["pi_up"] for p in pools},
            "gates": {k: v["pass"] for k, v in g.items()}, "hard_gates": sorted(k for k, v in g.items() if v["hard"]),
            "eligible": score["eligible"], "period_check": score["period_check"],
            "rel_new_windows": score["rel"]["headline"][score["rel"]["convention"]]["REL"]["headline"],
            "tail": score["tail"]["full"],
            "activity": {k: act[k] for k in ("min_active_days", "min_active_days_utc", "guard_share_of_active_days",
                                             "guard_share_of_active_days_utc", "mean_turnover", "mean_fees_e0",
                                             "mean_spread_e0")},
            "median_R": score["summary"]["median_R"], "worst10_R": score["summary"]["worst10_R"],
            "worst_R": score["summary"]["worst_R"], "commit": (score.get("code") or {}).get("commit"),
            "replay": score.get("replay"), **outputs}


def current(entries: list[dict], tool_version: str) -> list[dict]:
    """Full runs of this tool version, one per run key (the latest)."""
    seen: dict[str, dict] = {}
    for e in entries:
        if e.get("full") and e.get("tool_version") == tool_version:
            seen[e["run_key"]] = e
    return list(seen.values())


def latest_by_model(entries: list[dict], tool_version: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for e in entries:
        if e.get("full") and e.get("tool_version") == tool_version:
            out[e["model"]] = e
    return out


def rank(entries: list[dict], value: float) -> tuple[int, int]:
    """Rank of a primary value among entries (1 = best)."""
    vals = [e["primary"] for e in entries]
    return 1 + sum(v > value for v in vals), len(vals)


# ---------------- the leaderboard ----------------

def per_window(entry: dict) -> pd.DataFrame | None:
    """The per-window columns the tie test needs, from the run's score.json (None if the file is gone)."""
    p = resolve(entry["score_json"]) if entry.get("score_json") else None
    if p is None or not p.exists():
        return None
    pw = json.loads(p.read_text())["per_window"]
    cols = ["scored", "post_holdout", "w_final", "w_final_in_sample", "R", "R_liq"] + [f"hit_{b}" for b in BARS]
    df = pd.DataFrame({c: pw[c] for c in cols}, index=pd.to_datetime(pw["start"], utc=True))
    return df[df.scored.astype(bool)]


def tie_groups(rows: dict[str, dict], tables: dict[str, pd.DataFrame], sc: dict,
               margin: float | None = None) -> tuple[dict, dict, list[str]]:
    """{pool: {model: tie result}}, {pool: pick order}, and warnings. The weights must be the same in every run of
    the tool version (they are: the same windows and the same files); the first candidate's are used. With `margin`
    (backtest.scoring.selection), a model is tied only if also within `margin` of the top's HEADLINE_RET."""
    t = sc["tie"]
    ties, orders, warn = {}, {}, []
    names = [n for n in rows if n in tables]
    if len(names) < len(rows):
        warn.append("score.json missing for: " + ", ".join(sorted(set(rows) - set(names))))
    if not names:
        return ties, orders, warn
    for pool in POOLS:
        wcol = "w_final" if pool == "full" else "w_final_in_sample"
        ref = tables[names[0]]
        sel = ref.index if pool == "full" else ref.index[~ref.post_holdout.astype(bool).to_numpy()]
        w = ref.loc[sel, wcol].to_numpy(dtype=float)
        if not np.isfinite(w).all() or len(sel) == 0:
            continue
        for n in names:
            other = tables[n].reindex(sel)[wcol].to_numpy(dtype=float)
            if not np.allclose(other, w, rtol=0, atol=1e-15):
                warn.append(f"{n}: its {pool} weights differ from {names[0]}'s; not comparable")
        inds = {n: tables[n].reindex(sel)[[f"hit_{b}" for b in BARS]].to_numpy(dtype=float) for n in names}
        cands = {n: r for n, r in rows.items() if r["candidate"] and n in inds}
        elig = [n for n, r in cands.items() if r["eligible"]]
        if not elig:
            continue
        top = max(elig, key=lambda n: (rows[n]["headline_ret"][pool], n))
        mult = month_multiplicity(sel, int(t["reps"]), int(t["seed"]))
        ties[pool] = selection.apply_margin(tie_test(inds, w, top, mult, float(t["level"])), margin)
        pr = {n: {"eligible": r["eligible"], "headline_ret": r["headline_ret"][pool], "cs_hit": r["cs_hit"][pool],
                  "min_sc": (r.get("period_check") or {}).get("min")} for n, r in cands.items()}
        orders[pool] = pick_order(pr, {n: v for n, v in ties[pool].items() if n in cands}, float(t["cs_tolerance"]))
    return ties, orders, warn


def wquantile(x: np.ndarray, w: np.ndarray, q: float) -> float:
    """Weighted quantile: the smallest x whose cumulative weight share reaches q."""
    o = np.argsort(x, kind="stable")
    c = np.cumsum(w[o]) / w.sum()
    return float(x[o][min(int(np.searchsorted(c, q)), len(x) - 1)])


def return_stats(t: pd.DataFrame, pool: str) -> dict | None:
    """Report-only return magnitude of one run on one pool, from its score.json per-window table: the final weights
    w' (the same weights as HEADLINE_RET) applied to R_liq, plus the plain (unweighted) distribution."""
    wcol = "w_final" if pool == "full" else "w_final_in_sample"
    sel = t if pool == "full" else t[~t.post_holdout.astype(bool)]
    if sel.empty:
        return None
    w = sel[wcol].to_numpy(dtype=float)
    r = sel.R_liq.to_numpy(dtype=float)
    if not np.isfinite(w).all():
        return None
    return {"mean": float((w * r).sum() / w.sum()), "median": wquantile(r, w, 0.5), "p10": wquantile(r, w, 0.1),
            "p90": wquantile(r, w, 0.9), "positive": float((w * (r > 0)).sum() / w.sum()),
            "plain_median": float(np.median(r)), "worst": float(r.min()), "best": float(r.max())}


def return_view(rows: dict[str, dict], tables: dict[str, pd.DataFrame], order: list[str]) -> list[str]:
    """Report-only: candidates ranked by their weighted mean 14-day R_liq (the size of the return, not how often
    it clears a bar), with the benchmarks as reference rows. It never changes the pick or the main ranking."""
    st = {p: {n: return_stats(t, p) for n, t in tables.items()} for p in POOLS}
    rank_main = {n: k for k, n in enumerate(order, 1)}
    cands = sorted((n for n in rows if rows[n]["candidate"] and st["full"].get(n)), key=lambda n: -st["full"][n]["mean"])
    rank_in = {n: k for k, n in enumerate(sorted((n for n in cands if st["in_sample"].get(n)),
                                                 key=lambda n: -st["in_sample"][n]["mean"]), 1)}
    refs = sorted((n for n in rows if not rows[n]["candidate"] and st["full"].get(n)), key=lambda n: -st["full"][n]["mean"])
    L = ["", "## Return view (report-only): ranked by the size of the 14-day return", "",
         "The main ranking above is by HEADLINE_RET: how often the return clears the cut. This view ranks the same runs "
         "by how large the return is: the mean 14-day R_liq weighted with the same final weights w' (live-like, "
         "recency, direction-balanced). It is shown so both can be read side by side; it does not change the pick "
         "or the order above.", "",
         "| Return rank | Model | Mean R_liq (w') | without post-holdout (rank) | Median R_liq (w') | 10th pct | 90th pct | "
         "Share > 0 | Plain median | Worst | Best | Main rank (HEADLINE_RET) | Eligible |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]

    def line(k, n: str) -> str:
        a, b = st["full"][n], st["in_sample"].get(n)
        ins = "—" if b is None else f"{_pct(b['mean'], 2)}" + (f" (#{rank_in[n]})" if n in rank_in else "")
        return (f"| {k} | {LABELS.get(n, n)} | **{_pct(a['mean'], 2)}** | {ins} | {_pct(a['median'], 2)} | "
                f"{_pct(a['p10'])} | {_pct(a['p90'])} | {_share(a['positive'], 0)} | {_pct(a['plain_median'], 2)} | "
                f"{_pct(a['worst'])} | {_pct(a['best'])} | {('#' + str(rank_main[n])) if n in rank_main else 'ref'} | "
                f"{'yes' if rows[n]['eligible'] else 'no'} |")

    L += [line(k, n) for k, n in enumerate(cands, 1)]
    L += [line("ref", n) for n in refs]
    return L


def _pct(x, d=1) -> str:
    return "—" if x is None or not np.isfinite(x) else f"{x * 100:+.{d}f}%"


def _share(x, d=1) -> str:
    return "—" if x is None or not np.isfinite(x) else f"{x * 100:.{d}f}%"


def _num(x, d=3) -> str:
    return "—" if x is None or not np.isfinite(x) else f"{x:.{d}f}"


def _mean3(h: dict | None) -> float | None:
    return None if not h else float(np.mean([h[b] for b in BARS]))


def _replay(e: dict) -> str:
    rp = e.get("replay") or {}
    parts = []
    for w in rp.get("windows", []):
        ranks = "/".join(f"#{r['rank']}" for r in w["ranks"])
        parts.append(f"{w['R'] * 100:+.1f}% {ranks}")
    return " · ".join(parts) if parts else "—"


def leaderboard(entries: list[dict], tool_version: str, cfg: dict) -> str:
    sc = cfg["scoring"]
    rows = latest_by_model(entries, tool_version)
    tables = {n: t for n, e in rows.items() if (t := per_window(e)) is not None}
    rule, margin = selection.settings(cfg)
    ties, orders, warn = tie_groups(rows, tables, sc, margin)
    alt_margin = None if margin is not None else selection.proposal_margin(cfg)       # the other rule, shown too
    _, alt_orders, _ = tie_groups(rows, tables, sc, alt_margin)
    rule_name = "legacy (pre-registered)" if margin is None else f"margin {margin:g} (Pol's proposal)"
    alt_name = f"margin {alt_margin:g} (Pol's proposal)" if margin is None else "legacy (pre-registered)"
    old = latest_by_model(entries, str(sc.get("previous_tool_version", "")))
    old_rank = {n: k for k, n in enumerate(sorted(old, key=lambda n: -old[n]["primary"]), 1)}
    cash = rows.get("team_cash")
    cash_ret = {p: cash["headline_ret"].get(p) for p in POOLS} if cash else {}
    runs_by: dict[str, int] = {}
    for e in entries:
        if e.get("full") and e.get("tool_version") == tool_version:
            runs_by[e["author"]] = runs_by.get(e["author"], 0) + 1
    some = next(iter(rows.values()), None)
    pi = (some or {}).get("pi_up", {})
    L = [f"# Scoring leaderboard (tool version `{tool_version}`, scoring v{sc['version']})", "",
         "Primary: **HEADLINE_RET**, the mean over three return bars (LENIENT, MIDDLE, STRICT) of the share of "
         "live-like, direction-balanced windows whose 14-day R_liq clears the bar. Windows start at 12:00 UTC like "
         "the round. Candidates are in the pre-registered pick order (hard gates, HEADLINE_RET, CS_HIT inside the "
         "top model's tie group, then min(SCREEN, CONFIRM)); benchmarks are reference rows. "
         "Definitions: docs/EVALUATION.md; pre-registration: reports/review/20261002-prereg-return-first.md. "
         f"Latest full run of each model, regenerated after every registered run. pi_up (full / without the "
         f"post-holdout windows): {_num(pi.get('full'))} / {_num(pi.get('in_sample'))}.", ""]
    L += [f"Tie rule ordering this table: **{rule_name}**; the {alt_name} pick is shown under each pick "
          "(top-level `selection:` in config.yaml, backtest/scoring/selection.py).", ""]
    L += [f"- **Warning:** {w}" for w in warn]
    if warn:
        L.append("")
    head = ("| # | Model | HEADLINE_RET | without post-holdout | HIT L / M / S | HIT UP / DOWN | Tie group (90% interval vs top) | "
            "CS_HIT (V1 HKT) | V1 UTC days | old REL (rank) | Hard gates | Report-only gates failed | Worst R | "
            "Median MDD | Guard-only days | Turnover · fees / window | Replay R1 HK/SG · Final |")
    sep = "|" + "---|" * 17

    def line(k, n: str) -> str:
        e = rows[n]
        hr, hit, t = e["headline_ret"], e["hit"]["full"], ties.get("full", {}).get(n)
        tie = "—" if t is None else (f"{'**yes**' if t['tied'] else 'no'} [{t['lo']:+.3f}, {t['hi']:+.3f}]")
        hard_fail = [gk for gk in e["hard_gates"] if not e["gates"][gk]]
        soft_fail = [gk for gk, ok in e["gates"].items() if gk not in e["hard_gates"] and not ok]
        o = old.get(n)
        flag = ""
        if e["candidate"] and cash_ret.get("full") is not None and hr["full"] < cash_ret["full"]:
            flag = " ⚠ worse than doing nothing for the top-20 gate"
        name = LABELS.get(n, n)
        a = e["activity"]
        return (f"| {k} | {name}{flag} | **{hr['full']:.3f}** | {_num(hr.get('in_sample'))} | "
                f"{hit['LENIENT']:.2f} / {hit['MIDDLE']:.2f} / {hit['STRICT']:.2f} | "
                f"{_num(_mean3(e['hit_up']['full']), 2)} / {_num(_mean3(e['hit_down']['full']), 2)} | {tie} | "
                f"{_num(e['cs_hit']['full'])} | {_num(e['cs_hit_utc']['full'])} | "
                f"{(_num(o['primary'], 2) + f' (#{old_rank[n]})') if o else '—'} | "
                f"{'pass' if not hard_fail else '**FAIL ' + ', '.join(hard_fail) + '**'} | {', '.join(soft_fail) or 'none'} | "
                f"{_pct(e['tail']['worst_R'])} | {_share(e['tail']['median_MDD'])} | "
                f"{_share(a['guard_share_of_active_days'], 0)} | {a['mean_turnover']:.2f} · {_share(a['mean_fees_e0'], 2)} | "
                f"{_replay(e)} |")

    cands = [n for n in orders.get("full", []) if n in rows]
    cands += sorted((n for n, e in rows.items() if e["candidate"] and n not in cands), key=lambda n: -rows[n]["primary"])
    L += ["## Candidates (full pool)", "", head, sep]
    L += [line(k, n) for k, n in enumerate(cands, 1)]
    refs = sorted((n for n, e in rows.items() if not e["candidate"]), key=lambda n: -rows[n]["primary"])
    L += ["", "## Reference rows (benchmarks, CASH included)", "", head.replace("| # |", "| |"), sep]
    L += [line("", n) for n in refs]
    if cands:
        pick = orders.get("full", [None])[0]
        L += ["", f"**Pick (full pool), rule {rule_name}: `{pick}`.** Tie group: "
              + ", ".join(f"`{n}`" for n in cands if ties.get("full", {}).get(n, {}).get("tied")) + "."]
        alt = alt_orders.get("full", [None])[0]
        L += ["", f"Under the {alt_name} rule the pick would be `{alt}`"
              + (" (the same)." if alt == pick else ". Rule: top-level `selection:` in config.yaml; evidence in "
                 "reports/review/20261002-selection-rule.md.")]
    # ---- without the post-holdout windows
    ins = orders.get("in_sample", [])
    if ins:
        L += ["", "## Without the post-holdout windows (in-sample pool, its own weights, pi_up and tie group)", "",
              "| # | Model | HEADLINE_RET | HIT L / M / S | HIT UP / DOWN | Tie group (90% interval vs top) | CS_HIT | Full-pool rank |",
              "|---|---|---|---|---|---|---|---|"]
        for k, n in enumerate(ins, 1):
            e = rows[n]
            hit = e["hit"]["in_sample"]
            t = ties.get("in_sample", {}).get(n)
            tie = "—" if t is None else (f"{'**yes**' if t['tied'] else 'no'} [{t['lo']:+.3f}, {t['hi']:+.3f}]")
            flag = ""
            if cash_ret.get("in_sample") is not None and e["headline_ret"]["in_sample"] < cash_ret["in_sample"]:
                flag = " ⚠ worse than doing nothing"
            L.append(f"| {k} | {n}{flag}{'' if e['eligible'] else ' (not eligible)'} | {e['headline_ret']['in_sample']:.3f} | "
                     f"{hit['LENIENT']:.2f} / {hit['MIDDLE']:.2f} / {hit['STRICT']:.2f} | "
                     f"{_num(_mean3(e['hit_up']['in_sample']), 2)} / {_num(_mean3(e['hit_down']['in_sample']), 2)} | "
                     f"{tie} | {_num(e['cs_hit']['in_sample'])} | {cands.index(n) + 1 if n in cands else '—'} |")
        for n in refs:
            e = rows[n]
            L.append(f"| | {LABELS.get(n, n)} | {e['headline_ret'].get('in_sample', float('nan')):.3f} | "
                     f"{e['hit']['in_sample']['LENIENT']:.2f} / {e['hit']['in_sample']['MIDDLE']:.2f} / "
                     f"{e['hit']['in_sample']['STRICT']:.2f} | {_num(_mean3(e['hit_up']['in_sample']), 2)} / "
                     f"{_num(_mean3(e['hit_down']['in_sample']), 2)} | — | {_num(e['cs_hit']['in_sample'])} | — |")
        alt_ins = (alt_orders.get("in_sample") or [None])[0]
        L += ["", f"**Pick without the post-holdout windows, rule {rule_name}: `{ins[0]}`.** Under the {alt_name} rule: "
              f"`{alt_ins}`."]
    L += ["", "Columns: HIT L / M / S = the share of weight clearing LENIENT (−1.4965% in DOWN windows, 0% in UP "
          "windows, an assumption), MIDDLE (0%) and STRICT (max(0, the 6 gate benchmarks' median)); HIT UP / DOWN = "
          "the mean of the three HITs on UP and on DOWN windows, each group's weights renormalized. CS_HIT = mean "
          "composite (V1 FLOORED) over the windows clearing LENIENT, on HKT days and on UTC days. Old REL = the "
          f"primary of tool version `{sc.get('previous_tool_version')}` (report only). Hard gates: G1 (≥ 10 active HKT "
          "days in every window), G4 (long-only run completes), G5 (leakage). Report-only gates: G2, G3, G6_median, "
          "G6_worst. Replay: the previous edition's two real windows from cash, R and rank among its teams "
          "(numbers only)."]
    L += return_view(rows, tables, cands)
    L += ["", "## Runs per person (this tool version)", "", "| Person | Full runs | Best eligible candidate HEADLINE_RET |",
          "|---|---|---|"]
    for person in sorted(runs_by):
        mine = [e for e in rows.values() if e["author"] == person and e["candidate"] and e["eligible"]]
        be = max(mine, key=lambda e: e["primary"]) if mine else None
        best = "—" if be is None else "{:.3f} ({})".format(be["primary"], be["model"])
        L.append(f"| {person} | {runs_by[person]} | {best} |")
    L += previous_versions(entries, tool_version)
    return "\n".join(L) + "\n"


def previous_versions(entries: list[dict], tool_version: str) -> list[str]:
    """Older tool versions' rows, kept and marked: their numbers come from other formulas and are not comparable."""
    by: dict[str, dict[str, dict]] = {}
    order: list[str] = []
    for e in entries:
        tv = e.get("tool_version")
        if not e.get("full") or tv == tool_version:
            continue
        if tv not in by:
            by[tv] = {}
            order.append(tv)
        by[tv][e["model"]] = e
    if not by:
        return []
    L = ["", "## Previous tool versions (not comparable with the rows above)", "",
         "| Tool version | Scoring version | Latest run | Model | Primary of that version | Eligible then |", "|---|---|---|---|---|---|"]
    for tv in reversed(order):
        for n, e in sorted(by[tv].items(), key=lambda kv: -kv[1]["primary"]):
            L.append(f"| `{tv}` (previous version) | v{e.get('scoring_version', 1)} | {e['ts'][:16]} | {n} | "
                     f"{e['primary']:+.3f} | {'yes' if e['eligible'] else 'no'} |")
    return L


def write_leaderboard(cfg: dict, tool_version: str) -> Path:
    sc = cfg["scoring"]
    entries, _ = read(sc["registry"])
    md = leaderboard(entries, tool_version, cfg)
    out = resolve(sc["leaderboard"])
    out.parent.mkdir(parents=True, exist_ok=True)
    with locked():
        out.write_text(md)
    return out
