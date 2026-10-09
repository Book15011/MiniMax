# Book weak-market evaluator: completed evidence

The useful deliverable is a visible ranked fresh-cash comparison across historical weak-market checkpoints, plus a separate short-onset table. It replaces the previous secondary board's generic continuation diagnostics. Original leaderboard/main/live execution are unchanged.

## Decision and practical baseline

Among all 38compatible registered models, **baitoey_vt_dual ranks 1**, **book_vt_dual ranks 2**, and incumbent **pol_switch_vt_tl_e20v45 ranks 23**. The best experiment has archived-profile 228h mean+2.95%, freshBTC mean+2.29%, median+3.63%, p 10-8.52%, worst 10%mean-11.46%, worst-15.67%, and CS 0.2334.

The incumbent's same case mean is+0.74%, freshmean+0.58%, p 10-11.75%, and CS 0.1234. The leader's paired mean advantage is+2.21%. This is a different selector from the original broad-market hit-rate score; H 1/book_orch is now rank 4.

**No candidate has established positive simultaneous advantage over both cash and fixed e 20 in every primary profile/horizon.** The leading conservative score is-2.58%; it is a historical lower-bound statistic, not a forecast of loss. The table provides a concrete benchmark for testing a new short strategy, and a shortlist for prospective experiments. It does not authorize a real-account switch.

## Observed market context and signal discipline

The source-verified archived reference is Oct 8 00UTC. Its price percentage changes (converted from log features) are BTC 24h-2.60%,48h-2.85%,30d+5.32%; BTC is+16.10% above its 200-day average, with only 2/30 assets positive over 48h. This describes broad weakness inside a longer upward trend, making rebound risk material.

The Oct 9 00UTC BTC-only sensitivity uses ticker-assisted hourly samples:24h-1.84%,48h-4.40%. Fresh BCH breadth is missing 29/30; its full breadth features remainNaN. Those prices are finite available observations, not independently archive-confirmed hourly closes.

Only completed, causal price/volume-derived features enter matching. Options/funding/macro narratives do not enter numerical weights because an aligned point-in-time validated panel is not available in this comparison. Earlier detailed market/macro research remains in /home/ubuntu/test/MiniMax/.worktrees/book-book-regime-eval/research/book/regime_eval/RESEARCH.md. Its direction call is not treated as validated evidence.

Historical weak starts do not necessarily lead to further falls: archived matched BTC 240h mean is+1.54%, and 40% finishnegative. Fresh-profile mean is+0.88%, with 44% negative. Therefore this method does not establish a reliable next 10-day downward forecast. A permanent short should not be rewarded merely for matching that narrative.

## Causal windows and aggregation

At each historical cash start t0, BTC 48h log return must lie[-10%,0],48h positive breadth<=40%, and BTC 24h logreturn<=1%. Nearest cases use equal group rank-space distances, never future returns. Both primary profiles select 25 starts, >=14daysapart, <=3in 90days, with 24h maturity embargo. Each has 16 rawquarter groups; cross-profile replay overlaps join to 17resampling clusters.

Every model uses the same dated cases and first 216/228/240h from cash.228h matches Oct 9 00 to the documented Oct 18 12 competition end. Historical 12UTC versus query 00UTC timing is disclosed. This is not continuation from a candidate's invented old holdings, and not simulation of current EC 2 holdings.

Risk reuses the old FLOORED.V1/HKT CS formula on shortened liquidation-adjusted paths. Ordinary cached execution costs and 1-bar lag remain intact; the chosen endpoint pays liquidation once. UTC CS and original 14-day CS_HIT are separate. CS_HIT_positive averages only profitable shorter cases.

The conservative score is the minimum joint one-sided 90% lower advantage across 2profiles x 3horizons xcash/e 20.20,000 fixed-seed shared merged-quarter draws and a centered standardized maximum across 38 models give the multiple-comparison penalty. This uses a fixed bootstrap SE, not full bootstrap-t. Strengthened evidence also requires original eligibility, >=12 rawquarters in each primary profile and>=12 mergedclusters. Zero-variance constants are exact only if their supported values are constant. Long market dependence, selected-neighbor uncertainty, spent historical research and discarded experiments remain outside guaranteed coverage.

## Downside and rebound evidence

Archived 25 cases contain 7 ex-post downstress cases (BTC 240h<=-2%) and 13 rebound cases (BTC 240h>=+2%). These labels do not select or weight the main score. Strategy results below remain 228h.

Leader downstress mean-3.28% versus incumbent-10.26%; rebound means+6.73% versus+6.52%. Thus the leader reduces observed downside here but still loses during continued market decline. The small down-only subset is not a safe deployment selector.

baitoey_tg_mom has the highest observed downstress mean+0.54% over those 7 cases, but its main rank 35 and weak short-proxy returns warn against selecting solely on that conditional average.

Leader mean advantages remain positive in 15/40-case sensitivities; see sensitivity.csv for exact values. Its leave-one-quarter-out robust mean cash/e 20 advantage ranges+0.58% to+1.78%. These are descriptive stability checks, not additional confidence bounds or untouched holdout results.

