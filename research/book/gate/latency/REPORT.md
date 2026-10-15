# Penalized latency experiment — Book, October 15

**Built and tested. No prototype demonstrates a verified repeatable edge; no deployment recommended.**

Scope: this six-second-resolution screen on BTC/ETH/BONK/PEPE/STO does not settle a one-second execution opportunity.
Its fee pattern and conditional matched cash gains warrant a different declared test. No actual subsecond order-processing delay has been measured.

## Historical recent-day results

| Prototype | Logic | Oct 14 net gain before penalty | Closed trips | Net wins | Fees (initial USD 100k) |
|---|---|---:|---:|---:|---:|
|latency_both50|Long/short gap >=0.50%|-1.24%|2|0.0%|USD 297|
|latency_long25|Long only gap >=0.25%|-9.89%|25|0.0%|USD 4,707|
|latency_short25|Short only gap >=0.25%|-16.13%|83|0.0%|USD 7,609|
|latency_both25|Long/short gap >=0.25%|-23.56%|104|0.0%|USD 11,191|

Every recent-day clock/cost/delay stress result is nonpositive. Zero return from an idle prototype is not recovery success.
The historical screen uses closed 1s trade bars as external signals and recorded Roostoo bid/ask for execution. It is not a historical external-book or packet-arrival test.
All four hypotheses and thresholds were fixed before outcomes. Parameters are in config.yaml; no best asset or lag was fitted.

## Fresh public packet tests

| Source | Prototype | Net gain | Closed trips | Net wins |
|---|---|---:|---:|---:|
|received_rest_book|latency_both25|+0.00%|0|NA|
|received_rest_book|latency_both50|+0.00%|0|NA|
|received_rest_book|latency_long25|+0.00%|0|NA|
|received_rest_book|latency_short25|+0.00%|0|NA|
|received_stream_book|latency_both25|+0.00%|0|NA|
|received_stream_book|latency_both50|+0.00%|0|NA|
|received_stream_book|latency_long25|+0.00%|0|NA|
|received_stream_book|latency_short25|+0.00%|0|NA|

Even the largest observed basis-adjusted gaps were below the roughly 0.2002% two-taker-fee break-even hurdle:
- rest: maximum 0.0562%; 0 sampled coin observations exceed fees-only break-even.
- stream: maximum 0.0273%; 0 sampled coin observations exceed fees-only break-even.

This explains the zero-trade outcome without relying on the extra 0.25% entry buffer. It applies only at sampled observations; brief moves between them were not observed.
Network measurements are from metallurgy-server, not the actual EC2 trading host. A different route could change timing and needs a separate declared test.

The REST and stream sources are separate samples. REST capture lasted 20 minutes; stream capture 10, each with a five-minute warmup.
The samples cannot establish repeatability or a 68/72-hour recovery probability. Zero trades means unavailable accuracy, not 100% accuracy.
All decisions use external packets received before the Roostoo packet, on one monotonic clock. No future packet or assumed clock correction is used.
Current server-time probes place both exchange clocks roughly six seconds ahead of the host. Historical offset 3.15s and 0s/6s alternatives are sensitivity assumptions.
BookTicker has no event timestamp: exact source-feed age is UNVERIFIED. REST quotes expire after 3s; per-symbol stream books after 30s.
A modeled 2s order still executes at the first observed later quote, typically 6s/12s later. Prices between snapshots are unknown.
No actual orders were submitted. Quote-to-order delay, actual short fills, large-order capacity and refusal states remain UNVERIFIED.

## Trading mechanics

Past-only five-minute median Roostoo-mid/external-mid ratio adjusts persistent venue/currency basis. At least 15 prior observations and five minutes of warmup are required.
Long when adjusted external bid exceeds Roostoo ask by the fixed hurdle; short when Roostoo bid exceeds adjusted external ask by the hurdle. Rank discrepancy, one position.
Long target 99%; short target 50% proxy. Truncate quantity; respect minimum order. Taker fee 0.1% each side.
Exit when directional gap closes, after 120s, or at a 2% adverse executable-price move. Both entry and exit wait for a later eligible observed quote.
Charge spread through actual ask/bid, fees, adverse moves and complete terminal inventory. Never book a fill at LastPrice.

