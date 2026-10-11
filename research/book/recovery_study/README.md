# Recovery study on the current brk-cash strategy

**Recommendation: none. No tested change passed the frozen improvement rule. Live bot unchanged.**

Baseline: book_e20combo_brk_cash from ef1b0dd. Study source 49c39e3131ec.
Tests: 252 passed. Independent raw-array audit: PASS, all return/drawdown reconstruction errors zero.

## How to read the table

All rows use the same 2,298 cash-start 14-day windows, one-hour lag, fees, spreads and endpoint liquidation.
Mean is an unweighted average. It differs from Pol’s weighted HEADLINE_RET and is not that score.
Bad 10% uses NumPy linear quantiles in this study; the old weak leaderboard uses an empirical quantile.
CS is the floored daily-HKT 0.4 Sortino + 0.3 Sharpe + 0.3 Calmar convention; larger is better.
Drawdowns are losses; lower magnitudes are better. An improvement on one column is not an overall pass.

| Model | Mean return | Median | Bad 10% | Worst | Mean drawdown | CS | Pass |
|---|---:|---:|---:|---:|---:|---:|---|
| book_e20combo_brk_cash | +3.732% | +0.283% | -11.522% | -26.049% | 10.770% | 0.15230 | baseline |
| book_recovery_vol | +3.196% | +0.288% | -10.863% | -25.113% | 9.770% | 0.16413 | NO |
| book_recovery_short | +3.731% | +0.283% | -11.522% | -26.049% | 10.770% | 0.15229 | NO |
| book_recovery_both | +3.196% | +0.288% | -10.863% | -25.113% | 9.770% | 0.16412 | NO |

## Interpretation and limits

The volatility control reduces losses and drawdown but also cuts average return, especially in recent data.
Short confirmation barely changes returns and has no demonstrated positive edge. Combining them does not fix this.
No parameter was retuned after these outcomes. No rejected candidate goes live or is called a winning strategy.

The old weak profiles are frozen on Oct9. Their 25+25 cases overlap; they are not 50 independent samples.
168/192h results address the current 7/8-day horizon; 216/228/240h are retained only as old-board diagnostics.
All historical periods are spent. The quarter bound controls only three new comparisons, not project-wide selection.
The live runner’s endgame lock-in is absent here, so these are model-core diagnostics, not full account-switch validation.
The actual EC2 account and deployment are UNVERIFIED. Server holdings are paper. No signed API was called.

## Research basis

[Moreira & Muir](https://www.nber.org/papers/w22208) motivates testing less exposure during elevated volatility.
[Daniel & Moskowitz](https://www.aqr.com/insights/research/journal-article/momentum-crashes) motivates testing rebound risk in momentum shorts.
These papers describe other markets and horizons. Neither supplies an accurate crypto forecast or validates our rules.

Evidence: /home/ubuntu/test/MiniMax/results/book/20261011-recovery-study-v1/comparison.base.csv, decision.base.json, independent_audit.json, full_tests.log.