## Separate short performance

Incumbent archived-profile short onsets:103 across 13/25 windows. Only 28/103 were positive 6h unit-short proxies afterfees/spread (27.2%); window-average proxy return-0.49%. Sampled profitable opportunities followed by losing cover:38. Freshprofile precision and all 1/3/6h counts are in short_table.csv.

The diagnostic counts actual cached entry/decision short onsets, excluding additions and separatingguards. Fixed-horizon direction labels can extend beyond actual cover; cover proxies are separate. Both sides 0.10%fee and 0.05%half-spread are explicit assumptions. Unit returns ignore addition/partial cover sizes, so they are not actual account short PnL. Missing/horizon-censored prices are unresolved. Hourly barriers retain intrahour ambiguity. Live-only quotes and previously biased open-time minute panels cannot establish multiyear second/minute timing.

Use window level support and quarter cluster precision intervals, not thousands of trades as independent observations. A new fast short model needs finer executable data labelled at causal close times and realistic signal/orderdelay. Short metrics never enter main rank.

## Source validation and preserved failures

A sourcecheck of 60initial publisher-checksummed endpointarchives found 6storedprices and 10 volumes differing from the shadowStore. Version 1, its raw audit and previousboard remain saved in results/book/20261009-weak-eval. None of its candidate scenario returns were inspected before source correction.

Version 2 applies 95 publisher-checksummed archives: all 30 reference assetsOct 57 andBTC Sep 30Oct 7.2,280 reference hourly bars matchrawarchives exactly;207 price and 240 volume cells were corrected onlyin new Book snapshots. Corrected causal top 30membership stayed unchanged. Shared original history/live store/cache files remainuntouched.

Bothprimary cases and all 15/40/control sets were frozen before first candidate scenario comparisons; source/model/cache SHA 256 pins are saved. All 38registered full compatible tool/data/window models are included. Originalinventory also lists 56unregistered cache names as UNASSESSED; their existence does not establish compatible published evidence.

Five source windows lacking BTCmaximum horizon endpoints/98% path coverage are excluded with explicitdates/reasons.32of 2298historical states are incomplete and fail causal feature requirements. This is missing-data exclusion, not selection by return direction.

The old Oct 8 12 adaptiveforecast study remains failed with 29/30breadth, incompletefresharchive confirmation and unestablished direction nondegradation. Its alpha 0/failure logs were not rewritten. Earlier e 20first 96h paper-prefix diagnostics remain in its REPORT.md: observed-8.0646%, near 4thpercentile of 25descriptivelegacycases. They are paper replays, not actual EC 2account equity. They do not become a cash start switching test.

## Validation and reproduction

Full suite:457 passed in 191.20s.151focused weak/legacy-score2tests passed. Independent 14board-review tests cover source/cache tampering, fixed baseline acrossrevisions, older revision reactivation, manifest completeness and rollback under one-time renamefailure. All causal selection/statistical/fee/CS/short tests passed. Final presentation/fingerprint change also passed 19boardtests.

Actual command verified:
    .venv/bin/python -B -m backtest.run --model pol_switch_vt_tl_e20v45 --score2

It reproduced the full compatible scoring run and automatically updated the secondary board. Standalone leaderboard2 refresh verified. --score2 alone leaves the original registry/board untouched. Existingboth-flags integration tests cover publishing toboth via one scoring computation. Failed publications stageviews beforecommit and restore after recoverable renameerrors; there is no claim of multi-file atomicity under hardware failure.

Implementation:/home/ubuntu/test/MiniMax/.worktrees/book-book-bear-eval
Branch:feature/book-bear-eval
Protocol:603da2948b68ee0f5c8a
Read:/home/ubuntu/test/MiniMax/.worktrees/book-book-bear-eval/docs/SCORE2.md
Board:/home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md
ShortCSV:/home/ubuntu/test/MiniMax/results/scoring/short_leaderboard_2.csv
Evidence:/home/ubuntu/test/MiniMax/results/book/20261009-weak-eval-v2

Keyfiles: PROTOCOL.md,frozen_config.json,artifact_manifest.json,source_cache_manifest.json,selection_validation.json,cases.parquet,query_features.parquet,prepare_verification.json,publisher_bar_checks.csv,all_models.csv,model_windows.csv,sensitivity.csv,leave_quarter_out.csv,short_table.csv,independent_case_audit.json,verification_final.json. Per-model source/vectors/shortepisode ledgers live under results/scoring/score2/603da2948b68ee0f5c8a/.

Real current-account positions/fills/shortpermission, final competition scoring formula and net switching execution remain UNVERIFIED. Main/live were not changed; no secrets or signedcompetition API calls were used, and no repository wascopied locally.

Independent final audit: all50checks passed for protocol603da2948b68ee0f5c8a. Direct money/risk metrics and all38-model jointbounds reproduced; maximum bound difference9.7e-17. Post-CLI original files and frozen caches remain byte-identical.
