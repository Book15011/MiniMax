# Standalone native execution research service

Built as Book on feature/latency-gate. All runtime logic in this directory is C++17; Python only builds, tests and summarizes artifacts. This is a public shadow/replay service with a simulated order state machine. Signed execution through the existing live gateway and shared account coordinator is NOT integrated; real EC2 fills and 50-hour profitability remain UNVERIFIED. Never describe protocol/mock results as actual trades.

Build, from Book's worktree:
    .venv/bin/python -B -m research.book.gate.fast_exec.native.build
Tests:
    .venv/bin/python -B -m pytest -q research/book/gate/fast_exec/native/test_service.py

Binary: /home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-native-v2/build/fast_exec_native
Configuration: research/book/gate/fast_exec/config.json (absolute path recommended).
Modes:
- protocol CONFIG: line-delimited JSON simulation/replay. size, prepare (dummy HMAC), book, decision, quota, begin, timeout, ack. Nothing is sent to Roostoo.
- cpu CONFIG NEW_OUT ITERATIONS: complete native preparation microbenchmark with explicit synthetic timing/account inputs; no fill/network inference.
- shadow CONFIG NEW_OUT SECONDS: concurrent public WS plus paced GET snapshots, monotonic timing and bounded asynchronous JSONL audit; 60..1800seconds. The execution gate stays closed without verified actual order statistics.
- order-fixture CONFIG http://127.0.0.1:PORT/fixture: one dummy order POST to a local simulator with an expiring 1..1000ms timeout, cumulative state validation and no resend; never a competition API.
- http-fixture / ws-fixture CONFIG http://127.0.0.1:PORT/fixture: local transport tests only.

One feed thread, one paced public-quote thread and one audit writer. The feed does not wait for health probes. Model update IDs, message sizes, burst episodes, deadlines, exact money and cumulative fills are validated. Unknown order outcomes block another begin; retries are absent. The simulated process limiter reserves3 calls for exits; account usage must be supplied by the eventual authoritative coordinator. It is NOT a cross-process/account coordinator.

The pure Detector::update function is shared by protocol replay and prospective shadow. Parameters retain existing config thresholds. decision() rejects unverified order timing, stale/future account/feed/quotes, inadequate fee room or equity and pessimistic deadline budgets. The model is a frozen upward-burst diagnostic; no short contract or profitable edge is inferred from execution speed. No stale-price or minute-high return is assumed.

Current boundaries: no live order gateway adapter; no actual account/position reconciliation; no durable restart recovery; state-machine IDs/cumulative filled quantities are simulation contracts, not claimed Roostoo response fields. A restart cannot resume a live session. All those contracts need validation before a requested live pilot. Paper/mock tests prove programming behavior under their specified inputs only.

See ABI_SOURCES.md for dependency choices, and the parent CPP_EXECUTION_PLAN.md/PILOT_SPEC.json for the already-requested live test scope. EC2 access remains through the user's separate Session Manager session. Do not run both old/new observers together at15calls/min each on a shared quota.
