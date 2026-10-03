"""Skip the lock-in while BTC is in a strong rally? (research/baitoey/prereg/20261004-lock-btc-filter.md).

Method of Pol's results/pol/20261002-v2check/endgame2.py (cached v2 equity paths, v2 weights and bars, V1 FLOORED
composite for CS_HIT, his ~150-team cut), with the lock's BTC filter added.

    python -m research.baitoey.lock_btc_filter
"""
from __future__ import annotations

import glob
import json
import logging

import numpy as np
import pandas as pd

from backtest.data import load_market
from backtest.scoring.evaluate import simulate
from backtest.scoring.metrics import window_metrics
from backtest.scoring.returnfirst import month_multiplicity, tie_test
from backtest.scoring.windows import pool_starts
from research.baitoey.vt_study import ROOT
from src.config import load_config
from src.models import get

OUT = ROOT / "results" / "baitoey" / "20261004-lock-btc-filter"
TOOL = "3036a0d8bfdaa6a0"
H, EXIT, LOCK, DAY = 336, 0.0013, 0.03, 10
RULES = {"N": None, "L0": np.inf, "B8": 0.08, "B10": 0.10, "B12": 0.12}       # BTC line; inf = never blocks
GAIN, HR_TOL, CS_TOL = 0.005, 0.01, 0.02


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.WARNING)
    cfg = load_config(); sc = cfg["scoring"]; market = load_market(cfg)
    starts = pool_starts(market, cfg)
    liq = float(sc["liquidation_cost"])
    points = np.array([0] + list(range(4, H, 24)) + [H])
    ref = [json.load(open(f)) for f in glob.glob(str(ROOT / "results/*/*/team_rot_ew-*/score.json"))]
    ref = [s for s in ref if s.get("tool_version") == TOOL][-1]
    pw = pd.DataFrame(ref["per_window"]); pw.index = pd.to_datetime(pw.pop("start"), utc=True)
    pw = pw[pw.scored.astype(bool)].reindex(starts)
    up = pw.btc_up.astype(bool).to_numpy(); fmed = pw.field_median_R_liq.to_numpy()
    w = pw.w_final.to_numpy(); w = w / w.sum()
    bars = np.column_stack([np.where(up, 0.0, -0.014965215), np.zeros(len(starts)), np.maximum(0.0, fmed)])
    fr = {}
    for n in sc["field"]:
        rr = simulate(get(n), market, cfg, starts, use_cache=True)
        k = rr.windows.index.get_indexer(starts)
        fr[n] = rr.equity[k, -1] * (1 - liq * rr.gross[k, -1]) - 1
    fr = pd.DataFrame(fr, index=starts)
    cuts = {"~150-team cut": np.where(up, np.maximum(0, fr.max(axis=1).to_numpy()), 0.006),
            "best of six": np.maximum(0, fr.max(axis=1).to_numpy())}
    btc = market.close["BTCUSDT"]
    offs = pd.to_timedelta(np.arange(H + 1), unit="h")
    B = np.vstack([btc.reindex(t0 + offs, method="ffill").to_numpy() for t0 in starts])
    btc_ret = B / B[:, :1] - 1
    strong = btc_ret[:, DAY * 24] >= 0.10
    mult = month_multiplicity(starts, 2000, 20261004)

    def score(E, G):
        R = E[:, -1] * (1 - liq * G[:, -1]) / E[:, 0] - 1
        comp = window_metrics(E, G[:, -1], sc, points=points)["FLOORED.V1.composite"].to_numpy()
        ind = (R[:, None] >= bars).astype(float)
        ok = ind[:, 0] > 0
        cut = {k: (R >= v).astype(float) for k, v in cuts.items()}
        return {"HR": float((w[:, None] * ind).sum(0).mean()), "CS_HIT": float((w[ok] * comp[ok]).sum() / w[ok].sum()),
                "mean_R": float((w * R).sum()), "worst_R": float(R.min()), "ind": ind, "cut": cut, "R": R}

    def lock(E, G, line):
        E, G = E.copy(), G.copy()
        R = E / E[:, :1] - 1
        ok = R[:, DAY * 24:H - 1] >= LOCK
        ok &= btc_ret[:, DAY * 24:H - 1] < line
        n = 0
        for k in range(len(E)):
            hit = np.nonzero(ok[k])[0]
            if len(hit):
                h = DAY * 24 + hit[0] + 1
                E[k, h:] = E[k, h] * (1 - EXIT * G[k, h]); G[k, h:] = 0.0; n += 1
        return E, G, n

    def boot_share(hit):
        return (mult @ (w * hit)) / (mult @ w)

    P = lambda x: f"{100 * x:+.2f}%"
    lines = ["# Skip the lock-in while BTC is in a strong rally? (scoring v2)", "",
             "Pre-registration: `research/baitoey/prereg/20261004-lock-btc-filter.md`. Method of Pol's endgame2.py on the cached",
             "v2 paths (2,298 windows). Cut shares are weighted (w') shares of rounds whose R_liq clears the cut.", ""]
    verdict = None
    for name, primary in (("pol_switch_vt_tl_e20v45", True), ("baitoey_vt_mom", False)):
        run = simulate(get(name), market, cfg, starts, use_cache=True)
        sel = run.windows.index.get_indexer(starts)
        E0, G0 = run.equity[sel], run.gross[sel]
        sf = [json.load(open(f)) for f in glob.glob(str(ROOT / f"results/*/*/{name}-*/score.json"))]
        sf = [s for s in sf if s.get("tool_version") == TOOL][-1]
        res, inds = {}, {}
        for key, line in RULES.items():
            E, G, n = (E0, G0, 0) if line is None else lock(E0, G0, line)
            r = score(E, G); r["exits"] = n / len(E0)
            res[key] = r; inds[key] = r["ind"]
        tie = tie_test(inds, w, "L0", mult, 0.90)
        base = res["N"]
        lines += [f"## {name}{' (primary)' if primary else ' (report-only)'}", "",
                  f"Unmodified paths: HEADLINE_RET {base['HR']:.4f} (score file {sf['return_first']['full']['headline_ret']:.4f}), "
                  f"CS_HIT {base['CS_HIT']:.3f} ({sf['return_first']['full']['cs_hit']:.3f}).", "",
                  "| Rule | Exits | HEADLINE_RET | vs L0 [90%] | CS_HIT | ~150-team cut | vs L0 [90%] | Best of six | Mean R | Worst R | Strong-rally rounds: ~150 cut / best of six |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
        l0c = res["L0"]["cut"]["~150-team cut"]; bl0 = boot_share(l0c)
        for key, r in res.items():
            c = r["cut"]["~150-team cut"]; d = boot_share(c) - bl0
            cs = float((w * c).sum()); cs0 = float((w * l0c).sum())
            ws = w[strong] / w[strong].sum()
            lines.append(f"| {key} | {100 * r['exits']:.0f}% | {r['HR']:.4f} | {tie[key]['diff']:+.4f} [{tie[key]['lo']:+.4f}, {tie[key]['hi']:+.4f}] | "
                         f"{r['CS_HIT']:.3f} | {cs:.3f} | {cs - cs0:+.4f} [{np.quantile(d, 0.05):+.4f}, {np.quantile(d, 0.95):+.4f}] | "
                         f"{float((w * r['cut']['best of six']).sum()):.3f} | {P(r['mean_R'])} | {P(r['worst_R'])} | "
                         f"{float((ws * c[strong]).sum()):.3f} / {float((ws * r['cut']['best of six'][strong]).sum()):.3f} |")
        lines.append("")
        if primary:
            l0 = res["L0"]; l0cut = float((w * l0c).sum())
            ok = {k: (float((w * res[k]["cut"]["~150-team cut"]).sum()) >= l0cut + GAIN and res[k]["HR"] >= l0["HR"] - HR_TOL
                      and res[k]["CS_HIT"] >= l0["CS_HIT"] - CS_TOL) for k in ("B8", "B10", "B12")}
            verdict = (", ".join(f"{k} {'passes' if v else 'fails'}" for k, v in ok.items())
                       + f" -> **{'PROPOSE THE FILTER' if all(ok.values()) else 'KEEP THE LOCK-IN AS IT IS'}**.")
    lines += [f"Strong-rally rounds: BTC up at least 10% at day 10 ({int(strong.sum())} of {len(starts)}).", "",
              f"- Verdict (e20v45): {verdict}", "", f"Tool version: {TOOL}."]
    (OUT / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
