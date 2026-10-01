"""Stress test of MR @4h (research/baitoey/prereg/20261001-mean-reversion-stress.md).

    python -m research.baitoey.mr_stress

Uses the mean-reversion study outputs (results/baitoey/20261001-mr-study/) and the field runs registered for the
same tool version; scores the four plateau neighbours like --score without registering them.
"""
from __future__ import annotations

import copy
import dataclasses
import json
import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.data import load_market
from backtest.scoring.competition import block_bootstrap
from backtest.scoring.score import score_model
from research.baitoey.rot_max_study import stats
from research.baitoey.vt_study import ROOT, per_window, period
from src.config import load_config
from src.models import get

NAME = "baitoey_mr_bbrsi"
STUDY = ROOT / "results" / "baitoey" / "20261001-mr-study"
OUT = ROOT / "results" / "baitoey" / "20261001-mr-stress"
NEIGHBOURS = {"bb_k_1.5": {"bb_k": 1.5}, "bb_k_2.5": {"bb_k": 2.5}, "rsi_25": {"rsi_entry": 25}, "rsi_35": {"rsi_entry": 35}}
VARIANTS = ("V1", "V2", "V3", "V4")
log = logging.getLogger("mr_stress")


def field_windows(cfg: dict, tool: str) -> dict[str, pd.DataFrame]:
    reg = [json.loads(x) for x in (ROOT / "results" / "scoring" / "registry.jsonl").read_text().splitlines()]
    latest = {r["model"]: r for r in reg if r["tool_version"] == tool and r.get("full")}
    out = {}
    for m in cfg["scoring"]["field"]:
        p = Path(latest[m]["score_json"])
        out[m] = per_window(json.loads((p if p.is_absolute() else ROOT / p).read_text()))
    return out


def rel(per: dict[str, pd.DataFrame], field: list[str], keep: np.ndarray, wl: pd.Series, wr: pd.Series) -> dict:
    """HEADLINE REL FLOORED on the kept windows, the REL unit recomputed from the field on the same windows."""
    def head(d, v):
        cs = d[f"FLOORED.{v}.cs"].to_numpy()[keep]
        a, b = wl.to_numpy()[keep], wr.to_numpy()[keep]
        return 0.7 * (cs * a).sum() / a.sum() + 0.3 * (cs * b).sum() / b.sum()
    H = {m: {v: head(d, v) for v in VARIANTS} for m, d in per.items()}
    F = {v: np.mean([H[m][v] for m in field]) for v in VARIANTS}
    return {m: float(np.mean([H[m][v] / F[v] for v in VARIANTS])) for m in per}


