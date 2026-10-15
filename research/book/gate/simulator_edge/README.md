# Book simulator-edge research

Start with [the decision report](final_recommendation.md), then [the mechanism inventory](edge_inventory.md) and [the complete comparison CSV](edge_results.csv).

## How to read the ranking

The separate server board is /home/ubuntu/test/MiniMax/results/scoring/leaderboard_simulator_edge.md (with a CSV beside it). Its nine ranks compare the corrected hourly benchmarks over the same 68-hour horizon. The highest rank means the highest historical frequency of recovering the assumed loss; it does not mean a safe model or a verified current top-20 probability.

The scenario starts from a reported round loss of 16%. Reaching round 0% requires a 19.0476% gain from that reduced account; reaching round +2% requires 21.4286%. The p_gate0 and p_gate2 columns measure those exact fixed thresholds. The p19, p215 and p25 columns instead use rounded 19%, 21.5% and 25% thresholds. Check median_return, worst_return, drawdown and p_loss10 alongside the recovery frequency.

The cs_mean column applies the existing risk-score formula (40% Sortino, 30% Sharpe, 30% Calmar). These short paths contain only three daily returns, so CS is a diagnostic, not the official score or a reliable 14-day estimate. Hourly CS uses marked equity; quote-window CS uses net liquidation NAV. The cs_scope column identifies that difference. Compare CS within the same source family. CS does not determine the gate rank.

## How to filter the complete CSV

Filter source_family, split, scenario, hours and regime before comparing rows. Different sources and horizons must not be pooled into one performance sample.

- hourly_proxy: nine corrected hourly benchmarks. The proxy_gate_rank column is calculated only from their 68-hour, all-regime, spent historical check.
- roostoo_quote_proxy: 17 fixed candidates on recorded bid/ask/last, including recent-day cost, delay and fill sensitivities.
- roostoo_quote_windows: averages over four overlapping cash-start paths. Only two 72-hour anchor paths are disjoint.
- legacy_*: earlier settings preserved for audit. Their execution assumptions and metrics differ.

The actual_top20_probability column is deliberately blank: current holdings, the moving cutoff and the funded transition have not been verified. Other missing values mean unavailable, never zero risk. No model is production eligible.

Quote win_rate uses closed net profit after modeled costs. Hourly target traces are not reconciled Roostoo round trips, so their trade win/loss and fill statistics remain unavailable. Quote total_costs contains commissions; spread is already embedded in ask-entry/bid-exit prices. Do not subtract it twice. Window costs and trade counts are per-window means.

Confidence ranges are conditional quarter-cluster diagnostics for 26 candidates, not guarantees for the whole project search or the current market. October 14 is one 24-hour recent check, not a new 72-hour holdout. Never choose a model on one high win rate or one attractive path.

## Updating or extending this study

The existing primary/recovery leaderboards and live bot are unchanged. The existing --score command does not automatically refresh this separate board. Reproduction commands and assumptions are in the decision report. Register a new hypothesis and its fixed parameters before testing; keep its results and failed variants rather than selecting only favorable windows.

All code and results are on metallurgy-server. Raw quotes, arrays and logs remain untracked at /home/ubuntu/test/MiniMax/results/book/20261015-simulator-edge-v1. Derived comparison tables and reports are committed in this Book worktree.
