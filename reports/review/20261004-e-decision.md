# E at band 0.05 (E5), the decision table, shadow mode, and the E5 vs vt_mom analysis (2026-10-04, Book)

| | |
|---|---|
| Pre-registration | `reports/review/20261004-prereg-e-decision.md` (`04ce882`): part 1's rule and part 5's rule, committed before anything was computed |
| Shadow-mode code | `bb8b7ee` (`src/orchestrator/shadow.py`, 3 tests) |
| Tool | `3036a0d8bfdaa6a0`. E5 on the scratch path; **nothing registered** (the part 1 rule failed) |
| Scripts and outputs | `results/book/20261004-e-decision/` (not committed): `precheck.py`, `run_e5.py`, `part1.py`, `part4.py`, `part5.py`, their JSON, `cases/<window>.csv` (hour-by-hour logs) |
| Charts | `reports/review/figures/20261004-e5/<window>.svg` (committed) |
| Not done | writes to `data/`, Roostoo calls (apart from the shadow bots' public price reads), registration |

| Part | Result |
|---|---|
| 1. E5 and the decision table | **Rule fails: vt_mom stands.** E5 is tied with vt_mom in four views but **behind in UP windows** (−0.030 [−0.056, −0.001]). The live model is behind vt_mom in four views and tied in DOWN windows |
| 2. Shadow mode | **Running.** `mm-book-shadow-a` (every layer off = vt_mom) and `mm-book-shadow-e5`, paper mode, logging every hour. Pol's guard fix 149d564 was already in this branch. Parity check pending: no shadow hour is in the research panel yet |
| 3. Write-up | `docs/research/book_orch.md`, with a conclusion section added |
| 4. E5 vs vt_mom | Staging pays in falling markets and costs in rising ones: **+0.37 pp per DOWN window, −0.48 pp per UP window**, −0.10 pp overall. Two hybrid rules are proposed, **not tested** |
| 5. Quick-exit breakdown shorts | **Rule fails: not pursued.** The pre-registered set loses 0.21% to 0.30% a trade (t −6 to −15) in every variant and every year 2023–2026 |
| 6. Shadow log export | `mm-book-shadow-export` writes `reports/shadow/<YYYYMMDD>-<bot>.md` at 00:30 UTC. The first one is due 2026-10-05 00:30 UTC |

## 1. E5 at band 0.05, and the decision table

### Check before scoring
E5's targets are identical to v2 E's: targets do not depend on the band, and FS is off. The engine trades a coin only
when the change exceeds the band, so a staged half from an empty position executes only if it is above 0.05.

| | Staged halves | Median half-weight | 10th / 90th percentile | At or below 0.05 |
|---|---|---|---|---|
| 16:00 decisions (v2 E's target history) | 1,499 of 1,774 new entries | 5.9% | 4.0% / 8.3% | **27.6%** |
| Window starts (each window's first decision) | 11,350 of 13,697 | 5.9% | 4.0% / 8.3% | 29.4% |

**After scoring (E5's trade log, all windows):**
- **16:00 decisions:** **26.9%** of staged halves did not execute (5,081 of 18,890). Those coins were bought in full at
  the top-up instead.
- **Window starts:** **none.** The first decision of a window trades every difference exactly, as the live runner does.

### E5's score
HEADLINE_RET **0.5835** (without post-holdout 0.5644). Run key `684de91ab6798af8`; 20 minutes.

### The decision table
- **Ranks** are among the three models.
- **Bootstrap:** paired against vt_mom, 2,000 month-block draws, 90% intervals.

| Model | (a) as now | (b) without post-holdout | (c) 2021–26 equal | (d) UP only | (e) DOWN only |
|---|---|---|---|---|---|
| **vt_mom** | **0.609 (#1)** | 0.556 (#2) | **0.510 (#1)** | **0.805 (#1)** | 0.376 (#2) |
| **E5** | 0.583 (#2): −0.025 [−0.053, +0.006] tied | **0.564 (#1)**: +0.008 [−0.000, +0.016] tied | 0.504 (#2): −0.007 [−0.018, +0.008] tied | 0.774 (#2): −0.030 [−0.056, **−0.001**] **behind** | 0.357 (#3): −0.019 [−0.056, +0.017] tied |
| Live: pol_switch_vt_tl_e20v45 | 0.568 (#3): −0.041 [−0.083, −0.002] behind | 0.501 (#3): −0.056 behind | 0.461 (#3): −0.049 behind | 0.699 (#3): −0.105 behind | **0.412 (#1)**: +0.036 [−0.023, +0.108] tied |

**Rule:** E5 must be tied or ahead in all five views. It is **behind in (d), UP only**, so it is **not** a "statistically
tied alternative", and **vt_mom stands**. The miss is narrow: the interval's upper end is −0.001.

| | E5 | vt_mom | Live model |
|---|---|---|---|
| Worst R | **−29.7%** | −30.8% | −26.1% |
| Median max drawdown | **9.7%** | 10.1% | 9.8% |
| Single-coin blow-up share (one coin > 40% of a loss) | **3.66%** | 3.96% | 7.27% |
| Fees per window (% of E₀) | **0.341%** | 0.362% | 0.531% |
| Turnover per window | 3.38 | 3.59 | 5.31 |
| Coins bought in a window's first hour (mean) | 5.96 | 5.96 | 3.87 |
| Equity put to work in the first hour (mean weight) | **0.42** | 0.72 | 0.61 |

## 2. Shadow mode (Phase C)

**Pol's guard fix 149d564** ("the activity guard also runs after a decision that filled nothing") is **already an
ancestor of this branch**. It arrived with the stacked merges of `feature/volume` and `feature/v2check`, and it is in
`main` too, so there was nothing to merge. `src/live/runner.py` here contains the fix.

**The bots.** Both run the team's paper runner, exactly as the existing paper bots do (`src.live.runner.build`,
unchanged). The differences are only these:
- the state directories are outside `data/`: `results/book/shadow/{a,e5}/`;
- the model object is wrapped so that each hour's `explain()` records are logged (`src/orchestrator/shadow.py`).

They use public prices only (the Roostoo ticker, server time and exchange info, a few calls an hour): no keys, no
orders, paper fills only.

| Session | Model | Lock | State and logs |
|---|---|---|---|
| `mm-book-shadow-a` | book_orch, every layer off (= vt_mom), band 0.05 | `book-shadow-a` | `results/book/shadow/a/` |
| `mm-book-shadow-e5` | book_orch with E on, band 0.05 | `book-shadow-e5` | `results/book/shadow/e5/` |
| `mm-book-shadow-export` | daily summaries at 00:30 UTC | `book-shadow-export` | `reports/shadow/` |

**History check, before starting.**
- **Seed:** 300 days from the research panel, 2025-12-04 to 2026-09-30 00:00 UTC. All 90 series are more than 99%
  filled over the last 61 days, which covers the 60-day trend lookback.
- **At the first hour:** the Binance archive added 8,640 bars, completing the history through 2026-10-04 00:00 UTC, and
  the ticker filled the current hour. The bars from 01:00 to 04:00 UTC on Oct 4 come from neither source; they are
  carried forward, at most 48 hours, as for the team's bots.

**First log lines** (bar 2026-10-04 05:00 UTC, each bot's first hour):

| Bot | Coin | Decision | Reason | Target | Would-be order |
|---|---|---|---|---|---|
| a | AAVE, HBAR, LTC, PUMP, SUI, WLD | enter | base decision | 12.25% each | BUY $12,246 each |
| e5 | AAVE, LTC | enter | base decision (trend score 1, volatility below the median) | 12.25% | BUY $12,246 |
| e5 | HBAR, PUMP, SUI, WLD | stage | new coin: half now, the rest at the next 16:00 UTC decision | 6.12% | BUY $6,123 |

Hour lines: bot a has paper equity 99,917.93 and gross 0.735; bot e5 has 99,945.51 and 0.490. Both are stamped with
commit `bb8b7ee43413`.

**Parity check.** It is pending. `python -m src.orchestrator.shadow parity --bot <a|e5> --state-dir
results/book/shadow/<bot>` replays the logged hours in the backtest's view once the research panel covers them. The
panel ends 2026-09-30 00:00, so today no shadow hour is covered. The panel is refreshed only by the data scripts, and
this task may not write to `data/`. No mismatch can be reported yet.

## 4. E5 vs vt_mom: strengths and weaknesses (descriptive; nothing is tuned on it)

**How the gap is decomposed.** Every window is replayed hour by hour from the trade logs. The gap R(E5) − R(vt_mom)
splits exactly into the components below, and the sum is checked to 1e-9 in every window.
- **Engine:** R(A) − R(vt_mom), where A is book_orch with every layer off at band 0.05. This is the same daily
  decisions, run hourly with drift-band trades and guards to drifted weights, against vt_mom's daily book: the "guard
  and drift trades" part outside E.
- **E5 vs A**, per coin-hour:
  - **entry timing (staged halves):** A holds the coin and E5 holds less than 0.75 of A's weight;
  - **exits:** E5 holds a coin A no longer holds;
  - **drift and guard (E5 vs A):** both hold it, and the weights differ through drift and the band;
  - **equity path:** the two books' different equity;
  - **fees and spread:** E5's costs minus A's.
- **Volatility-cap scaling** is 0 by construction. E5 keeps the base's vol-capped weights and never rescales other
  coins, and the base sees the same held coins in both books.

### 4.1 Case windows

Each window runs 14 days from 12:00 UTC. Hour-by-hour per-coin logs are in
`results/book/20261004-e-decision/cases/<window>.csv` (both models' weights, the coin's return, the gap, and both
models' trades). Charts are linked under each table.

The window that starts **2026-09-16 is not complete**: the panel ends 2026-09-30 00:00, before its end at 12:00. The
most recent complete window starts **2026-09-15**.

**(i) Most recent complete window, 2026-09-15** (BTC +9.6%)
- vt_mom +27.33%, E5 **+28.68%**, A +27.42%.

| Component | pp |
|---|---|
| Entry timing (staged halves) | +0.73 |
| Exits | 0.00 |
| Drift and guard (E5 vs A) | +0.28 |
| Equity path | +0.22 |
| Fees and spread | +0.04 |
| Volatility-cap scaling | 0 |
| Engine (A − vt_mom) | +0.08 |
| **Gap** | **+1.34** |

Moments:
1. 09-15 15:00: UNI −3.6% while E5 held half (+0.64 pp).
2. 09-15 23:00: ARB +4.5% while E5 held half (−0.30 pp).
3. 09-18 15:00: NEAR +3.6% with E5 overweight after drift (+0.31 pp).

![E5 vs vt_mom, most recent window](figures/20261004-e5/i_recent.svg)

**(ii) Most like now: highest live-like weight, 2026-07-23** (BTC −1.4%)
- vt_mom +2.67%, E5 **+3.72%**, A +2.67%.

| Component | pp |
|---|---|
| Entry timing | **+1.04** |
| Drift and guard | −0.03 |
| Equity path | +0.03 |
| Fees | +0.01 |
| Engine | 0.00 |
| **Gap** | **+1.05** |

Moments:
1. 07-23 14:00: ENA −1.7% on half (+0.21 pp).
2. 07-28 18:00: SHIB −1.1% on half (+0.16 pp).
3. 07-30 20:00: PUMP +2.9% on half (−0.22 pp).

![E5 vs vt_mom, window most like now](figures/20261004-e5/ii_lookalike.svg)

**(iii) Rising window where vt_mom beat E5 by the most, 2021-01-28** (BTC +46.5%)
- vt_mom **+61.56%**, E5 +33.98%, A +37.05%.

| Component | pp |
|---|---|
| Entry timing | −2.01 |
| Drift and guard | −0.32 |
| Equity path | −0.76 |
| Fees | +0.03 |
| **Engine (A − vt_mom)** | **−24.52** |
| **Gap** | **−27.59** |

Moments:
1. 01-28 15:00: DOGE +38% while E5 held half (−1.10 pp).
2. **01-29 04:00: DOGE +70% in one hour.** vt_mom's daily book held 0.198, while book_orch (A and E5) held 0.056
   after its hourly drift-band trades (−11.87 pp).
3. 02-02 01:00: DOGE −12% while E5 held none of it, because its staged half was not executed (+0.81 pp).

This is v1's known parity outlier: almost all of the gap is the engine, not E.

![E5 vs vt_mom, rising window, vt_mom best](figures/20261004-e5/iii_up_vt_best.svg)

**(iv) Falling window where E5 beat vt_mom by the most, 2022-05-05** (BTC −25.3%)
- vt_mom −23.26%, E5 **−17.57%**, A −22.39%.

| Component | pp |
|---|---|
| Entry timing | **+5.42** |
| Drift and guard | −0.10 |
| Equity path | −0.61 |
| Fees | +0.11 |
| Engine | +0.87 |
| **Gap** | **+5.69** |

Moments:
1. 05-05 16:00: ADA −4.1% on half (+1.37 pp).
2. 05-12 15:00: ETH +6.1% on half (−0.79 pp).
3. 05-13 22:00: NEAR +6.9%, with E5's half not executed (−0.87 pp).

![E5 vs vt_mom, falling window, E5 best](figures/20261004-e5/iv_down_e5_best.svg)

**(v) Flat and choppy, 2021-02-15** (BTC −0.2% over the window, a 31.5% swing inside it)
- vt_mom **+3.78%**, E5 +1.79%, A +3.78%.

| Component | pp |
|---|---|
| Entry timing | **−1.99** |
| Drift and guard | +0.01 |
| Equity path | −0.01 |
| Fees | +0.01 |
| Engine | 0.00 |
| **Gap** | **−1.99** |

Moments:
1. 02-15 14:00: AVAX +13.5% on half (−0.71 pp).
2. 02-15 22:00: AVAX −9.1% on half (+0.99 pp).
3. 02-23 21:00: UNI +7.8%, with E5's half not executed (−1.05 pp).

![E5 vs vt_mom, flat, choppy window](figures/20261004-e5/v_flat_choppy.svg)

**(vi-a) Last edition's falling round, 2026-03-21** (BTC −5.0%)
- vt_mom −1.57%, E5 **−0.98%**, A −1.57%.

| Component | pp |
|---|---|
| Entry timing | +0.36 |
| Drift and guard | +0.21 |
| Equity path | +0.01 |
| Fees | +0.02 |
| Engine | 0.00 |
| **Gap** | **+0.60** |

Moments:
1. 03-26 21:00: WLFI +1.1% on half (−0.18 pp).
2. 03-27 11:00: SOL −2.4%, with E5 below A after drift (+0.16 pp).
3. 03-29 00:00: FET −1.7% on half (+0.21 pp).

![E5 vs vt_mom, last edition's falling round](figures/20261004-e5/vi_round_falling.svg)

**(vi-b) Last edition's rising round, 2026-04-04** (BTC +13.2%)
- vt_mom +9.92%, E5 +7.47%, A **+11.68%**.

| Component | pp |
|---|---|
| Entry timing | **−4.28** |
| Drift and guard | +0.28 |
| Equity path | −0.27 |
| Fees | +0.05 |
| Engine | +1.76 |
| **Gap** | **−2.45** |

Moments:
1. 04-04 18:00: STO +21% on half (−1.29 pp).
2. 04-05 02:00: STO −12%, with A and E5 below vt_mom after a drift trade (engine, +0.78 pp).
3. 04-16 19:00: ENA +3.4% on half (−0.33 pp).

![E5 vs vt_mom, last edition's rising round](figures/20261004-e5/vi_round_rising.svg)

### 4.2 Over all 2,298 windows (what counts)

**Market type.** UP if BTC's 14-day return is above +2%, DOWN if below −2%, flat otherwise. All values are per window.

| | UP (1,003) | DOWN (808) | Flat (487) | All |
|---|---|---|---|---|
| Mean gap R(E5) − R(vt_mom) | **−0.48 pp** | **+0.37 pp** | −0.09 pp | −0.10 pp |
| Median gap | −0.30 pp | +0.33 pp | +0.04 pp | |
| Share of windows E5 ahead | 41% | 61% | 52% | |
| HIT (mean of the 3 bars, w′): E5 vs vt_mom | 0.843 vs 0.841 | 0.312 vs 0.317 | **0.523 vs 0.607** | |
| Entry timing (staged halves) | −0.49 | +0.27 | −0.07 | −0.13 |
| Drift and guard (E5 vs A) | +0.04 | −0.01 | −0.06 | 0.00 |
| Equity path | −0.02 | +0.01 | +0.02 | 0.00 |
| Fees and spread saved | +0.02 | +0.03 | +0.02 | +0.03 |
| Engine (A − vt_mom) | −0.04 | +0.07 | 0.00 | +0.00 |
| First 24 hours / rest of the window | −0.12 / −0.36 | +0.10 / +0.27 | −0.02 / −0.07 | −0.02 / −0.08 |

**By coin volatility third.** Coins are split by their median 30-day volatility at the 16:00 decisions. Values are pp
per window.

| | Low vol | Mid vol | High vol |
|---|---|---|---|
| All windows | −0.06 | +0.03 | −0.07 |
| UP | −0.22 | −0.13 | −0.13 |
| DOWN | +0.16 | +0.22 | −0.01 |
| Flat | −0.08 | +0.03 | −0.04 |

**The staged halves themselves.** Each value is what the wait between the first and the second fill earned (+) or cost
(−): the added weight × −(price change between the fills), in % of equity per event. In brackets: the number of events
(each real event repeats in up to 14 windows).

| | Half executed, then topped up | Half not executed, bought in full at the top-up |
|---|---|---|
| All | −0.005% per event (24,117; 51% positive; median 8 hours between fills) | −0.011% (5,081; 50% positive) |
| UP windows | **−0.027%** (10,292) | −0.042% (1,563) |
| DOWN windows | **+0.021%** (8,398) | +0.007% (2,595) |
| Flat windows | −0.002% (5,427) | −0.010% (923) |
| Low-vol coins | −0.006% (12,561) | −0.011% (2,423) |
| Mid-vol coins | +0.008% (7,908) | −0.027% (1,976) |
| High-vol coins | **−0.028%** (3,648) | +0.031% (682) |

1,042 staged halves were never topped up (the coin exited first, or it broke down).

**Reading.**
- E5's strength is falling markets: half-size new entries lose less when the market keeps falling.
- Its weakness is rising markets: the second half is bought later and higher.
- In flat windows the mean return gap is small, but E5 clears the bars less often (w′-weighted HIT 0.523 vs 0.607).
  A likely reason (UNVERIFIED): its lower exposure in the first days leaves more windows just under the 0% bars.
- The first 24 hours carry about a fifth of the gap. The rest builds while staged halves wait for their top-up, and
  through the path effects that follow.

### 4.3 Resilience (all windows)

| | E5 | vt_mom |
|---|---|---|
| Worst day (full UTC days inside windows) | −14.7% | −14.7% |
| Worst 14-day R | **−29.7%** | −30.8% |
| 5th-percentile R | **−14.8%** | −15.7% |
| Longest losing streak (days in a row, inside a window): max / mean | 12 / 2.82 | 12 / 2.81 |
| Max drawdown: median / 90th percentile | **9.7% / 17.9%** | 10.1% / 18.7% |
| Single-coin blow-up share | **3.66%** | 3.96% |
| Rank across views (a, b, c, d, e), among E5, vt_mom and the live model | 2, 1, 2, 2, 3 | 1, 2, 1, 1, 2 |

E5 is slightly more resilient in every row except the worst day and the streaks, which are equal. vt_mom ranks first
in three of the five views; E5 ranks first in one.

### 4.4 Hybrid hypotheses: proposed, NOT tested (stopped here for approval and pre-registration)

**The mechanism (from 4.2).** Staging earns in falling markets and costs in rising ones:
- entry timing gives +0.27 pp per DOWN window and −0.49 pp per UP window;
- per staged half, +0.021% in DOWN windows and −0.027% in UP windows.

So staging should only be on when the market is weak at the decision.

**Caveat (UNVERIFIED).** It is not known whether any signal known at the decision separates the coming fortnight's
direction. `docs/EVALUATION.md` notes that the 14-day direction failed the validation's up-probability test.

**H1, "E-breadth": stage only in a weak market.**
- At every base decision (16:00 UTC, and a window's first hour), compute breadth_t = `_trend.breadth(view, book_trend)`:
  the share of the 20 most liquid point-in-time coins with trend score ≥ 0.6.
- If breadth_t < **0.60**, E's staging rule applies unchanged: a new coin enters in full if its trend score is 1 and
  its 30-day volatility is below the median of the base's coins, otherwise at half (`fraction` 0.5), completed at
  00:00 UTC if still in B′ and not broken down, or else at the next 16:00 decision.
- If breadth_t ≥ 0.60, every new coin enters in full.
- Everything else as E5: base vt_mom with its config, band 0.05, the option-1 hold and option-2 previous holdings,
  every other layer off.

**H2, "E-trend": stage only while BTC is in a down-trend.**
- At every base decision, read the BTC state with Pol's switch code, `src/models/pol/_combo.btc_state(view,
  {team_trend_2's parameters, ema_days: 20})`: a 20-day EMA of hourly closes with ±3% hysteresis, the same state as
  v3's BH and pol_switch_vt_tl_e20v45.
- If the state is **down**, E's staging rule applies as above. If **up**, every new coin enters in full.
- Everything else as E5.

**Not proposed: staging only the top volatility third** (one of the suggested examples). 4.2 shows staged halves of
high-volatility coins cost the most per event (−0.028%), the opposite of that rule's premise.

**Neither hybrid has been run.** Both wait for your approval and a pre-registration.

## 5. Quick-exit breakdown shorts (read-only event study)

**Events.** Check 3's events, rebuilt by the same definitions (2020-06-02 to 2026-09-29). Two of 11,725 were dropped,
having no close at the first hour.
- **Cost:** a short round trip, 0.2% plus 2 × the half-spread.
- **t:** day blocks.

**Raw net P&L** (1, 2 and 4 hours after entry):

| Variant | Events | 1 h (t) | 2 h | 4 h |
|---|---|---|---|---|
| a, all | 11,723 | −0.307% (−16.4) | −0.309% | −0.342% |
| b, breadth < 0.3 and BTC below its 20-day average | 4,348 | −0.298% (−7.7) | −0.332% | −0.366% |
| c, b and still below the level 4 hours later | 3,211 | −0.217% (−6.7) | −0.300% | −0.240% |

**THE pre-registered set** (take profit +0.6%, stop −1.2%, at most 4 hours, hourly closes):

| Variant | Mean net | Median | Win rate | t | Worst loss | 2023 / 2024 / 2025 / 2026 | Exits: target / **stop** / time |
|---|---|---|---|---|---|---|---|
| a | −0.304% | −0.210% | 46.2% | −15.4 | −24.4% | −0.36 / −0.31 / −0.29 / −0.31 % | 42% / **29%** / 29% |
| b | −0.299% | −0.168% | 46.9% | −7.8 | −24.4% | −0.28 / −0.18 / −0.31 / −0.31 % | 44% / **31%** / 25% |
| c | −0.214% | −0.036% | 49.1% | −6.1 | −12.1% | −0.37 / −0.14 / −0.30 / −0.44 % | 44% / **26%** / 30% |

**Information only:**

| Variant | +0.4% / −0.8% / 2 h | +1.0% / −2.0% / 8 h | Re-short after a take-profit |
|---|---|---|---|
| a | −0.319% | −0.282% | −0.391% (26% of events re-shorted) |
| b | −0.327% | −0.310% | −0.415% (27%) |
| c | −0.214% | −0.173% (median +0.18%, win rate 51.5%) | −0.295% (24%) |

**Decision rule:** no variant has a positive mean with t ≥ 2, and none is positive in any of 2023–2026. **Not pursued.**

The target is hit more often than the stop (42–44% vs 26–31%). But a take-profit nets only about +0.4% after costs,
while a stop nets about −1.4%, and hourly gaps reach −24%. So every set loses.

## 6. Shadow log export

`mm-book-shadow-export` runs `python -m src.orchestrator.shadow export --loop`. At 00:30 UTC each day it writes
`reports/shadow/<YYYYMMDD>-<bot>.md` for the previous UTC day.
- **Content:** per coin, its hours held, decisions and reasons, would-be orders and approximate paper P&L, plus the
  day's totals.
- **Paper amounts only:** no keys, no account data, no other teams' data.
- **First summary:** due 2026-10-05 00:30 UTC, covering Oct 4 from 05:00. A preview from the first two hours was checked
  (`results/book/shadow/preview/`); nothing partial was committed.
- **Committing:** each day's two small files are committed by hand with
  `git add reports/shadow && git commit -m "Shadow summaries <date>"`. The exporter does not commit by itself.

**Raw hourly logs** stay on the server, outside git: `results/` is a symlink outside the repository.
- `results/book/shadow/<bot>/shadow/*.jsonl`: the per-coin decision log.
- `results/book/shadow/<bot>/logs/*.jsonl`: the runner's own log.

To download them from your laptop:

```
scp -r metallurgy-server:/home/ubuntu/test/MiniMax/results/book/shadow ./book-shadow
```

## 7. Notes and UNVERIFIED items
- **Chart palette.** The palette validator could not be run: Node.js is not installed locally or on the server. The
  charts use the reference palette's first two categorical slots (blue for vt_mom, orange for E5), which its
  documentation lists as validated as a pair in both light and dark mode.
- **Engine component.** The "engine" part of the gap (A − vt_mom) is v1's parity gap: identical R in 2,061 of 2,298
  windows, and 0.00015 HEADLINE_RET. It dominates only the 2021-01-28 window, v1's 24.5 pp outlier.
- **Parity of the shadow bots** is pending until the research panel covers the shadow hours (section 2).
- **Shadow P&L is never used to decide anything.**
