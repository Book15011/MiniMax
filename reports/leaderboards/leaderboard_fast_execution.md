# Book execution timing research

**Native public service built; live integration and subsecond fills remain UNVERIFIED.** See the [detailed results](/home/ubuntu/test/MiniMax/.worktrees/book-latency-gate/research/book/gate/fast_exec/native/RESULTS.md) and [EC2 handoff](/home/ubuntu/test/MiniMax/.worktrees/book-latency-gate/research/book/gate/fast_exec/native/EC2_HANDOFF.md).

Read this table as engineering evidence. Local processing excludes network/fills. Mock fills are simulated. Zero trades means unavailable trading accuracy/F1/CS, not100%success. This component is not a ranked trading strategy or a verified replacement for the live model.

| Component | Evidence | Result |
|---|---|---|
| Standalone C++17 local pipeline |50,000cycles;median0.021450ms;p990.032691ms;max1.589314ms|Local p99 target passes;1cycle above1ms|
| Money/order/feed regression tests |81focused passes;30portable passes overlap|Pass|
| Synthetic latency permission |450cases;35admitted,415rejected;0oracle mismatches|Test frequencies are not probabilities|
| Corrected180s public shadow |20,205books;16episodes;45GETs;0request/feed failures|0eligible entries;actual order timing unavailable|
| Signal implementation agreement |All20,205updates match independent Python and optimized native replay|Programming check;not trading accuracy|
| Real EC2 feed-to-FILLED time |No real order measured|UNVERIFIED|
| Live gateway/shared quota/restart recovery |Reviewable native component and handoff ready|Integration pending|
| Already-requested small live pilot |USD10entry;max3round trips;not executed|EC2/session and gateway stage pending|
|50-hour expected trading return |No verified opportunity/fill distribution|Unavailable;conditional fee scenarios in detailed results|

The closed gate adds0% if it stays inactive; this does not forecast the live portfolio. Example sensitivity:50completedUSD1,000trips,USD100,000equity,30bps retained move,10bps fee each side and5bps extra friction yields+USD24.85(+0.02485%). These inputs are assumptions, not measured expected returns. Reported20%competition-penalty mechanics remain unknown.

Lab public GET median599.774ms,p951551.806ms; these are not EC2 order measurements. Earlier failures and negative prototypes remain preserved. Main/live code and other numeric leaderboards are unchanged. The ordinary --score command does not certify this execution component.

All artifacts: /home/ubuntu/test/MiniMax/results/book/20261015-fast-execution-native-v2
