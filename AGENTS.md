# MiniMax: rules for agents and teammates

Every agent (Claude Code, Codex/ChatGPT, Copilot) reads this file at the start of every session and follows it.
It overrides tool defaults. Change it only through a reviewed merge (§4). Last updated 2026-09-30.

**Start every agent session with:** `ssh metallurgy-server 'git -C /home/ubuntu/test/MiniMax show main:AGENTS.md'`

## 1. Project

- Autonomous crypto trading bot for the Roostoo Quant Trading Hackathon (Team101-MiniMax, HKU).
- Scored live round: **Oct 4–17, 2026**, $100k mock account, spot 1x long and short.
- The live bot runs **only** on the organizers' AWS EC2 (Sydney). This server is for data, research and tests.
- Git is **local to this server**: no GitHub day to day. Book pushes `main` to GitHub once, for submission.
- The repo goes public at submission, so write every file, commit and comment as if it's already public.
- Plan and workstreams: `docs/TEAM_PLAN.md`.

## 2. Hard rules

1. **Stay in scope.** Work only inside `/home/ubuntu/test/MiniMax`. Nothing else on this machine is ours to change.
2. **Run on the server.** An agent running on a laptop executes every command on this server through `ssh metallurgy-server`, never in a local sandbox.
3. **Never touch secrets.** Never read, print, paste, log or commit API keys, `.env*` files, passwords or tokens.
   - The **competition key** lives only on EC2 and is used only by the running bot. Never call Roostoo with it by hand; the organizers treat that as manual trading.
   - The **test key** is used only through scripts in this repo.
4. **Share the machine politely.** Never stop, restart or renice a process you didn't start. Run heavy jobs with `nice -n 10` and at most 8 workers.
5. **Git hygiene.**
   - Never commit to `main` directly; changes reach it only through `scripts/wt merge` with a reviewer.
   - Never rewrite or delete someone else's branch.
   - Never commit data, logs, secrets, or files over 5 MB.
6. **Respect the competition rules in code.**
   - Directional strategies only: no market-making, arbitrage, pair trading or HFT.
   - Gross exposure ≤ 100% of equity.
   - At most 20 Roostoo calls per minute per process.
   - Order requests are never retried automatically.
7. **Keep other teams out of our work.** Describe strategies by what they do. Never name other teams, and never copy their code, anywhere (code, commits, docs, prompts).
8. **Don't guess.** Mark an unverified fact `UNVERIFIED` in code or docs and say so in your report.

## 3. Environment

| Item | Value |
|---|---|
| Host | `metallurgy-server` (hostname `ubuntu-6`); one shared `ubuntu` account |
| Project root | `/home/ubuntu/test/MiniMax`: the shared checkout. Read here; don't develop here |
| Python | 3.10, shared venv `.venv/` (`source .venv/bin/activate`) |
| Network | Outbound traffic goes through a proxy. Roostoo calls take 1.5–6 s. **Binance's live API is blocked here**; the archive `data.binance.vision` works |
| Clock | Can be wrong. Never sign with local time; always apply the offset from `/v3/serverTime` |
| Data | `data/` at the project root, shared by every worktree and gitignored. Only data scripts write to it |
| Tests | `pytest -q` must pass before every merge (`scripts/wt merge` enforces it) |

## 4. Working at the same time

Three people and their agents share one account. Each task gets its own **git worktree**, so no one's files, branch or uncommitted work collide.

```bash
cd /home/ubuntu/test/MiniMax
scripts/wt new <member> <task>                        # -> .worktrees/<member>-<task> on branch feature/<task>, from main
cd .worktrees/<member>-<task>                         # do all work here; commit often
scripts/wt merge <member>-<task> --reviewed-by <m>    # tests, then merge into main with a Reviewed-by line
scripts/wt rm <member>-<task>                         # after the merge
scripts/status                                        # worktrees, tmux sessions, locks, load, disk
```

Members: `pol`, `book`, `baitoey`.

