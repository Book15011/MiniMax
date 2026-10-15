# Frozen directional comparison — Book

The user clarified that USD2,000 is a possible later live-test budget, contingent on strong simulation results. It is not a USD2,000 profit target or a requirement to win a single one-hour path. Primary horizon stays50hours from the earlier request. No live allocation, account change or signed request is authorized by merely finishing this file.

Choice: use the strongest registered directional backbone as benchmark B, and test a small, researched predictive family A. A claim that B is almost certain to profit is UNVERIFIED; the main leaderboard measures14days. A profitable average does not imply near-certain positive short-horizon outcomes. Logged targets/order timing do not uniquely identify a hidden predictive strategy.

B: exact latest registered book_orch run033c466d54a7766f at bd30554e9c94; current-committed model pol_switch_vt_tl_e20v45 run0ec3cf0ca1185b36 is a reference, actual current EC2 deployment remains unverified. Start with cached original-engine cash-start50h evidence; keep that historical-price proxy separate from new actual-quote execution simulations. Never give B a maker-fee discount without changing its fill path. A smaller fee bill alone is not trading alpha.

A fixed families, before inspecting new outcomes:
1. Ridge prediction using past returns/volatility and signed aggressive trade flow.
2. Price-only ridge ablation, to see whether flow adds value.
3. Flat-price/one-sided-flow rule: directional pressure while price has not yet chased, symmetric long/short.
4. Apply ordinary market execution and a passive-entry long variant. Shorts retain the documented10bps each side, including limit shorts; no invented short maker discount.
Coins BTC/ETH/SOL/BNB/XRP are fixed liquid references, not chosen by later profit. Parameters live in config.yaml. Train on August2026only; ten-minute labels must finish before September1. Purge labels crossing boundaries. No parameter tuning on October check returns.

Research basis:
- Queue imbalance can predict the next mid-price movement in some equity books, not guaranteed net crypto profits: https://arxiv.org/abs/1512.03492
- Order flow imbalance is associated with short-interval price moves and available depth: https://arxiv.org/abs/1011.6402
- Roostoo reports actual Role, Status, fills and commissions; LIMIT alone does not prove MAKER: https://github.com/roostoo/Roostoo-API-Documents
Our minute aggressive-trade flow is NOT full order-book imbalance. Treat this transfer to crypto/10-minute returns as a hypothesis.

Recorded October6–14 Roostoo quotes supply bid/ask execution and terminal liquidation; original receipts are second-resolution and about6seconds apart. No interpolation or subsecond fills. Use next observed quotes after the configured delay, and explicit maker expiry, queue/fill sensitivity, taker charges when a limit crosses on arrival and all losing open inventory. Quote-only maker eligibility does not verify queue position or real fill capacity. Minute features must be closed and old enough when used. Terminal and short collateral arithmetic need independent tests first.

Chronological October10–14 is a spent-history diagnostic, not an untouched holdout: the project has already inspected these market paths. August fitting does not change that label. Show recent single-day and disjoint50h paths separately; overlapping windows are not independent. Save every fixed candidate and failed scenario, trade counts, actual net return denominator, drawdown and all fees.

Promotion requires positive after-cost results and paired evidence against B, stress survival, reconciled trades, gross≤equity and no reliance on fictional queue fills. Insufficient sample or missing B coverage cannot produce a passing comparison. There is no model winner merely because it beats zero in one selected period. Preserve all earlier negative latency results and numeric leaderboards.
