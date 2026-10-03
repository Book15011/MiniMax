# Research: layers on top of a momentum strategy (book_orch)

This page summarizes one line of research for the README and the finals presentation: what we tried on top of our momentum strategy, how we tested it, and what we found. It describes the tests and their results. **It does not choose the launch model.** That decision waits for the results of a separate batch of models and a combined test.

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

## Sources

| Report | Pre-registration or plan | Content |
|---|---|---|
| [`20261003-orch-phase-a.md`](../../reports/review/20261003-orch-phase-a.md) | [`20261003-prereg-orch.md`](../../reports/review/20261003-prereg-orch.md) (`9f8640d`) | v1: ML gate, tests, parity |
| [`20261003-orch-phase-b.md`](../../reports/review/20261003-orch-phase-b.md) | same | v1: shock, short sleeve, partial moves, ML diagnostics |
| [`20261003-orch-v2.md`](../../reports/review/20261003-orch-v2.md) | [`20261003-prereg-orch-v2.md`](../../reports/review/20261003-prereg-orch-v2.md) (`70ebc8c`) | v2: forecaster gate, R and E, per-coin analysis |
| [`20261003-orch-checks.md`](../../reports/review/20261003-orch-checks.md) | [`20261003-orch-checks-plan.md`](../../reports/review/20261003-orch-checks-plan.md) (`f2ee1d4`) | volatility-controlled ranking, stretched entries, breakdown shorts, behaviour, fees, data |
| [`20261003-final-steps.md`](../../reports/review/20261003-final-steps.md) | [`20261003-prereg-final-steps.md`](../../reports/review/20261003-prereg-final-steps.md) (`b49ecb0`) | macro risk check, hold longer, logging fixes, the batch 4 table |
