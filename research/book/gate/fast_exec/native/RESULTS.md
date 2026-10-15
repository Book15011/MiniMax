# Native execution results — Book, 15 October 2026 HKT

The standalone public research service is built and tested. Feed handling, model calculation, execution permission, exact sizing, serialization and dummy signing run in C++17. The requested end-to-end live system is NOT finished: signed gateway integration, shared account coordination, durable reconciliation and actual EC2 fill testing remain outstanding. No actual order or live-bot change occurred.

## Measured local processing

Frozen source/binary build: commit78cb4f9c440221fd600a24f44bae508e92997cfc, clean tree at build. See build_manifest.json in the result folder for compiler flags, source hashes and binary hash.

The final50,000-cycle benchmark includes book JSON parsing/validation, the pure burst calculation, independent latency permission, fee/risk checks, exact sizing, request serialization and OpenSSL HMAC with a PUBLIC dummy key. Inputs include explicitly synthetic verified order/account data.

| Local processing | Observed time |
|---|---:|
| Median |0.021450 ms|
| p95 |0.025338 ms|
| p99 |0.032691 ms|
| Maximum |1.589314 ms|
| Cycles above1 ms |1/50,000|
| Decision/calculation errors |0|

This does not include source delivery age, IPC to a live gateway, quota waiting, HTTP order transport, exchange processing or fill confirmation. The p99 local preparation target passes; zero misses/perfect scheduling is NOT claimed. A subsecond real fill remains UNVERIFIED.

The initial narrow benchmark excluded the book/history stage. Adding that stage exposed linear repeated history scans: cpu_full/ records median0.084589ms,p990.099557ms,max5.223150ms and3cycles above1ms. The optimized detector maintains the latest eligible reference as a rolling queue; each tick is visited once. Thresholds and signals did not change. Earlier cpu/,cpu_full/,cpu_optimized/ results remain, including all overruns. Timing differences across runs include scheduling noise; no cherry-picked best-run headline or claim of beating another implementation.

## Reliability checks

81 focused tests pass:30new native tests plus51existing latency/core tests. The independently built portable source bundle passes the same30native tests; these overlap rather than add to81. A separate AddressSanitizer/UndefinedBehaviorSanitizer build also passes all30native tests with no reported sanitizer failure; that is another overlapping run.

Coverage includes120independent Decimal sizing-oracle cases, prior400core oracle cases, fee rounding, request bytes/dummy HMAC, invalid precision/overflow, stale/future inputs, reserved exit quota, account counter bounds, duplicate IDs, timeout freeze, monotonic cumulative partial fills, cancellation after a partial fill, malformed/mismatched acknowledgments and exact full-fill quantities.

Actual local HTTP fixtures exercise one dummy POST, complete/pending/partial/canceled/rejected replies, HTTP500, an inconsistent fill and an expiring200ms response timeout. They stay on127.0.0.1 and do NOT call a signed competition endpoint. Unknown results freeze the simulated order state; orders are not resent. A mocked FILLED is not an actual competition fill or proof of account inventory.

The installed native HTTP/JSON/OpenSSL libraries provide TLS, parsing and crypto. No homemade TLS/crypto and no runtime Python are involved. A narrow WebSocket adapter is tested with fragmented/coalesced text, ping/pong, masking, handshake validation and malformed frames. See ABI_SOURCES.md for exact primary references and deployment ABI limits.

450deterministic admission scenarios use opportunity windows0/250/500/750/1000ms and delay cases50/187/548/999/1000ms, fresh/stale inputs and clock bounds.35admitted and415rejected match the independent arithmetic oracle exactly. These are chosen test cases, NOT a market success probability. The187/548ms inputs are scenarios based on the supplied GET measurements, not a measured actual-order latency distribution.

## Prospective public evidence

The corrected180-second run was frozen at e5657b9 before its market observations:
-20,205valid book updates;16burst episodes.
-45public GET requests,0request failures,0feed errors; audit writer healthy.
-Maximum15starts in any rolling minute; minimum spacing4000.041982ms.
-Public GET RTT median599.774338ms and p951551.805809ms on metallurgy-server.
-16execution rejections because actual order timing is unverified;0eligible entries,0orders and0signed calls.
-Simulated/actual incremental cash gain0; no trading accuracy,F1,CS or capacity score is available.

