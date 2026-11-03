# Research log

What the team did, in order, and what came of it. Dates are 2026. Research kept in the team's private archive is listed without links.

## Before the round

| Date | Work | Outcome |
|---|---|---|
| Sep 29 | Binance downloader, loader, integrity sweep | Base data for everything after |
| Sep 30 | Team plan and rules, Roostoo client, validation set | First evidence: switching between methods lost about 1 point of median return per fortnight ([TEAM_PLAN](TEAM_PLAN.md)) |
| Oct 1 | Backtest harness, competition-style scoring, live runner, paper bots | About 150 teams in the region, so the bar became the field's best ([final selection](../reports/review/20261001-final-selection.md)) |
| Oct 2 | Scoring v2 (return first), pick-rule study, volume models, orchestrator review | A 0.03 tie margin beat the original rule (0.470 vs 0.417). The hourly layer loses after costs; a shock rule helps |
| Oct 2 | Launch readiness on the live code | +3.63% on last season's falling Round 1 and +0.34% on the rising Final, 0 errors ([readiness](../reports/review/20261002-e20v45-readiness.md)) |
| Oct 3 | Flaw review, one-step go-live script, end-of-round lock-in | [Flaws](../reports/review/20261003-flaws.md) fixed. Lock-in on from day 10 at +3% |

## During the round

| Date | Work | Outcome |
|---|---|---|
| Oct 4 | Round starts with `pol_switch_vt_tl_e20v45`. `book_orch` scored after launch | `book_orch` tops the table at 0.617 but stays research |
| Oct 5 | Organizers rule on tick scalping | Allowed, but judges will not value it as a strategy ([statement](../reports/review/20261005-organiser-statement.md)) |
| Oct 7 to 8 | Forward paper test and review of a tick-scalping sleeve | 14 flaws fixed. Replay shows +15.6% over 46 hours, on an assumed fill rule |
| Oct 9 | Lower switch band for the launch model | 6 of 6 variants fail; launch model unchanged |
| Oct 9 to 10 | Short-model families: exhaustion, forecast, bear exit, intraday, daily channel, cash-funded | 13 ranked, all fail the reliable-profit checks ([leaderboard](../reports/leaderboards/leaderboard_short_ranked.md)) |
| Oct 10 | Coin-short add-ons (Baitoey) | SOL passes narrowly; ETH and the basket do not |
| Oct 11 | **Live model switches to `book_e20combo_brk_cash`** | Team decision for downside protection. Ties on history; loses about a point less on 25 weak markets if the fall continues |
| Oct 11 to 12 | Recovery models, with a frozen BTC-only diagnostic | No live recommendation ([leaderboard](../reports/leaderboards/leaderboard_recovery.md)) |
| Oct 12 | Independent rest-of-round test of the short models (Baitoey) | No short model passes against the live model |
| Oct 13 | **Sleeve goes live** next to the model | Stops itself after one test buy. A cancelled order was reported as filled, so it booked a loss that never happened; no money lost |
| Oct 14 | Sleeve fixed; fill rules measured on the live account | Resting orders do not fill the way the replay assumed. No version has an edge, and all 36 market-buy variants lose ([roostoo_fills](../research/book/roostoo_fills/README.md)) |
| Oct 15 | Latency prototypes | All 4 non-positive on Oct 14 ([report](../research/book/gate/latency/REPORT.md)) |
| Oct 15 | Simulator-edge search and shortlist | All 17 fixed candidates lost on Oct 14. **Decision: no new deployment, keep the live system unchanged** ([recommendation](../research/book/gate/simulator_edge/final_recommendation.md)) |
| Oct 15 | C++ native execution service | 0.021 ms median local processing, 81 focused tests. Live integration and sub-second fills unverified ([results](../research/book/gate/fast_exec/native/RESULTS.md)) |
| Oct 18 | Round ends | Final result not recorded in this repo |

## After the round

| Date | Work |
|---|---|
| Nov 3 | Repository prepared for public release and this documentation written |
