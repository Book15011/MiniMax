# Book conditional short round — frozen before outcomes

Two candidates only: book_cashshort_confirm and book_cashshort_pullback. Preserve the empirically reproduced baitoey_ovl_brk_dual long backbone (published cache f30fa79cde92399a), passing positive previous targets only. No incumbent long is reduced to fund a short. Daily16UTC decisions plus the scorer's fresh12UTC cash-start bootstrap; shorts evaluated at the same calls.

Open shorts only when BTC below hourly EMA480 (60-day warmup), BTC168h return negative and48h breadth no more than40%. Rank up to30 eligible universe coins by trailing168h volume, require at least20 and complete endpoints for every selected coin. Bottom3 negative7/14-day risk-adjusted momentum, excluding longs; short gross min(25%, cash), inverse30-day hourly volatility,10% coin cap and conservative perfectly-correlated daily short-volatility bound1%. Pullback variant additionally requires return from24h ago to4h ago positive and last4h negative. Exact engineering definitions are in the candidate config/source; no outcome-driven tuning in this pool.

Primary publication uses the unchanged frozen --score2 protocol603da2948b68ee0f5c8a/tool3036a0d8bfdaa6a0. Both candidates must appear in leaderboard_2.md, including failures. Do not change old board, protocol, lookalike filters, ranking, coverage gates or holdout. Preserve BCH absence and29/30 fresh query coverage.

Additional diagnostics: same97 prior nonoverlap228h starts, paired against strongest baseline as well as cash/e20; actual re-execution at doubled fee/spread on the same160 prior starts; fixed competition prefix Oct4 12UTC to Oct9 01:15UTC. Those are descriptive spent-data comparisons, not independent model selection. Never call a profitable prefix a reliable advantage.

Competition signals use the frozen completed shadow hourly store through Oct9 00UTC, excluding ticker-only hourly rows. Eligible universe follows existing causal daily rule and public tradable list; each model starts cash. Execute same planner/PaperBroker after1h, using as-of recorded bid/ask (<=30s) or checksummed minute archive proxies (<=120s,1bp halfspread). All use0.1% fees/side and terminal full-close cost. Archive proxies and hourly store provenance limitations are stated. No activity guard in this fine replay: primary score2 remains the full harness. Observed literal ledger retains original capital/fee caveats. Match date and seed exactly when reporting comparison.

Before publication: source identity graph must include explicit wrapper, BASE and helpers; targeted causal/risk tests and existing full suite; raw input hashes before/after; no project I/O in targets. No deployment or main merge.

## Research rationale

[Boyd et al., Multi-Period Trading via Convex Optimization](https://stanford.edu/~boyd/papers/cvx_portfolio.html) supports separating forecast, risk limits and costs. Its optimizer does not supply an alpha forecast. This motivates testing a small short sleeve without replacing verified long allocations, rather than treating exposure itself as edge.

[Kitron and Wengrowicz,2026 preprint](https://arxiv.org/abs/2608.21888) reports statistically detectable15-minute reversal but roughly1.3bp gross edge against5bp round-trip benchmark costs. It is an unreviewed external-market study, not evidence for our rules. Our assumed20bp fee round trip is larger still: direction accuracy alone cannot establish profitable micro trading. We therefore freeze slower conditional entries and require net-cost evidence.

[Daniel and Moskowitz, Momentum Crashes](https://www.nber.org/papers/w20439) finds momentum losses cluster around rebounds after weak, volatile markets. Its broad-asset evidence is a reason to test rebound failure and downside tails, not a crypto10-day forecast or proof of our filter.

[Liu and Tsyvinski, Risks and Returns of Cryptocurrency](https://www.nber.org/papers/w24877) reports historical crypto time-series momentum. [Liu, Tsyvinski and Wu, Common Risk Factors in Cryptocurrency](https://www.nber.org/papers/w25882) studies market, size and momentum factors. These justify a directed momentum hypothesis; their samples and portfolio construction do not validate this competition universe or the exact7/14-day setting. Net-cost paired evidence here remains decisive.
