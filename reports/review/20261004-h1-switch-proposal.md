# Proposal: switch the live model to H1 ("E-breadth")? (draft for the team, 2026-10-04, Book)

**Status: draft for discussion. Nothing has been changed on EC2, in the live bot or in its config.** The plain-language
explanation of H1, with example windows, is in [`docs/research/h1_brief.md`](../../docs/research/h1_brief.md).

## 1. The reason
- The reason is **backtest evidence that existed before the live round, not live P&L.** H1 passed its pre-registered
  rule as a CANDIDATE ([`20261004-hybrids.md`](20261004-hybrids.md)).
- **Against vt_mom:** HEADLINE_RET 0.617 vs 0.609, ahead in two of five views and tied in three, with risk measures no
  worse.
- **Against the live model (pol_switch_vt_tl_e20v45, 0.568):** H1 is ahead in four views and tied in falling windows
  only.
- **The limits.** The edge over vt_mom is small (+0.009; SCREEN +0.0015), and the idea came from analysing the same
  history. The live round is the first out-of-sample test.
- Shadow P&L (the paper bots) is never part of this case.

## 2. What would change

**H1 itself.** book_orch with E's staged entries switched on only while breadth < 0.60. Everything else is vt_mom's
logic, at band 0.05: long only, hourly runs, the daily activity guard.

**Step 1: merge `feature/book-orch` into `main`.** This is 32 commits as of `aaa93c7`; the full list is in the appendix.
- **Conflicts:** none. `config.yaml` changed on both sides, but `git merge-tree` shows no conflict.
- **What it brings:**

| Area | Files | Owner, so reviewer |
|---|---|---|
| book_orch and its layers; batch 4 models | `src/models/book/` (book_orch, _trend, _orch_features, _orch_ml, book_vt_dual, book_coin_trend, book_vt_breadth, book_vt_top4) | Book, built on Baitoey's vt_mom: **Baitoey** |
| Model blocks in `config.yaml` | book_orch (default = H1) and the batch 4 models | strategy section: **Baitoey** |
| Pol's client fix 9c3bbf3, "read the balance from SpotWallet" | `src/api/client.py`, `tests/test_api.py` | **Pol**: it arrives through a local stack of `feature/v2check`; Pol to confirm it belongs in main (and whether EC2 already has it) |
| Research tooling and shadow mode | `backtest/orch_*.py`, `src/orchestrator/` | Book |
| Forecast manifests, each under 5 MB | `validation/book_orch_*.json` | Book |
| Tests | `tests/test_book_orch.py`, `test_book_batch4.py`, `test_shadow.py` | as above |
| Reports and docs | `reports/`, `docs/research/` | Book |

  Through `scripts/wt merge book-book-orch --reviewed-by <member>` (tests run first; 309 pass on the branch), reviewed
  by **Baitoey** (models, strategy config) and **Pol** (client fix).

**Step 2: the live switch.** Pol's area (W1: live engine and ops).
- **Config change:** one line in `config.yaml`'s `live:` block, `model: pol_switch_vt_tl_e20v45` → `model: book_orch`.
  It is a separate small commit and branch, reviewed by Pol, and deployed to EC2 by Pol under his procedure.
- **Nothing else changes.** The runner, its settings and `book_orch`'s block (already H1) stay as they are.

**Step 3: the README.** It must describe the strategy that actually runs. `main`'s README has only "Setup" and
"Layout". The submission draft on `feature/launch-e20v45` declares the current live model, and these sections would
be rewritten for H1:
- "The strategy";
- "Risk and position sizing";
- "How the bot works";
- "How it was chosen";
- "Backtest results";
- "Known limitations and assumptions";
- the model name in "Running it".

Owners: Baitoey for the strategy sections, Pol for the engine sections.

## 3. Readiness of the live runner (read-only check)

| Item | Finding |
|---|---|
| Hourly schedule | Supported. `Runner.due_decision` runs a decision every hour for `rebalance_hours: 1`. book_orch has run hourly through this runner in three paper shadow bots since 2026-10-04 |
| Guard fix 149d564 | **In `main`.** The activity guard also runs after a decision that filled nothing, as an hourly model needs |
| State after a restart | Restored from `state.json` (previous targets, standing targets, active days) and the price store. book_orch keeps no other state: its decision depends only on the market view and its previous targets, and its caches rebuild themselves. A missed hour is not replayed; an overdue decision or guard runs at the next hour |
| What the model needs | pandas and numpy; 60 days of hourly history (the live store keeps 300). scikit-learn is not imported (only the forecast layers, which are off, need it) |
| A model change | The runner resets the previous targets, and the new model decides at the next hour from an empty book; active days are kept. That first decision trades every difference exactly |
| Runner code | `src/live/` is identical on this branch and on `main` (no diff) |

**API calls per hour** (live mode; the client's rate limiter caps every process at 20 a minute):

| Hour | Calls | Detail |
|---|---|---|
| Quiet hour | about 6 | server time, ticker, and a balance plus short-positions read at the start and the end |
| Decision hour | about 8 + 1 per order | |
| H1's busiest decision in the backtest | 12 orders, so about 20 calls in that hour | orders spaced 3 s apart (the live model's busiest is 20 orders) |
| The switch hour (section 4) | 8 orders, so about 16 calls | |

