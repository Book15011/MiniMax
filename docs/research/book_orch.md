# Research: layers on top of a momentum strategy (book_orch)

This page summarizes one line of research for the README and the finals presentation: what we tried on top of our momentum strategy, how we tested it, and what we found. [Section 8](#8-conclusion) gives the conclusion of this line of research: **no layer was added to vt_mom**. Which model trades in the live round is a team decision outside this page.

Every number below comes from the reports linked in [Sources](#sources).

## 1. The goal

**What the competition rewards.** The competition first keeps the top 20 teams by return over the round, and only then ranks them by risk-adjusted measures (Sortino, Sharpe, Calmar). So our main score asks one question: **how often does a strategy's 14-day return clear the cut needed to reach the top 20?**

**HEADLINE_RET** answers it. It is the share of past 14-day windows in which the strategy clears three bars, averaged over the bars:
- **Lenient:** −1.5% in falling markets (last edition's measured #20 cut), 0% in rising ones.
- **Middle:** 0%.
- **Strict:** the median return of six simple benchmark strategies over the same window, and at least 0%.

**How the windows are built.**
- 2,298 windows, one starting at 12:00 UTC every day from June 2020 to September 2026.
- Each starts from $100,000 in cash.
- Each pays 0.10% fees plus the spread and trades one hour after each decision.
- Windows whose market resembles the coming round, and recent ones, weigh more.

A window is **UP** if BTC ended it at or above where it started, and **DOWN** otherwise. HIT UP and HIT DOWN are the same score on each group.

**The starting point** is `baitoey_vt_mom` ("vt_mom"), a daily momentum rotation:
- it holds the 6 strongest coins by 7- and 14-day risk-adjusted momentum, and keeps a coin while it ranks in the top 12;
- it caps the book's estimated volatility at 3% a day;
- it skips a coin for a day after a high-volume breakdown.

It scores **HEADLINE_RET 0.609**. The question for book_orch was whether extra layers (forecasts, risk rules, shorts, different timing) could make it clear the cut more often.

## 2. How we tested

- **Rules first.** Each round was pre-registered before any code was written or any result seen: what to build, how to score it, and the exact rule a change must pass to be kept.
- **One change at a time, against the same base.** Every layer is switchable. With every layer off, book_orch reproduces vt_mom (HEADLINE_RET 0.6086 vs 0.6087).
- **Keep rules.** A layer must at least:
  - beat the base on HEADLINE_RET overall **and** in two separate periods: SCREEN (July 2022 to June 2024) and CONFIRM (July 2024 to July 2026);
  - not hurt the worst window by more than 2 percentage points;
  - not trade much more.
  Each round lists further conditions.
- **Forecasts out of sample only.** The models were retrained on a fixed schedule using only data available at the time. Each was checked against a **shuffled-label control**: a model trained on scrambled answers, which should show no skill.
- **Nothing on the scratch path counts until it passes.** Runs that fail are recorded, not registered.

## 3. Every version tested

| Round | Pre-registration | What was added on top of vt_mom | Outcome | Report |
|---|---|---|---|---|
| **v1** | `9f8640d` | **T:** a daily ML forecast (1 and 3 days ahead) tilting weights<br>**S:** a shock rule (halve longs after a BTC crash), with **S-cash** (go to cash) report-only<br>**X:** a short sleeve in weak markets<br>**P** (report-only): partial moves toward the target | ML gate **failed** (shuffled control showed skill), so T was not scored<br>S and X **failed** the keep rule<br>Nothing kept | [Phase A](../../reports/review/20261003-orch-phase-a.md), [Phase B](../../reports/review/20261003-orch-phase-b.md) |
| **v2** | `70ebc8c` | A per-coin forecaster for the next 2, 4 and 8 hours (gradient-boosted classifier, retrained weekly), and four layers:<br>**R:** equal-risk sizing<br>**E:** staged entries (half now, half later)<br>**F:** forecast-led longs<br>**FS:** forecast-led shorts<br>A′ is the base at a smaller trading band (0.015) | Forecaster **failed** its skill gate, so F and FS were not scored<br>R and E **failed** the keep rule<br>Nothing kept | [v2 report](../../reports/review/20261003-orch-v2.md) |
| **Checks** | `f2ee1d4` (plan) | Read-only checks:<br>does the forecast rank pay once volatility is controlled?<br>do stretched entries do worse?<br>does shorting a confirmed breakdown pay?<br>does the strategy trade as written?<br>fees<br>data | Both decision rules said no: the ML line stops, and no short rule | [Checks](../../reports/review/20261003-orch-checks.md) |
| **Final steps** | `b49ecb0` | A macro risk brake (VIX, S&P 500, dollar, BTC funding)<br>"Hold longer": keep a coin while in the top 15 (or 18) instead of 12 | Both decision rules said no; nothing registered | [Final steps](../../reports/review/20261003-final-steps.md) |
| **v3** | `c0c0730` | **TS:** a per-coin trailing stop (exit below the 7-day high minus 3 daily volatilities; 48-hour cool-down), with **TS-k2** (2 volatilities) report-only<br>**BH:** a 20% BTC short with spare cash when BTC is in a down-trend and few coins are trending up<br>Also a read-only check of how much the score depends on recent windows | TS, BH and TS+BH all **failed** the keep rule<br>Nothing registered | [v3](../../reports/review/20261004-orch-v3.md) |
| **E decision** | `04ce882` | **E5:** v2's staged entries at the real band (0.05), compared with vt_mom and the live model in five score views<br>Quick-exit breakdown shorts (read-only)<br>Shadow mode: paper bots logging every decision | E5 is tied in four views but **behind in rising (UP) windows**, so it is not a tied alternative and vt_mom stands<br>Quick-exit shorts lose<br>Nothing registered | [E decision](../../reports/review/20261004-e-decision.md) |

## 4. Results

All runs use the same scoring tool (version `3036a0d8bfdaa6a0`) and the same 2,298 windows.
- **HIT UP / DOWN:** how often the bars are cleared in rising and in falling markets.
- **Worst R:** the worst 14-day return.
- **Turnover:** the average amount traded per window, as a multiple of equity.

| Version | HEADLINE_RET | SCREEN | CONFIRM | HIT UP / DOWN | Worst R | Turnover | Kept? |
|---|---|---|---|---|---|---|---|
| **vt_mom** (registered) | **0.609** | 0.447 | 0.584 | 0.805 / 0.376 | −30.8% | 3.59 | reference |
| v1 A: all layers off | 0.609 | 0.447 | 0.584 | 0.804 / 0.376 | −30.8% | 3.60 | equals vt_mom |
| v1 S: shock rule, halve longs | 0.608 | 0.438 | 0.590 | 0.800 / 0.380 | −28.9% | 3.70 | no |
| v1 S-cash: shock rule, go to cash | 0.607 | 0.431 | 0.592 | 0.790 / 0.390 | −26.8% | 3.82 | report-only |
| v1 P: partial moves | 0.615 | 0.425 | 0.589 | 0.785 / 0.413 | −27.4% | 3.01 | report-only |
| v1 X: short sleeve | 0.597 | 0.433 | 0.570 | 0.784 / 0.375 | −27.9% | 4.45 | no |
| v2 A′: base at band 0.015 | 0.603 | 0.446 | 0.579 | 0.803 / 0.365 | −31.2% | 3.61 | reference for v2 |
| v2 R: equal-risk sizing | 0.563 | 0.452 | 0.544 | 0.730 / 0.364 | −29.0% | 3.54 | no |
| v2 E: staged entries | 0.583 | 0.458 | 0.590 | 0.779 / 0.349 | −31.2% | 3.46 | no |
| Hold longer, top 15 | 0.540 | 0.471 | 0.551 | 0.742 / 0.299 | −30.9% | 3.05 | no |
| Hold longer, top 18 | 0.552 | 0.476 | 0.544 | 0.747 / 0.320 | −29.6% | 2.74 | report-only |
| v3 TS: trailing stop | 0.537 | 0.417 | 0.499 | 0.774 / 0.255 | −25.3% | 4.49 | no |
| v3 TS-k2: tighter stop | 0.520 | 0.402 | 0.503 | 0.695 / 0.312 | −20.6% | 5.36 | report-only |
| v3 BH: BTC hedge | 0.601 | 0.429 | 0.580 | 0.785 / 0.382 | −30.8% | 4.40 | no |
| v3 TS+BH | 0.521 | 0.397 | 0.479 | 0.748 / 0.251 | −23.8% | 5.62 | no |
| E5: staged entries at band 0.05 | 0.583 | 0.453 | 0.597 | 0.774 / 0.357 | −29.7% | 3.38 | no (behind in UP windows) |

**Not scored, because their gate failed:** v1's ML tilt (T), and v2's forecast longs and shorts (F, FS).

**The two report-only near misses.**
- **v1 P** had the highest overall score (0.615), but it was lower in SCREEN and gave up 2 points in strong rebounds.
- **v2 E** was ahead in both periods, but lost overall because of the most recent windows, and it was statistically tied.

## 5. What did not work, and why

**Forecasts mostly found volatile coins, not rising ones (the volatility confound in the labels).**
- **The labels.** v2's classes were "rise", "flat" and "fall" beyond a fixed threshold (the round-trip cost), the same for calm and volatile coins.
- **What the model learned.** It ranked coins better than chance: rank correlation +0.047 with the next 8 hours, t 14.9. But its extreme calls in *either* direction picked the volatile coins. The top and bottom fifths by forecast earned the same (spread −0.002%, t −0.1).
- **Volatility controlled.** Once coins were compared only with coins of similar volatility, the top half by forecast earned slightly *less* than the bottom half: 0 of 3 volatility groups and 0 of 4 years were positive.
- **v1 showed the same.** Almost all of v1's apparent skill was market timing: a control that shuffled answers within each day kept 0.050 of the 0.052.

**The probabilities were overconfident.**
- When the model gave a 60–70% chance of a fall, a fall followed only 49.6% of the time.
- Its "confident fall" calls were followed by an average *gain* of +0.17% over 8 hours.
- Its "confident rise" calls gained +0.46%, just short of the +0.47% needed to cover costs.
- The shorter-memory half of the model (180 days) was worse than simply predicting the average at 4 and 8 hours.

**Shorting breakdowns buys the bounce.**
- v1's short sleeve won only 46% of its short-days after costs. It cost 3 points in rebound windows.
- In the checks, every way of shorting a confirmed breakdown lost money at 8, 24 and 72 hours (−0.45% to −0.67% net at 24 hours).
- One in ten such shorts saw the price bounce at least +8% within a day, and about +15% within three days.

**Risk-based sizing gave up upside.**
- Weighting coins by inverse volatility (v2 R) moved money from the strong, volatile winners to calm coins.
- It improved the worst window by 2.2 points but cut HIT UP by 7 points.
- The shock rule (v1 S) did the same on a smaller scale: worst window +1.9 points, HEADLINE_RET −0.001.

**Stretched entries did best.**
- Coins bought when already far above their recent average did better, not worse. Entries with a daily RSI above 80 returned +9.3% over the next 7 days (t 2.3), against +0.5% for entries below 70.
- They also had deeper worst drops (−14% vs −9%), and the yearly signs were mixed.
- A filter against overextended entries would have caught the single worst case (one coin bought at RSI 99 that fell 80%), but it would have given up that average.

**Stepping aside in macro stress did not help.**
- A stress score built from VIX, the S&P 500, the dollar and BTC funding did not predict worse windows (rank correlation with return −0.02).
- The most stressed fifth of windows cleared the bars *more* often (0.746 vs 0.580).
- Halving exposure in them would have lowered HEADLINE_RET (0.609 to 0.600, approximate).

**Holding longer cut trading but cleared the bar less often.**
- Keeping coins while in the top 15 cut turnover by 15% and quick round trips by a third.
- But HEADLINE_RET fell from 0.609 to 0.540, in both rising and falling markets (HIT UP 0.805 to 0.742, HIT DOWN 0.376 to 0.299).

**Trailing stops sold before bounces.**
- A stop 3 daily volatilities below a coin's 7-day high (v3 TS) improved the worst window from −30.8% to −25.3%.
- But the coins it sold rose on average afterwards: +0.75% the next day and +0.99% over 3 days. Over 7 days it was a
  coin flip.
- It cleared the bar much less often in falling markets (HIT DOWN 0.376 to 0.255), and HEADLINE_RET fell from
  0.609 to 0.537.

**A BTC-only hedge cost about its trading costs.**
- Shorting 20% of BTC while BTC trended down and few coins trended up (v3 BH) switched on and off quickly, with a
  median episode of 4 hours.
- Only 31% of the episodes made money after costs.
- It moved HIT DOWN by +0.006 and HEADLINE_RET by −0.008, and gave back 2 points in rebound windows.

**Much of the score weight sits on recent windows.**
- The 52 most recent windows carry 22% of the weight, and 2026 carries 48%.
- vt_mom ranks first under the current weights, but its margin over the next-best variants comes mostly from 2026.
- Without the most recent windows, one variant (v2 E) is narrowly ahead of it.
- With each year weighted equally, three variants are statistically tied with it.

**Trading more often did not help either.**
- A smaller trading band (v2 A′, 0.015 instead of 0.05) made 20 times more trades between daily decisions (8,553 vs 415), for the same turnover.
- It scored 0.006 lower.

## 6. Per-coin findings

**Where the profit came from** (v2 A′, profit split by each coin's typical volatility):
- **Low volatility: 54.5%.** These are coins such as ETH, BNB, BTC, DOGE and XRP.
- Mid volatility: 25.2%.
- High volatility: 20.3%.

**Largest contributors:**

| Coin | Share of profit |
|---|---|
| FET | 10.6% |
| SOL | 9.9% |
| ETH | 9.7% |
| DOGE | 9.1% |
| BNB | 8.5% |

Fewer than half of the positions made money: 44.6% to 46.1% by volatility group.

**Single-coin losses.** In 87 of 1,056 losing windows, one coin caused more than 40% of the loss. FET was the most frequent such coin (6 windows).

**Forecast skill per coin.**
- 46 of 55 coins had a positive rank correlation, but no coin's own timing was predictable.
- "Rise" calls covered costs only on SHIB, PEPE and SUI.
- "Fall" calls were followed by gains on most coins.

**Worst entries.** Of the 10 entries with the worst 7-day drop:
- one was overextended (TUT, August 2026, −80%);
- the rest were bought in the crash weeks of May 2021 and May 2022, several of them already oversold.

PUMP's worst entry lost 18.8% at its lowest point.

## 7. How the strategy behaves when it trades (checks)

- **It trades as written.** In six windows replayed hour by hour, every trade matched a logged decision except two exits of coins that dropped out of the eligible universe. Those trades were correct, but the log had no reason for them. That gap and a misleading log message are now fixed ([final steps](../../reports/review/20261003-final-steps.md), section 3).
- **Fees** are about 0.36% of starting equity per 14-day window.
  - About two thirds come from the daily decisions and exits.
  - The daily activity guard makes many small trades (about 77 per window, median $237), but they are only 7% of fees.
- **About 1.6 positions per window are opened and closed within 24 hours.** Almost all of these are the strategy dropping a coin at the next daily decision.

## 8. Conclusion

### No layer was added
Every layer was tested against vt_mom alone, under rules fixed in advance. None earned its place:

| Layer | Round | Why it was not added |
|---|---|---|
| Daily ML tilt (T) | v1 | The forecast failed its gate. Most of its apparent skill was market timing, not coin picking |
| Shock rule: halve or cash after a BTC crash (S, S-cash) | v1 | A slightly better worst window, but a slightly lower score |
| Short sleeve in weak markets (X) | v1 | Its shorts won less than half the time and gave back rebounds |
| Partial moves (P) | v1 | The highest overall score, but lower in one period and in rebounds |
| Equal-risk sizing (R) | v2 | Moved money from strong winners to calm coins: less upside |
| Hourly forecaster, forecast longs and shorts (F, FS) | v2 | Failed its gate: its confident calls mostly picked volatile coins, and its probabilities were overconfident |
| Staged entries (E at band 0.015; E5 at band 0.05) | v2, E decision | Closest of all, but behind in rising windows (below) |
| Shorting breakdowns, slow or quick exit | checks, E decision | They lose: the coins bounce |
| A filter against stretched entries | checks | Stretched entries did best on average |
| A macro risk brake | final steps | Stress did not predict worse windows |
| Holding longer (top 15 or 18) | final steps | Less trading, but a lower score |
| Per-coin trailing stop (TS) | v3 | Sold before bounces |
| BTC-only hedge (BH) | v3 | Cost about its trading costs |

### How much the score depends on recent windows
- The score weights each past window by how much it resembles the coming market, and recent windows weigh more.
- So **48% of the weight sits on 2026 windows**, and 22% on the 52 most recent ones. The weight spreads over about
  **44 effectively independent fortnights**, not the 165 non-overlapping ones in the data.
- vt_mom ranks first under the current weights. But its margin over the closest variants comes mostly from 2026. With
  each year weighted equally, it is statistically tied with three of them.

### vt_mom vs E5
E5 was tested as a possible tied alternative: same returns statistically, a different risk profile. The rule required
E5 to be tied or ahead in all five views.

| View | vt_mom | E5 (vs vt_mom, 90% interval) | Live model, pol_switch_vt_tl_e20v45 (vs vt_mom) |
|---|---|---|---|
| (a) as now | **0.609** | 0.583: tied [−0.053, +0.006] | 0.568: behind |
| (b) without the most recent windows | 0.556 | **0.564**: tied [−0.000, +0.016] | 0.501: behind |
| (c) each year 2021–2026 weighted equally | **0.510** | 0.504: tied [−0.018, +0.008] | 0.461: behind |
| (d) rising (UP) windows only | **0.805** | 0.774: **behind** [−0.056, −0.001] | 0.699: behind |
| (e) falling (DOWN) windows only | 0.376 | 0.357: tied [−0.056, +0.017] | **0.412**: tied |

**E5 is behind in rising windows, so it is not a tied alternative, and vt_mom stands.**

E5's profile is still worth knowing:
- it does better in falling markets (+0.37 points per falling window) and worse in rising ones (−0.48);
- its worst fortnight is slightly better (−29.7% vs −30.8%), with slightly smaller drawdowns and lower fees.

### What remains outside this research
- **Limit-order (maker) execution.** Paying the 0.05% maker fee instead of the 0.10% taker fee would save at most
  about 0.17% of starting equity per window. That figure is an upper bound and UNVERIFIED: it assumes every order fills
  as a maker. It cannot be tested until the test wallet is funded.
- **Shadow mode.** Two paper bots (vt_mom, and E5) log every hourly decision with its reasons. A check that the backtest
  reproduces their decisions waits until the research data covers those hours. Their paper results are never used to
  decide anything.

## Sources

| Report | Pre-registration or plan | Content |
|---|---|---|
| [`20261003-orch-phase-a.md`](../../reports/review/20261003-orch-phase-a.md) | [`20261003-prereg-orch.md`](../../reports/review/20261003-prereg-orch.md) (`9f8640d`) | v1: ML gate, tests, parity |
| [`20261003-orch-phase-b.md`](../../reports/review/20261003-orch-phase-b.md) | same | v1: shock, short sleeve, partial moves, ML diagnostics |
| [`20261003-orch-v2.md`](../../reports/review/20261003-orch-v2.md) | [`20261003-prereg-orch-v2.md`](../../reports/review/20261003-prereg-orch-v2.md) (`70ebc8c`) | v2: forecaster gate, R and E, per-coin analysis |
| [`20261003-orch-checks.md`](../../reports/review/20261003-orch-checks.md) | [`20261003-orch-checks-plan.md`](../../reports/review/20261003-orch-checks-plan.md) (`f2ee1d4`) | volatility-controlled ranking, stretched entries, breakdown shorts, behaviour, fees, data |
| [`20261003-final-steps.md`](../../reports/review/20261003-final-steps.md) | [`20261003-prereg-final-steps.md`](../../reports/review/20261003-prereg-final-steps.md) (`b49ecb0`) | macro risk check, hold longer, logging fixes, the batch 4 table |
| [`20261004-orch-v3.md`](../../reports/review/20261004-orch-v3.md) | [`20261003-prereg-orch-v3.md`](../../reports/review/20261003-prereg-orch-v3.md) (`c0c0730`) | score robustness, trailing stop, BTC hedge, per-coin stops |
| [`20261004-e-decision.md`](../../reports/review/20261004-e-decision.md) | [`20261004-prereg-e-decision.md`](../../reports/review/20261004-prereg-e-decision.md) (`04ce882`) | E5 decision table, E5 vs vt_mom analysis, quick-exit shorts, shadow mode |
