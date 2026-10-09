# Allocation mechanism research and strict replay

**Decision: this directed research does not improve the strict execution clone on the later diagnostic dates. The 85% requirement remains unmet.**

Worktree: /home/ubuntu/test/MiniMax/.worktrees/book-book-allocation-mechanisms
Evidence: /home/ubuntu/test/MiniMax/results/book/20261009-allocation-mechanisms
Source dependency: /home/ubuntu/test/MiniMax/.worktrees/book-book-observed-baseline with executable code from commit 3f3524c (current head 088cdbf adds correction documentation only). The existing pure price loader, shared brokerage replay and one-to-one matching are imported read-only from that worktree.


## Research-led hypotheses

This study tests allocation mechanisms that were missing or less explicit in the earlier indicator sweep. It does not search participant code and does not infer an indicator merely from a similar return.

1. **Bounded forecasts and capital limits.** An allocation system can combine forecasts, risk penalties, transaction costs and exposure constraints. The primary [Boyd et al. optimization framework](https://stanford.edu/~boyd/papers/cvx_portfolio.html) formalizes these components but deliberately treats forecasting as a separate input. This supports separating signal inference, sizing and brokerage behavior. It does not identify which inputs produced the supplied orders.

2. **Signal plus risk scaling.** [Moskowitz, Ooi and Pedersen](https://doi.org/10.1016/j.jfineco.2011.11.003) separate directional signals from ex ante volatility scaling. Their study concerns liquid futures over months, so it supplies a mechanism to test rather than evidence that an hourly crypto variant is profitable. [Kim, Tse and Wald](https://www.sciencedirect.com/science/article/abs/pii/S1386418116301379) further show why a control without the signal and a control without risk scaling matter: portfolio results can arise materially from the scaling layer.

3. **Inverse portfolio estimation.** [Yu, Wang and Dong](https://arxiv.org/abs/2010.01687) infer risk preferences using observed portfolios and market data within a specified mean-variance framework. This motivates a fixed-model inverse test. It does not establish that an unknown forecast, unknown covariance model and unknown constraints can all be recovered from five sessions. Algebraically, in unconstrained mean-variance utility, any observed weight vector w can be rationalized by setting the unknown forecast to gamma*Sigma*w. Without restrictions on the forecast this construction has no predictive content.

## What the observed allocations suggest

Daily net exposures are reconstructed from the supplied positions and fees at the recorded prices. They are executed exposures, so capital fitting and other execution rules can make them differ from desired targets.

- All five opening exposures are approximately 20% each. Several tested capped models produce this naturally from the available price history, without a special first-day equal-weight rule.
- BNB and ETH have almost identical absolute dollar exposure on 7 October: their normalized weights differ by only0.000599% relative.
- BTC, ETH, SOL and XRP have almost equal absolute dollar exposure on 8 October, with pairwise relative differences below0.141%.
- These clusters are consistent with a forecast or position cap followed by common capital scaling. They do not prove a particular cap value, indicator, index or implementation.
- Gross net exposure varies substantially: approximately 100%, 42%, 100%, 96%, 91%. A permanently fully invested inverse-volatility portfolio does not explain this.

Pure risk budgeting also fails an easy conditional diagnostic. Even supplying the observed gross exposure and directions, inverse-volatility allocation using the previous 24 hourly returns has 16.07 percentage points mean absolute error in the normalized absolute mix on6 October. On9 October that error falls to 1.23 points. Thus risk scaling may contribute on some dates, but cannot explain the whole sequence by itself. The risk-contribution diagnostic in the CSV uses absolute exposures as a long-only comparison; it is not a claim that mixed signed portfolios must have equal positive risk contributions.

## Fixed directed search

The full grids and assumptions are saved in research/book/allocation_mechanisms/config.yaml.

The fitting dates are 5-7 October, including the first session. Later 8-9 October dates had already been seen in prior work and are retrospective diagnostics. No clean prospective validation is claimed.

Single-stage models:

- Momentum horizons 6, 12, 24, 48, 72, 168 hours, or six fixed EMA pairs.
- Signal delay 0, 1, 2 hours.
- Raw, inverse volatility, inverse variance, or shrinkage covariance-inverse scaling.
- Rolling risk estimates 24, 72, 168 hours; covariance shrinkage 25%, 50%, 90%.
- Common absolute per-coin caps 20%, 25%, 30%, 35%, 40%, 50%, 100%, with gross at most100%.
- One shared scale, selected from 64 fixed factors using fitting-period target error.

Formula: raw_i = k*signal_i/risk_i, then clip each signed exposure to a common cap and proportionally scale only if gross exceeds100%. Covariance variants replace per-coin division with a fixed shrinkage inverse covariance matrix. No asset-specific or date-specific coefficients are fitted.

Two-stage models test a bounded forecast before risk scaling:

forecast_i = clip(EMA_gap_i / forecast_clip,-1,1)
raw_i = k*forecast_i / volatility_i^power
weight_i = clip(raw_i,-position_cap,position_cap), then enforce total gross<=100%.

The forecast clip, power, risk window, cap and common scale are shared across dates and assets.

There are 4032 single-stage target candidates and 900 two-stage target candidates, each considering 64 scale values. From these, 24 mechanisms are shortlisted by fitting-period target error. Each receives 20 execution variants: fixed delay 3-7 minutes and rebalance bands 0, 1, 2, 5 percentage points. All 480 execution trials are retained. These counts matter because repeated fitting increases overfitting risk; the best training fit is not independent evidence.

## Target fitting findings

| Mechanism | Fit mean absolute weight error | Later diagnostic error |
|---|---:|---:|
| Capped raw EMA 5/23, delay2h |1.661pp|2.841pp|
| Capped inverse-volatility EMA 5/23, delay2h |0.806pp|2.791pp|
| Capped inverse-variance EMA 5/23, delay2h |0.683pp|3.001pp|
| Shrunk covariance EMA 6/24, delay0h |1.033pp|4.984pp|

The covariance model obtains the fitting signs for 15/15 coin-date observations, but predicts a positive BNB target on 8 October while the observed portfolio is short. More complexity improves a training diagnostic without improving later explanation.

The inverse-variance model naturally produces equal opening weights, equal capped BNB/ETH weights on 7 October and four equal capped shorts on 8 October. It remains materially wrong on 9 October: predicted BNB exposure about-30.5% versus observed-19.95%.

Two-stage clipping gives a concrete identification problem. Forecast clips 0.0025, 0.005 and0.010 produce identical fitting weights for one EMA 5/23 inverse-variance parameter family. Their later BNB targets on 9 October are approximately -6.10%, -12.20%, -23.34%. Fitting dates cannot choose among these explanations. Choosing the later best would be retrospective tuning.

Target weight similarity is only a screening device. Quantity matching depends on prior holdings, fees, execution prices, collateral release and order sequencing.

## Strict shared-broker replay

Replay begins 4 October 2026 20:00 HKT, uses the same $100,000 seed and cutoff 9 October 09:15 HKT, and uses the project's shared planner and paper broker. Taker fees, quantities, collateral, available USD and recorded bid/ask prices use the existing brokerage implementation. All decision signals use only completed historical prices. The new candidates do not force equal first-day targets.

Matching keeps the agreed same coin/action, within 2 minutes, quantity within 5%. Minute-only timestamps denote a minute interval, as in the existing comparison. Matching is globally one-to-one. Extra predicted trades lower precision; tiny observed covers remain in the denominator.

Selection uses fitting strict F1, then fitting action-only F1, smaller target error and fixed deterministic execution tie breaks. Parameters are written to execution_selection_freeze.json before the later comparison.

| Candidate | Fit matches | Later matches | Full matches | Full precision | Full recall |
|---|---:|---:|---:|---:|---:|
| Original frozen candidate, corrected T001 |11/20|2/13|13/33|54.17%|39.39%|
| New training-selected capped inverse variance |12/20|0/13|12/33|40.00%|36.36%|

The new selected model uses EMA 5/23, a 2h historical delay, inverse variance over 24 hours, common scale 0.0014954600121561, position cap 50%, zero rebalance band and 3-minute fixed operational delay.

Its fitting F1 is 61.54%; full F1 is 38.10%. Later no strict matches occur. The training tie break chooses a 3-minute execution delay; the later observed 8 October batch is around 09:06-09:07 HKT. Operational timing contributes to failure as well as quantity errors. It cannot be repaired with per-date observed execution times in a causal clone.

Across the 24 shortlisted mechanisms with their own fitting-selected execution assumptions, the most full-period strict matches is 13/33. The largest later count is 3/13 for a different two-stage model. Those are descriptive diagnostics; neither qualifies as an 85% clone. This result does not rule out every other possible hidden strategy.

The selected replica returns approximately +4.9997% at the common cutoff after simulated fees. This is not a cloning success criterion and is not historical robustness evidence.

## Reliability checks

Six focused tests passed, covering absolute caps and gross, vectorized scale application, shrinkage positivity and two independent future-data mutation checks. The existing money/order implementation is reused; these research additions do not change the live engine or shared contracts.

ee960143b3e113ea44d03e9cfdf5694c2a1c8b1698eb1173f4c748cc086c5209.

Minimum sampled free USD is $97.37; maximum sampled gross/equity is 99.899%. These sampled states do not establish bounds at every intervening tick. The first session still predates the project's recorded Roostoo seconds and uses the existing labeled minute-price proxy.

The corrected first timestamp improves the original frozen result to 13/33. It does not resolve the unexplained sizing and scheduling differences.

## Efficient next shortlist

1. Capped trend forecast with inverse-volatility or inverse-variance sizing. It explains the observed cap structure and should remain an interpretable exploratory baseline.
2. Two-stage forecast clipping then risk sizing. Keep its indistinguishable fitting parameter set, rather than choosing a later successful-looking clip and claiming identification.
3. A simple independent trend/short control for performance research. Compare it directly with the observed portfolio and cash; it should not inherit an 85% clone label.

Do not spend further cycles first on a high-dimensional covariance optimizer. Its small fitting advantage deteriorates on the later dates. Next evidence should differentiate forecasts and execution behavior, or test a frozen rule on newly observed sessions. The separate short-strategy development must pass the larger historical reliability protocol even if it beats this short supplied prefix.

## Files and reruns

Inspect selected_metrics.json, selected_event_comparison.csv, selected_events.csv and original_frozen_metrics.json first. allocation_trials.csv, twostage_trials.csv and execution_training_trials.csv retain all trials. all_shortlist_retrospective_diagnostics.csv is explicitly retrospective. same_dollar_clusters.csv, risk_budget_diagnostics.csv and mechanism_weights.csv explain the mechanism evidence.

Commands run remotely in the allocation-mechanisms worktree:

```bash
.venv/bin/python -m pytest -q research/book/allocation_mechanisms/test_probe.py
scripts/lock book-allocation-mechanisms -- nice -n 10 .venv/bin/python -B research/book/allocation_mechanisms/probe.py
scripts/lock book-allocation-mechanisms -- nice -n 10 .venv/bin/python -B research/book/allocation_mechanisms/twostage.py
scripts/lock book-allocation-mechanisms -- nice -n 10 .venv/bin/python -B research/book/allocation_mechanisms/execution_probe.py
.venv/bin/python -B research/book/allocation_mechanisms/execution_probe.py --predict-only
```

No main merge, live change, signed competition API call or shared leaderboard write is performed.
