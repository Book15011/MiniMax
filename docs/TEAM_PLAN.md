# MiniMax team plan

_Version 2 · 2026-09-30 · replaces v1. Decisions become final when the team merges this file into `main`._

## 0. Summary

| Topic | Decision |
|---|---|
| Process | **No fixed roles.** Each member builds their own models in each method (`momentum`, `trend`, `selector`). One harness scores every model the same way. The best of the three in each method wins, by the pre-registered rule in `docs/STRATEGY_GUIDE.md` |
| Launch default | The **momentum** winner, unless a selector passes the selection ladder or the trend winner beats it in both test periods (§4.3) |
| Lookalike validation | Built and pre-registered (`reports/validation_set_v1.md`). It predicts the market's volatility and dispersion better than all of history, but **not direction**, and no better than recent history. Used to size risk and as a scenario set, not to pick strategies (§3) |
| Selectors (orchestrators) | Go live only if they pass the selection ladder (`docs/STRATEGY_GUIDE.md` §6) |
| Activity rule | Enforced by the engine: a guaranteed daily strategy trade |
| Reports | `reports/<model_name>/<YYYYMMDD-HHMM>.md` (committed) + `.log` (not committed) |
| AWS | Invite expected around Oct 2. Everything that doesn't need EC2 proceeds now |

## 1. Rules check: does every method in the plan comply?

The rules come from the Luma page, the info-session deck, the FAQ and the organizers' email. What they mean for a strategy:
- It must be directional (long, sell, short, close).
- No market-making, arbitrage, HFT or leverage.
- At most 30 calls per minute, and at least 10 active days out of 14.
- It runs fully autonomously on EC2.
- It trades only with the competition key, only from the live start.
- Every change goes through a commit.

| Method (from the plan) | Allowed? | Condition to stay compliant |
|---|---|---|
| Baselines: cash, BTC hold, equal-weight hold | Benchmarks only | Never deploy: they trade once, which fails the activity rule |
| ROT-EW / ROT-IV (long-only momentum rotation) | ✅ | Needs the forced daily trade (raw: only 37% of windows reach 10 active days) |
| TREND-2 (slow BTC/ETH trend) | ✅ | Needs the forced daily trade (raw: 2%) |
| B: trend per coin, long **and** short (TS-LS) | ✅ | Keep net exposure driven by the signals (never forced to zero), so the book stays clearly directional |
| C: long-only rotation | ✅ | Forced daily trade |
| D: momentum + short sleeve (MOM-SS) | ✅ | Shorts use the `/v6` endpoints (0.10% on open and close). Confirm shorting works with the **test key**; fall back to long-only automatically if it doesn't |
| E: dual momentum | ✅ | MOM-SS already applies it: longs need positive momentum of their own, shorts negative |
| F: dynamic momentum | ✅ | — |
| G: two speeds (slow trend + fast rotation) | ✅ | — |
| H: market-neutral long/short | ❌ | The deck allows directional strategies only. Dropped |
| Pair trading | ❌ | Counts as arbitrage. Dropped |
| X: on/off switch, mean reversion, drawdown brake | ✅ allowed | The evidence is weak (§2); keep them only as tested overlays |
| **Baitoey's method** (TG-MOM: BTC 50h/200h trend gate, top 3–5 by 24–72h return with high volume, inverse-vol weights, 30% cap, 1–1.5%/day vol target, brakes at −3%/−6%, 10–20% BTC when risk-off) | ✅ every part | (1) The 4-hourly rebalance produces up to ~26 orders/day; fine within 30 calls/min if paced. (2) The risk-off BTC position must **actually trade daily**, so use the forced daily rebalance. (3) The brakes are bot logic, so they're allowed |
| Lookalike validation (macro, funding, calendar features) | ✅ | Research only. Any data source is allowed; nothing live depends on it |
| **Orchestrator** (picks a method by market state) | ✅ if automatic | Deterministic code. Every switch logged with its reason. Declared in the README as the strategy. Never switched by hand |
| Limit order first, market-order fallback | ✅ | One resting order per coin, single-sided, cancelled on timeout. That's execution, not market-making |
| Bot-enforced stop-losses | ✅ | Roostoo has no stop orders, so the bot must monitor and close |

