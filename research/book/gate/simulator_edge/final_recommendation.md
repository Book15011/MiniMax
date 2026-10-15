| Rank | Strategy | Verified net edge | Probability of reaching gate | Evidence quality | Penalty | Verdict |
|---|---|---|---|---|---|---|
|1|Top1 three-day momentum /4h|Unverified; proxy median -2.88%|68h static-cutoff proxy 7.3%/6.5%; actual unknown|Spent historical proxy|No latency mechanism|Research only|
|2|Top1 one-day momentum /daily|Unverified; proxy median -2.40%|68h static-cutoff proxy 6.5%/5.4%; actual unknown|Spent historical proxy|No latency mechanism|Research only|
|3|Top1 seven-day momentum /4h|Unverified; proxy median -2.89%|68h static-cutoff proxy 6.3%/5.0%; actual unknown|Spent historical proxy|No latency mechanism|Research only|
|4|Top1 one-day momentum /4h|Unverified; proxy median -3.09%|68h static-cutoff proxy 6.2%/5.0%; actual unknown|Spent historical proxy|No latency mechanism|Research only|
|5|24h volume breakout /4% trail|Unverified; proxy median -1.57%|68h static-cutoff proxy 3.8%/3.2%; actual unknown|Spent historical proxy|No latency mechanism|Research only|

The two proxy frequencies correspond to round 0%/+2% cutoffs from reported current -16% equity, after modeled costs.
**Decision: reject new simulator-edge deployment. No repeatable execution edge was verified.**
If the objective is exclusively the largest historical chance of recovery, mom72_4h leads this fixed benchmark family.
That is a high-risk research shortlist, not a reliable or deployment-qualified improvement.

## 1. What simulator-specific advantage did we actually find?

Coarse minimum price steps: BONK, STO and PEPE are the three largest tick/price ratios in the public snapshot.
Their one-tick maker/maker winning trips can beat fees arithmetically. This explains why these assets attract tick loops.
It does not establish a positive expected profit: an entry at the bid can wait indefinitely or fill into a decline.
Market buys pay the ask. Marketable limits pay taker fees. Resting sells need the bid to reach the limit in the committed live tests.
No hidden discount, guaranteed bid-touch fill or large-order impact independence was established.
The reported live evidence is the committed roostoo_fills test record. Raw authenticated probe/wallet output was not present locally.

## 2. Can we make repeatable net profits using it?

Not demonstrated. All 17 fixed quote candidates lost the recent October 14 day in strict base, extra-delay, double-fee,
partial-maker and optimistic-last scenarios. Both fast short variants also lost.
The unchanged earlier 36 market-buy variants all lose over Oct 8–13, including high win-rate/no-stop versions.
One maker/reversal 72h replay gained 19.95%, but another lost 44.19%; its median across four starts is -4.49%.
The positive 19.95% path is not one of the two disjoint anchor paths: those have 0/2 hits at 19%.
Recent Oct 14 maker/reversal loses 20.73%. Selecting only its attractive path would be overfitting.
This rejects deployment from the tested evidence; it does not prove every possible future strategy unprofitable.

## 3. Is it strong enough to get us into the top20?

No verified simulator strategy meets that standard. The observed quote history supplies only four overlapping 72h starts
and two disjoint anchors. There is no fresh 72h holdout and no moving-cutoff history for a current top20 probability.
Approximate current -16% implies equity 84k from 100k. To finish at 100k/102k requires 19.0476%/21.4286% from current equity.
Those figures exclude any unmodeled initial transition cost or cutoff drift.
At an Oct 15 16UTC first decision and the mission's Oct 18 12UTC deadline, there are 68h, not 72h.
The deadline is also the committed live.end_at. Public Luma retains broad Oct 4–17 wording; precise organizer timing is UNVERIFIED.

## 4. Which strategy should we choose now?

