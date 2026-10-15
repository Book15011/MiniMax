# Book simulator-edge protocol —2026-10-15, before new results

Parent feature/gate92da283, incorporating measured-fill research6357531/670b9be/7e76e3b and committed one-sided tick-sleeve amendment.
New isolated feature/simulator-edge; no live edits, orders, secrets, signed calls or merge. Public exchangeInfo/ticker only.
Objective: recovery-gate probability, not long-run mean. Scenario current round return-16%, cutoff0/+2%; actual account/threshold unverified.
Use user-stated Oct18 12UTC endpoint as SCENARIO. Public Luma still saysOct4–17; exact official endpoint remains unverified.
Oct15 16UTC first decision implies68h left;72h stays benchmark. Actual account funded transition is not reconstructed.

## Existing evidence and immutable comparison
Old40 gate candidates'2022–24 discovery /2025–Sep2026 check and old36 market-buy variants are SPENT evidence.
Prior14 recovery trials and all frozen future cohorts remain untouched; no failed model becomes eligible.
Independent verification of this mission is a separate objective, not proof original gates passed.
Read recent live-fill reports as committed evidence; no raw authenticated probe output found locally at inspection.
Do not run fillprobe.py/mkttest.py, sleeve CLI, live runner or another account client.

## New finite quote screen
Recorded Roostoo quotes only. Complete files Oct7–14 hashed;Oct7 warmup, Oct8–12 calibration,Oct13 validation,Oct14 recent24h check.
Oct14 is NOT guaranteed untouched project-wide; no genuine fresh72h holdout exists. No parameter chosen on it.
Use30s completed sampling, recorder offset+3.15s from prior measured study, max60s stale carry,1sample30s execution lag.
Sensitivity60s delay and doubled fees; ambiguous resting buys modeled both ask-cross (strict) and last-at-limit (optimistic proxy).
A touch alone is insufficient: require2 consecutive eligible samples after arrival; no same-observation fill.
Market BUY at ask, SELL at bid; marketable limits taker, resting maker scenario; fixed expiration120s.
Quantity truncated to current exchange amount precision; reserve1% cash. Missing/crossed/nonpositive quotes => no order.
Do not use accounting errors or cancelled FilledQuantity as profits. Close remaining positions at observed bid/ask and taker cost.
One position at a time, directional decisions no faster than5min, holds10/30/60min. One-sided tick loop checks30s and no concurrent buy/sell.
Measured full-book short execution is UNVERIFIED: any quote-short replay explicitly proxy, not executable profit proof.

Fixed quote candidate family:
tick_mm (bid buy/one-tick sell/stop2ticks/expire120s); taker_tick (ask buy/one-tick maker sell/stop2ticks);
rev5_mm,rev5_mt,rev5_tm,rev5_tt (5min decline,30min hold, maker/taker combinations);
tick_rev1/2/3 (last30s bid declines>=1/2/3ticks,10min taker/taker);
mom5_tt (5min returnpositive),rev5_tt as above;break60_tt (above prior60min high);
bidask5_tt (bid and ask rise5min);last_low_tt (last<=bid);
spread_compress_tt (spread below preceding30min median after prior spread above it);
market60_tt (BTC/ETH60min returnpositive and own5minpositive,60min hold);
short_mom5_proxy (own5min negative,30min hold);short_fade_proxy (60minpositive and5minnegative,30min hold).
Price-change entry hurdle: spread +0.2% roundtrip taker cost, fixed before testing.
Signal ranks follow signed return magnitude. Tradable coins from current88-pair public info; tick loops restrictedBONK/PEPE/STO.
Current universe/precision is not historical listing proof. Missing pairs/gaps explicitly reported; never fill missing symbols.
17 named hypotheses; alternate costs/delays/fill rules are sensitivity scenarios, not tuned candidates.
No selective best coin or setting fit on recent check. Report ALL failures in one CSV.

## Corrected hourly gate benchmark
Fixed five concentrated strategies selected from earlier discovery, before new outcomes:
top1 24h,72h,168h momentum rebalance4h;top1 24h momentum daily;24h volume-confirmed breakout/trail4%/hold24h.
Parent baseline retains signed targets, unlike older gate_odds.py clipping negatives.
Same established Simulator, fees/spread,1h lag, cash-start daily16UTC windows68/72h.
Top1 momentum selects from point-in-time universe;99% target cap for fee reserve; no leverage.
Use2022–24 calibration and2025–Sep2026 historical check, remove all boundary-crossing windows.
No fresh or exact-Roostoo label for hourly Binance proxy. Old8% success is not a current probability.
Count independent disjoint paths separately; daily/6h overlapping counts are not independent evidence.
Quarter-cluster conditional bounds account for23 candidates (17 quote+6 benchmark), not project-wide selection.
Full reproduction of existing Simulator money math, including limitations, with no new fill optimism.

## Audit and outputs
Audit logs separately (no merging overlapping CSVs), remove only exact duplicates/known cancellations, quarantine bad numerics/anomalies,
explicitly mark absent order IDs/commission/Role/dates and unmatched inventory; no adjacent-row P&L shortcut.
Every quote strategy: trades,fill rates,wins,average win/loss,EV,costs,DD,72h median/worst,>=19/21.5/25% frequencies where computable.
Empty/not supported metrics are NA, never zero proof. No extrapolated top20 probability without cutoff history.
Inventory every requested track; untestable fields (depth,24h activity,queue,actual large orders) stay unverified.
Penalty20% exact wording not found in repo/public rules; request pending. Latency stays last and forbidden by present repo rules.
Only conditional penalty arithmetic. Never disguise an external-price/stale-quote trade as directional.
Commit code/reports; raw data stay untracked. No deployment recommendation without executable evidence and funded-state transition.
