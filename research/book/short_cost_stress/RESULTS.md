# Exact cost sensitivity: frozen short models
Book research; separate from leaderboard scoring.
Three frozen models,160 fixed14-day-spaced starts from2020-06-01 12UTC,228hours per path. No case enters the sealed boundary. No parameter changes.
Each original equity prefix is reproduced from its full published cache within1e-12; only then are fees and halfspreads doubled and the simulator actually rerun. Terminal closing costs come from final holdings using Simulator._trade. Returns are not scaled after the fact.

| Model | Original-cost mean | Doubled-cost mean | Doubled P10 | Doubled worst |
|---|---:|---:|---:|---:|
| book_short_trend |−0.20%|−0.49%|−3.89%|−7.80%|
| book_short_rebound |−0.19%|−0.49%|−3.90%|−8.07%|
| book_short_breakdown |−0.04%|−0.07%|−1.02%|−3.73%|

These160 general-market cases differ from the97 chronological cases and the25 weak checkpoints. All three original-cost means are negative in this broad cohort. No reliable trading edge is established.
No score/registry/leaderboard is published from this incompatible cost scenario.

Artifacts: /home/ubuntu/test/MiniMax/results/book/20261009-short-cost-stress
Read summary.csv and paired_deltas.csv; inspect each paired_windows.MODEL.csv, curves.MODEL.npz and manifest.MODEL.json for exact paths and hashes.
Three money tests pass. All original-prefix equivalence, source/config/wrapper and before/after cache checks passed for each model.

Source helper/params317a600; wrapper identity02b06ff, loaded read-only from Book's short-study worktree.
Run research/book/short_cost_stress/run_all.py in the cost-stress worktree under scripts/lock and nice10 to reproduce all three.
Engine remains hourly weight accounting with static modern spread proxies, approximate minimum-order behavior and unchanged activity guard. This sensitivity is retrospective research, not independent prospective validation.
