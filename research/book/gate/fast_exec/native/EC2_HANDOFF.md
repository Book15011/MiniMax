# EC2 handoff: native public test and remaining pilot integration

Use the existing Session Manager/Claude EC2 session. Codex has no EC2 connection and has NOT placed any actual order. The user has already requested a small live pilot; this is an access/integration prerequisite, not another permission request.

Source-only bundle on metallurgy-server:
/home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-native-v2/fast_exec_native_ec2.tar.gz
Verify its SHA256 against native_package_manifest.json before running. Transfer only this reviewable research bundle through your approved existing route; no API keys, .env or live account output belong in chat.

In the extracted fast_exec directory, first run the public-only native CPU test with a new output path:
    MM_NATIVE_RESULTS=/absolute/new/ec2-native-cpu bash ec2_native_public.sh cpu
Then run a separate public-only10-minute shadow test:
    MM_NATIVE_RESULTS=/absolute/new/ec2-native-shadow bash ec2_native_public.sh shadow
Do not overlap this with the old observer/matrix: each uses about15publiccalls/minute. Coordinate the existing bot/account quota as applicable. The script installs nothing and changes no bot/service. It needs g++17 plus libcurl.so.4, libjson-c.so.5 and libcrypto.so.3 runtime ABIs. If missing, preserve the error and have the existing EC2 operator resolve dependencies; do not silently swap ABI versions.

Return cpu/cpu.json, public_shadow/summary.json and event JSONL via the project's approved artifact path. These timestamps are public and no headers/keys are logged. The source feed has no bookTicker event timestamp, so source delivery age remains unmeasured. A public GET RTT is not an actual order fill RTT.

Before the already-requested live pilot:
1. Integrate native decision output with the existing autonomous bot's single order writer and authoritative shared account call coordinator. Do not start a competing script/order writer. No signed/manual competition API command is supplied.
2. Wire current account equity/cash/gross/position state, exchange pair precision/minimums, real order latency samples, durable reconciliation and exit priority. The native CLI mock protocol uses simulation field names, NOT a Roostoo adapter. Never set verified_order_stats=true from public ticker timings.
3. Existing order gateway keeps credentials/signing and its no-retry rule. Order timeout -> reconcile and freeze new entries. Acknowledgment alone does not prove inventory/fill.
4. Pilot scope remains parent PILOT_SPEC:USD10 maximum entry, one test position, at most3completedroundtrips, no scaling, stop new entries on unresolved orders/deadline/quota conflict orUSD0.25 cumulative test loss threshold. This stop threshold cannot guarantee a maximum loss.
5. Count real feed-receipt-to-FILLED elapsed time, incomplete fills, Role/fees, actual entry/exit prices and test inventory reconciliation. Report every failure. If no genuine qualifying opportunity appears, report no trade rather than force one.

The native service/local mock tests are ready. Live gateway wiring, restart recovery and actual EC2/pilot evidence remain outstanding. No source patch was merged and the existing live strategy remains unchanged.