A separate Python reference reproduced every burst flag. The final optimized native binary also replayed all20,205received updates with zero signal disagreements. That proves programming agreement on this capture, not trading accuracy or future profitability.

The earlier180-second run remains in prospective/:22,817books,10episodes,45GETs and two feed-connect timeouts before connection. Those failures are retained. Its older timestamp implementation is not substituted for the corrected run. The original supervisor's public trials and all earlier negative latency studies also remain unchanged.

Receipt/send times are independent and monotonic. Sparse Roostoo responses are not interpolated into fabricated subsecond prices. These lab observations cannot establish a0.5-second lag or represent the EC2 network path.

## What the EC2 measurements mean

The reported187ms median/548ms p90 already used a persistent Roostoo session; the timer includes quota waiting and read-only retries.133ms Binance refers to REST round-trip time, not WebSocket delivery age. The0.5s/correlation0.77 estimate came from sequential reads and interpolation. It is a research hypothesis.

The native calculation now costs a tiny part of a500ms scenario. It does not remove network tails, a newly required quote request, fee/spread costs, unknown fills or the timing-estimation uncertainty. Adding medians is not a measured joint execution percentile.

The portable source-only bundle and public EC2 runner are ready. Follow EC2_HANDOFF.md using the user's existing Session Manager session. That session has not been accessible to this Codex task.

## Conditional50-hour return math

No reliable positive expected return can be supplied yet. The entry gate is closed; if it stays closed for50hours, this component adds0% before any account-level competition penalty. That is an inactivity result, not a forecast for the live portfolio.

For intuition only, assume50completed round trips in50hours,USD1,000cash per entry, aUSD100,000account,10bps fee on each side and an additional5bps of round-trip adverse movement/spread/slippage. Keep capital fixed; assume all stated fills occur. These conditions have NOT been observed for this strategy.

| Assumed gross captured move before execution friction | Net gain over50trips | Account return |
|---|---:|---:|
|0bps|−USD124.85|−0.12485%|
|10bps|−USD74.95|−0.07495%|
|30bps|+USD24.85|+0.02485%|
|50bps|+USD124.65|+0.12465%|

Formula per completed long round trip: cash_budget × [(1 + retained_move − additional_friction) × (1 − exit_fee)/(1 + entry_fee) −1].
Under these assumptions the retained move must exceed25.02002bps merely to break even. A momentary external price gap or minute high is not the retained move at an executable exit.

return_50h_scenarios.json contains20explicit sensitivities, including0/10/50/100completed trips. It does not assign probabilities, imply those trade counts occur, scale the chosen historical log's gain to50hours or mix these numbers into model rankings.

The reported20%competition penalty is accepted, but its trigger/formula remain unknown. A20%haircut on positive profit and a20%account-equity penalty are very different; neither is silently applied to this table. The scenarios are trading cash results before that unresolved adjustment.

## Location and remaining work

Source: /home/ubuntu/test/MiniMax/.worktrees/book-latency-gate/research/book/gate/fast_exec/native/
Results: /home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-native-v2/
Status board: /home/ubuntu/test/MiniMax/results/scoring/leaderboard_fast_execution.md
Source-only EC2 package: fast_exec_native_ec2.tar.gz with native_package_manifest.json.

The user already authorized a small pilot. Its execution still needs the normal autonomous gateway/single writer, shared account quota, actual account and pair metadata, real order timing, restart reconciliation and verified EC2 access. The public CLI has no credential loader and cannot place live orders. Pilot defaults remainUSD10per entry, one test position, at most3round trips and the stated stop conditions; these limits do not guarantee a maximum loss.

No deployment recommendation, positive return forecast, winner comparison or completed-live-test claim is supported. Existing main/live models and numeric leaderboards are unchanged. Preserve the85% shortfall, BCH29/30coverage failure, adaptiveOFF and all previous failed studies.
