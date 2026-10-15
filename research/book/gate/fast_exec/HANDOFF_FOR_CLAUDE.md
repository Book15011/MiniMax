# EC2 research handoff for the user's Claude session

The current Book branch is feature/latency-gate on metallurgy-server. Code lives at /home/ubuntu/test/MiniMax/.worktrees/book-latency-gate/research/book/gate/fast_exec. Read CPP_EXECUTION_PLAN.md and RESEARCH.md first.

The user requested a full simple C++ execution service with an independent latency guard, simulation, then a small live pilot. The current artifact contains a tested C++ money/risk/state/timing core and public-only prototype; full native WebSocket/order transport and the actual live pilot are not built/verified yet.

Portable bundle: /home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-v1/fast_exec_public_ec2.tar.gz. Verify its hash against portable_manifest.json. Transfer only this isolated artifact to a new EC2 research directory using the existing approved Session Manager workflow. It contains no bot/credentials/raw data and cannot place orders.

Run these from the extracted bundle, sequentially:
1. bash ec2_cpp_prereq_check.sh
2. bash ec2_public_observer.sh

The first checks g++, curl/OpenSSL/Boost.Beast/JSON headers without installing anything. The second records600s of independently timed public Binance-stream/Roostoo-REST observations, at most15 Roostoo starts/minute, and preserves all failures. It does not read secrets, call signed endpoints, modify services or restart the bot. Use the current bot's Python environment if requests is not in the default Python, by setting MM_FAST_PYTHON to its executable path. Coordinate the shared API budget with the existing bot.

Return the prerequisite result and the new observer output directory/files, or place the public outputs in a new results/book folder on metallurgy-server for Book to analyze remotely. Do not replace prior raw captures or reinterpret rate-limiter waiting as network latency. The original187/548ms already used persistent connections;133ms is REST, not WebSocket delivery delay. The0.5s peak remains a hypothesis pending independent timestamps.

Do not run a manual competition order as a ping/test. The user has authorized a subsequent small live trial; it is proposed atUSD10/entry, one test position, maximum three round trips, only through the autonomous bot's normal order gateway after the preceding stages. That later stage needs one order writer, shared quota, existing-holdings-aware risk, exact fee/quantity reconciliation and freeze-on-unknown behavior. No scaling or model replacement is authorized by this public measurement step.
