# Handoff: book_orch / H1 research, the live round, and a starting kit for MFT / HFT

Book (with Claude), 2026-10-05, day 1 of the live round. Branch `feature/book-orch` (worktree
`.worktrees/book-book-orch`). This page is the state of play for whoever picks up next, human or agent. Anything
not checked by us is marked UNVERIFIED.

## 1. Where things stand (read this first)

| | |
|---|---|
| **Live round** | Roostoo competition 538. Runs 2026-10-04 12:00 UTC to 2026-10-18 12:00 UTC (20:00 HKT both ends), $100,000 start, taker 0.1% / maker 0.05%, no leverage |
| **Live bot (EC2)** | Deployed by the team at the start. Main's `config.yaml`: `live.model: pol_switch_vt_tl_e20v45` (e20v45), `live.endgame.enabled: false` (lock-in off). I have not looked at EC2: confirm what is actually running |
| **Team decision before 2026-10-14 20:00 HKT (day 10)** | Turn the lock-in on? One config line plus a restart. Historically +0.040 HEADLINE_RET for e20v45, 0.568 → 0.608 (§4) |
| **Switch the live model mid-round?** | Suggestion: **no, stay with e20v45** (pre-registered test, §4). Closest alternative: `pol_abl_shock` |
| **Our best backtest model** | `book_orch` = H1 ("E-breadth"), registered run `033c466d54a7766f`, HEADLINE_RET **0.6173**, #1 on the shared leaderboard. Not on main |
| **Branch status** | `feature/book-orch` is 37 commits ahead of main, not pushed, not merged. `config.yaml` changed on both sides, but the old-style `git merge-tree` shows no conflict markers. Merging needs reviewers via `scripts/wt merge … --reviewed-by`: Baitoey (models, config), Pol (runner-adjacent: shadow, paper tools) |
| **Next direction (team, 2026-10-05)** | Explore medium- and high-frequency strategies (MFT / HFT). The team's view is that the top outliers on the live leaderboard trade that way (UNVERIFIED by us) |

## 2. What is running on the research server (all mine, all paper, no keys, no orders)

