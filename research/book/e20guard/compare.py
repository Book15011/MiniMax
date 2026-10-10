"""EXPERIMENTAL / report-only: the e20v45 guard and combo candidates side by side on the weak-market board
(results/scoring/leaderboard_2.csv: 228 h from 25 weak checkpoints like 2026-10-09, two data profiles)."""
import pandas as pd

B = "/home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.csv"
NAMES = ["pol_switch_vt_tl_e20v45", "book_e20guard_pullback", "book_e20guard_confirm", "baitoey_ovl_altbtc_b_e20",
         "baitoey_ovl_brk_e20", "book_e20combo_alt_cash", "book_e20combo_alt_cash_pb", "book_e20combo_alt_trim",
         "book_e20combo_brk_cash", "book_e20combo_alt_half_cash", "book_cashshort_pullback", "baitoey_ovl_brk_dual",
         "pol_mom_ss"]
lb = pd.read_csv(B)
lb["rank"] = range(1, len(lb) + 1)
d = lb[lb.model.isin(NAMES)].set_index("model").reindex([n for n in NAMES if n in set(lb.model)])
pct = lambda x: f"{100 * x:+.2f}%"
cols = {"rank": "rank", "selection_score": "selection", "return_mean": "mean 9.5 d", "return_median": "median",
        "return_p10": "bad 10%", "return_worst": "worst", "future_down_stress_mean": "if it keeps falling",
        "future_rebound_stress_mean": "if it rebounds", "return_positive": "share > 0", "mdd_mean": "mean max DD"}
print("| model | " + " | ".join(cols.values()) + " |")
print("|---|" + "---|" * len(cols))
for m, r in d.iterrows():
    vals = [str(int(r["rank"]))] + [pct(r[k]) if k not in ("rank",) else "" for k in list(cols)[1:]]
    print(f"| {m} | " + " | ".join(vals) + " |")
missing = [n for n in NAMES if n not in set(lb.model)]
print("\nnot on the board yet:", missing)
