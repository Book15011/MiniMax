# Book penalized latency research

Start with [REPORT.md](REPORT.md). The server's separate research board is /home/ubuntu/test/MiniMax/results/scoring/leaderboard_latency.md, with a CSV beside it.

Built prototypes: latency_both25, latency_both50, latency_long25 and latency_short25. These are offline/paper research functions, not registered live strategies. No candidate is approved for deployment.

## Read the outputs

- latency_results.csv: 156 runs. Filter source_family, split and scenario before comparing. Historical external trade bars, received REST books and received stream books are different evidence.
- latency_windows.csv: 40 candidate/horizon/penalty aggregates. There are four overlapping paths and only two disjoint anchors per candidate/horizon. Frequencies are descriptive, not current top20 probabilities.
- Return is the incremental strategy gain after modeled fees and spread. round_return_* includes the assumed existing -16% round return and the named hypothetical penalty. Do not confuse those two returns.
- Penalty formula and trigger are unverified. We assume it triggers on a filled latency trade; zero-trade runs receive no hypothetical penalty.
- A blank win rate or F1 means unavailable. No trades does not mean perfect accuracy or a useful recovery strategy.
- CS in the window CSV is the existing risk formula on three daily returns and net liquidation NAV. It is a short-horizon diagnostic, not the official score.
- actual_fill_verified, capacity_verified and production_eligible are false. actual_top20_probability is unavailable.

The historical screen loses before any penalty. Fresh sampled gaps do not exceed two taker fees; no fresh base-case trade qualifies. This does not rule out every future event, other asset, faster EC2 route or unobserved price between snapshots.

## Reproduce

Work remotely in /home/ubuntu/test/MiniMax/.worktrees/book-latency-gate. Run Python modules research.book.gate.latency.data, run, prospective, verify and publish in that order with python -B -m.

collect and stream are bounded public-only recorders and refuse to overwrite existing captures. Historical inputs are downloaded from the official public archive and verified against checksums. Raw packets/archives/arrays/trades/logs stay untracked in results/book/20261015-latency-gate-v1.

The existing --score command does not update this separate board automatically. Run publish only after its required evidence passes. Do not reuse or extend a short test as though it were a fresh 72-hour holdout. Declare new hypotheses and parameters before new outcomes.

The current live model, holdings, bot processes, old leaderboards and main branch were not changed.
