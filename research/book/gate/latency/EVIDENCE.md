# Evidence and corrections — October 15

Book branch feature/latency-gate, based on fb4e347. Read main:AGENTS.md first. The user's later explicit request authorized penalized latency research; it did not establish organizer eligibility or authorize signed calls, orders or deployment.

## Frozen decisions and checks

Protocol/config/collector committed at c7742f1; causal money tests at c799f9b before core implementation; finite historical implementation frozen at 9e2c23d. Four fixed hypotheses, five assets and seven historical scenarios. No result-selected threshold, asset or clock lag.

304 core plus research tests passed in 196.90 seconds before the extra stream/positive-path coverage. Expanded latency suite: 18 tests passed in 0.45 seconds, overlapping the prior tests. Do not add these counts.

Independent saved-quote/cash/position reconstruction checked 156 runs and 12,257 simulated round trips. Maximum cash-ledger discrepancy USD 3.4560798667371273e-10; fee discrepancy USD 5.820766091346741e-11. Return/drawdown discrepancies below 1e-10. This is independent calculation, not independent researcher review or proof of actual executions.

35 daily external archives passed their official SHA256 checksums. Original Roostoo quote hashes and cleaning counts are retained in data_audit.json. The archive has no historical packet receipts or external best book; old clock offset remains unverified.

## New public measurements

- REST: 795 successful external snapshots and 100 successful Roostoo snapshots over the bounded 20-minute capture.
- Stream: 151,409 external book packets and 100 successful Roostoo snapshots over the bounded 10-minute capture.
- Three public clock probes per venue place both exchange clocks about six seconds ahead of the host.
- Receipt ordering uses one monotonic clock. No external packet received in the future is available to a decision.
- Fresh basis-adjusted maximum gaps are below the 0.2002% fee-only hurdle: about 0.0562% REST and 0.0273% stream, across the fixed five instruments at sampled observations.
- No fresh base-case trades qualified. This is not a profitable trial and not a statistically reliable current-market probability.
- No secrets, credentials, signed account calls, orders, restarts, merges or live modifications.

The collector records Git HEAD at completion, so it can differ from the start commit while other research files were committed. collect.py remained byte-identical to its initial c7742f1 version; raw and source hashes retain exact provenance.

## Failures preserved

Initial money and stream tests failed on missing implementations, as expected before implementation. Red logs are retained.

PyPI and GitHub dependency acquisition timed out; shared dependencies were not changed. A standard certificate-verified RFC6455 public handshake succeeded. The small tested reader received the stream without third-party dependencies or authentication/control bypass. Dependency and handshake probes remain separate JSON evidence.

A local orchestration syntax error and a shell-quoting error occurred before remote code executed; both were corrected without affecting signals or outcomes. No failed market trial was discarded.

## Limits and decision

Four overlapping 68/72-hour paths give two disjoint anchors, all failing the recovery hurdle even without a penalty. Current top20 probability remains unavailable.

The reported 20% WhatsApp penalty is accepted. Its formula and trigger remain unknown. All named denominators are separate scenarios, never silently interchangeable. The penalty cannot rescue negative gross results.

Fresh captures are short, partly separate/overlapping, limited to five instruments and conducted from metallurgy-server, not live EC2. Exact order delay, intermediate prices, actual short mechanics, full-size impact/queue/capacity, current funded transition and organizer eligibility remain unverified.

New PEPE maker research bfdd185 is a conditional comparator; its strict-through sensitivity loses and no PEPE live fill was verified. It is not a verified replacement.

No candidate is production eligible. The earlier target, BCH coverage failure and adaptive-scoring failure are unchanged. This finite latency test is complete; the broader recovery/top20 goal has not been achieved.

Raw evidence and final manifest: /home/ubuntu/test/MiniMax/results/book/20261015-latency-gate-v1.
