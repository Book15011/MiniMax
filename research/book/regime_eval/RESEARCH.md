# Current-market evaluator: research and frozen design

Owner: **Book**. Status: **research/review draft; no deployment recommendation**.
Written: 2026-10-08 14:29 UTC. Market observations frozen at or before 13:00 UTC.
Evaluator checkpoint: October 8 12:00 UTC, 96h after configured round start.
Round end used: October 18 12:00 UTC; older AGENTS dates differ.
Branch: feature/book-regime-eval. Official leaderboard and live configuration remain unchanged.

The protocol below is frozen before examining its new candidate-evaluation results. Tunables belong
in this worktree's config.yaml. Historical observations have already been available to the team;
chronological validation here is retrospective, not a pristine holdout.

## 1. Direction through the remaining round

**Research judgment: DOWN, with limited confidence, for the broad competition altcoin universe.**
BTC has downside pressure but a stronger longer trend than the altcoin basket. This is a qualitative
evidence-weighted lean, not a calibrated probability or a prediction of uninterrupted decline.
A rebound is plausible. Ten-day direction does not establish a profitable minute/second short.

The read-only team market audit at October 8 13:00 UTC records BTC around $82,252, down 4.60%/48h.
All trailing-liquidity top-30 coins were negative/48h; median change was about -8.01%. Broad weakness
and relative altcoin deterioration support DOWN more directly than an assumption that a peak has
been reached. These are market/paper-store observations, not verified competition-account fills.

### Verified macro context supporting downside pressure

- September 16 FOMC unanimously increased the target range to 3.75%-4.00%.
  Source: https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm
- Minutes became public October 7 18:00 UTC. Most participants expected another increase by year-end;
  several considered policy nonrestrictive or only mildly restrictive. Their economic descriptions
  reflect September information. Historical feature availability begins at publication, not meeting.
  Sources: https://www.federalreserve.gov/newsevents/pressreleases/monetary20261007a.htm
  and https://www.federalreserve.gov/monetarypolicy/fomcminutes20260916.htm
- Latest published Treasury close audited, October 7: 2Y nominal 4.77%, 10Y nominal 5.28%, 10Y real
  2.92%. October 1 values: 4.78%, 5.24%, 2.88%. High real yields are a headwind, but only +4bp in
  the long nominal/real rates and a flat front end do not prove an accelerating rate shock.
  Sources:
  https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=2026&field_tdr_date_value_month=202610
  https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_real_yield_curve&field_tdr_date_value=2026&field_tdr_date_value_month=202610
- October 7 NY Fed household survey: one-year inflation expectations 3.6% to 3.9%, three-year 3.2%
  to 3.3%, five-year unchanged at 3.0%. These are household expectations, not realized inflation.
  Source: https://www.newyorkfed.org/newsevents/news/research/2026/20261007

### Contrary evidence

BTC was still +4.85%/30d. The earlier audit measured it about 14.9% above its 200d moving average.
Monthly drawdown was about 5.64%; annual drawdown about 33.69%. This is not equivalent to an
established long-term bear market or proof of an absolute annual peak.

The first refreshed original-CORE list was not bearish: 14/25 forward ten-day BTC outcomes positive,
median +1.08%, mean +0.73%. K=15 median +1.86%; K=40 median -0.21%. Only four matches overlapped the
older September-state list; 22 overlapped the October 7 refresh. These already-inspected descriptive
frequencies do not validate a forecast or establish physical probabilities. Original CORE omits
24h/48h/7d returns and recent breadth, motivating the new predeclared test rather than assuming it
will deliver a preferred answer.

September 30 BEA revised August PCE to 3.4% headline/3.0% core year-over-year. Williams September 29
and Jefferson October 1 described time to assess more data. Waller's October 8 speech, scheduled
08:30 UTC, said hikes need not occur at consecutive meetings. He cited October 7 futures pricing:
85% chance of at least one hike by December, nearly 20% of two. Those are December rate expectations,
not verified current October odds or physical crypto direction probabilities.
Sources:
https://www.bea.gov/news/2026/personal-income-and-outlays-august-2026
https://www.newyorkfed.org/newsevents/speeches/2026/wil260929
https://www.federalreserve.gov/newsevents/speech/jefferson20261001a.htm
https://www.federalreserve.gov/newsevents/speech/waller20261008a.htm
https://www.federalreserve.gov/newsevents/2026-october.htm

The DOWN judgment rests principally on recent breadth and altcoin relative weakness, with macro
context. Recovered breadth, improving altcoin-relative performance, or reversal of the short trend
would weaken it. Evaluator results must be reported unchanged if they contradict this narrative.