**Plan-level risks:**

1. **Scope vs. time.** The validation build is done. The live engine and the harness were unstarted on Sep 30; both are now on the build list (§4.1) and start first.
2. **"≥ 10 active days in 100% of windows" is unreachable for raw strategies.** Build it into the engine as a guaranteed daily trade (§2.3 shows 100% with the guard).
3. **The lab server's clock is ~12.8 h off, and Binance's live API is blocked here.** Signed requests must use the `/v3/serverTime` offset. The live data path must be tested on EC2.
4. **The lookalike skill test may show no skill.** Our quick walk-forward test of lookalike-based *method selection* did worse than a fixed choice (§2.2). Pre-register what happens if it fails: fall back to the fixed choice.

## 2. Evidence

**Setup:**
- Binance spot hourly closes, Jan 2020 – Sep 29 2026, 34 liquid coins (the ones Roostoo lists today, which is mild survivorship bias).
- 0.10% fee on every trade, 1-bar execution lag, gross exposure ≤ 100%.
- Every 14-day window at a daily step.
- Strategy parameters were set before testing. MOM-SS was designed on 2024–2026 data, so **2020–2023 is unseen data for it**.

### 2.1 Methods, 2022-01 to 2026-09 (every 14-day window)

| Method | Median fortnight | Worst 10% | Worst | Fortnights > 0 | Median max DD | Median composite* | ≥ 10 active days (raw) |
|---|---|---|---|---|---|---|---|
| BTC hold | +0.42% | −10.7% | −36.5% | 52% | −8.3% | 0.96 | 0% |
| **MOM-SS (v1)** | **+0.12%** | **−6.1%** | **−11.4%** | **51%** | **−4.9%** | **0.48** | 95% |
| TG-MOM (Baitoey) | −0.82% | **−4.0%** | −10.8% | 37% | **−3.3%** | −3.35 | 35% |
| TS-LS (trend per coin L/S) | −0.61% | −7.4% | −19.3% | 46% | −6.6% | −1.00 | 83% |
| ROT-EW (long-only rotation) | −0.28% | −13.0% | −29.4% | 49% | −10.5% | −0.03 | 37% |
| TREND-2 (BTC/ETH trend) | −0.36% | −6.6% | −17.2% | 44% | −5.0% | −1.63 | 2% |
| BLEND5 (equal mix of the five) | −0.14% | −5.8% | −16.5% | 49% | −4.8% | −0.30 | 94% |

\* 0.4·Sortino + 0.3·Sharpe + 0.3·Calmar on daily returns, annualized. The official formula is unknown.

**Whole-year returns** (max drawdown in brackets):

| Year | BTC | MOM-SS | TG-MOM | TS-LS | ROT-EW | TREND-2 |
|---|---|---|---|---|---|---|
| 2020 (Jun–Dec) | +209% | +38% (−17%) | +48% (−7%) | +99% | +104% | +139% |
| 2021 | +61% | +64% (−17%) | +42% (−10%) | +160% | +388% | +74% |
| 2022 | −64% | **−3%** (−28%) | −28% (−29%) | 0% | −60% | −41% |
| 2023 | +167% | +46% (−26%) | +8% (−26%) | +14% | +153% | +81% |
| 2024 | +123% | +39% (−22%) | +54% (−9%) | +18% | +184% | +50% |
| 2025 | −6% | −5% (−25%) | −21% (−25%) | −14% | −41% | +9% |
| 2026 to Sep 29 | −5% | **+48%** (−17%) | −2% (−28%) | +3% | +83% | +14% |

**Reading it:**
- **MOM-SS is the only method that's reliable in every year.** It survived 2022 (−3% while BTC fell 64%) and never lost more than 5% in a calendar year. Its bad fortnights are about half as bad as BTC's.
- **TG-MOM has the smallest losses but rarely ends positive** (37% of fortnights). Its on/off BTC gate whipsaws in choppy markets (2022, 2025), and it trades ~0.6 of the book a day, which costs about 0.8% a fortnight in fees. Its strength is shallow drawdowns, not returns.
- **ROT-EW and TREND-2 are bull-market bets.** They're huge in 2021, 2023 and 2024 but lost 41–60% in 2022, a coin flip for the return cut and heavy on the risk score.

