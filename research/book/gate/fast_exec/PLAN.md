# Book: simple native execution research and prototype

User request: research first, then build the simplest correct low-latency prototype for the existing EC2. Target: a qualifying external feed event to a confirmed FILLED response in less than 1,000ms. This is a target, not a promise about a public network or resting order.

## Research decisions

1. Keep market data on one persistent Binance public WebSocket. Use received bid/ask updates and monotonic timestamps; never a future trade high. A bookTicker event lacks a source event timestamp, so receipt freshness is not proof of source freshness. Do not invent exchange latency.
2. Use C++17, established TLS/HTTP/WebSocket libraries, one state owner, and reusable HTTPS connections. Avoid fresh DNS/TCP/TLS setup on each decision. Compare native cold/warm HTTP1/HTTP2 against fresh/reused Python requests before attributing speed to language. HTTP2 is measured, not presumed faster or supported.
3. Fast path: decode -> validate freshness and risk -> fixed-point quantity -> exact canonical body/signature -> order intent. TLS certificates stay verified. There is no terminal command, credential read or file flush in the timed decision path. Buffered audit output is outside it.
4. There is no documented Roostoo order WebSocket in the available official API. Orders use signed REST; FILLED and PENDING are different outcomes. A 1s timeout does not cancel an order. Unknown outcome freezes new orders for reconciliation; never retry an order automatically.
5. The limit is 20 Roostoo calls per minute per process and30/account, including quotes/status/cancels/orders. A continuous20/min quote loop samples at best every3s on average. Event-triggered quotes plus reserved order/exit/reconciliation calls are the useful simple alternative. The existing bot needs one shared account budget before integration. Never create multiple keys/processes to evade this limit.
6. EC2 is documented as Sydney and Session-Manager-only, one permitted instance. The user is arranging a public-only EC2 benchmark. Build/test on metallurgy-server meanwhile; do not touch the live bot or assume lab measurements describe EC2. ENA Express needs supported/configured endpoints and AWS routing; it is not a generic speed switch for an external public API. Do not change instances, kernel settings or networking without concrete evidence and authorization.
7. A faster loop is not evidence of positive expected return. Keep price/fee/fill validation separate. Start with market-cost assumptions on both sides; maker savings require observed fills.

## Bounded implementation and evidence

- Write money, canonical request, stale-feed, rate-budget and ambiguous-order tests before implementing them. Native exact fixed-point integers, checked arithmetic, Python Decimal oracle. No float money sizing.
- Build native request preparation, state/risk gates and received-book processing; mock-only order acknowledgment path. Public transport has a fixed GET allowlist and no credentials or order endpoints. The eventual production gateway needs owner review; live integration is outside this experiment.
- Local timing distributions: parse/decision/quantity/body/HMAC, plus local mock request/response, with failures and rejection counts. Do not call simulated fills actual fills.
- Public matrix: 60 ticker requests,10 per variant (Python fresh/reused HTTP1 and native fresh/reused HTTP1/HTTP2), interleaved, at least4s between Roostoo request starts. Three clock probes counted in the same schedule. Save errors, actual protocol, connection reuse, DNS/connect/TLS/TTFB/total where available. No endpoint/route or sample selection after outcomes. Small-sample percentiles are descriptive only.
- Received-book shadow test on the14 timed log coins; bounded duration, no orders. Strict freshness/fee/budget gates. Record stage timing and missed/rejected opportunities, not only successful fast cases.
- Prepare a reproducible public-only EC2 command/bundle. EC2 benchmark must report the same boundaries and actual host provenance. Actual decision-to-filled latency remains UNVERIFIED until approved automatic order measurements exist through the bot's gateway.
- Report median,p95,p99,max, failures, deadline misses and cold/reconnection cases separately. A successful parse or HTTP200 is not a fill. Keep previous negative results and the20% penalty uncertainty.

## Sources checked October15

- Roostoo REST endpoints, signing, server time and order statuses: https://github.com/roostoo/Roostoo-API-Documents
- Binance market-data stream, bookTicker, combined streams, ping/pong and limits: https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md
- Connection reuse and TCP_NODELAY (already enabled by default): https://curl.se/libcurl/c/CURLOPT_FRESH_CONNECT.html and https://curl.se/libcurl/c/CURLOPT_TCP_NODELAY.html
- HTTP negotiation/fallback: https://curl.se/libcurl/c/CURLOPT_HTTP_VERSION.html
- AWS time sync: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/set-time.html
- ENA Express requirements/limitations: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ena-express.html

Work only in Book's feature/latency-gate worktree. Results: /home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-v1. Public research only; no secret reads, signed calls, orders, live changes or main merge. Build outputs/dependency archives/raw evidence remain ignored under results.

## Implementation addendum: dependency evidence
Official APT downloads were interrupted after stalled acquisition; HTTPS Ubuntu package downloads and individual official raw header requests also timed out. Logs remain in the ignored results folder. No global package/runtime was modified.
Build the exact sizing/risk/state core in dependency-free C++17. A thin Python supervisor supplies the installed C-backed JSON/TLS/HMAC facilities, and an isolated libcurl C-ABI binding measures native HTTP1/HTTP2 with connection reuse. This is a C++ core plus supervisor, not a standalone all-C++ trading application. Benchmark the complete supervisor path before any claim that rewriting the remaining network glue matters. A clean full-C++ transport build remains a later option when development headers are available.
The user's EC2 measurements are pending; do not duplicate or interfere with that EC2 job.