Choose no new scalping/simulator strategy for deployment. Keep the live system unchanged while the funded transition is unverified.
For a deliberate endgame gamble judged only by recovery frequency, the strongest historical candidate is mom72_4h:
rank tradable point-in-time coins by 72h return, hold the single strongest at 99% target exposure, and reselect every 4h on 16UTC anchors.
The source implements one-hour delayed backtest fills, 0.10% taker fees, fixed historical spread and terminal charge.
There is no fitted profit target or stop in this concentrated momentum rule. It can incur very large losses.
An approved first decision must land at 16UTC; changing the model can otherwise trigger an immediate off-schedule decision.
Do not deploy this research class directly: it is not registered/configured in the live runner, and actual wallet, pending orders,
reserve/precision, short-refusal state, sleeve inventory, endgame and liquidation must first be reconciled.

## 5. Is the 20% latency penalty worth paying?

No demonstrated reason to pay it. The user confirmed a WhatsApp 20% penalty update; the calculation formula was not supplied.
Current repository rules prohibit external-price latency arbitrage, and no latency strategy or order experiment was run.
Conditional arithmetic: subtract 20 percentage points from round return => 42.86%/45.24% gain needed from 84k.
A 20% haircut on final equity => 48.81%/51.79%. A 20% haircut only on positive round profit => 19.05%/22.02%.
A haircut on incremental strategy profit gives different numbers again; see penalty_sensitivity.csv.
These are sensitivity cases, not competing interpretations asserted as official rules. No stale-price trade is disguised as directional.

## Historical risk and uncertainty

All 2025–Sep2026 results are spent historical checks. There are 634 daily starts, about 212 disjoint paths, not 634 independent experiments.
The earlier gate screen selected settings on 2022–24, and its later-period outcomes were already inspected before this mission.
Our corrected comparison uses cash starts, signed parent targets, 1h lag, fees/spread and exact 68/72h horizons.
The old gate script used continuous paths and clipped parent shorts; its 8% benchmark is not current qualifying probability.
The inherited parent simulator exceeds 100% marked gross in 110/634 check windows (maximum 107.46%).
This is a limitation of its historical exposure drift, not evidence about current live holdings or a permission to breach the cap.
The five concentrated long candidates remain below 100% marked gross; the slower shorts remain below 53%.
The parent comparison is therefore not a certified compliant execution baseline. Group cap diagnostics are retained in the CSV.

| Candidate |68h gate0 proxy|68h gate2 proxy|68h median|P(loss>=10%)|Worst68h|72h P(>=19%)|CS mean diagnostic|
|---|---:|---:|---:|---:|---:|---:|---:|
|mom72_4h|7.3%|6.5%|-2.88%|27.6%|-65.12%|9.1%|2.652|
|mom24_24h|6.5%|5.4%|-2.40%|17.2%|-32.34%|6.9%|2.688|
|mom168_4h|6.3%|5.0%|-2.89%|21.5%|-68.88%|6.3%|1.780|
|mom24_4h|6.2%|5.0%|-3.09%|26.3%|-38.20%|6.2%|2.427|
|break24_trail4_hold24|3.8%|3.2%|-1.57%|8.5%|-25.66%|3.9%|1.445|
|book_e20combo_brk_cash|0.9%|0.8%|-0.34%|1.9%|-15.36%|1.1%|1.226|
|slow_short24|0.9%|0.8%|-1.20%|4.4%|-16.04%|0.9%|1.143|
|slow_short72|0.3%|0.3%|-1.03%|5.4%|-39.04%|0.5%|0.901|
|slow_short168|0.2%|0.2%|-0.31%|3.2%|-18.81%|0.2%|1.321|

mom72_4h's loss of 10% frequency is 27.6%, versus 1.9% for the committed parent.
Its conditional purged-quarter bootstrap gate0 range is 3.6% to 11.2%.
This 26-candidate range is conditional for one metric/horizon/regime. It is not a joint guarantee across all columns or project-wide search,
and there are few calendar clusters. No live probability, certainty or current-market recommendation is inferred.
BTC-negative 7d regime rows are descriptive post-result diagnostics, not a new untouched test or tuned model.

