# Research and first prototype — Book, October15

**Local request preparation passes its timing target. Real EC2 order-to-FILLED timing and profitable latency trading remain unverified.** Full C++ service architecture is in CPP_EXECUTION_PLAN.md. The current running prototype is a C++ core with a thin Python supervisor and installed native libcurl transport; it cannot submit an order.

## What the new EC2 numbers establish

The user reports Roostoo ticker RTT187ms median/548ms p90, Binance REST133ms, and a BTC correlation peak at0.5s/corr0.77. The source was found earlier in an earlier latency study, read without modification.

RoostooClient already keeps requests.Session connections. Its outer timer includes the rate limiter and any read-only retries; a reported48s pause is consistent with the20/min limiter, not necessarily a network stall. Raw stage timestamps are needed to attribute it. Binance133ms comes from urllib REST; it does not measure WebSocket delivery age.

lag.py reads Roostoo before Binance, assigns them one averaged timestamp, interpolates both onto a0.25s grid, and considers only nonnegative lags. These choices can smear or bias a small subsecond estimate. Keep0.5s as a hypothesis, not a fixed guaranteed tradable window.

A ticker GET is not an order POST. Response receipt is later than order arrival; half-RTT is not a verified one-way measurement. The sum of two medians is not a percentile of the full path. A fresh quote request adds another network stage. A cached quote helps only while genuinely fresh. No trade success probability follows from the reported p90.

observe_ec2.py instead records a continuous Binance stream and independently paced Roostoo reads on one monotonic clock. It stores every request send/receive interval, budget waiting separately, and all failures. It does not create fake dense quote observations or execute trades. BTC is primary; the14 timed log coins are retained.

## Simple execution design

The model proposes an intent. A separate native permission check uses received-feed freshness, pessimistic recent application timing, required quote refresh, clock uncertainty, actual price/fee room, exact account risk and the shared call budget. One writer signs/sends once. An unknown outcome freezes entries for reconciliation. Known risk-reducing exits keep reserved priority.

Public server-time heartbeats are useful when idle, inside the same quota. Most health observations should reuse normal quote/order/status traffic. ICMP ping and a separate uncontrolled polling process do not provide the needed application budget.

Use standard TLS/WebSocket/HTTP/JSON libraries. C++ addresses deterministic local logic; the main measured cost is networking. Development headers are absent on the lab and official package/raw-header downloads timed out. The full standalone C++ networking build is not claimed complete. The existing native core compiles without those dependencies.

## Local correctness and timing

51 focused tests pass:400 independent Python Decimal sizing cases, canonical request/HMAC bytes, freshness, fees/risk, call reserves, unknown/pending/canceled outcomes, zero-depth/crossed books, burst episodes and latency admission. Counts overlap earlier suites.

Final complete synthetic path—decode, book validation, native timing permission, native risk/sizing, decimal formatting, canonical body and dummy HMAC—over20,000 events: median28.18us, p9941.38us, max1581.48us. Zero preparations exceeded the5ms local allowance. Earlier runs and their outliers remain saved. This is not a network/order/fill benchmark. The Decimal-only comparator is narrower and must not be used as a language-speed comparison.

The deterministic admission simulator checks200 timing cases and three duplicate-order-state cases. Sixteen timing scenarios are admitted and184 rejected. These case frequencies are not probabilities or strategy returns. Full fill/partial/cancel/reconciliation simulation belongs to the standalone order-service stage.

## Lab public connection experiment

63 requests including three clock probes;60 ticker comparisons,10 per variant. Interleaved order, at least4s between starts. Native libcurl negotiates actual HTTP2 where requested. A cold native case forces a new connection, while library DNS/TLS-session caches can persist; it is not identical to a fresh process. Small-sample percentiles are descriptive.

| Variant | Attempts | Failures | Successful median | Successful max | All attempts >=1s |
|---|---:|---:|---:|---:|---:|
|python_fresh_h1|10|0|1792ms|3523ms|10|
|native_warm_h2|10|1|923ms|3225ms|4|
|native_cold_h1|10|0|1677ms|2430ms|9|
|python_reused_h1|10|0|549ms|2074ms|3|
|native_warm_h1|10|0|920ms|1390ms|2|
|native_cold_h2|10|0|1525ms|2524ms|8|

Connection reuse helps here. Native HTTP2 is not consistently superior. Every variant has deadline misses; one warm-HTTP2 attempt failed. Public GET timing cannot certify order execution, and these lab results do not replace EC2 measurements.

## Event-triggered public shadow run

The initial bounded capture received31,436 valid books over180s after setup. There were15 public Roostoo calls including startup checks,11 completed candidate evaluations and no eligible intents. Nine evaluations exceeded the reserved quote/preparation deadline; two lacked the required fee room. No order or signed/account call occurred.

Initial threshold logic repeated1,458 updates from sustained bursts. It was corrected to emit once per episode, with unchanged10bp/1s threshold; replaying the exact spent stream gives27 episode triggers. The corrected detector is unit-tested; its replay is not a new prospective market trial.

The prototype charges conservative0.10% entry and0.10% exit assumptions plus a5bp extra-cost allowance, requires30bp gross quote room and all freshness/deadline gates. It does not assume maker fills. Portfolio return, model precision/F1 and full-size capacity are unavailable.

The independent saved-observation check confirms78 combined public Roostoo requests, no more than15 in any rolling minute, one matrix failure retained and all11 shadow dispositions preserved. It does not constitute an independent researcher's review or actual fill validation.

## Next stages and live pilot

CPP_EXECUTION_PLAN.md specifies a full C++ service, one execution owner, an independent health gate, timing/fault simulation, corrected EC2 capture, shadow validation, then the user-requested small live pilot through the bot's normal gateway.

The proposed pilot isUSD10 per entry, one test position, at most three round trips, with no size escalation. Unknown orders, quota conflicts, deadline violations or aUSD0.25 cumulative loss threshold stop new entries; known test inventory exits have reserved priority. The threshold is not a guaranteed loss cap. Existing holdings must be included in risk and matched separately from the test delta.

The pilot has not run. A small test establishes mechanics only, not reliable p99, profitability or large-order capacity. No live model, service, source engine or main branch was changed. The reported20% penalty is accepted; its formula and effect on any eventual strategy remain unresolved.

## Evidence and sources

All raw data, logs, simulations and hashes: /home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-v1. No raw data or binary/dependency archive is committed.

Primary references: [Roostoo API](https://github.com/roostoo/Roostoo-API-Documents), [Binance streams](https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md), [libcurl reuse](https://curl.se/libcurl/c/CURLOPT_FRESH_CONNECT.html), [HTTP negotiation](https://curl.se/libcurl/c/CURLOPT_HTTP_VERSION.html), [TCP_NODELAY defaults](https://curl.se/libcurl/c/CURLOPT_TCP_NODELAY.html), [AWS clock sync](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/set-time.html), [ENA requirements](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ena-express.html).

The venue API documents REST order statuses and signatures; it does not promise subsecond fills. bookTicker lacks an exchange event timestamp. ENA Express requires compatible endpoints/routing, so it is not a generic shortcut for a public external API. CPU/compiler/kernel/network changes require measured evidence of benefit.
