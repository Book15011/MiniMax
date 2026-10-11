# Near-high selection: frozen finite study

Book, 2026-10-11 HKT. Research only in feature/book-high-recovery.
Exact baseline book_e20combo_brk_cash at ef1b0dd. Actual EC2 deployment and holdings UNVERIFIED.
All eight earlier recovery variants remain rejected; do not tune them or lower gates.

## Mechanism and source
Fičura (2023), Impact of size and volume on cryptocurrency momentum and reversal, FFA Working Paper 3/2023:
https://quantitative.cz/wp-content/uploads/2023/09/impact_of_size_and_volume_on_cryptocurrency_momentum_and_reversal.pdf
This primary working paper studies weekly momentum and distance from recent highs. It finds different behavior
in large/liquid and small/illiquid coins. It motivates testing, not a guarantee or a next-week forecast.
Our supported universe lacks comparable point-in-time aggregate market capitalization. Its Binance quote-volume
screen is not the paper's size/liquidity definition. Hourly CLOSE maxima proxy intraday highs; this is an adaptation,
not a replication. The available peer-reviewed intraday-predictability abstract motivates caution about reversal,
but no intraday rule is inferred or implemented.

## Exactly two fixed candidates before outcome reads
book_recovery_high: in parent UP mode only, rank long candidates by mean log(current close / maximum close)
over the inclusive last 7 and 14 days (169 and 337 hourly closes). Closer to zero is better.
Every hourly formation close must be finite and positive. Incomplete coins are ineligible.
book_recovery_high_blend: equal 50/50 average of cross-sectional percentile ranks of near-high scores and the
parent's ordinary 7/14-day risk-adjusted momentum; no optimized weight.

Both keep daily16UTC, band3%, top6/keep12, equal weights and the parent's volume/daily20-day breakdown filters.
They may use only the positive gross of the parent decision given the same previous book.
Preserve parent shorts exactly and exclude their symbols from long candidates. No new short rule, pair hedge or leverage.
Match long risk down to the parent with complete30-day covariance; require90% complete rows.
If full signed risk exceeds parent, exact parent fallback.
Down mode, no long budget, unavailable features or no eligible coin: exact parent.
Risk/cash budgets conditional on supplied previous book are not promised to equal the standalone parent's path.

## Evaluation and stopping
Same2298 cash-start14-day windows, execution/cost/guard/liquidation assumptions and six horizons168/192/216/228/240/336h.
Retain every gate in recovery_study/PROTOCOL.md, including full mean/median/p10, mean/worst drawdown,
positive purged-quarter lower difference, recent2024-on and weak/current-horizon conditions.
Conditional task family count increases8 to10, never decreases. No project-wide false-positive guarantee.
Historical passes alone receive2x costs and+1hour lag stress; require passes there too.
All existing history is spent. No coin/date exception, outcome-based window choice, weight search or retuning.
Add both models to the frozen25-case BTC-only diagnostic without reselecting its cases; joint bound includes131models.
Strict original broad query remains FAILED: BCH missing29/30; adaptiveOFF.
The original seven-model future cohort/worktree stays untouched. These two later-developed candidates have no
pre-start forward evidence. Full original competition hard gates and actual-account/endgame switch remain UNVERIFIED.
All failures and hashes saved; no live changes or merges. A finished finite study is not a finished improvement goal.