- **Per 14-day window:** H1 averages 94 orders against the live model's 144.
- **UNVERIFIED:** book_orch declares shorts possible, so the runner also reads short positions each time. Starting it
  with `--long-only` would save one call per read. H1 never shorts.

## 4. The switch cost

This is a stand-in for the live account: the live model's paper bot (`data/live_e20v45`, read only) at bar
2026-10-04 09:00 UTC.
- **Prices:** the bot's last closes, widened by each pair's half-spread from the newest Roostoo ticker snapshot.
- **Planner:** the shared one, with an exact first trade.
- **H1's decision that hour:** breadth 1.00, so staging was off.

**Holdings.** The paper equity is $101,298. The live model holds AAVE, AVAX, LINK, PUMP, SUI and WLD at about 16.6%
each, with $1,017 in cash. H1 targets AAVE, HBAR, LTC, PUMP, SUI and WLD at 12.26% each, a gross of 0.74 (vt_mom's
3%-a-day volatility cap, against the live model's 4.5%).

| Order | Pair | Quantity | Notional | Fee (0.10%) |
|---|---|---|---|---|
| SELL | AVAX | 1,523.33 (all) | $16,775.66 | $16.78 |
| SELL | LINK | 1,192.11 (all) | $16,752.16 | $16.75 |
| SELL | AAVE | 24.161 | $4,393.78 | $4.39 |
| SELL | PUMP | 703,908 | $4,482.73 | $4.48 |
| SELL | SUI | 3,705.9 | $4,353.87 | $4.35 |
| SELL | WLD | 6,638.7 | $3,854.03 | $3.85 |
| BUY | HBAR | 121,661 | $12,417.25 | $12.42 |
| BUY | LTC | 176.218 | $12,417.23 | $12.42 |
| **Total** | | **8 orders** | **$75,446.72** | **$75.45** (0.074% of equity), plus about $3.95 of spread |

**UNVERIFIED:** the live account's holdings and prices at the actual switch hour will differ. If breadth were below 0.60
then, new coins would be bought half first, with a second set of orders at 00:00 UTC.

## 5. Rollback rule (agreed before any switch)
- **Revert to the previous model (pol_switch_vt_tl_e20v45) only for a bug or a rule breach, never for P&L.**
- **A bug** is any of these:
  - a live decision that differs from the backtest's replay of the same hour (the shadow parity check);
  - an exception that stops the bot trading;
  - orders that are refused repeatedly;
  - a state that cannot be restored after a restart.
- **A rule breach** is any of these:
  - gross exposure above 100% after a trade;
  - a short position opened (H1 is long only);
  - more than 20 API calls in a minute;
  - a day without a trade caused by the model.
- **Not a reason:** a losing day or week, trailing the old model or vt_mom, or a drawdown within the backtest's range
  (90th-percentile max drawdown 18%, worst fortnight −30%).
- **Who decides:** 2 of 3 members, written down in `reports/` with the evidence before the revert.

## 6. Open risks (UNVERIFIED)
- **Live vs backtest:** fills, spreads and the one-hour lag could differ from the backtest. Shadow parity is pending
  until the research data covers the shadow hours.
- **Whether breadth keeps separating weak from strong markets live.** The 14-day direction itself is not predictable
  (`docs/EVALUATION.md`).
- **A small, in-sample edge**, the better of two hybrids. The live result may simply match vt_mom.
- **book_orch's hourly drift trades in extreme hours.** In 2021-01-28 they cost 24 points against vt_mom's daily
  rebalancing. This is included in every backtest number above.
- **Pol's client fix 9c3bbf3** would reach `main` with this merge; whether EC2 already runs it is unknown.
- **The EC2 environment and deploy steps** were not checked here (the task forbids touching EC2).
- **Switching mid-round** turns over about 75% of equity once (section 4). The account's active days are kept.

## Appendix: commits on `feature/book-orch` not in `main` (oldest first)
`9c3bbf3` (Pol: client balance fix) · `93e13eb` · `4dbd7db` (batch 4) · `d9aa8a8` · `4dc473d` (local stack merges) ·
`9f8640d` · `71cfb2a` · `d085fce` · `183827f` (v1) · `70ebc8c` · `191496e` · `8a92877` · `030b90a` (v2) · `f2ee1d4` ·
`1788c62` (checks) · `b49ecb0` · `4852fb1` · `f9ce047` (final steps) · `c0c0730` · `e3b6c0e` · `ed381ab` · `4ebe776`
(v3) · `04ce882` · `bb8b7ee` · `476d3bc` (E decision, shadow mode) · `53d08ef` · `9667422` · `2ca8964` · `bd30554` ·
`2401185` (hybrids; **`9667422` = the gate code, `bd30554` = H1 as default**) · `aaa93c7` (H1 shadow bot), plus this
proposal's commit.
