# Book: full C++ latency service plan

Goal: correct, simple execution with a measured feed-receipt-to-confirmed-FILLED time below1,000ms. Detect and reject stale opportunities before submission. Network completion cannot be guaranteed; no timeout or acknowledgment is called a fill.

## Architecture
One C++17 service, separate model and execution permission:
1. Feed worker: one verified Binance public WebSocket, received bid/ask timestamps, update-ID checks and heartbeat/reconnect state.
2. Health worker: immutable rolling HTTP timing/clock snapshots. Reuse normal quote/order/status observations; use a public server-time heartbeat only when idle and the shared call budget allows. Track rate waiting separately from HTTP transport. ICMP ping does not substitute for application latency.
3. One execution owner: accepts an expiring model intent, reads one consistent feed/health/risk snapshot, runs exact sizing and fee/price/deadline checks, serializes/signs once and submits once. Bounded queue retains only a current intent; it never accumulates a backlog.
The model never waits for a ping. A BUY signal can be rejected by execution permission. Health failure blocks new entries; known risk-reducing exits get reserved budget and priority. An unknown order outcome freezes entries until reconciliation, without duplicate order or close requests.

Use established OpenSSL/libcurl and Boost.Beast, with a small general JSON parser. Use one configuration file, persistent TLS connections, monotonic stage timestamps and an asynchronous audit writer. No homemade TLS/crypto, per-signal process launch, aggressive system tuning or new cloud instances. The current tested prototype has a C++ core plus Python supervisor; it is not yet this standalone C++ service. Missing development headers/package-download failures are recorded and the full native transport build must be verified on EC2.

## Permission to execute
Require:
- A received and still-current model signal; valid external bid/ask, current Roostoo executable quote and adequate post-fee price room.
- Fresh feed, quote and account state; measured clock uncertainty inside the configured bound.
- A pessimistic timing budget that includes any required quote request, preparation, order transport/acknowledgment, clock uncertainty and safety margin. Fresh cached quotes may avoid a query; stale cache may not.
- A shared account call budget across the existing bot and this path:20/process,30/account, including public quotes, orders, cancels and reconciliation. Reserve exits before admitting an entry.
- Exact pair precision/minimum-order validation; gross exposure including the existing account remains at most equity after fees.
- No pending/unknown conflicting order and no unresolved timeout.

The reported0.5s correlation peak is a research hypothesis, not a fixed order expiry. Recent ticker GET timing is a transport proxy, not actual order timing. The original187ms already uses a persistent client;133ms is REST timing, not WebSocket delivery. A p90 does not identify a trade success rate or outbound one-way time.

## Tests, in order
1. Native unit tests: exact money oracle, signatures/request bytes, all order states, stale/future/reordered inputs, fees, risk caps, shared quota, expired intent and unknown-outcome handling.
2. Timing/fault simulator: synthetic0/0.25/0.5/0.75/1s opportunity windows and observed187/548ms latency cases; delay, timeout, disconnection, duplicate response, rejected/pending/partial fills. Verify no duplicate sends and no late new entry after the admission budget fails. A timing simulator does not prove trading P&L.
3. Correct EC2 public capture: independent continuous Binance stream and paced Roostoo snapshots on one monotonic clock; actual request intervals and failures. No fabricated subsecond observations from interpolation. Compare warmed HTTP1/HTTP2 only on measured tails.
4. EC2 shadow service: frozen signal and unchanged gates, actual received quotes, fee/spread/capacity assumptions and independent reproduction. Record all accepted and rejected opportunities. Simulated returns remain separate from actual fills.
5. Small live pilot, as requested: propose one position at a time,USD10 entry notional, at most three completed round trips, no scaling. Run only through the autonomous bot's normal reviewed order gateway and shared account budget, with no competing order writer. Stop new entries on any unresolved order, deadline violation, quota conflict orUSD0.25 cumulative test loss threshold; close known test inventory with reserved priority and reconcile unknown state first. These are stop conditions, not a guaranteed loss cap. Test only when a genuine qualifying signal exists; no forced profitable-looking trades.
6. Small live results establish mechanics only. Log actual feed receipt, model decision, queue wait, network send/response, server create/finish, Role, fees, fill price and matched test inventory. Confirmed FILLED alone counts as execution; PENDING/cancel/timeout do not. Keep actual returns and timing failures in the research board. Larger-size capacity/profitability remain separate.

## Passing criteria
Local complete request preparation p99 under1ms (already comfortably below that in synthetic tests). No arithmetic/risk/duplicate-order failure. Real fill timing and costs must pass their declared acceptance criteria; short pilot counts cannot establish reliable p99 or perfect future execution. Do not force activation by weakening gates.
The first path is long entry and its risk-reducing exit. Native short_open/short_close require their own collateral/position contracts and tests before use.

## Integration and status
Work as Book in feature/latency-gate. Keep code and pilot instructions reviewable. Preserve main/live model and prior failed studies until the actual integration step is explicitly carried out. The user has requested a small live pilot; do not ask for that authorization again. EC2 execution/access is coordinated through the user's Claude session. Never read or paste credentials into this chat, manually call the competition API, automatically retry an order, merge without reviewer or claim actual live testing occurred on metallurgy-server.
