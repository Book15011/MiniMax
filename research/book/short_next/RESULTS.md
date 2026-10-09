# Book: short-strategy and reconstruction results

The 85% cloning target has **not been met**. The best frozen clone matches **19 of 33 trades (57.58%) under literal +/-2 minutes and quantity +/-5%**. The original inclusive minute-interval rule gives 21/33 (63.64%). Both figures are retained.

Three new short-capable models are tested and published through ordinary --score2. The four-hour model reduced losses during the observed competition prefix, but still lost money and trailed the observed portfolio. These experiments have not established a verified replacement for the live account.

## Where to look

- Current board: /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md
- Short labels: /home/ubuntu/test/MiniMax/results/scoring/short_leaderboard_2.csv
- Immutable board snapshot and this report: /home/ubuntu/test/MiniMax/results/book/20261010-short-next-final/
- Evaluation source and protocols: /home/ubuntu/test/MiniMax/.worktrees/book-book-short-next/research/book/short_next/
- Model source: /home/ubuntu/test/MiniMax/.worktrees/book-book-short-next/src/models/book/
- Clone report: /home/ubuntu/test/MiniMax/.worktrees/book-book-clone-reconcile/research/book/clone_execution_fit/RESULTS.md

All project work was remote. No main merge, live-bot change, signed competition API call or local repository copy was performed.

## Primary weak-market selection

The protocol remains 603da2948b68ee0f5c8a, at the frozen October 9 00UTC checkpoint. Its dated documented endpoint is October 18 12UTC: the main horizon is 228 hours, with 216/240-hour sensitivity. AGENTS lists October 17; that conflict and unsuccessful fresh unsigned verification remain documented. This is not a refreshed October 10 macro forecast.

Each cohort has 25 historical weak-market starts. Eligibility uses trailing BTC 48-hour return between -10% and 0%, BTC 24-hour log return <=1%, and positive 48-hour breadth <=40%, all known at entry. Starts are at least 14 days apart, with at most three in any 90-day span.

The archive-full profile is October 8. The fresh profile deliberately uses BTC-only features at October 9. The failed fresh broad-market query remains **29/30** because BCH is absent from competition ticker data.

| Model | Rank | Mean weak 228h | Fresh BTC mean | Conservative selection score | CS | Mean MDD | Stronger evidence |
|---|---:|---:|---:|---:|---:|---:|---|
| baitoey_ovl_brk_dual | 1 | +2.944% | +2.396% | -2.909% | 0.234 | 7.752% | NO |
| book_cashshort_pullback | 3 | +2.760% | +2.193% | -3.098% | 0.225 | 7.795% | NO |
| book_cashshort_confirm | 4 | +2.574% | +2.256% | -3.269% | 0.220 | 7.845% | NO |
| book_transition_short | 11 | +1.316% | +0.932% | -4.978% | 0.122 | 7.606% | NO |

Read **Stronger evidence** separately from rank and original gates. The rank is useful for selecting experiments; it does not prove that switching improves a live account. Cash starts omit existing holdings, pending orders and earlier losses.

The selection score is the smallest simultaneous lower return bound across two profiles, three horizons and two comparators, cash and fixed e20. The existing quarter-block bootstrap, 20,000 draws and correction for tried models are unchanged. It is an evidence bound, not expected profit.

CS is 0.4 Sortino + 0.3 Sharpe + 0.3 Calmar, using unchanged FLOORED.V1 and daily HKT buckets. CS UTC changes the day clock. No separate CSL metric is implemented.

On the same 160 cost-test paths, the transition model's mean return differed from the strongest long model by -0.513 percentage points at ordinary costs and -0.818 points at doubled costs. These paired descriptive comparisons are separate from the primary ranking.

## What the new models do

**book_cashshort_confirm** preserves the exact strongest daily long target chain, then uses spare cash for at most three shorts. It requires BTC below its 20-day EMA, negative seven-day BTC return and weak complete breadth. It selects negative seven-/14-day risk-adjusted momentum outside held longs.