## Recovery and the reported 20% penalty

From round -16%, reaching round 0%/+2% needs 19.05%/21.43% from current equity before a penalty.
All four prototypes have zero qualifying outcomes across four overlapping 68/72h starts, including zero of the two disjoint anchors.
This is an observed failure count, not a zero future-probability estimate. Actual top20 probability remains unavailable.
The WhatsApp 20% penalty is accepted; formula and trigger remain UNVERIFIED. We do not request the wording again.
The hypothetical calculation assumes a penalty triggers when a latency trade fills; no-trade runs do not incur it. Different official treatment would require recalculation.

| Penalty case | Required gain for round 0% | Required gain for round +2% |
|---|---:|---:|
|none|+19.05%|+21.43%|
|subtract_20pp|+42.86%|+45.24%|
|equity_haircut20|+48.81%|+51.79%|
|round_profit_haircut20|+19.05%|+22.02%|
|incremental_profit_haircut20|+23.81%|+26.79%|

No tested latency prototype qualifies before the penalty. Paying it has no demonstrated benefit.
If organizers reduce only a final risk score, these return adjustments do not describe that rule; scoring treatment remains unknown.

## Comparison and choice

Prior mom72_4h remains the strongest spent hourly recovery proxy: 7.3%/6.5% static-gate frequency over 68h, median -2.88%, loss of at least 10% frequency 27.6%, worst -65.12%. It is research only.
Hourly benchmarks and this quote screen use different historical sources. Do not pool their frequencies or present a single comparable global rank.
Newer PEPE maker research at bfdd185 reports +25.2% on a USD 20k allocation over Oct 10–14 under trade-at-bid full fills. Its strict-through scenario loses 51.2%; no PEPE live fill was verified.
Random 50% fill survival does not prove adverse selection or capacity. USD 20k *25.2% is USD 5,040, not 25.2% on the USD 100k account. Scaling and 68h recovery remain unverified.
**Reject these latency prototypes for deployment. No live source, model, holdings, risk settings or bot process was changed.**

## Reading and reliability

latency_results.csv contains all runs, splits, scenarios and conditional penalty-adjusted round returns. latency_windows.csv contains descriptive 68/72h frequencies, downside, disjoint counts and CS.
CS is the existing 40% Sortino /30% Sharpe /30% Calmar formula applied to three daily returns on net liquidation NAV. It is a diagnostic, not the official judge score.
Complete results include winners, losers, net EV per trade, fees, drawdown and entry wait. F1/recall is unavailable without defensible independent opportunity labels.
Actual fill rate, capacity and top20 probability remain unverified; production_eligible is false throughout.
Independent quote/cash/position reconstruction verified 156 runs and 12257 simulated round trips.
304 core/research tests passed before the extra stream framing tests. The expanded latency suite has 18 passing tests; counts overlap.

## Reproduction and sources

Remote Book worktree: /home/ubuntu/test/MiniMax/.worktrees/book-latency-gate
Modules, in order: research.book.gate.latency.data, run, prospective, verify, publish. Run each with python -B -m and its full module name.
Collectors collect and stream refuse to overwrite captures. A fresh experiment needs a newly declared output directory; old evidence stays intact.
Use scripts/lock, Book-owned tmux, nice -n 10 and at most two workers. No account client is instantiated by these modules.
Raw packets, checksum-verified archives, arrays, traces, logs and audits: /home/ubuntu/test/MiniMax/results/book/20261015-latency-gate-v1.
Sources: [official public API](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md), [official stream specification](https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md), [official archive format](https://github.com/binance/binance-public-data).
Measured small-order execution source: research/book/roostoo_fills/README.md at 6357531. No new live fill evidence was generated.
