"""EXPERIMENTAL / report-only: the decision table for the rest of the round (feature/e20-shortguard).

Weak-market board (results/scoring/leaderboard_2.csv): each model run from cash for 228 h from 25 historical
checkpoints that match the market on 2026-10-09 (BTC down 0-10% over 48 h, weak breadth), two data profiles.
Columns: mean, median, bad 10% (p10), good 10% (p90), worst, share of windows > 0, and the mean in the windows where
the market kept falling ("down") and where it rebounded ("rebound"), with their counts.
"""
import pandas as pd

B = "/home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.csv"
GROUPS = [
    ("Stay", ["pol_switch_vt_tl_e20v45"]),
    ("Short as a guard only", ["book_e20guard_confirm", "book_e20guard_pullback"]),
    ("Protect by cash (+ shorts)", ["book_e20combo_alt_half_cash", "book_e20combo_alt_cash", "baitoey_ovl_altbtc_b_e20",
                                    "book_e20combo_brk_cash"]),
    ("Clone rule", ["book_e20clone_flip", "book_e20clone_cash", "book_clone_ourcoins", "book_pooled_offsets"]),
]
lb = pd.read_csv(B)
lb["rank"] = range(1, len(lb) + 1)
lb = lb.set_index("model")
pct = lambda x: "-" if pd.isna(x) else f"{100 * x:+.2f}%"
print("| Choice | Model | Rank | Mean | Median | Bad 10% | Good 10% | Worst | > 0 | If it keeps falling (n) | If it rebounds (n) |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for g, names in GROUPS:
    for n in names:
        if n not in lb.index:
            print(f"| {g} | {n} | pending | | | | | | | | |")
            continue
        r = lb.loc[n]
        print(f"| {g} | {n} | {int(r['rank'])} | {pct(r.return_mean)} | {pct(r.return_median)} | {pct(r.return_p10)} | "
              f"{pct(r.return_p90)} | {pct(r.return_worst)} | {100 * r.return_positive:.0f}% | "
              f"{pct(r.future_down_stress_mean)} ({int(r.future_down_stress_n)}) | "
              f"{pct(r.future_rebound_stress_mean)} ({int(r.future_rebound_stress_n)}) |")