## 2. Reliable signal candidates

Retain a minimal causally reconstructable price/volume state. Each group has equal influence;
correlated features within a group do not count as independent confirmations.

| Group | Features at checkpoint |
|---|---|
| FAST | BTC log returns 24h, 48h, 7d |
| TREND | BTC 30d log return; distance from the 200-day MA; distance from the trailing 30-day high |
| BREADTH | Top-30 eligible share positive over 48h; median altcoin 48h log return minus BTC 48h log return |
| VOL | BTC 7-day realized volatility; 7-day/30-day volatility ratio |

Historical top 30 uses StateEngine eligibility and trailing quote-volume ranking at that timestamp,
not today's coin list. Rename series stay unstitched. Listing-survivorship limitations remain.
Bars must close at or before the checkpoint; units, sampling frequency, and annualization must
match between historical and current states. Critical missing features cannot silently define a
new protocol. Export coverage, staleness, missing values, input hashes, and source provenance.

**Macro numeric features excluded initially:** existing code uses pinned modern FRED snapshots and
an assumed CPI release day. A snapshot pinned today is not an original vintage. Numerical matching
would require true availability timestamps/vintages and demonstrated incremental forecast skill.
Verified event context is reported separately without a matching weight.

**Options, funding, OI, order flow excluded from main matching:** require adequate historical
coverage, observed timestamps, and incremental validation. A current option chain cannot be backfilled
as historical information. Implied uncertainty is not a calibrated real-world direction probability.
DVOL minute history is limited and futures archives contain gaps.

Current archive-confirmed hourly history in this audit is complete through October 8 00:00 UTC;
01:00-13:00 includes ticker-assisted observations. The 12:00 query must disclose that provenance.
New backfills may revise the feature state. All table artifacts must identify the frozen input.

## 3. Verified event context

| Release | UTC timestamp |
|---|---|
| CPI | October 14 12:30 |
| Beige Book | October 14 18:00 |
| PPI | October 15 12:30 |
| Import/export prices | October 16 12:30 |
| Industrial production | October 16 13:15 |

Sources: https://www.bls.gov/schedule/2026/10_sched.htm
and https://www.federalreserve.gov/newsevents/2026-october.htm

Next FOMC decision October 28 is outside the round. Event proximity indicates timing risk, not the
sign of unreleased news. No current October CME FedWatch probability was verified: the live embedded
tool was inaccessible. No invented consensus surprises or future release data enter this evaluator.

## 4. Existing causal validation and failures

Reusable code: src/validation/features.py, selection.py, guard.py, walkforward.py, crps.py.
These provide historical features, prior-pool percentile transforms, feature-only selection,
separated episodes, outcome-access guards, chronological pools, and forecast scores.

reports/live_like_v1.md found useful skill for volatility/dispersion/rebound forecasts. Its direction
test failed: Brier skill SCREEN -0.065 and CONFIRM -0.005. No direction reweighting was applied.
Predicting volatility does not establish return-direction skill.

results/book/20261003-book-orch-v2/ml/gate.json: confident FALL signals still had mean future 8h return
+0.165%, directional hit 49.17%, and failed the short gate; shuffled controls also failed.

Old live-like weighting forecasts an environment and weights historical outcomes by its density.
The new direct feature matcher is a different estimator; its validation must be reported separately.

## 5. Frozen window alignment and matcher

Historical score windows start t0 and last 336h. Observe state D = t0 + 96h, forecast following 240h.
For any query D, training windows satisfy t0_train + 336h <= D - 24h: full-outcome maturity plus a 24h embargo.

Fit percentile transforms only on the completed prior pool. Compute equal-group percentile distance.
Select K = 25 nearest starts, minimum 14d separation, maximum 3 starts in any 90d span.
The selector reads features only; join historical outcomes only after query weights are frozen.

Candidate mixture:
w=(1-alpha)*uniform_prior_all + alpha*equal_weight_LOOK = 25;
alpha in {0,0.25,0.5}. No additional recency parameter.

Export selected dates, distances, feature differences, weights, weight concentration, and episode
concentration. Numerous overlapping windows and different coins in the same crash are not independent
observations. A low feature distance alone does not validate a forecast.

## 6. Forecast reliability protocol and fallback

Query every 28d. Recompute each prior pool and transform causally.

