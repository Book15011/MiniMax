"""Trade only the biggest coins? (research/baitoey/prereg/20261003-big-coins.md).

The base runs are read from the registry; each variant keeps only the top N of the usual Roostoo universe by
trailing 30-day quote volume and is scored with score_model like --score, not registered.

    python -m research.baitoey.big_coins
"""
from __future__ import annotations

import copy
import json
import logging
from dataclasses import replace

import numpy as np
import pandas as pd

from backtest.data import Market, load_market
import backtest.scoring.score as scoring
from backtest.scoring.registry import resolve
from backtest.scoring.score import dumps, score_model
from research.baitoey.shock_plateau import TYPES, volatile_hit
from research.baitoey.vt_dual import registered_score, summarize
from research.baitoey.vt_plateau import pct
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models import get

OUT = ROOT / "results" / "baitoey" / "20261003-big-coins"
MODELS = {"V": "baitoey_vt_mom", "E": "pol_switch_vt_tl_e20v45"}
SIZES = (10, 15)
VOLUME_HOURS = 30 * 24
MARGIN, NOISE, WORST_GAIN, CS_GAIN = 0.03, 0.01, 0.02, 0.02


def top_by_volume(market: Market, n: int) -> Market:
    """The usual universe cut to its top n by trailing 30-day quote volume at each universe date (no look-ahead)."""
    qv = market.quote_volume.fillna(0.0).rolling(VOLUME_HOURS, min_periods=1).sum()
    out = {}
    for t, ids in market.universe_by_day.items():
        if not ids:
            out[t] = ids
            continue
        row = qv.loc[:t].iloc[-1] if t >= qv.index[0] else pd.Series(0.0, index=list(ids))
        v = row.reindex(list(ids)).fillna(0.0)
        keep = sorted(v.sort_values(ascending=False, kind="stable").index[:n])
        out[t] = tuple(keep)
    return replace(market, universe_by_day=pd.Series(out), notes={**market.notes, "universe_top_n": n})


def verdict(x: dict, base: dict) -> str:
    if not x["eligible"] or x["headline"] < base["headline"] - MARGIN:
        return "worse"
    if x["headline"] >= base["headline"] - NOISE and (x["worst_R"] - base["worst_R"] >= WORST_GAIN
                                                      or x["cs_hit"] - base["cs_hit"] >= CS_GAIN):
        return "better"
    return "no clear difference"


def report(rows: dict[str, dict]) -> str:
    lines = ["# Trade only the biggest coins? (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261003-big-coins.md`. Variants keep the top N of the usual",
             "Roostoo universe by trailing 30-day traded value; scored like `--score`, not registered. Type columns: hit",
             "rate (mean of the three bars) by BTC's 14-day move (<= -5% / -5..0% / 0..+5% / >= +5%) and in the most",
             "volatile windows.", "",
             "| Run | Coins | HEADLINE_RET | vs base | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Fees | Hard gates | Same bars | Verdict |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, x in rows.items():
        base = rows[key[0] + "0"]
        ty = " | ".join("—" if x["types"][k] is None else f"{100 * x['types'][k]:.0f}%" for k in TYPES)
        vol = "—" if x.get("volatile") is None else f"{100 * x['volatile']:.0f}%"
        rp = " · ".join(f"{pct(p['R'])} #{p['rank']}/{p['teams']}" for p in x["replay"]) or "—"
        lines.append(f"| {key} | {x['change']} | **{x['headline']:.3f}** | {x['headline'] - base['headline']:+.3f} | "
                     f"{x['in_sample']:.3f} | {x['cs_hit']:.3f} | {ty} | {vol} | {pct(x['median_R'])} / {pct(x['mean_R'])} | "
                     f"{pct(x['worst_R'])} | {rp} | {pct(x['fees'], 2)} | {'pass' if x['eligible'] else 'FAIL'} | "
                     f"{x.get('same_bars', '—')} | {x.get('verdict', 'base')} |")
    lines.append("")
    for p, name in MODELS.items():
        done = [f"{p}{n}" for n in SIZES if f"{p}{n}" in rows]
        if len(done) < len(SIZES):
            lines.append(f"- `{name}`: pending ({len(done)} of {len(SIZES)} variants scored).")
            continue
        ok = all(rows[r]["verdict"] == "better" for r in done)
        lines.append(f"- `{name}`: " + ", ".join(f"{r} {rows[r]['verdict']}" for r in done)
                     + f" -> **{'PROPOSE' if ok else 'DO NOT PROPOSE'}**.")
    lines += ["", f"Tool version(s): {', '.join(sorted({x['tool_version'] for x in rows.values()}))}."]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(OUT / "run.log"), logging.StreamHandler()])
    log = logging.getLogger("big_coins")
    cfg = load_config()
    btc = pd.read_parquet(resolve(cfg["harness"]["panel_dir"]) / "panel_close_1h.parquet", columns=["BTCUSDT"])["BTCUSDT"]
    rows, bars = {}, {}
    for p, name in MODELS.items():
        s = registered_score(name)
        bars[p] = np.array(s["per_window"]["bar_STRICT"], dtype=float)
        rows[f"{p}0"] = {**summarize(f"{p}0", "all", s, btc), "volatile": volatile_hit(s, btc), "cs_hit": s["primary"]["cs_hit"]}
    market = load_market(cfg)
    field_runs = scoring.field_runs                     # the benchmarks (and so the bars) use the usual universe
    scoring.field_runs = lambda _m, *a, **k: field_runs(market, *a, **k)
    for n in SIZES:
        m = top_by_volume(market, n)
        log.info("top %d: universe size median %d", n, int(np.median([len(x) for x in m.universe_by_day])))
        for p, name in MODELS.items():
            key = f"{p}{n}"
            c = copy.deepcopy(cfg)
            c["models"][name] = {**copy.deepcopy(cfg["models"][name]), "research_universe_top_n": n}  # own cache key
            log.info("%s (%s, top %d): scoring", key, name, n)
            score, _ = score_model(get(name), m, c, use_cache=True, log=log)
            (OUT / f"{key}-score.json").write_text(dumps(score))
            x = {**summarize(key, f"top {n}", score, btc), "volatile": volatile_hit(score, btc), "cs_hit": score["primary"]["cs_hit"]}
            new = np.array(score["per_window"]["bar_STRICT"], dtype=float)
            x["same_bars"] = "yes" if new.shape == bars[p].shape and np.allclose(new, bars[p], equal_nan=True) else "NO"
            x["verdict"] = verdict(x, rows[f"{p}0"])
            rows[key] = x
            (OUT / "report.md").write_text(report(rows))
            log.info("%s: HEADLINE_RET %.4f (%s)", key, x["headline"], x["verdict"])
    (OUT / "rows.json").write_text(json.dumps(rows, indent=1, default=str))
    log.info("done: %s", OUT / "report.md")


if __name__ == "__main__":
    main()