def run_one(n: str) -> str:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    cfg = load_config()
    base = get(NAME)
    model = copy.copy(base)
    model.spec = dataclasses.replace(base.spec, rebalance_hours=4)
    vcfg = copy.deepcopy(cfg)
    vcfg["models"][NAME] = {**cfg["models"][NAME], "bar_hours": 4, **NEIGHBOURS[n], "_rebalance_hours": 4}
    score, _ = score_model(model, load_market(cfg), vcfg, use_cache=True, log=logging.getLogger(n))
    (OUT / f"{n}.json").write_text(json.dumps(score))
    return n


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_config()
    mr = json.loads((STUDY / "MR_4h.json").read_text())
    ref = json.loads((STUDY / "team_rot_ew.json").read_text())
    md, rd = per_window(mr), per_window(ref)
    field = field_windows(cfg, mr["tool_version"])
    per = {"MR_4h": md, "team_rot_ew": rd, **{f"field:{m}": d for m, d in field.items()}}
    names = [f"field:{m}" for m in field]
    idx = md.index
    for d in per.values():
        assert d.index.equals(idx), "window sets differ"
    wl, wr = md.w_live.astype(float), md.w_rec.astype(float)

    L = ["# Stress test of MR @4h", "", "## 1. Leave one month out", ""]
    full = rel(per, names, np.ones(len(idx), bool), wl, wr)
    L.append(f"All windows: MR @4h {full['MR_4h']:.3f}, team_rot_ew {full['team_rot_ew']:.3f} "
             f"(diff {full['MR_4h'] - full['team_rot_ew']:+.3f})")
    ends = idx + pd.Timedelta(days=14)
    rows = []
    for m in pd.period_range("2020-06", "2026-07", freq="M"):
        a, b = m.start_time.tz_localize("UTC"), (m.end_time + pd.Timedelta(1)).tz_localize("UTC")
        keep = ~((idx < b) & (ends > a))
        r = rel(per, names, np.asarray(keep), wl, wr)
        rows.append((str(m), int((~keep).sum()), r["MR_4h"], r["team_rot_ew"], r["MR_4h"] - r["team_rot_ew"]))
    t = pd.DataFrame(rows, columns=["month", "dropped", "MR", "ROT", "diff"]).set_index("month")
    jul = t.loc["2026-07"]
    share = float((t["diff"] > 0).mean())
    ok1 = bool(jul["diff"] > 0 and share >= 0.9)
    L += [f"July 2026 dropped ({int(jul['dropped'])} windows): MR {jul['MR']:.3f}, ROT {jul['ROT']:.3f}, diff {jul['diff']:+.3f}",
          f"MR above ROT in {share:.0%} of {len(t)} one-month exclusions; smallest diff {t['diff'].min():+.3f} "
          f"({t['diff'].idxmin()}), largest {t['diff'].max():+.3f} ({t['diff'].idxmax()})",
          "Most influential months (dropping them lowers the diff most):", "",
          "| Month dropped | Windows dropped | MR | ROT | Diff |", "|---|---|---|---|---|"]
    L += [f"| {m} | {r.dropped} | {r.MR:.3f} | {r.ROT:.3f} | {r['diff']:+.3f} |" for m, r in t.sort_values("diff").head(6).iterrows()]
    L += ["", f"**Check 1 {'PASSES' if ok1 else 'FAILS'}** (needs diff > 0 without July 2026 and in >= 90% of exclusions)", ""]

    with ProcessPoolExecutor(max_workers=4) as ex:
        for n in ex.map(run_one, NEIGHBOURS):
            log.info("finished %s", n)
    base = stats(period(md, "SCREEN"))
    L += ["## 2. Plateau (SCREEN only for the check; REL reported)", "",
          "| Run | SCREEN gate passed | SCREEN median R | SCREEN worst 10% | REL | vs team_rot_ew [90%] |", "|---|---|---|---|---|---|",
          f"| MR @4h (base) | {base['gate_pass']:.0%} | {base['median_R']:+.2%} | {base['worst10_R']:+.2%} | {mr['primary']['headline']:.3f} | (study) |"]
    sc = cfg["scoring"]
    ok2 = True
    for n in NEIGHBOURS:
        s = json.loads((OUT / f"{n}.json").read_text())
        d = per_window(s)
        st = stats(period(d, "SCREEN"))
        ok2 &= bool(st["median_R"] >= base["median_R"] - 0.005 and st["gate_pass"] >= base["gate_pass"] - 0.05)
        diff = (d["FLOORED.REL.cs"] - rd["FLOORED.REL.cs"].reindex(d.index)).dropna()
        b = block_bootstrap(diff, d.w_live, d.w_rec, sc["headline"], int(sc["compare"]["block_windows"]),
                            int(sc["compare"]["reps"]), float(sc["compare"]["level"]), int(sc["compare"]["seed"]))
        L.append(f"| {n} | {st['gate_pass']:.0%} | {st['median_R']:+.2%} | {st['worst10_R']:+.2%} | "
                 f"{s['primary']['headline']:.3f} | {b['diff']:+.3f} [{b['lo']:+.3f}, {b['hi']:+.3f}] |")
    L += ["", f"**Check 2 {'PASSES' if ok2 else 'FAILS'}** (each neighbour within 0.5 pt of median R and 5 pt of gate pass on SCREEN)"]
    text = "\n".join(L)
    (OUT / "report.md").write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
