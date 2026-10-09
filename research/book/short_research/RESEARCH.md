# Research-led short-capable strategy shortlist
Date: 2026-10-09, HKT. Research only; no deployment, live-account change, or main merge.

## Decision
Test three mechanisms in a small frozen experiment, rather than searching hundreds of indicators: (A) signed multi-speed trend with conservative risk sizing, (B) A plus a fast short exit, and (C) confirmed close breakdowns. A is the reference; B tests whether exits repair its rebound weakness; C tests a distinct entry mechanism. The candidate pool is exactly A/B/C: no additional variants or parameter sweep. None has established profitability yet.

The observed five-coin log is useful for its daily schedule, fixed basket and portfolio allocation. It does not identify a unique rule. Cloning and outperforming its observed portfolio are separate questions. Do not select a general model merely because it matches or beats five already inspected dates.

## Implementation declaration (before candidate outcomes)
The exact frozen implementation is specified by research/book/short_study/PROTOCOL.md and commit317a600.
Its volatility cap uses the conservative perfectly-correlated bound sum(|weight| × hourlyvol × sqrt24), rather than estimating a covariance matrix. This avoids optimistic diversification assumptions for a small highly correlated basket.
CandidateC additionally requires current five-major BTC48h weakness and at most40% positive breadth among at least3 valid majors; this is a declared entry condition, not the frozen30-asset query or a coverage repair.
The25% cap is applied to inverse-volatility base weights before multiplying by bounded conviction, preserving cash. ShortC positions already held do not require a new volume surge at every check.
The fixed3pp band is ModelSpec metadata, as in the existing contract; other tunables are in config.yaml.
These details were fixed before results and are not changes made to improve a displayed score.

## Timestamped local evidence
I read main:AGENTS.md through SSH before research. All project inspection and artifact writing stayed on metallurgy-server. The source model files are our own repository code.

1. The archived, source-checked weak reference at Oct 8 00:00 UTC reports BTC 24h -2.60%, 48h -2.85%, 30d +5.32%, 16.10% above its 200-day average, and 2/30 assets positive over 48h. This describes a correction inside a longer uptrend, with material reversal risk. Frozen original fresh-profile coverage is still 29/30; no failure was waived.
2. The 25 matched historical weak starts do not forecast a reliably falling next ten days: their BTC 240h mean is +1.54%, with 40% negative outcomes. They were selected from information known at the starting time, not future direction. A permanent short is therefore a required control, not an established optimum.
3. At internal recorded Oct 9 07:00 UTC (15:00 HKT), BTC/ETH/BNB/SOL/XRP all rose over 6h (+0.90/+0.86/+1.10/+1.23/+0.89%) while their 48h returns remained negative (-2.01/-4.60/-3.34/-6.93/-5.10%). Those latest seven hourly observations are explicitly ticker_only in store_meta.json. They are not independently archive-confirmed hourly closes in this audit, and their independent real-world timestamp calibration is UNVERIFIED. This contemporaneous rebound is a risk observation, not a forecast.
4. Historical hourly close panel: 2018-01-01 01UTC to 2026-09-30 00UTC, 97 columns. The five-coin universe needs an aligned start after all five have real data; never synthesize pre-listing SOL history. The minute coverage manifest inventories publisher availability through Aug 2026; it does not prove that all minute files have been downloaded or source-validated.
5. The shared weak table is being refreshed by another workstream. My extracted read was 44 rows, with baitoey_ovl_brk_dual rank 1. All selection lower bounds remain negative. Existing pol_trend_ls mean -0.76% and downstress mean -3.07%; baitoey_tg_mom downstress mean +0.54%, but rank 41 and lower bound -8.57%. Therefore old trend or a favorable seven-case bearish subset is not enough.

Machine-readable evidence:
- /home/ubuntu/test/MiniMax/results/book/20261009-short-research/local_evidence.json
- /home/ubuntu/test/MiniMax/results/book/20261009-short-research/existing_mechanism_evidence.csv

Prior detailed reports:
- /home/ubuntu/test/MiniMax/.worktrees/book-book-bear-eval/research/book/weak_eval/PROTOCOL.md
- /home/ubuntu/test/MiniMax/.worktrees/book-book-bear-eval/research/book/weak_eval/RESULTS.md

The extracted table hash pins one read; it does not make the live shared table immutable. Freeze a new full snapshot before computing candidate ranks.

