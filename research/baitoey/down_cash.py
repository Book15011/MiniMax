"""e20v45 with cash in down mode (research/baitoey/prereg/20261004-down-cash.md).

    python -m research.baitoey.down_cash [DC15 DC20 DC25]     score runs (one label per process)
    python -m research.baitoey.down_cash report                rebuild the report, with the lock-in numbers
"""
from __future__ import annotations

import copy
import glob
import json
import logging
import sys

import numpy as np
import pandas as pd

from backtest.data import load_market
from backtest.scoring.evaluate import simulate
from backtest.scoring.metrics import window_metrics
from backtest.scoring.registry import resolve
from backtest.scoring.score import dumps, score_model
from backtest.scoring.windows import pool_starts
from research.baitoey.shock_plateau import TYPES, volatile_hit
from research.baitoey.vt_dual import registered_score, summarize
from research.baitoey.vt_plateau import pct
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models import get

NAME = "pol_switch_vt_tl_e20v45"
OUT = ROOT / "results" / "baitoey" / "20261004-down-cash"
PLATEAU = ROOT / "results" / "baitoey" / "20261003-e20v45-plateau"
RUNS = {"DC15": 15, "DC20": 20, "DC25": 25}
REF = {"DC15": "E1", "DC20": "E0", "DC25": "E2"}
TOOL = "3036a0d8bfdaa6a0"
MARGIN, NOISE, WORST_GAIN, CS_GAIN = 0.03, 0.01, 0.02, 0.02
H, EXIT, LOCK, DAY = 336, 0.0013, 0.03, 10


def params(cfg: dict, ema: int) -> dict:
    p = copy.deepcopy(cfg["models"][NAME])
    p["sleeves"] = {k: v for k, v in p["sleeves"].items() if k != "pol_trend_ls"}
    p["switch"] = {**p["switch"], "ema_days": ema}
    return p


def config(cfg: dict, ema: int) -> dict:
    c = copy.deepcopy(cfg)
    c["models"][NAME] = params(cfg, ema)
    return c


def row(label: str, change: str, score: dict, btc: pd.Series) -> dict:
    return {**summarize(label, change, score, btc), "volatile": volatile_hit(score, btc), "cs_hit": score["primary"]["cs_hit"]}


def with_lock(cfg: dict, market) -> dict:
    """HEADLINE_RET and CS_HIT of E0 and DC20 with the live lock-in (method of Pol's endgame2.py)."""
    sc = cfg["scoring"]; starts = pool_starts(market, cfg); liq = float(sc["liquidation_cost"])
    points = np.array([0] + list(range(4, H, 24)) + [H])
    ref = [json.load(open(f)) for f in glob.glob(str(ROOT / "results/*/*/team_rot_ew-*/score.json"))]
    ref = [s for s in ref if s.get("tool_version") == TOOL][-1]
    pw = pd.DataFrame(ref["per_window"]); pw.index = pd.to_datetime(pw.pop("start"), utc=True)
    pw = pw[pw.scored.astype(bool)].reindex(starts)
    up = pw.btc_up.astype(bool).to_numpy(); w = pw.w_final.to_numpy(); w = w / w.sum()
    bars = np.column_stack([np.where(up, 0.0, -0.014965215), np.zeros(len(starts)), np.maximum(0.0, pw.field_median_R_liq.to_numpy())])
    out = {}
    for key, c in (("E0", cfg), ("DC20", config(cfg, 20))):
        run = simulate(get(NAME), market, c, starts, use_cache=True)
        sel = run.windows.index.get_indexer(starts)
        E, G = run.equity[sel].astype(float), run.gross[sel].astype(float)
        R0 = E / E[:, :1] - 1
        for k in range(len(E)):
            hit = np.nonzero(R0[k, DAY * 24:H - 1] >= LOCK)[0]
            if len(hit):
                h = DAY * 24 + hit[0] + 1
                E[k, h:] = E[k, h] * (1 - EXIT * G[k, h]); G[k, h:] = 0.0
        R = E[:, -1] * (1 - liq * G[:, -1]) / E[:, 0] - 1
        comp = window_metrics(E, G[:, -1], sc, points=points)["FLOORED.V1.composite"].to_numpy()
        ind = (R[:, None] >= bars).astype(float); ok = ind[:, 0] > 0
        out[key] = (float((w[:, None] * ind).sum(0).mean()), float((w[ok] * comp[ok]).sum() / w[ok].sum()), float(R.min()))
    return out


