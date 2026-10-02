# The simplified orchestrator (1h + 1d, conservative hourly layer): evidence, point by point (2026-10-02, Pol)

Response to a teammate's comment on Book's plan: keep the hierarchy, forecasts at 1h and 1d only, the 2x cost filter
unchanged, a simple shock rule, a small separately-labelled activity guard, the hourly layer only deciding small
adjustments. Scripts: `results/pol/20261002-v2check/` (`overlay_1h1d.py`, `ml_premise.py`, `guard_kinds.py`,
`guard_dependence.py`); earlier results: `20261002-v2-review.md`.

| Proposal | Evidence | Verdict |
|---|---|---|
| Keep the hierarchy; the daily strategy sets direction | Daily `baitoey_vt_mom` is the v2 top (0.609) | Agree |
| Hourly layer at 1h and 1d only, small adjustments, 2x cost filter | The exact layer, priced with walk-forward forecasts (ridge, refit monthly on the past year, out of sample 2023-01 to 2026-09): 1h layer **-0.29% of equity per 14 days** at a 1% tilt cap (-0.59% at 2%), negative before costs too; 1d layer **-0.37%** at 1% (-0.74% at 2%): +0.13% gross, -0.49% costs. Negative in every year for both | **Not for launch.** A smaller cap only loses less; the layer adds value only with a forecast that clears its costs out of sample, which we do not have |
| Keep the 2x cost filter, never lower it for activity | It works as intended: it blocks 99% of 1h coin-hours; the trades it lets through still lose (the forecast's large values are not reliable) | Agree; activity is solved separately (below) |
| Simple deterministic shock rule | `pol_abl_shock` (cash 24 h after BTC -5% in 4 h; 2.8% of days): same HEADLINE_RET (0.607 vs 0.609), worst fortnight -26.8% vs -30.8% | Agree: the one layer that helps |
| Activity guard: small, non-directional, labelled, not assumed to count | Our guard already is that. In the v2 backtests the momentum models never needed the 0.2% keep-alive: every guard day was a **rebalance back to the strategy's own target weights** (keep-alive-only days: 0 in every window). With those rebalances, 15 of 15 days are active through trades that follow the strategy; counting decision trades only, `baitoey_vt_mom` has a median of 8 such days (56% of windows reach 8), `pol_switch_vt_tl_e20v45` 10 (78%). Logs label `rebalance`, `guard` and `keep_alive` separately | Agree; describe "daily rebalancing to target weights" in the strategy description, and ask the organizers to confirm |
| Fire the guard near the end of the day | Ours fires from 04:00 UTC (12 hours before the HKT day ends) and retries every hour until a fill is confirmed from the account | Keep 04:00: a guard at the end of the day has no time to retry a failed order |
| Organizer definition | Relayed (another team, 2026-09-28): an active day = at least 1 trade that looks like the stated strategy, not manual trading; at least 8 active days. Our scoring requires 10 of 15 | Still to confirm in writing |

**Fixed today (live runner, 149d564):** the runner skipped the guard on any decision hour, so a model that decides
every hour (any hourly layer) would never have had a guard live, while the backtest engine fires it. Now the guard
runs whenever the day has no confirmed fill, also right after a decision that filled nothing. Daily models are
unchanged. Test: `test_guard_also_runs_for_a_model_that_decides_every_hour`.

**So the simplified architecture for launch is:** daily strategy + shock rule + the existing guard, with no hourly ML
layer until a forecast clears its costs out of sample. That is `pol_abl_shock` today (research-registered on
`feature/v2check`), or the same rule on whichever daily model the team picks.
