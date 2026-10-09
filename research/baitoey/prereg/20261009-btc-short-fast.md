# Pre-registration addendum: lower BTC-short triggers (Baitoey, 2026-10-09)

Written while the A-D runs of `20261009-btc-short.md` were in progress, before any A-D or A2/B2 result was seen;
not edited after results; no tuning after results. Same common rules (40% size, 4.5% hourly hard stop, 168-hour time
stop, event block, re-arm, 90-day replay, band 0.10, never long).

Baitoey's request: lower the triggers "so it actually shorts". Known when writing: both triggers below fired at the
2026-10-08 16:00 UTC close and not since; at 2026-10-09 11:00 UTC BTC was 0.88% below its 20-day EMA and 1.9% above
its 10-day low (neither fires). The triggers were chosen knowing this market, so the history is not a fair test of them.

| Variant | Entry at a daily close | Cover |
|---|---|---|
| A2 fast trend (baitoey_btc_short_a2) | close < 20-day EMA x 0.99 and 7-day return < 0 | daily close > 20-day EMA x 1.01, or the stops |
| B2 fast breakdown (baitoey_btc_short_b2) | close < lowest of the previous 10 daily closes | daily close > highest of the previous 5 daily closes, or the stops |

Add-ons **without** the switch gate (the short acts whenever its own rule says so; e20v45's book is scaled to at most
60% gross while it is open): baitoey_e20_btcs_a2, baitoey_e20_btcs_b2.

Scoring, report and reading rule exactly as in `20261009-btc-short.md` (add-ons against e20v45). The code change that
adds these parameters must leave A-D's trades identical (checked against the trade lists saved before the change).