**book_cashshort_pullback** adds a preceding rebound followed by negative four-hour return before a new short. This tests whether avoiding an extended decline helps entry timing. The results do not establish that the filter works.

**book_transition_short** is one separate frozen four-hour hypothesis. When BTC's 48-hour return is <=-2%, drawdown from its 96-hour high is >=3%, and positive 48-hour breadth is <=40%, it halves long targets and permits capped shorts. It uses negative 48-hour risk-adjusted momentum and negative four-hour entry confirmation. Previously negative target weights can survive a small rebound, but clear on a four-hour rebound >=2%, nonnegative 48-hour return, loss of rank or cleared regime. Four-hour calls intentionally change the long-selection cadence. Retention uses previous intended targets, as required by MarketView; a small target may not have executed because of band, quantity precision or cash. Actual fills must therefore be read from the replay ledger.

Every sleeve has total shorts <=25%, each short <=10%, and an additional 1% daily short-volatility bound. Liquidity selection requires complete 168-hour volume, top 30 with at least 20 coins, and every selected breadth endpoint. Tunable parameters live in config.yaml.

No threshold was lowered to obtain a trade. The daily variants reproduced the strongest model's positive target chain with maximum error zero across 2,311 decisions. The four-hour model intentionally changes that chain.

## Separate short-trigger table

An onset is a new short episode, not an addition. Correct 1/3/6-hour labels mean a fixed-horizon **unit short proxy** is positive after its declared costs. This is not actual quantity-weighted account PnL or seconds-level execution accuracy. Window-mean proxy gives each firing window equal weight.

| Model/profile | Onsets | Windows firing | Correct1h / valid | Correct6h / valid | 6h precision90% range | Window-mean6h unit proxy |
|---|---:|---:|---:|---:|---:|---:|
| book_cashshort_confirm/weak_archived | 62 | 12/25 | 15/62 | 19/62 | 8.6% to 46.5% | -1.210% |
| book_cashshort_confirm/weak_fresh_btc | 93 | 15/25 | 34/93 | 38/93 | 30.1% to 51.4% | -0.150% |
| book_cashshort_pullback/weak_archived | 38 | 8/25 | 9/38 | 11/38 | 16.7% to 45.0% | -0.316% |
| book_cashshort_pullback/weak_fresh_btc | 68 | 11/25 | 13/68 | 29/68 | 28.6% to 57.1% | -0.858% |
| book_short_breakdown/weak_archived | 29 | 12/25 | 11/29 | 16/29 | 34.3% to 75.0% | +0.504% |
| book_short_breakdown/weak_fresh_btc | 32 | 10/25 | 11/32 | 12/27 | 25.0% to 64.0% | +0.998% |
| book_transition_short/weak_archived | 264 | 16/25 | 65/264 | 95/262 | 28.8% to 43.8% | -0.354% |
| book_transition_short/weak_fresh_btc | 294 | 19/25 | 99/294 | 115/289 | 31.1% to 46.3% | -0.554% |

Inspect valid denominators, unresolved labels, terminal censorship and the 90% interval. Several signals in one market episode do not constitute independent evidence. Sampled hourly profit/stop barriers can be ambiguous inside the hour; reweighted episodes complicate cover proxies. These labels do not enter the main ranking.

The unit proxy uses 0.10% per-side fees and the existing 0.05% halfspread per side. The fine replay below uses recorded bid/ask where available and its separately declared archive proxy. Do not conflate the two.

## Observed competition-prefix comparison

Fixed start: October 4 20HKT (12UTC). Fixed end: October 9 09:15HKT (01:15UTC). Each short candidate starts with $100k cash and uses the shared planner and PaperBroker, one-hour decision lag, ten-second order spacing, pair precision and 0.10% fees. The separately fitted frozen reconstruction retains five-minute batching; its execution schedule differs.