### 2.2 Orchestrators (walk-forward, weekly decisions, 2022–2026)

Each week, pick one of {MOM-SS, TG-MOM, TS-LS, ROT-EW, TREND-2} using only data available at the time. The pick maximizes 14-day return + ½ × max drawdown, measured three ways:

| Orchestrator | How it picks | Median fortnight | Worst 10% | Median composite |
|---|---|---|---|---|
| LOOK | The method that did best in the 25 most similar past market states (7 features: BTC trend, cycle, volatility, breadth, correlation, dispersion) | −0.86% | −7.0% | −2.82 |
| HIST | The method that did best over all past history | −0.81% | −6.0% | −2.26 |
| PERF | The method that did best in the last 14 days | −0.74% | −8.8% | −1.41 |
| **no switching: MOM-SS** | — | **+0.12%** | **−6.1%** | **+0.48** |
| no switching: BLEND5 | — | −0.14% | −5.8% | −0.30 |

**Conclusion:** switching between methods lost about 1 pp of median return per fortnight and most of the risk score. Selection is noisy with only ~160 independent fortnights, and every switch pays fees.

The orchestrator stays a research goal, run in this order:
1. A **fixed blend**.
2. **Soft tilts**: bounded weights around the blend (±20 pp), driven by market state.
3. Live use **only if** it beats MOM-SS and the blend on 2022–2026 walk-forward under both metric conventions.

### 2.3 Brakes, and the forced daily trade (per 14-day window from cash, 2022–2026)

| Method | Brakes (halve at −3% from peak, 10% at −6%) | Median | Worst 10% | Worst | Median composite | ≥ 10 active days |
|---|---|---|---|---|---|---|
| MOM-SS | off | +0.09% | −5.9% | −11.7% | 0.33 | **100%** |
| MOM-SS | on | −0.48% | −4.6% | −7.0% | −1.49 | 100% |
| TG-MOM | off | −0.80% | −4.0% | −10.1% | −3.26 | **100%** |
| TG-MOM | on | −0.89% | −3.5% | −6.6% | −3.85 | 100% |