- SCREEN: July 2022-June 2024. CONFIRM: July 2024-July 25, 2026.
- Forecast outcomes: BTC remaining 240h return, maximum drawdown, realized volatility.
- Select alpha once on SCREEN using average CRPS skill across outcomes relative to alpha = 0.
  Exact outcome definitions, normalization, and ties belong in config.yaml.
- Require CONFIRM improvement with paired 90% interval lower bound > 0; directional Brier must not
  deteriorate. Predeclared coverage and stability checks must pass.
- Use common resampling draws across alternatives and chronological episode/block uncertainty.
  28-day query spacing reduces overlapping outcome windows, but regimes remain dependent.
- Inspect modest K/group perturbations, removal of highly weighted episodes, coverage and concentration.
  Diagnostics cannot be chosen because they favor a strategy.
- If adaptation fails, alpha = 0 is the explicit fallback. A directional story cannot override failure.

Use standard empirical CRPS for the forecast distribution. Any finite-ensemble fairness correction
must disclose its assumptions; overlapping outcomes are not independent draws. Evaluate Brier and
calibration over chronological queries, not a single attractive current frequency.

All historical periods are already observed by the team. CONFIRM here is a chronological audit,
not a restored unseen holdout. Genuine prospective evidence starts after this protocol freeze.

## 7. Cached strategy table and limits

Read cached artifacts for 38 registered models. Separate first 96h performance and subsequent 240h;
apply the same validated/fallback weights across candidates. Show return distributions, downside
tails, activity, original eligibility, uncertainty, and original-score context.

**Each model continues from its own historical state at hour96.**
This is not a shared-incumbent holdings simulation; it cannot rank production switches or quantify
transition benefit. No model is credited with avoiding losses already suffered in the live account.
The official leaderboard is unchanged.

Actual competition equity, holdings, fills, pending orders, active days, deployed commit, and short
capability are UNVERIFIED in this task. Paper/cached observations must be labeled. A future
account-aware switch study requires verified shared state, costs, and whole-round activity.

## 8. Separate fast-short/rebound-cover diagnostic

The fast-short objective is separate from the main score. A correct ten-day directional forecast
does not establish correct executable entry or safe rebound exit. This work audits prior evidence
and specifies measurements; it does not create/deploy a seconds-level strategy.

Prior report:
.worktrees/book-book-scalp/reports/review/20261008-scalp-realism-and-shorts.md
Prior artifacts: results/book/shorts/short_overlay.csv and short_events.csv.

The fixed 72-variant overlay study used rapid BTC decline/breakdown triggers, optional DVOL or spot
taker-flow confirmation, 30%/60% allocation, rebound covers, and 12h stop. No variant was positive
in all three pre-round periods; all 72 lost in April-August2026. Median differences versus holding
e20v45 were -2.8 pp / -10.4 pp / -10.9 pp, versus 0 pp live median and about +1.7 pp live best. Live winners
were poor in preceding months. A 24-signal post-drop coin study lost on average in every prior period.
Faster cash exits commonly sold after the initial plunge and paid to re-enter a rebound.

A future separate table must report:

- Trigger precision/recall, false alarms, missed independent drop events, and episode count.
- Decision time, observed quote time, earliest executable entry, and delay.
- Net PnL after short open/close costs, spread, slippage, and transition costs.
- Favorable/adverse excursion after executable entry, remaining drop caught, rebound profit surrendered.
- Cover delay, rebound-stop/time-stop losses, exposure duration, and independent episode uncertainty.
- Rising/sideways/declining-period results; no-short and slow-short baselines; rate-matched triggers.
- Rejections, partial fills, stale quotes, and adverse execution assumptions.

No entry at a future-identified low. Rebound logic uses only lows observed since entry. A quote
cannot be observed before arrival. The server rules record 1.5-6s Roostoo latency: any seconds edge
must survive it. Hourly history cannot validate seconds timing; minute OHLC cannot order intraminute
stop and target hits. Explicitly stress both entry delay and rebound-cover delay.

Main rules remain: directional strategies; gross <= 100%;20 calls/min/process and 30/account including
queries; no automatic order resends; competition keys only in the running EC2 bot. The separate
tick-scalping amendment is not merged into main and does not automatically authorize HFT or prove a
fast-short implementation permitted. This evaluator makes no signed calls/orders/production changes.

## 9. Completed validation and team review

Completed during the one-time October 9 02:00 Asia/Shanghai continuation. This remains the frozen October 8 12:00 UTC evaluator checkpoint; the earlier 13:00 market observations above are contextual research and are not feature inputs at 12:00.