Daily models refresh at 16UTC. The transition model acts every four hours with the same daily universe refresh. This fine diagnostic omits the activity guard; primary score2 retains it.

| Model | Full-cost return | MDD | Orders | Short-opening orders | Completed / censored short cycles | Profitable completed cycles |
|---|---:|---:|---:|---:|---:|---:|
| baitoey_ovl_brk_dual | -8.4767% | 12.4889% | 12 | 0 | 0/0 | unknown |
| book_cashshort_confirm | -8.4248% | 11.8076% | 17 | 4 | 1/3 | 100.0% |
| book_cashshort_pullback | -8.4758% | 12.4871% | 13 | 1 | 0/1 | unknown |
| observed_literal_ledger | +5.1794% | 2.8667% | 33 | 10 | 0/5 | unknown |
| book_transition_short | -6.4612% | 8.8778% | 43 | 10 | 6/3 | 33.3% |
| frozen_calibrated_reconstruction | +4.8133% | 2.8423% | 32 | 10 | 0/5 | unknown |

Full-cost return marks positions at closing bid/ask and charges terminal fees once. Independent checks reconstruct equity paths, fill prices, positions and short-cycle PnL.

The observed ledger retains literal quantities and prices, the confirmed T001 fee of $19.98, and assumed 0.10% fees elsewhere. Its opening $11.34 cash deficit is preserved without resizing. It is a conditional reference, rather than an executable $100k cash-start strategy.

A short-opening order can add to an existing episode. Completed-cycle hit rates exclude censored positions still open at the endpoint. Six completed cycles are too few to infer stable accuracy. The transition model's completed short PnL was +$313.47 while total portfolio return was negative. The confirmation model's one completed cycle earned +$192.38; that is not a reliable 100% success estimate.

## Data repair and verification

The first prefix used a shadow panel with complete 168-hour volume for only 14 of 29 universe coins. Its no-short result was coverage-limited; it did not prove that price filters never passed.

A minimal gap-only repair was rejected because existing shadow closes and volumes conflicted with archived bars. The failure remains in results/book/20261010-short-next-prefix-v2/. No tolerance was relaxed to accept that mixture.

The accepted third dataset consistently replaces all recent values using publisher-checksummed hourly archives for 89 eligible symbols, September 30 through October 8: 801 archives and 216 hours per symbol. Earlier warmup exactly matches the frozen validated historical panel.

An independent zip-based reconstruction verified 19,224 close cells, 19,224 volume cells, completed-bar UTC timestamps and historical warmup. PAXG stays explicitly ineligible. This repair does not fix the separate 29/30 competition-query failure.

The three-model prefix uses 90 verified minute archives for 18 assets; the transition replay uses 85 for 17. Recorded quotes use causal asof age <=30 seconds. The minute-close proxy allows age <=120 seconds and 1bp halfspread. Identical duplicate full rows collapse; all conflicting timestamp/pair groups are quarantined. No favorable quote is selected from a conflict.

## Chronological diagnostic

The same 97 fixed, nonoverlapping 228-hour paths span eight half-years, 2022H2 through 2026H1. Starts are 14 days apart and paths crossing a fold boundary are excluded. No model is fitted or selected inside a fold. All history has already been seen, so these are descriptive time blocks, not an untouched holdout.

| Model | Mean | Median | P10 | Worst | Mean MDD | Mean CS |
|---|---:|---:|---:|---:|---:|---:|
| baitoey_ovl_brk_dual | +1.351% | -0.279% | -7.417% | -17.245% | 7.303% | 0.143 |
| book_cashshort_confirm | +1.356% | -0.276% | -7.339% | -17.245% | 7.185% | 0.141 |
| book_cashshort_pullback | +1.312% | -0.213% | -7.722% | -17.245% | 7.244% | 0.140 |
| book_transition_short | +0.797% | -1.130% | -8.251% | -16.080% | 6.753% | 0.084 |