- Both use the forced daily trade, which makes the activity rule pass in **100%** of windows.
- The brakes are insurance: they cut the worst fortnight by about a third and cost typical return.
- A gentler floor (shrink smoothly toward −10% of the round's starting equity) cost less in earlier tests. Team decision.

## 3. Lookalike validation: what it tells us

**Setup** (`reports/validation_set_v1.md`, as of Sep 30 00:00 UTC):
- Pre-registered.
- Picks the 25 past 14-day windows whose starting market state (trend, cycle, volatility, market structure) is closest to the live start.
- Funding, macro and calendar features were tested and didn't earn a place.

**Verdict:**

| Question | Answer (from the report's own numbers) |
|---|---|
| Better than using all of history? | **Yes, once scored fairly.** The standard score gives +0.007 and +0.025, both intervals including 0. The fair-CRPS side check gives **+0.056 [+0.039, +0.076]** and **+0.069 [+0.037, +0.098]** (`reports/validation_set_v1_fair_crps/`) |
| Better than the 25 most recent windows? | **No.** −0.060 / −0.022 (fair: −0.051 / −0.014); intervals reach 0, so no better than recent history |
| What it does predict | BTC volatility (+0.16), cross-coin dispersion (+0.13), rebounds (+0.07) |
| What it predicts worse than doing nothing | BTC direction (−0.045) and cross-coin correlation (−0.059) |
| Stability | Dropping VOL keeps 19% of the 25 windows; dropping STRUCTURE keeps 14% |
| The 25 windows | Cover every regime; their outcomes look like the whole pool's (BTC 14-day p10 −12.9% vs −12.0%) |

**How we use it:**
1. **As a scenario set.** The harness reports every model on the 25 lookalikes and on the 25 most recent windows, next to all windows.
2. **To size risk, not to pick direction.** It predicts volatility and dispersion, which can set how much risk to take. That's a model idea, tested like any other.
3. **Not to choose the launch strategy.** In the selection ladder (`reports/selection/`), a picker choosing between the models by lookalikes wins only 48% of CONFIRM test dates against simply holding the momentum winner. Predicting the market's character isn't the same as predicting which strategy will do better.

**Two measurement notes, for the record (the pre-registered choice doesn't change):**
- The report scores with the standard sample CRPS, which penalizes a 25-window set against the ~2,000-window pool. The fair-CRPS side check shows this hid real skill against all of history (above).
- Future pre-registrations should use the fair CRPS and require the interval's lower bound > 0 **and** beating the recent-windows baseline, not only a positive point estimate.

## 4. The plan

### 4.1 Build list (shared; anyone takes an item by opening a worktree for it)

| # | Item | Needs EC2? | Status |
|---|---|---|---|
| H1 | Harness: backtest engine, metrics (both conventions), 14-day windows from cash, reports, per-method comparison | No | `feature/harness` (Pol), in review |
| H2 | Selection ladder for selectors | No | `feature/selection-ladder` (Pol), after H1 |
| H3 | Fair-CRPS side check of the validation set | No | with H2 |
| E1 | Roostoo client (signing, clock offset, rate budget, `Success` rules, reconcile), order planner, paper broker, test-key self-check | No (the self-check needs the test key in `.env`) | `feature/roostoo-client` (Pol) |
| E2 | Live runner, systemd unit, warm start, JSONL logging, EC2 setup script | Deploy only | after E1 |
| M | Models: every member at least one model per method | No | due **Oct 1, 20:00 HKT** |
| D | README sections: strategy, backtests, engine, fees, risk (markdown only) | No | by Oct 10 |

### 4.2 Timeline (HKT)

| Date | Milestone |
|---|---|
| Sep 30 | Process v2, harness, selection ladder, client and planner |
| Oct 1, 20:00 | Models due. Then `backtest.compare` per method, then the selection ladder |
| Oct 1–2 | Test-key self-check (signing, fills, fees, shorts, rate limit). Paper trading on live Roostoo prices |
| ~Oct 2 | AWS invite: EC2 setup, Binance reachability from Sydney, systemd, 24 h paper run |
| Oct 3, 16:00 UTC | Freeze the launch model by §4.3. Open the holdout once for it. Rehearse on EC2 with the test key |
| **Oct 4, 00:00** | Live with the competition key |
| Oct 4–10 | Monitor. Upgrades only by the rule in `docs/STRATEGY_GUIDE.md` §7 |
| Oct 10 | Repo submission-ready; Book pushes `main` to GitHub |
| Oct 14–17 | Bug fixes only |

### 4.3 Launch decision rule (pre-registered)

1. In each method, the winner is chosen by the rule in `docs/STRATEGY_GUIDE.md` §5.
2. **Launch = the momentum winner**, unless:
   - a selector passes the selection ladder, in which case it launches; or
   - the trend winner has the better combined rank in **both** SCREEN and CONFIRM, in which case it launches.
3. The holdout (windows ending after 2026-08-08 16:00 UTC) is opened **once**, on Oct 3, for the chosen model. It is reported, and changes the choice only if it reveals a bug (e.g. a rules failure).
4. The final lookalike re-run on Oct 3 is informational only.

## 5. Risks

| Risk | Mitigation |
|---|---|
| Engine not ready for Oct 4 | E1 starts now (no keys needed). E2 is scripted before AWS arrives |
| Too many models, too little time | Models due Oct 1 20:00; after that only the ones already registered compete |
| Overfitting through many tests | One harness, pre-registered comparison rule, holdout opened once |
| Shorts disabled on the competition account | Every model with shorts has a long-only fallback flag; the engine switches automatically |
| Key leak | Keys only in `.env` files (server test key, EC2 competition key); never in chats, docs or prompts |
| Shared-server collisions | Worktrees, locks, reviewed merges (`AGENTS.md` §4) |