## Primary research and what it actually supports
- Moskowitz, Ooi and Pedersen (2012), Time Series Momentum: an instrument's own past return predicts subsequent returns in diversified futures/forwards. Their principal lookbacks and holding periods are months, not seconds. This supports trying interpretable trend rules but does not validate an hourly crypto strategy or our chosen parameters. https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum
- Liu and Tsyvinski (2018 working paper, later published 2021), Risks and Returns of Cryptocurrency: daily and weekly crypto momentum is a more relevant hypothesis than directly importing equity macro predictors. Their sample and market structure predate this competition. Importantly, their low-momentum weekly group can still have positive average return, so momentum sorting alone does not prove that shorting losers is profitable after costs. https://www.nber.org/papers/w24877 and https://www.nber.org/papers/w24877.pdf
- Daniel and Moskowitz (2014 working paper; 2016 JFE), Momentum Crashes: momentum losses cluster after declines, in volatile conditions and alongside market rebounds. This motivates testing a rebound exit separately. It is not evidence that our 24-hour-high exit will work in crypto. https://www.nber.org/papers/w20439
- Moreira and Muir (2016 working paper; 2017 JF), Volatility-Managed Portfolios: reducing exposure after high realized variance can improve several factor portfolios. Their inverse-variance monthly construction differs from our inverse-vol coin allocation and fixed daily risk cap. Treat the idea as risk budgeting, not guaranteed extra return. https://conference.nber.org/confer/2016/LTAMs16/Moreira_Muir.pdf
- Cederburg, O'Doherty, Wang and Yan (2020), On the Performance of Volatility-Managed Portfolios: broad real-time tests do not show systematic superiority and expose structural instability. This motivates fixed risk targets and caution about attributing profits to scaling. The present three-candidate experiment does not add a scaling parameter sweep. https://www.sciencedirect.com/science/article/pii/S0304405X2030132X
- Caporale and Plastun (2020), Momentum Effects in the Cryptocurrency Market after One-day Abnormal Returns: event-conditional hourly behavior is a plausible distinct mechanism. Its historical sample and chosen event/timing rules do not establish a universal current edge. A causal abnormal move or breakdown experiment must include fees, delays, failed signals and rebound cases. https://link.springer.com/article/10.1007/s11408-020-00357-1

Search results and available primary texts were inspected on the client date. Some publisher/NBER opens returned HTTP403; search-index primary-source abstracts remained available. No dated 2026 news, external current-price assertion, options positioning, or macro prediction is used in the numerical proposals.

## Frozen mechanism candidates
All numerical defaults below are engineering priors to test, not fitted recommendations or claims from those papers. Keep parameters in config.yaml. For comparison with the reference log, use BTC/ETH/BNB/SOL/XRP only and a daily scheduled decision at 01UTC (09HKT). A historical engine that rebalances relative to its window start must explicitly implement this phase; 12UTC-start daily rebalances are not the same schedule.

### A. Signed multi-speed trend with risk sizing
Use completed hourly close prices. For each coin, compute 24h, 72h and 168h log returns; normalize each by the hourly return standard deviation over 168h multiplied by sqrt(lookback hours). Average the three normalized signals and clip to [-1,1]. Zero or incomplete volatility/history means no new exposure.

Set raw signed weights proportional to clipped signal divided by hourly volatility. Normalize by the sum of inverse volatilities across all valid five coins (not the sum of absolute active signals), preserving cash when conviction is weak. Cap each coin at 25% absolute weight and gross at 100%. Scale downward, never upward beyond these caps, to a fixed 1.25% daily covariance-based portfolio volatility target. Need a minimum well-defined volatility floor and complete aligned covariance observations; avoid fillna(0) manufacturing low risk.

Daily decision; 3 percentage-point target rebalance band. Use the shared planner/broker's fees, precision, collateral, order sequence and minimum order rules. Allow both directions based on signals; do not force short exposure.

Rationale: close to the observed daily multiasset behavior, fewer degrees of freedom than indicator voting, and risk changes can explain varying size without hand-picked date rules.
Failures: late entries, choppy sign changes, rapid rebound before next daily decision, correlated positions, stale volatility after a jump.
Discrimination: compare with fixed equal-weight long/short controls and the existing 21-day pol_trend_ls. Report cash exposure and realized risk so apparent advantage caused by lower exposure is visible. Do not tune sizing after seeing results.

### B. A with fast short rebound exit
Keep A's entries, parameters and daily schedule fixed. Check at absolute UTC hours 01,07,13,19. Close an existing short if its latest completed hourly close exceeds the highest close of the prior 24h (exclude the current close). Keep it flat until the next strictly later daily01UTC entry decision; no same-check exit/re-entry. If an exit occurs at01UTC, suppress re-entry until01UTC the following day. If at07/13/19UTC, the earliest re-entry is01UTC the following day. Re-entry also requires A's fresh signal to remain negative. Long rules unchanged. These clock/cooldown defaults are engineering choices, not parameters validated by the cited papers.

This is an exit experiment. Do not add a breadth gate to the three-candidate pool: it would confound the B-A contrast and add another trial. Report breadth and BTC trend as descriptive slices only. Missing full breadth remains a failed source-coverage requirement.