CS mean applies the existing FLOORED.V1 formula: 40% Sortino + 30% Sharpe + 30% Calmar.
Here it has only three daily returns per 68/72h path. It is a short-horizon diagnostic, not the official judge score or a 14-day score.
Hourly CS uses the native marked equity path; terminal liquidation cost is separately included in the gate-return calculation.
Quote-window CS uses net liquidation NAV and no extra terminal charge. Compare CS within a source family, not across those accounting scopes.
Gate ranking does not use CS. The added CS column changed none of the original outcomes or ranks (cs_addition_audit.json).

## Recent actual-quote screen

These are conditional simulations using recorded Roostoo bid/ask/last, not submitted trades.
Current precision and universe are applied retrospectively; exact past listing membership and large-order capacity are unverified.
All quote scenarios enforce one position, 30s observation/execution lag, 5min directional decisions, quantity truncation, 1% reserve,
pending expiration, consecutive maker eligibility, marketable-limit taker fees and terminal bid/ask liquidation.
The partial-maker scenario halves maker inventory and completes residual exits at the market.
Maker eligibility is not proof of queue fills. The quote record cannot resolve queue priority or hidden partial executions.

| Candidate |Oct 14 net return|Closed trips|Fill rate|Net win rate|Average winUSD|Average lossUSD|FeesUSD|
|---|---:|---:|---:|---:|---:|---:|---:|
|short_fade_proxy|-4.20%|36|100.0%|33.3%|921.17|-635.52|6,918.39|
|short_mom5_proxy|-6.65%|41|100.0%|34.1%|753.43|-636.84|7,836.05|
|market60_tt|-10.48%|11|100.0%|18.2%|868.97|-1,357.65|2,045.36|
|last_low_tt|-11.50%|42|100.0%|19.0%|559.52|-469.99|7,914.32|
|rev5_tt|-12.69%|41|100.0%|41.5%|408.75|-818.33|7,585.15|
|break60_tt|-13.06%|21|100.0%|33.3%|359.80|-1,112.55|3,839.25|
|rev5_tm|-13.52%|41|100.0%|39.0%|447.63|-827.25|7,342.12|
|spread_compress_tt|-15.68%|42|100.0%|31.0%|411.03|-724.93|7,512.78|
|bidask5_tt|-15.91%|39|97.5%|33.3%|299.76|-761.99|6,925.13|
|mom5_tt|-15.91%|39|97.5%|33.3%|299.76|-761.99|6,925.13|
|tick_rev2|-20.21%|96|99.0%|30.2%|369.33|-461.47|17,572.26|
|rev5_mt|-20.50%|33|46.5%|27.3%|400.95|-1,004.69|5,419.23|
|rev5_mm|-20.73%|33|47.8%|24.2%|386.16|-952.75|5,153.26|
|tick_mm|-21.00%|60|13.3%|1.7%|148.61|-358.45|9,241.84|
|tick_rev3|-21.38%|96|99.0%|31.2%|336.80|-477.01|17,554.24|
|tick_rev1|-22.03%|96|99.0%|27.1%|372.23|-452.91|17,334.70|
|taker_tick|-86.13%|379|100.0%|0.0%|NA|-227.25|32,881.66|

Fees above are commissions. Spread is already embedded in ask-entry/bid-exit prices; its separate estimate must not be deducted twice.
F1/short-opportunity recall are not inferred from these portfolio/trade results.


## Recent live commits that matter

