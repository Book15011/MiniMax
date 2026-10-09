# Conditional short protocol, frozen before candidate outcomes

Book, 9 October 2026. This preregistration records two hypotheses only. The parent
study's research/book/short_next/PROTOCOL.md governs the frozen score evaluation.
No candidate P&L or candidate score was inspected before fixing these rules.

## Evidence and scope

The immutable 53-model snapshot is
results/book/20261009-short-study-v2/leaderboard_snapshot/leaderboard_2.csv,
SHA256 3a96736253948e262577f3609a0613879e7141a07f0c255b8b8ddb749103001a.
All selection lower bounds are negative. Best rank is baitoey_ovl_brk_dual,
followed by baitoey_vt_dual and book_vt_dual. All three are LONG-ONLY:
their ModelSpec.uses_shorts=False. Their performance cannot establish an
existing short edge. The best model's weak-cohort mean228h return is +2.9436%,
but its selection score is −2.7890%, tail10 mean −11.3453%, and retrospective
down-stress mean −3.2697% across only7cases. Its rebound-stress mean is +6.7262%
across13cases. These ex-post stress labels cannot enter a strategy's inputs.
The top overlay's weak mean differs from dual by only −0.0019 percentagepoints;
its rank advantage alone is weak evidence of economic improvement.

Prior frozen trend/rebound/breakdown additions failed to improve the weak score.
They remain disclosed; no parameter retuning of those candidates is hidden here.
The five observed competition dates are spent diagnostics, not a pristine holdout.

## Primary research and interpretation

- Liu, Tsyvinski and Wu, 2019 working paper / 2022 Journal of Finance:
  [Common Risk Factors in Cryptocurrency](https://www.nber.org/papers/w25882).
  Their historical crypto evidence supports examining market and momentum
  information. Relative long-short factor profits do not prove that shorting
  losers alone has positive absolute return after our costs.
- Daniel and Moskowitz, 2014 working paper / 2016 JFE:
  [Momentum Crashes](https://www.nber.org/papers/w20439).
  Rebounds following declines and elevated volatility are a documented failure
  context for momentum. This motivates a small conditional budget and explicit
  rebound tests; the paper does not validate our4/24h rule.
- Babu et al., 2020:
  [You Can't Always Trend When You Want](https://www.aqr.com/Insights/Research/Journal-Article/You-Cant-Always-Trend-When-You-Want).
  Their multiasset futures study relates trend payoffs to the size of persistent
  moves. It supports avoiding a blanket claim that trend always hedges losses.
  It is not crypto evidence or a ten-day forecast.

Sources were checked on client9Oct2026; papers predate this study. NBER direct
page access returned403; its primary indexed abstracts and primary PDFs supplied
the statements. Numeric thresholds below are ENGINEERING PRIORS, not published
optimal or validated parameters. No current news, options, macro forecast,
or unpublished future data is used in targets.

## Frozen mechanisms

Both candidates preserve the exact f30fa79cde92399a long backbone with published
model.params: baitoey_ovl_brk_dual, own-team sources pinned to
0b2c2630da058eab8abb0c8881cdbcbb1b54a1ff. Original main helper sources for
VT_MOM, volume signals and rotation were verified identical to that commit.
Only positive previous targets reach the long model; past shorts cannot change
the long rank hysteresis. Long target weights are never rescaled to fund shorts. Exact preservation refers
to targets at the same view and positive previous targets; portfolio equity,
fees, weight drift, and the shared order planner can change dollar long trades.

At every scorer call, including its cash-start bootstrap12UTC, compute longs and
shorts together. Ordinary ModelSpec calls are daily16UTC. The shared engine fills
one hour later. This bootstrap exception matches existing baseline semantics.

Open shorts only when BOTH BTCclose<EMA20 AND trailing168hBTCreturn<0, and
liquid breadth is at most40%positive over48h. EMA20 uses480hourly span,
adjust=False, on a fixed1441hour grid endingnow; every BTCvalue must be finite
and positive. No permanence forecast or intrabar stop is implied.

Breadth first selects top30 by trailing168h quote-volume sum among view.universe.
Eligibility requires168finite nonnegative volume bars and a positive sum.
Sort descending sum, then symbol for ties. At least20eligible must be selected.
Only AFTER selection, check every chosen coin's current and exact48h price:
any missing/nonpositive/nonfinite endpoint disables shorts. Never replace a
selected missing-price coin with a lower-liquidity one. Positive fraction uses
return>0; zero counts nonpositive.

This separately declared dynamic model breadth can have20–30coins. It does not
repair or replace the frozen metric's original broad-universe query, which remains
FAILED29/30 because BCH is absent from competition ticker data. Preserve that
failure and protocol603da2948b68ee0f5c8a without changing evidence thresholds.

Short candidates exclude positive long holdings and require all721hourlyprices
for30dayvolatility. Use existing risk-adjusted momentum: mean of7day and14day
return divided by its own return standard deviation scaled to each lookback.
Keep negative scores only; choose bottom3, symbol ties deterministic.

- book_cashshort_confirm: the above confirmation is sufficient.
- book_cashshort_pullback: also require price[t−4h]/price[t−24h]−1>0 AND
  price[t]/price[t−4h]−1<0. This is a closed-bar failed-rebound hypothesis,
  not evidence about an intrabar event ordering.

Initial short weights are inverse30dayhourly volatility, normalized to
min(25%,1−longgross). Clip each coin at10%, without redistributing the clipping.
Then only scale down until sum(abs(shortweight)*hourlysigma*sqrt24)<=1%/day.
This triangle-inequality standalone-short risk bound ignores correlations and
potential long hedging benefits. It is conservative for estimated short risk;
it is not a realized risk guarantee or a total-book volatility cap.
Gross long+short exposure never exceeds100%. No shorts overlap longs.
Loss of gate or coin eligibility produces zero short target at the next daily
call; actual fills remain subject to shared5%band/order planner and1h lag.
Thus a small target may not create an executed short; target and fill diagnostics
must remain distinct.

## Discrimination and honest reporting

Use the unchanged frozen score2 protocol and historical cash-start windows,
216/228/240h horizons, unchanged CS and short episode diagnostics, explicit
liquidation costs, and separate turnover/commission. Compare against exact best
long baseline, next dual baseline, incumbent, and prior failed study.
Chronological and stress contexts are descriptive checks; five competition dates
are retrospective only. Minute replay must use real bid/ask where available,
otherwise explicitly timestamped1m proxies, common mark, and the frozen1h lag.
Observed actual ledger and original clone retain their own frozen timing and
conditional actualfee provenance; never call those an execution-identical test.

Report all two candidates even if inactive or worse. Disclose entry/exit counts,
completed versus censored short cycles, and no hitrate if no completed cycles.
New-model superiority, ten-day bearish forecast, and switch readiness are
UNVERIFIED until evaluation and independent validation. No new live bot changes
or account-switch claims are authorized by this code.

No parameter sweep, threshold relaxation, or candidate replacement after outcomes.