def report(cfg: dict, market, btc: pd.Series) -> None:
    rows = {"E0": row("E0", "long/short trend, EMA 20 (base)", registered_score(NAME), btc)}
    for k, lab in (("E1", "long/short trend, EMA 15"), ("E2", "long/short trend, EMA 25")):
        f = PLATEAU / f"{k}-score.json"
        if f.exists():
            rows[k] = row(k, lab, json.loads(f.read_text()), btc)
    for k, ema in RUNS.items():
        f = OUT / f"{k}-score.json"
        if f.exists():
            rows[k] = row(k, f"cash, EMA {ema}", json.loads(f.read_text()), btc)
    e0 = rows["E0"]
    lines = ["# e20v45 with cash in down mode (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261004-down-cash.md`. Scored like `--score`, not registered. Type",
             "columns: hit rate (mean of the three bars) by BTC's 14-day move (<= -5% / -5..0% / 0..+5% / >= +5%) and in the",
             "most volatile windows.", "",
             "| Run | Down mode | HEADLINE_RET | vs E0 | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Fees | Hard gates |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key in ("E0", "DC20", "E1", "DC15", "E2", "DC25"):
        if key not in rows:
            continue
        x = rows[key]
        ty = " | ".join("—" if x["types"][k] is None else f"{100 * x['types'][k]:.0f}%" for k in TYPES)
        vol = "—" if x.get("volatile") is None else f"{100 * x['volatile']:.0f}%"
        rp = " · ".join(f"{pct(p['R'])} #{p['rank']}/{p['teams']}" for p in x["replay"]) or "—"
        lines.append(f"| {key} | {x['change']} | **{x['headline']:.3f}** | {x['headline'] - e0['headline']:+.3f} | {x['in_sample']:.3f} | "
                     f"{x['cs_hit']:.3f} | {ty} | {vol} | {pct(x['median_R'])} / {pct(x['mean_R'])} | {pct(x['worst_R'])} | {rp} | "
                     f"{pct(x['fees'], 2)} | {'pass' if x['eligible'] else 'FAIL'} |")
    lines.append("")
    if all(k in rows for k in ("DC15", "DC20", "DC25", "E1", "E2")):
        d = rows["DC20"]
        better = d["eligible"] and (d["headline"] >= e0["headline"] + MARGIN or (d["headline"] >= e0["headline"] - NOISE and (
            d["worst_R"] - e0["worst_R"] >= WORST_GAIN or d["cs_hit"] - e0["cs_hit"] >= CS_GAIN)))
        hold = all(rows[k]["eligible"] and rows[k]["headline"] >= rows[REF[k]]["headline"] - MARGIN for k in ("DC15", "DC25"))
        lines.append(f"- DC20 {'better' if better else 'not better'} than E0; neighbours {'hold' if hold else 'do not hold'} -> "
                     f"**{'PROPOSE' if better and hold else 'KEEP THE TREND SLEEVE IN DOWN MODE'}**.")
        lk = with_lock(cfg, market)
        lines.append(f"- With the live lock-in (report-only): E0 HEADLINE_RET {lk['E0'][0]:.3f}, CS_HIT {lk['E0'][1]:.3f}, worst {pct(lk['E0'][2])}; "
                     f"DC20 {lk['DC20'][0]:.3f}, CS_HIT {lk['DC20'][1]:.3f}, worst {pct(lk['DC20'][2])}.")
    else:
        lines.append("- Verdict: pending.")
    lines += ["", f"Tool version(s): {', '.join(sorted({x['tool_version'] for x in rows.values()}))}."]
    (OUT / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(args: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(OUT / f"run-{'-'.join(args) or 'all'}.log"), logging.StreamHandler()])
    log = logging.getLogger("down_cash")
    cfg = load_config(); market = load_market(cfg)
    btc = pd.read_parquet(resolve(cfg["harness"]["panel_dir"]) / "panel_close_1h.parquet", columns=["BTCUSDT"])["BTCUSDT"]
    if args == ["report"]:
        report(cfg, market, btc)
        return
    for label in args or list(RUNS):
        log.info("%s (cash in down mode, EMA %d days): scoring", label, RUNS[label])
        score, _ = score_model(get(NAME), market, config(cfg, RUNS[label]), use_cache=True, log=log)
        (OUT / f"{label}-score.json").write_text(dumps(score))
        log.info("%s: HEADLINE_RET %.4f", label, score["primary"]["headline"])


if __name__ == "__main__":
    main(sys.argv[1:])
