# Penalized latency experiment — 2026-10-15

User now explicitly requests building and testing latency research after the non-latency screen. This supersedes the earlier research priority, but does not establish organizer eligibility or authorize orders/deployment. The reported 20% penalty is accepted; its formula remains unknown. Report all penalty denominators already documented, with no disguise or bypass.

Remote Book feature/latency-gate from fb4e347. Public unauthenticated APIs and offline/paper only. No account client, secrets, signed calls, orders, restarts or merge. Keep all previous evidence and boards.

## Fixed design, before new outcome reads

Five fixed instruments: BTC, ETH, BONK, PEPE, STO, each against USDT externally and USD on Roostoo. Current precision from the previous public snapshot. No fitted best asset.

Four signals: both directions at 25bp and 50bp discrepancy; long-only 25bp; short-only 25bp. Fair price adjusts the external price by a past-only five-minute median Roostoo-mid/external ratio. Require a complete five-minute warmup and at least 15 past observations. This removes persistent currency/venue basis; it is not evidence the venues are economically identical.

Long: adjusted external price / Roostoo ask - 1 exceeds threshold. Short: Roostoo bid / adjusted external price - 1 exceeds threshold. Rank by discrepancy, stable coin tie-break, one position at a time. Long exposure 99%; short 50% proxy. Fee 0.1% each side, quantity truncated and minimum order enforced. No leverage claim for actual short mechanics.

Exit when the directional discrepancy reaches zero, after 120 seconds, or after a 2% adverse executable-price move. Entry and exit wait for the first recorded valid quote at or after the execution delay. No same-observation fills. Terminal full bid/ask liquidation and fee. No mark at LastPrice.

Base order delay 6s; 2s and 12s sensitivities. Double fees and 6s external availability delay are stress cases. The archive external 1s closed trade bar is available only after close + 2s in the base. It is a trade-price proxy, not historical external executable book or known historical packet receipt.

Historical quote dates: Oct 8–12 calibration, Oct 13 validation, Oct 14 spent recent check. Host-clock offset 3.15s base, 0/6s alternatives. These are sensitivity scenarios, not fitted optimal lag. Use Oct 7 only if warmup is needed. Preserve conflicts/duplicates as in prior study. Fixed 68/72h cash starts; overlapping and disjoint counts separate. No actual top20 probability from a few paths.

A new bounded 20-minute two-feed public capture runs independently while implementation proceeds. Decisions use external packets received before Roostoo packet receipt on the same monotonic clock. No clock offset estimation is needed for causal ordering. Public server-time probes characterize clock uncertainty only. Roostoo at most one poll per 12s (five/minute), with no automatic retry. Existing recorder is untouched. Capture establishes observed discrepancies and disappearance; it cannot establish real fills or profitable execution.

Historical and prospective results remain separate. Never label a positive offline result as executable profit. Test future-information rejection, lag, costs, shorts, precision, terminal inventory and penalty arithmetic before implementing the engine.

## New comparator

Read-only feature/gate bfdd185 reports PEPE gains under trade-at-bid whole-order fills. Its strict-through sensitivity loses and no PEPE order was verified live. Include as a conditional comparator, not a verified production alternative.

## Outputs

research/book/gate/latency/: config, tests, pure decision/replay code, public collector, reproduction and report.
Raw files/logs: results/book/20261015-latency-gate-v1.
Publish a separate latency board with explicit latency penalty and evidence flags. Commit research only.
