# Book low-latency research

Current standalone native results (15October2026): see [native/RESULTS.md](native/RESULTS.md) and [native/EC2_HANDOFF.md](native/EC2_HANDOFF.md). The C++ public service is now built; live gateway/EC2 fills and50-hour profitability remain unverified. The older supervisor results below are preserved history.

Read CPP_EXECUTION_PLAN.md for the full C++ architecture and staged simulation/EC2/small-live plan. RESEARCH.md gives measured results and the audit of the supplied EC2 benchmark. Actual subsecond filled orders are not yet verified.

Built: exact C++17 sizing, risk, rate/state and independent timing permission; a thin public-only supervisor; native persistent HTTP1/HTTP2 comparisons; event-triggered shadow prototype; timing/fault admission simulator. The standalone C++ feed/order service and live pilot are subsequent stages, not completed features.

## Files
- core.cpp: compiled exact money/risk/state/latency logic.
- config.json: frozen parameters. Fees, freshness and quota gates are not lowered to force trades.
- signal.py/shadow.py: received-price burst hypothesis and public-only event-triggered quote/intent test.
- observe_ec2.py: corrected concurrent public measurement, independent feed/request timestamps and no interpolation.
- CPP_EXECUTION_PLAN.md: whole native service and small live pilot specification.
- RESEARCH.md: complete measurements, failures, limits and sources.

## Reproduce on metallurgy-server
Work in /home/ubuntu/test/MiniMax/.worktrees/book-latency-gate:
1. python -B -m research.book.gate.fast_exec.build
2. python -B -m pytest -q research/book/gate/fast_exec research/book/gate/latency
3. python -B -m research.book.gate.fast_exec.simulate
4. python -B -m research.book.gate.fast_exec.verify
Use the shared .venv Python. Heavy jobs use Book-owned tmux, scripts/lock and nice10. Public captures refuse to overwrite earlier results. A new capture requires a new output folder; never silently extend or relabel a spent sample.

## EC2 handoff
The ignored results folder contains fast_exec_public_ec2.tar.gz and portable_manifest.json. It contains isolated research source/config/tests, no bot or credentials. It does not enable live orders.

After the operator transfers and extracts the bundle, ec2_cpp_prereq_check.sh checks the full native development headers without installing anything. ec2_public_observer.sh records600s of public data using the existing Python/requests runtime. It neither restarts the bot nor reads keys. Run public measurement jobs sequentially and coordinate the account call budget with the existing bot.

The prototype bundle can compile its native core separately:
MM_FAST_RESULTS=/absolute/research/results python3 -B -m fast_exec.build
Then run python3 -B -m fast_exec.benchmark --out /absolute/new/output --core /absolute/research/results/build/core.so --host-role ec2 for the same public matrix. Requires g++17-compatible compiler, Python>=3.9, requests and installed libcurl runtime. A public GET result is not an order acknowledgment or fill.

The operator must not run a manual signed order as a latency benchmark. The requested small live pilot belongs to the autonomous normal order gateway, after the preceding implementation and tests; its proposed limits are in CPP_EXECUTION_PLAN.md. No repeated approval of the user's existing small-pilot request is needed, but this bundle does not supply EC2 access or finish that integration.

Results: /home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-v1.
Old trading-model leaderboards and all earlier156 latency simulation rows are unchanged.
