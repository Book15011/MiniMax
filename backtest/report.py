"""Report files: reports/<name>/<YYYYMMDD-HHMM>.md (committed) and .log with the same name (gitignored)."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from backtest.evaluate import Evaluation, must_pass, period_masks, summarize
from src.config import resolve

CONVENTIONS = ("Composite A: daily returns, annualized ratios, Calmar on the annualized return. "
               "Composite B: hourly returns, annualized ratios, Calmar on the raw 14-day return. "
               "Both = 0.4 Sortino + 0.3 Sharpe + 0.3 Calmar; the official formula is published only on Finale Day.")


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")


def open_run(cfg: dict, name: str, ts: str | None = None) -> tuple[Path, Path, logging.Logger]:
    """Create reports/<name>/ and a logger writing to <ts>.log (and the console)."""
    ts = ts or stamp()
    out = resolve(cfg["harness"]["reports_dir"]) / name
    out.mkdir(parents=True, exist_ok=True)
    md, lg = out / f"{ts}.md", out / f"{ts}.log"
    log = logging.getLogger(f"harness.{name}.{ts}")
    log.setLevel(logging.INFO)
    log.handlers.clear()
    fmt = logging.Formatter("%(asctime)sZ %(levelname)s %(message)s")
    fmt.converter = lambda *a: datetime.now(timezone.utc).timetuple()
    for hdl in (logging.FileHandler(lg), logging.StreamHandler()):
        hdl.setFormatter(fmt)
        log.addHandler(hdl)
    log.propagate = False
    return md, lg, log


def pct(x: float) -> str:
    return "—" if pd.isna(x) else f"{x * 100:+.2f}%"


def num(x: float) -> str:
    return "—" if pd.isna(x) else f"{x:+.2f}"


def period_table(ev: Evaluation, cfg: dict) -> tuple[str, dict]:
    need = cfg["harness"]["min_active_days"]
    rows, summ = [], {}
    for name, mask in period_masks(ev.windows, cfg, ev.holdout_opened).items():
        s = summarize(ev.windows[mask.to_numpy()], need)
        summ[name] = s
        if s["n"] == 0:
            rows.append(f"| {name} | 0 | | | | | | | | | | | |")
            continue
        rows.append(f"| {name} | {s['n']} | {pct(s['med'])} | {pct(s['p10'])} | {pct(s['p90'])} | {pct(s['worst'])} | "
                    f"{s['pos']:.0%} | {pct(s['mdd_med'])} | {pct(s['mdd_worst'])} | {num(s['comp_a'])} | "
                    f"{num(s['comp_b'])} | {s['active_ok']:.0%} | {s['turn_day']:.2f} |")
    head = (f"| Windows | n | Median | Worst 10% | Best 10% | Worst | > 0 | Median max DD | Worst max DD | "
            f"Median comp. A | Median comp. B | ≥ {need} active days | Turnover/day |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    return head + "\n" + "\n".join(rows), summ


def year_table(ev: Evaluation, cfg: dict) -> str:
    masks = period_masks(ev.windows, cfg, ev.holdout_opened)
    w = ev.windows[masks["ALL"].to_numpy()]
    rows = []
    for y, g in w.groupby(w.index.year):
        rows.append(f"| {y} | {len(g)} | {pct(g.ret.median())} | {pct(g.ret.quantile(0.1))} | {pct(g.ret.min())} | "
                    f"{num(g.comp_a.median())} |")
    return ("| Year (window start) | n | Median | Worst 10% | Worst | Median comp. A |\n|---|---|---|---|---|---|\n"
            + "\n".join(rows))


def write_model_report(ev: Evaluation, ref: Evaluation, market_notes: dict, cfg: dict, md: Path,
                       runtime_s: float) -> dict:
    spec = ev.spec
    table, summ = period_table(ev, cfg)
    checks = must_pass(ev, ref, cfg)
    ref_table, _ = period_table(ref, cfg)
    git = ev.meta.get("git", {})
    lines = [
        f"# {spec.name}",
        "",
        f"{spec.description}",
        "",
        "| | |", "|---|---|",
        f"| Method · author | {spec.method} · {spec.author} |",
        f"| Decisions | every {spec.rebalance_hours} h at 16:00 UTC anchor · drift band {spec.band:.0%} · shorts {'yes' if spec.uses_shorts else 'no'} |",
        f"| Code | commit `{git.get('commit', '?')}`{' (uncommitted changes!)' if git.get('dirty') else ''} · cache key `{ev.meta.get('cache_key')}` |",
        f"| Data | panel {market_notes['panel_first'][:10]} → {market_notes['panel_last'][:16]} UTC · universe `{market_notes['universe_mode']}` · spreads from {market_notes['spreads_source']} |",
        f"| Holdout | {'**opened** (windows ending after ' + cfg['harness']['holdout_from'] + ' UTC)' if ev.holdout_opened else 'sealed'} |",
        f"| Runtime | {runtime_s:.0f} s · {ev.meta.get('n_decisions')} decisions · median {ev.meta.get('coins_held_median'):.0f} coins held |",
        "",
        "## Must-pass checks (SCREEN + CONFIRM windows)",
        "",
        "| Check | Result | Detail |", "|---|---|---|",
        *[f"| {c} | {'PASS' if ok else '**FAIL**'} | {d} |" for c, ok, d in checks],
        "",
        "## Results: every 14-day window started from cash at 00:00 HKT",
        "",
        table,
        "",
        "## Same windows: BTC hold (reference)",
        "",
        ref_table,
        "",
        "## By year (context only)",
        "",
        year_table(ev, cfg),
        "",
        "## Parameters (`config.yaml` → `models:`)",
        "",
        "```json",
        json.dumps(ev.params, indent=1, sort_keys=True),
        "```",
        "",
        "## How to read this",
        "",
        f"- Costs: {cfg['harness']['fees']['taker']:.2%} per side (long and short) plus each coin's half-spread; orders fill one bar after the decision.",
        f"- The engine forces a trade on any HKT day with none by hour {cfg['harness']['activity_guard_offset_hours']} of the day.",
        f"- {CONVENTIONS}",
        "- SCREEN / CONFIRM follow the validation split; windows ending after the holdout date are sealed until the launch model is frozen.",
    ]
    md.write_text("\n".join(lines) + "\n")
    return {"summary": summ, "checks": checks}
