# Fixed cost-sensitivity diagnostic

This is a separate descriptive identity: short_cost_stress_v1_fixed_160_228h.
It does not publish to either leaderboard or claim compatibility with primary scoring numbers.

Exactly the original three frozen candidate rules and parameters are used:
book_short_trend, book_short_rebound, book_short_breakdown.
Helper and parameters are pinned to317a600; cache identity wrappers to02b06ff.
No outcomes select mechanisms, parameters, dates, horizon or cost assumptions.

Use160 fixed starts every14 calendar days from2020-06-01 12UTC, each228 hours from cash.
All selected windows must have bars and end before the sealed boundary.
The exact cases are common to every model and cost scenario.

Load only complete v2 original scorer caches with independently reconstructed run keys.
Reuse original causal targets; rebuild first decisions using the unchanged model and scorer.
Accept a model only if all baseline hourly equity curves match original cached prefixes within1e-12.
Record source, data, universe, spread and cache hashes before and after replay; fail closed if changed.

Replay both scenarios through unchanged Simulator:
- Original taker/short fees and saved per-coin half-spreads.
- Double taker fees, double short open/close fees, and double saved half-spreads.

Use the same targets, first decisions, band, lag and activity guard.
Each scenario makes its own explicit terminal close from trace w_end via Simulator._trade.
No approximation or final-PnL scaling substitutes for replay.

Report uniform paired-case mean, median, p10, worst, turnover including liquidation,
paid fees/spread per initial equity and paired stress deltas.
The cases cover many regimes; they are a cost check, not the weak-market selection score.
Constant snapshot spreads omit historical liquidity variation, price impact and changing depth.
The original hourly simulator is a fractional-weight research approximation, not an exchange fill certification.