- 6357531: market buy at ask and resting sell waiting for bid, completing the current execution evidence.
- 670b9be/7e76e3b: old touch-fill scalping hypothesis fails under measured rules; 36 market-buy variants lose.
- c1b521a/4518fe0/197661d: wallet reconciliation and run reset address false cancelled fills; they do not prove strategy profits.
- 92da283: gate-probability benchmarks, now independently checked with cash starts,delay and signed parent positions.
The committed PaperExchange still matches a buy onbid<=limit and can match a sell onmid>=limit.
Those optimistic assumptions remain in paper code even after wallet fixes. This research bypasses that class entirely.
Treat its attractive paper profits as unsuitable deployment evidence until matching is corrected and revalidated. No live source was changed here.

## Cutoff-aware endgame proposal

Use liquidatable portfolio value after observed bid/ask exits and exit fees.
Only consider locking when that net amount exceeds initial equity*(1+estimated regional cutoff+explicit drift buffer).
Do not confuse 3% from today's equity with 3% round return. The committed lock uses 3% round return from day 10.
No cutoff history was available to fit a drift buffer;0/+2/+5% are sensitivity cases, not forecasts.
At the user deadline, block new decisions before liquidation; the ordinary16UTC schedule does not itself close the book at 12UTC.
An approved verification plan would reconcile wallet/shorts/pending orders first, then test only small size and always clean up through a finally path.
No new controlled order test is recommended now because no simulator candidate passed; no orders or restarts were made.

## Evidence files and reproduction

edge_results.csv: all 26 finite candidates, 38 legacy gate settings and 36 old market-buy variants, separated by source_family/scenario/split/hours.
Missing metrics are NA, never zero. Hourly per-roundtrip win/loss/fill metrics are unavailable because targets are not reconciled Roostoo fills.
quote_summary.csv,quote_windows.csv,quote_trips.parquet and audited_quote_traces retain all scenarios and end inventory.
gate_recovery_comparison.csv includes 68/72h cutoffs, loss probabilities, purged ranges and disjoint counts.
transaction_audit.json and observed_log_*_audit.csv retain cancellations, anomalies, duplicates and unmatched inventory.
tick_economics.csv covers 86 observed pairs; 2 of 88 supported pairs have missing quote coverage.
penalty_sensitivity.csv separates all haircut denominators.
Independent verification reproduces 255 quote scenarios and 20,760 phase1 hourly outcomes exactly; all 31,140 outcomes from the 9 hourly models are reconstructed in publication.
The 5 completed phase1 hourly models are numerically identical after correcting 86 off-hour 2018 decision-grid timestamps outside the scored period.
Quote cash/fee ledger discrepancies are below USD 1e-7. Initial failed test/clock outputs were preserved, not hidden.
Publication verification independently reconstructs all 142 CS groups and the hourly marked-gross diagnostics.
Full final core/research tests: 290 pass; additional metric boundary coverage: 18 research tests pass including those overlapping earlier tests.
Raw quotes, trades, cache arrays and logs stay in /home/ubuntu/test/MiniMax/results/book/20261015-simulator-edge-v1.

From this Book worktree, offline reproduction:
python -B -m research.book.gate.simulator_edge.historical
python -B -m research.book.gate.simulator_edge.quotes
python -B -m research.book.gate.simulator_edge.slow_shorts
python -B -m research.book.gate.simulator_edge.verify
python -B -m research.book.gate.simulator_edge.verify_publication
python -B -m research.book.gate.simulator_edge.report
Run heavy jobs via scripts/lock and nice -n 10, <=8 workers. No account client is instantiated by these research modules.

## Sources

Primary public API: https://github.com/roostoo/Roostoo-API-Documents
Official public event/fee/top20 rules: https://luma.com/coghwiyt
Official FAQ link returned 404 during this research; user WhatsApp penalty update accepted without inventing its formula.
Committed organizer one-sided tick-scalping statement: reports/review/20261005-organiser-statement.md
Committed live observations: research/book/roostoo_fills/README.md at 6357531.
The actual EC2 account, cutoff drift and full funded transition remain UNVERIFIED. No live change or guaranteed recovery claim.