Read paired_summary.csv for same-window comparisons against cash, fixed e20, BTC hold, equal-weight long and the pinned strongest long model. These diagnostics do not replace the weak-market ranking.

The older two-model chronological template incorrectly mentions 09HKT decisions. Those models use 16UTC daily. The frozen plans and this report state the actual schedules. Its NOT_RUN cost statement applies only to that cache-only analysis; executable cost stress was run separately below.

## Actual cost sensitivity

The same 160 fixed 228-hour paths start every 14 days from June 1, 2020 at 12UTC. The actual historical simulator doubles both fees and halfspreads. Frozen decisions stay identical between scenarios, while execution costs, liquidation and risk are recomputed. Final returns are not simply multiplied.

| Model/scenario | Mean | Median | P10 | Worst | Mean MDD | Mean CS |
|---|---:|---:|---:|---:|---:|---:|
| baitoey_ovl_brk_dual/original | +1.613% | -0.470% | -7.219% | -18.769% | 7.369% | 0.257 |
| baitoey_ovl_brk_dual/doubled | +1.223% | -0.870% | -7.517% | -19.099% | 7.483% | 0.227 |
| book_cashshort_confirm/original | +1.459% | -0.787% | -7.561% | -18.769% | 7.405% | 0.248 |
| book_cashshort_confirm/doubled | +1.035% | -1.186% | -8.011% | -19.099% | 7.538% | 0.214 |
| book_cashshort_pullback/original | +1.559% | -0.554% | -7.219% | -18.769% | 7.356% | 0.253 |
| book_cashshort_pullback/doubled | +1.142% | -0.869% | -7.523% | -19.099% | 7.482% | 0.220 |
| book_transition_short/original | +1.101% | -0.530% | -8.484% | -16.995% | 7.267% | 0.156 |
| book_transition_short/doubled | +0.406% | -1.185% | -9.377% | -17.367% | 7.586% | 0.108 |

Every original-scenario equity hour must reproduce the published cache within 1e-12. Raw target order is restored from source to preserve previous-target hysteresis. Manifests pin source, parameters, raw data, universe, spreads, caches and publication evidence. These observations remain spent; descriptive gains do not establish a prospective edge.

## Clone reconstruction

The fixed five-asset family uses EMA6/24 trend, one-hour signal lag, EWMA24 log-return risk with two-hour lag, a clipped global forecast and inverse-volatility sizing. Coin, gross and daily-risk limits are shared. This is a plausible approximate mechanism, not verified knowledge of the observed portfolio's rules.

The preceding round retained 216 joint fits and 864 operational replays. The execution-aware follow-up retained 3,180 evaluations, 2,656 unique parameter/band combinations and 12 bounded converged searches. Prediction has no date-/coin-specific fitted coefficients or literal log quantities.

- Historical inclusive minute-interval rule: 21/33 recall, 63.64%; precision 65.63%; F1 64.62%.
- Literal +/-2-minute rule: 19/33 recall, 57.58%; precision 59.38%; F1 58.46%.
- Required 85% recall: at least 29/33 matches. Neither rule passes.
- Historical action/time-only agreement is 31/33. Ten misses have quantity errors and two actions are absent; this does not meet the quantity requirement.
- Early 15/20 and later 6/13 are calibrated descriptive slices.
- Fixed top-12 candidates across three global timing scenarios did not improve literal agreement beyond 19/33.

The historical rule can admit a prediction exactly three minutes after the displayed minute's start. The literal rule excludes it. The original matcher is preserved and the distinction is reported prominently.

Prediction-only and instrumented broker reruns reproduce event SHA256 8b4bcb4a27bc410535fbd7c142f7f2a7365e13ed884161089e41ac0fe360a00f. A read guard blocks observed CSV labels, selected events/targets and evaluation records; the frozen predictor still reproduces the hash. This proves label-read isolation at inference, not generalization after retrospective fitting.

