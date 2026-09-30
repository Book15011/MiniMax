# MiniMax team plan

_Version 1 · 2026-09-30 · proposal for team review. Decisions become final when the team merges this file into `main`._

## 0. Summary

| Decision | Proposal | Evidence |
|---|---|---|
| Launch strategy (v1) | **Momentum rotation + 25% short sleeve** (MOM-SS), with a forced daily trade | Best risk-adjusted record 2022–2026. Also positive in 2020–2023, data that did not exist when its parameters were set (§2) |
| Orchestrator | **Research track only.** No live method-switching until it beats MOM-SS and a fixed blend in a walk-forward test | All three switching orchestrators we tested lost to MOM-SS out of sample (§2.2) |
| Drawdown brakes / loss floor | Team decision. They cut the worst fortnight from about −11% to about −7%, and cost about 0.5 pp of the typical fortnight | §2.3 |
| Activity rule | Enforced by the **engine** (exact daily rebalance), not left to each strategy | Without it, most methods fail "≥ 10 active days" in 63–98% of windows |
| Workstreams | W1 Live engine & ops · W2 Data, backtest & validation · W3 Strategies & risk | §4 |
| Critical path | Engine + EC2 must be live-capable by **Oct 3**. Research never blocks it | §3 |

### Where the repo stands (Sep 30)

| Area | Status |
|---|---|
| Data: Binance downloader, loader, integrity sweep, FRED, futures funding/OI copy | ✅ built (`src/data/`, 3.2 GB in `data/`) |
| Lookalike validation pipeline with a pre-registered rule | ✅ built (`src/validation/`); results pending |
| Tests | ✅ 40 passing |
| Roostoo API client, order planner, paper/live engine, EC2 deploy | ❌ not started (W1) |
| Backtest engine + metrics + window evaluator | ❌ not started (W2) |
| Strategy functions and risk overlays | ❌ not started (W3) |

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

1. **Scope vs. time.** The validation build (macro data, walk-forward skill scoring, stress sets, a bootstrap simulator) plus eight strategy families plus tuning is more than 4 days of work. The **live engine has no named owner** in the plan, and it's the critical path. §4 fixes that.
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

## 3. Recommended plan

**Track A: live-capable v1 by Oct 3** (never blocked by research):
1. MOM-SS as a pure strategy function:
   - daily decision at 00:05 UTC
   - top 15 liquid coins, top 5 long, keep while in the top 10
   - 25% short sleeve on the 4 weakest coins with negative momentum
   - long book volatility-capped
2. The engine guarantees a daily trade, applies the §1 conditions, and falls back to long-only if the short check fails.
3. Market orders at launch. Limit-first execution only after the test key shows how limit orders fill.

**Track B: upgrades, Oct 1–10.** Each candidate must pass a pre-written rule:
- It beats MOM-SS on 2022–2026 walk-forward (median composite and worst-10%, under both metric conventions).
- It has paper-traded for 3 days without errors.
- Candidates, in order:
  1. Loss floor or profit lock (team decision)
  2. Limit-first execution
  3. Fixed blend
  4. Orchestrator soft tilts
  5. TG-MOM as a sleeve (its shallow drawdowns may help a blend)
  6. ML signal overlay

After Oct 10: bug fixes only. No strategy changes in the last 3 days.

## 4. Workstreams: who does what

The work is split by similarity of skills and code, so each person owns one coherent area with few hand-offs.

| | W1 Live engine & ops | W2 Data, backtest & validation | W3 Strategies & risk |
|---|---|---|---|
| **Owner (proposed)** | Pol | Book | Baitoey |
| **Why this fit** | Wrote the API/EC2/compliance plan | Already built the downloader and is on the validation set; has lab-server experience | Authored TG-MOM; strategy logic is the natural next step |
| **Owns** | `src/api/`, `src/execution/`, `src/live/`, `deploy/` | `src/data/`, `backtest/`, `src/validation/`, `src/orchestrator/` | `src/strategy/`, `src/risk/`, strategy section of `config.yaml` |
| **Sep 30 – Oct 1** | Signed client + HMAC test vector, serverTime offset, 20 calls/min budget, `Success` semantics, never-retry + `query_order` reconcile. Order planner (precision, $1 min, sells first) | 1h data 2020+ (incl. delisted coins), loader, backtest engine using W1's planner, metrics under both conventions, window evaluator | MOM-SS, TG-MOM, TS-LS, TREND-2, ROT-EW as pure `targets(bars, state) -> weights` functions. Unit tests |
| **Oct 1 – 2** | Test-key checks: market/limit fills, fees, shorts open/close, rate limit → `docs/API_NOTES.md`. Paper broker on live Roostoo prices | Reproduce §2 on the full data. Lookalike features + walk-forward skill test | Overlays: forced daily trade hook, loss floor, profit lock, brakes. Parameter plateau checks |
| **Oct 2 – 3** | EC2: Python, systemd auto-restart, warm start, logging (JSONL + trade CSV), 24 h paper run, crash/restart drill | Decision report: v1 confirmation + fallback | README strategy + risk sections |
| **Oct 4** | Switch EC2 to the competition key (commit + restart). Watch the first trades | — | — |
| **Oct 4 – 10** | Monitoring, reconciliation audits, limit-first execution v1.1 | Orchestrator research (blend → soft tilts), live-vs-backtest attribution | Upgrade candidates via the Track B rule. Finalist-deck material |
| **Oct 10 – 17** | Repo submission-ready (Oct 10); Book pushes `main` to GitHub and makes it public; bug fixes only | Post-mortem analytics | Deck draft |

**Shared contracts** (`src/contracts.py`; changes need all three members to review):
- `targets(bars: DataFrame, state: dict) -> pd.Series`: signed weights, Σ|w| ≤ 1, pure, no I/O. W3 writes them; W1 and W2 call them.
- `plan_orders(targets, holdings, prices, rules) -> list[Order]`: W1 writes it. It's used by both live and backtest, so the two can't drift apart.
- `load_bars(symbols, start, end, interval) -> DataFrame`: W2 writes it. Close-time UTC index, no look-ahead.
- `metrics(equity) -> dict`: W2 writes it. Both conventions.

**Hand-offs that must not slip:**
- W1's planner → W2's backtester (Oct 1).
- W3's MOM-SS function → W1's paper run (Oct 1).
- W2's v1 confirmation → W1's Oct 3 tag.

## 5. Risks

| Risk | Mitigation |
|---|---|
| Shorts disabled on the competition account | Automatic long-only fallback (MOM-SS long book at 75% gross) |
| Engine slips while research grows | Track A has a named owner and a fixed Oct 3 deadline; research can't block it |
| Overfitting through many tests | Pre-written accept rules, a fixed test budget, plateau (not peak) selection, the untouched last 8 weeks |
| Key leak | Keys only in `.env` (server/EC2). Never in chats, docs or prompts. **Rotate any key that was pasted into a chat or a shared link** |
| Shared-server collisions | Worktrees, locks and ownership (`AGENTS.md` §4–5) |