- **Identity:** `scripts/wt new` sets your git name and email for that worktree from `.team/identities` (never shared). Commits must show who did what.
- **Ownership:** every area has an owner (§5). Change another owner's area only on your own branch, and get that owner as the reviewer.
- **Review:** before `scripts/wt merge`, the reviewer reads `git diff main...feature/<task>` and confirms. `Reviewed-by` goes into the merge commit, so history shows who checked what.
- **Long jobs:** run them in tmux named `mm-<member>-<task>`, wrapped in `scripts/lock <name> -- <command>` so two copies can't run.
  - Outputs go to `results/<member>/<YYYYMMDD>-<task>/`.
  - Check `scripts/status` before starting anything heavy.
- **Main stays green:** `scripts/wt merge` refuses to merge if tests fail or the worktree has uncommitted changes. Merges run under a lock, so two people can't merge at once.

## 5. Ownership

| Workstream | Owner | Paths |
|---|---|---|
| W1 Live engine & ops | pol | `src/api/`, `src/execution/`, `src/live/`, `deploy/`, `tests/test_api*`, README engine section |
| W2 Data, backtest & validation | book | `src/data/`, `backtest/`, `src/validation/`, `src/orchestrator/`, `data/` |
| W3 Strategies & risk | baitoey | `src/strategy/`, `src/risk/`, `config.yaml` strategy section, README strategy section |

Shared contracts: `src/contracts.py`. Change them only with all three members reviewing. Details are in `docs/TEAM_PLAN.md`.

## 6. Every task

1. Read this file, then the docs for your task.
2. `scripts/wt new <member> <task>`.
3. Write tests first for anything that touches money: sizing, orders, fees, metrics.
4. Implement. Strategy code is pure (no I/O), and every tunable number lives in `config.yaml`.
5. `pytest -q`, then commit (say *why*), then `scripts/wt merge` once reviewed. If strategy behaviour changed, the merge needs a backtest diff in `results/`.
6. Report what changed, what was verified, and what is still unverified.

## 7. Code rules

- **Time:** UTC everywhere. Bars are indexed by their **close** time, and a value is usable at time *t* only if its bar closed at or before *t*. Look-ahead is a bug.
- **One strategy function** serves both backtest and live, and one order planner serves both.
- **Backtests:**
  - Charge 0.10% taker / 0.05% maker fees and cross the spread.
  - Apply a 1-bar execution lag.
  - Start each 14-day window from cash.
  - Report median, worst-10% and worst fortnight, never a single total return.
- **Money math:** truncate with `Decimal` to each pair's precision, respect the $1 minimum order, and send plain decimal strings.
- **Roostoo client:**
  - Check `Success` on every response.
  - A missing numeric field means 0.
  - `Success:false` from `pending_count` or `query_order` can mean "empty".
  - After an order timeout, reconcile with `query_order` and never resend.
- **Logging:** JSONL, one line per request, decision and order, stamped with the git commit. Never log headers or keys.

## 8. Competition facts

| Fact | Value | Source |
|---|---|---|
| Fees | 0.10% market (taker), 0.05% limit (maker); shorts 0.10% on open and close | Luma, API docs |
| Rate limit | 30 calls/min per account, queries included | FAQ Q22 |
| Activity | ≥ 10 active days (deck) or 8 (Luma). **Plan for all 14.** An active day = ≥ 1 strategy trade | Deck, organizers |
| Allowed | Directional long, sell, short, close. No leverage, HFT, market-making or arbitrage | Luma, deck |
| Keys | Test key during prep; competition key only from the live start | Organizer email |
| Scoring | Top 20 by return per region, then 0.4·Sortino + 0.3·Sharpe + 0.3·Calmar; formulas published on Finale Day | Luma, deck |
| Repo | Markdown-only README explaining strategy, backtests, engine, fees and risk. Target **Oct 10**, deadline Oct 14 | Organizer email, deck |
| Prices | Streamed from Binance, so Binance history is valid for backtests | FAQ Q17 |

## 9. Dates (HKT)

- Oct 1–3: prep, test key only.
- **Oct 4 00:00**: live start, competition key on EC2.
- Oct 10: repo submission-ready.
- Oct 14: submission deadline.
- Oct 17: round ends.