Per-fill minimum cash was $99.40, maximum gross was 99.8988%, and there were no rejections. Of 32 fills, 27 used recorded unsigned quotes and five used archive proxies.

The common-period frozen reconstruction returned **+4.8133%**, with **2.8423% MDD**, versus the observed ledger +5.1794%. It still matched only 19/33 literal trades. An independent signed-cash/positions/equity reconstruction passed; the unchanged prediction hash and zero rejections were verified. The auxiliary minute execution clock after October 9 00UTC is explicitly ticker-assisted (causal recorded last price within 30 seconds); those clock points are not represented as archived bars. Full-minute valuation uses the canonical quotes.

The calibrated reconstruction remains a separate diagnostic. Its five-session fit and batching/reconciliation behavior are not presented as a validated historical score2 model. No claim is made that 85% is impossible for every strategy; this tested family has not achieved it.

## Verification and preserved failures

- Strategy worktree: 521 full-suite tests passed; 30 focused model/backbone tests passed.
- Reconstructed prefix: 319 independent checks passed; transition prefix: 244 checks passed.
- Independent hourly reconstruction: all 801 archives and exact historical warmup passed.
- Clone worktree: 238 tests passed; isolated research suite: seven passed.
- Independent short entry-basis/partial-cover accounting fixture passed.
- Primary-run source/raw hashes match before and after evaluation. Actual cost replay reproduces published caches.

The first short-cash audit incorrectly equated signed cash containing short proceeds with free broker cash excluding collateral/proceeds. Its two failed checks remain saved. The corrected audit independently reconstructs entry basis and the collateral interval implied by truncation, then reconciles free plus locked cash. Independent equity and PnL checks passed throughout.

A combined clone project/research test call failed collection because the observed helpers pin another source worktree. Its log remains saved; both suites passed in isolated interpreters. Trading code was not altered to bypass it.

## Testing another model

After adding a model, configuration and meaningful sizing/causality tests, run from an evaluation-capable Book feature worktree:

    cd /home/ubuntu/test/MiniMax/.worktrees/book-book-short-next
    scripts/lock harness-book-weak-score -- nice -n 10 .venv/bin/python -B -m backtest.run --model YOUR_MODEL --score2

--score2 appends the separate registry and regenerates leaderboard_2.md and both CSV boards. Creating a model file alone does not score it. This command does not change the original --score board or deploy the model. The checkpoint does not automatically advance to today's market.

Read rank and selection score, original gates, return tails, MDD/CS, stronger-evidence flags, short-label denominators and the cost/chronological comparisons. A high short hit rate with negative account returns is insufficient. Parameter changes after results create another tried model.

Source remains on feature/book-short-next and an earlier branch. The repository requires owner review before a main merge.

## Research basis

[Daniel and Moskowitz, Momentum Crashes](https://www.nber.org/papers/w20439) motivates testing rebound risk after declines; it does not estimate these crypto thresholds.

[Liu and Tsyvinski](https://www.nber.org/papers/w24877) and [Liu, Tsyvinski and Wu](https://www.nber.org/papers/w25882) support investigating cryptocurrency momentum and common factors, not a guaranteed short edge.

[Boyd et al.](https://stanford.edu/~boyd/papers/cvx_portfolio.html) supports separating forecasts, risk and costs, without supplying alpha.

[Kitron and Wengrowicz, 2026 preprint](https://arxiv.org/abs/2608.21888) reports small short-horizon reversal effects relative to costs. It is unreviewed and does not validate these models. With 20bp round-trip fees before spread, minute/second strategies require strong executable after-cost evidence.

Implemented parameters are frozen engineering priors. Modern tradable-universe filtering creates possible survivorship bias; historical spreads are proxies; observations are dependent; calibration periods have been viewed. These results expose strengths and failures without certifying market direction or future returns.