**Decision: keep alpha = 0, UNIFORM_BASELINE_FALLBACK. No adaptive model-selection score or production ranking is enabled.** The directional research lean remains DOWN for the broad altcoin universe, with limited confidence. The evaluator does not establish a calibrated ten-day direction probability or an executable short edge.

Full findings, all 38 model rows and the early e20 paper comparison are in RESULTS.md. Raw evidence is in /home/ubuntu/test/MiniMax/results/book/20261008-regime-eval/.

### Forecast reliability

SCREEN selected alpha = 0.5 using average rank-space CRPS across BTC return, drawdown and volatility. There were 21 usable SCREEN and 27 CONFIRM queries, spaced 28 days apart. Six early SCREEN queries were skipped because the fixed separation/concentration rules could not supply 25 cases. Their dates and reasons remain in validation.json. The rules were not relaxed.

Paired confirmation uncertainty uses a moving circular bootstrap with four-query blocks, 2,000 draws, seed 20261008 and 90% intervals.

| Confirmation quantity | Mean | 90% interval | Decision |
|---|---:|---:|---|
| Baseline CRPS minus adaptive CRPS, averaged over three rank-space outcomes | +0.009634 | [+0.002177, +0.016824] | Average distribution score improved |
| Adaptive Brier minus baseline Brier | -0.002326 | [-0.015777, +0.010862] | Direction nondegradation guard failed |

The Brier point estimate is slightly better, but its upper bound permits degradation. This is insufficient evidence for the required guard; it does not prove that direction got worse. The average CRPS improvement is driven by drawdown and especially volatility. Return CRPS alone was 0.147263 for the baseline and 0.147724 for alpha = 0.5 on CONFIRM, a small worsening.

Current breadth has only 29/30 exact endpoints. BCHUSDT is absent from the configured competition's 65 ticker pairs; its price at the 12:00 query is missing. Both breadth features remain null under the unchanged 98% guard. Archived data are confirmed only through October 8 00:00 UTC, so the query also fails the archive-confirmation gate. Adaptive K sensitivity is unevaluable with the missing query features; stability_pass = false is not a measured instability result. No tradable-universe rewrite, imputation or threshold relaxation was used.

### Cached model and early-period evidence

All 38 registered models passed score hashes, common data/window signature, exact cache row alignment and original terminal-accounting reproduction. Of 2,298 registered windows, five starts (April 11-15, 2021 at 12:00 UTC) lack adequate BTC forward endpoint/hour coverage and are excluded uniformly, leaving 2,293. Their records are in coverage_exclusions.csv.

The legacy CORE list contains 25 cases. e20's current paper prefix is -8.0646%, compared with a case median of -0.3109%, p10 of -7.0745% and p90 of +9.9466%. Only one case was worse (empirical percentile 4%); five were within two percentage points (20%). Its paper path lies inside the pointwise 10th-90th percentile case band for 62.9% of hourly observations. These are descriptive resemblance measures, not p-values, calibrated probabilities, or proof of the actual account's loss.

Baseline mean own-state remainder is +2.6256% for e20, with p10 -10.3550%. H1/book_orch is +2.1332%, with p10 -9.4580%. rmax_tl has a mean only 0.0246 percentage points above e20; its family-adjusted lower delta is -1.3135 percentage points. No candidate replacement has a positive pointwise or family-adjusted lower bound versus e20. No replacement selection follows from this historical diagnostic table.

### Separate short table

short_timing_table.csv is present with status NOT_VALIDATED, zero validated independent episodes and null performance metrics. No executable short-event ledger was invented. Prior 72-variant failures, timestamp/exit-lag concerns, limited seconds data, account uncertainty and the HFT rule remain documented above. This table contributes no weight to the main score.

### Verification and review status

Tests cover fee arithmetic, gross drift, prefix continuation, weighted quantiles and CRPS, causal feature clipping, feature allowlisting, prior-only pool maturity/embargo, group weighting, coverage guards, drawdown, bootstrap inputs, activation fallback and frozen registry selection. Exact commands, results and code hashes accompany the output artifacts.

Source and frozen snapshot hashes are in input_manifest.json. Model selection is pinned in registered_snapshot.json; cache_inputs.json fingerprints arrays, windows and metadata. Changed registered score or cache inputs are rejected. Detailed code identity is saved separately from the unverifiable live-account identity.

Research summaries are committed only on Book's feature branch. Raw data, large caches and test logs stay uncommitted. No main merge, signed competition API call, order, live deployment or strategy setting change occurred. Reviewer observations remain pending; a passing test suite is not team approval or trading-edge validation.