Rationale: known momentum rebound vulnerability plus present recorded rebound; simple to falsify using hourly data.
Failures: covers too late after gaps, repeated stop-outs, cash drag when declines resume, apparent risk improvement caused only by lower exposure.
Discrimination: paired B-A after costs over every weak case and positive/rebound control. Report lost downtrend return, avoided rebound losses, turnover and time out of market. Also report exposure and volatility changes, so reduced risk is not mistaken for validated exit timing.

### C. Close breakdown with confirmation
Use completed hourly closes. Check at absolute UTC hours01,07,13,19. Enter a short only after close falls below the prior 72h minimum close (exclude current bar), while that coin's 24h quote volume is at least 1.5 times its prior seven-day average daily volume. Do not count current volume twice in numerator and denominator; specify exact trailing windows. Exit at a close above prior24h maximum close; permit entry on a strictly later scheduled6h check only, requiring the breakdown and volume rules again. At each check, exits have priority over entries for the same coin; no same-check exit/re-entry.

Use A's same sizing and gross caps; no leverage. First compare five-coin universe, then expand only if a separate point-in-time tradable/liquid universe and historical support pass validation. Never use the currently largest coins to select each historical universe.

Rationale: distinct event-entry mechanism; project already has a long-only72h breakout implementation and volume utilities. Mirroring it is an explicit hypothesis, not copying an external codebase.
Failures: high-volume selling climax is the bottom, repeated marginal breaks, late signal after large move, delayed cost-heavy exit.
Discrimination: compare C with A/B and frozen controls; log every potential72h breakdown and its volume ratio so the role of confirmation can be inspected without launching additional strategies. Reject a candidate that has attractive gross win rate but weak net mean, tail or independent support. Do not optimize entry/exit lengths on the five live dates.

Do not label any of these as a validated minute/second scalp. Close-only panels cannot establish true ATR/high-low barriers or intrabar stop ordering.

## Efficient validation order
1. Freeze source files, timestamp conventions, model/config hashes, three-candidate pool and costs before computing results. Confirm the current competition endpoint from authoritative project facts; old reports disagree (AGENTS says Oct17, one evaluator uses Oct18 12UTC), so preserve protocol identity and disclose horizon uncertainty rather than silently moving the goalposts.
2. Test pure signal causality, lag, time phase, short collateral, Decimal truncation, $1 minima and one-time liquidation cost. Use the same planner/broker for the fine comparison. Hourly engine results do not validate minute execution agreement.
3. Screen exactly A/B/C, with frozen existing/control benchmarks, on chronological folds. Reject causality/data/execution failures immediately. Use a common aligned five-coin sample and report every attempted variant. Existing historical data has already been researched, so label further retrospective splits as chronological out-of-fold evaluation, not pristine untouched holdout.
4. Reuse the frozen weak-case score2 profiles, 216/228/240h horizons and all historical risk/stress diagnostics. Start each case from cash, charge taker0.1% eachside and spread, apply onebarlag. A full round-trip costs roughly0.30% with the weak scorer's0.05%halfspread assumption; model-specific observed quotes may differ. A small gross move is not automatically tradeable profit.
5. Primary controls: cash, same-universe equal-weight long, equal-weight short, fixed incumbent revision and strongest eligible existing model from the pinned inventory. Report broad chronological results as well as weak starts. Cluster uncertainty by historical quarter/overlapping replay groups; do not treat thousands of hourly entries as independent. Update simultaneous bounds for the complete disclosed candidate pool rather than adding isolated confidence intervals.
6. In the exact competition prefix from Oct4 12UTC, compare actual reference ledger and all three candidates at common valuation times, equity, collateral and initial cash; include fees/unrealized PnL/terminal liquidation. This is one descriptive path, not proof of general superiority. Do not present gross FIFO realized PnL as portfolio return.
7. Freeze the finalist, run forward paper evaluation on future unseen decisions and retain all failures. A 10-day horizon has very limited fresh support; if no joint positive lower bound vs cash and incumbent plus acceptable risk is established, report no replacement evidence.

## Practical stop rules
- Stop adding indicators when two mechanisms produce materially identical positions: measure position/return correlation first.
- Stop after a candidate fails execution realism, causal history or gross limits; do not rank the broken run.
- Do not relax the existing evidence/coverage thresholds to manufacture a passing candidate.
- If net short outcomes are weak after spread/fees, use cash/risk reduction rather than forcing activity for a bearish narrative.
- Tuning this report's defaults after seeing live-period or score2 returns creates a new spent experiment; preserve it, count it and require forward confirmation.

## Scope and status
This report and its extracted diagnostics are research artifacts only. No strategy was deployed; no signed competition API or secret was accessed; no existing worktree/shared scoring output was edited. Further implementation remains with the parent task in its own isolated worktree.