| tmux session | What it does | Output | Stop with |
|---|---|---|---|
| `mm-book-paper-live` | **Live paper comparison since 20:00 HKT Oct 4.** Re-simulates every model from cash each hour with the scoring engine on the H1 shadow bot's bars. No extra API call | `results/book/paper-live/latest.md` (open with Markdown preview), `equity.svg/.csv`, `trades.csv`, `holdings.json` | `tmux kill-session -t =mm-book-paper-live` |
| `mm-book-shadow-h1` | H1 shadow bot: the live runner in paper mode with per-coin explanation logs. Its hourly bar store feeds the paper comparison | `results/book/shadow/h1/` | `tmux kill-session -t =mm-book-shadow-h1` (this also stops the paper comparison's price feed) |
| `mm-book-shadow-a`, `mm-book-shadow-e5` | Shadow bots for book_orch with every layer off (about vt_mom) and for E5 | `results/book/shadow/{a,e5}/` | same pattern |
| `mm-book-shadow-export`, `mm-book-shadow-export-h1` | Daily Markdown summaries of the shadow bots | `--out reports/shadow` (not committed) | same pattern |

Each shadow bot reads Roostoo's public ticker about once an hour (well under our 20 calls/min ceiling). The other
`mm-pol-*` and `mm-baitoey-*` sessions belong to Pol and Baitoey: do not touch them.

**What the paper comparison does:**
- **Models:** e20v45 (live), `pol_abl_shock`, vt_mom, H1, vt_top4 and pol_switch_vt_tl.
- **Ranking table:** return, the lock-in column, max drawdown, orders, fees, holdings and the latest decisions, plus
  every trade.
- **Live table:** "if the live bot switched from e20v45 now", with orders, USD traded and fees.
- **Fills:** a decision fills at the next hourly close, a 1-hour lag. The real bot fills at about HH:01, so compare
  models with each other, not to the cent with the real account.

## 3. How the research was run (the rules we kept)

- **AGENTS.md:**
  - work only in `/home/ubuntu/test/MiniMax`;
  - never commit to main;
  - no push;
  - `nice -n 10`, ≤ 8 workers, long jobs under `scripts/lock <name> --`;
  - never commit data, logs, secrets or files over 5 MB;
  - mark unknowns UNVERIFIED.
- **Never read `.env` or key files.** No Roostoo calls except the paper bots' public price reads. No writes to
  `data/`. Never touch EC2, the live bot or its config.
- **Pre-register before computing.** Every test had a `reports/review/<date>-prereg-*.md` committed before the code
  ran, with one setting per idea, no threshold grid and a fixed decision rule. Keep doing this: most ideas fail, and
  the rule stops us from fooling ourselves.
- **Scoring tool** (version `3036a0d8bfdaa6a0`):
  - 2,298 overlapping 14-day windows starting at 12:00 UTC, like the round.
  - Primary measure: HEADLINE_RET, the weighted share of windows whose R_liq clears three bars (LENIENT, MIDDLE,
    STRICT), averaged.
  - Five views: as now, without post-holdout, years equal, UP only, DOWN only.
  - Comparisons use a paired month-block bootstrap (2,000 draws, seed 20261002, 90%).
  - Scratch runs go through `backtest.scoring.score.score_model` with a scratch registry (see
    `results/book/20261004-breadth-ideas/run_idea.py`).
  - Registration goes through `backtest.scoring.report.score_and_publish`. Not `backtest.run --score`: that also
    writes `data/harness`.

## 4. Results so far (so nobody re-runs them)

**Shared leaderboard (HEADLINE_RET, full pool):**

| # | Model | Score |
|---|---|---|
| 1 | book_orch (H1) | 0.617 |
| 2 | pol_abl_shock | 0.607 |
| 3 | baitoey_vt_mom | 0.609 |
| 4 | baitoey_vt_dual | 0.587 |
| 5 | book_vt_top4 | 0.572 |
| 6 | **e20v45 (live)** | 0.568 |

The order follows the margin-0.03 pick rule, which is why #2 scores below #3. Full table:
`results/scoring/leaderboard.md`.

**book_orch: what worked and what did not** (details in `docs/research/book_orch.md` and `reports/review/2026100*`):

| Test | Result |
|---|---|
| E5 (vt_mom base, hold rule, staged entries, band 0.05) vs vt_mom | Not a tied alternative: behind in UP windows (−0.030) |
| **H1 = E5, staging only when breadth < 0.60** | **CANDIDATE, registered, 0.6173.** Ahead of vt_mom in (a) and (e); better worst R, 5th-pct R, drawdown and blow-up share |
| H2 = E5, staging only when BTC's switch is down | CANDIDATE, 0.6110, not registered |
| Macro brake; "hold longer"; per-coin trailing stop; BTC-only hedge; quick-exit breakdown shorts | All no |
| Breadth ideas: A hourly emergency trigger / B hysteresis 0.55–0.65 / C breadth falling | All NOT BETTER than H1: A 0.6175, B 0.6187 (tail fractionally worse), C 0.6100 (`reports/review/20261004-breadth-ideas.md`) |

**Lock-in** (the live `live.endgame` rule: from day 10, at +3%, sell everything and hold cash). Every model gains:
- e20v45: 0.568 → **0.608**;
- vt_mom: 0.609 → 0.637;
- `pol_abl_shock`: 0.607 → 0.637;
- H1: 0.617 → **0.645**.

H1 + lock-in is only tied with e20v45 + lock-in (+0.037 [−0.005, +0.083]). e20v45 + lock-in is better on CS_HIT
(0.470), on the ~150-team cut proxy (0.390) and on worst R (−26.2% vs −30.1%). Sources: Pol's
`reports/review/20261002-new-rules.md` and our appendix in the breadth-ideas report.

**Mid-round switch** (`reports/review/20261004-midround-switch.md`): e20v45 for k days, then X from e20v45's
holdings.
- **Gain:** in rounds that looked like the start of this one (BTC switch up, breadth ≥ 0.60), switching on day 1–2
  to `pol_abl_shock`, vt_mom or H1 raised HEADLINE_RET by about **+0.06** (significant).
- **Cost:** every switch deepens the worst round (−27% to −32% vs −26.2%).
- **Verdict:** pre-registered rule says **STAY**. Switch cost about 0.1% of equity. From day 7 on, a switch makes no
  difference.

**Market state at the round start** (20:00 HKT Oct 4): breadth 1.00 (all 20 liquid coins trending up), e20v45's BTC
switch up, BTC +6% over 14 days. All six models picked the same 6 coins: AAVE, HBAR, LTC, PUMP, SUI and WLD. Sizes
differed: e20v45 at about 100% invested, the vt_mom family at about 74%.

## 5. Starting kit for MFT / HFT

**Constraints that decide what is possible:**
- **API budget:** 30 calls/min documented, queries included; our ceiling is 20 (`execution.calls_per_minute`). There
  is no cap on trades per minute, but each order is a call. True HFT (sub-second, many orders) is not possible on
  Roostoo. Minute-scale trading is, with a few orders per minute at most.
- **Fees:** taker 0.1%, maker 0.05%, plus the spread. A taker round trip costs about 0.2% plus spread, so the edge
  per trade has to clear that.
- **Limit orders:** whether passive limit orders fill on Roostoo, and how fast, is **UNVERIFIED**.
  `python -m src.live.fillcheck --limit` (Pol, 20a0a29) was written for this and needed a funded test wallet. I found
  no result. The upper bound if every trade were a maker fill is +0.016 HEADLINE_RET for the daily models (Pol's
  `reports/review/20261002-v2-review.md`, row E). For MFT the maker / taker question is probably the whole game:
  answer it first.
- **The round is 14 days.** Per Pol's `reports/review/20261002-new-rules.md`, the real ranking has a risk score as
  its second stage, after return. Check the organisers' rules before designing for it (UNVERIFIED in detail).

**Lessons from everything faster than daily we tried (all on hourly bars, all after costs):**
- An hourly ML layer at 1-hour, 1-day and 3-day horizons, with or without a 2× cost filter, loses after costs
  every year (Pol, new-rules §4).
- Hourly volume exits are worse: e20v45 −0.052, vt_mom −0.039 (Baitoey, `feature/mom-ss`).
- Hourly rebalancing of e20v45 on a 3% band did worse than daily (same source).
- Per-coin stops of 5% and 10% are worse: 0.568 → 0.529 / 0.526 (Baitoey).
- Our own hourly layers are worse or no better: trailing stop, BTC hedge, quick-exit shorts and the emergency
  trigger.
- Short-horizon mean reversion scores low on HEADLINE_RET, though some do well on CS_HIT: `baitoey_mr_4h` 0.472
  (CS_HIT 0.461), `pol_mr_cap` 0.509 (a fragile peak), `baitoey_mr_bbrsi` 0.499.
- **The pattern:** each extra trade costs about 0.1–0.2%. Signals at these horizons had less edge than that. MFT has
  to be cost-first: maker fills, fewer and larger moves, or a signal whose edge per trade is clearly above 0.2%.

**Data and code you can start from:**

| What | Where | Note |
|---|---|---|
| 1-minute klines, 65 symbols, 2025-09 to 2026-09-29 | `data/binance_spot/klines_1m/<SYMBOL>/*.zip`, manifest in `data/binance_spot/_manifest.jsonl` | Read-only. The hourly panel uses resampled 1m data from 2025-09-01 (`hourly_from_1m` in config) |
| Hourly panel (all research) | `cfg["harness"]["panel_dir"]`, loaded by `backtest.data.load_market` | Point-in-time universe, half-spreads from Roostoo snapshots |
| Hourly engine | `backtest/engine.py` (`Simulator`) | 1-hour fill lag, band, activity guard. Not built for sub-hour. Changing it may change the tool version |
| Live runner | `src/live/runner.py` (hourly loop, paper / live) | An MFT bot needs its own loop (every 1–5 minutes) inside the call budget. Treat the live runner as frozen during the round |
| Live-data replay | `results/book/paper-live/paper_live.py` | **Gotcha:** the live bar store has gaps. The runner forward-fills up to `live.max_fill_hours` (48 h) before deciding. Without that, every model returns all cash |
| Shadow and explanation logs | `src/orchestrator/shadow.py` | Wraps any runner in paper mode. Example of logging decisions per coin |

**Suggested first steps (each pre-registered):**
1. **Do limit orders fill?** Run `fillcheck --limit` on the test wallet: fill rate, time to fill and fee. This sets
   the cost model for everything else.
2. **Build a minute-bar harness from the 1m data.** Realistic costs (taker / maker plus spread), the 20 calls/min
   budget, 14-day windows at 12:00 UTC, scored with the same HEADLINE_RET bars so results compare with the
   leaderboard.
3. **Study the top teams from what is public on the live leaderboard.** If trade counts or equity paths are visible,
   check whether their edge looks like volume (maker rebates?), intraday mean reversion or momentum bursts, before
   building anything (UNVERIFIED what is visible).
4. **Start with one simple MFT idea at one setting**, and compare it against the daily models on the same windows.

## 6. File map (this branch)

| Path | What |
|---|---|
| `src/models/book/book_orch.py` | The orchestrator: vt_mom base and layers R / E / F / FS / TS / BH, the stage gate (H1 default), the breadth ideas (off). **CRLF line endings: keep them** |
| `tests/test_book_orch.py` | Its tests, also CRLF. Full suite at last run: 312 passed |
| `src/orchestrator/shadow.py`, `tests/test_shadow.py` | Shadow bots (seed / run / export / parity) |
| `docs/research/book_orch.md` | The full research write-up, with the conclusion and H1 sections |
| `docs/research/h1_brief.md`, `h1_examples.md` | Team brief on H1, and one rising, one falling and one flat window, hour by hour |
| `reports/review/2026100{3,4}-*.md` | Every pre-registration and report, in order |
| `reports/book_orch/20261004-0828-score.md` | H1's registered score report |
| `results/book/…` | Scratch: scripts, versions, JSON outputs, shadow state and paper-live. Not committed |

## 7. Gotchas that cost us time
- **SSH drops** ("Connection closed … port 21806"). Run anything longer than a minute under `nohup` or tmux, and keep
  ssh calls short.
- **CRLF files.** `book_orch.py` and its tests use CRLF, and `sed -i` turns them to LF. Edit with Python and write
  CRLF back.
- **tmux names.** `tmux kill-session -t name` matches by prefix. Use `-t =name`.
- **pgrep.** `pgrep -f <script>` inside an ssh command matches the ssh command line itself.
- **Old git.** The server has git 2.34, with no `merge-tree --write-tree`. Use the old form,
  `git merge-tree $(git merge-base A B) A B`.
- **Commit messages.** Inside single-quoted ssh commands, apostrophes break. Write the message to a file and use
  `git commit -F`.
- **Encoding.** Python on the Windows laptop defaults to cp874. Pass `encoding="utf-8"` when editing files locally.
- **Model registry.** Models from other branches (for example `baitoey_vt_dual`) are not in this branch's registry.
